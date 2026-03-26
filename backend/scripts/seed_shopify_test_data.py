#!/usr/bin/env python3
"""Seed a Shopify dev store with realistic Visionarias-style e-commerce data.

Populates products (offer ladder), customers (Latin American), and orders
(paid, discounted, refunded, partially_refunded) spread across the last
45 days so the ShopifyProvider ETL pipeline can extract all 12 sales metrics.

Usage (inside Docker — auto-retrieves credentials from DB):
    python scripts/seed_shopify_test_data.py --from-db --tenant-slug visi-test-6

Usage (manual credentials):
    python scripts/seed_shopify_test_data.py \
        --shop-domain nicolify-testing.myshopify.com \
        --access-token shpat_XXXX

Rate limits:
    Dev stores cap orderCreate at 5/min.  The script batches 5 orders
    then sleeps 62 s.  Total runtime ≈ 22 min for ~90 orders + refunds.
"""

import argparse
import base64
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# ── Shopify GraphQL endpoint ────────────────────────────────────────────
API_VERSION = "2026-01"


def gql_url(shop: str) -> str:
    return f"https://{shop}/admin/api/{API_VERSION}/graphql.json"


# ── Products — Visionarias Offer Ladder (12 products) ───────────────────
# (title, price, requires_shipping, weight_for_random_selection)
NEW_PRODUCTS = [
    # LOW TICKET — weight 3 (bought most often)
    ("Ebook: Guia de Ventas Online",        "19.00",  False, 3),
    ("Pack Plantillas para Redes Sociales", "29.00",  False, 3),
    ("Webinar Grabado: Funnels de Venta",   "37.00",  False, 3),
    ("Mini Curso: Crea Tu Marca Personal",  "47.00",  False, 3),
    # MID TICKET — weight 2
    ("Curso: Emprende desde Cero",          "97.00",  False, 2),
    ("Workshop: Storytelling para Ventas",  "149.00", False, 2),
    ("Curso Avanzado: Email Marketing",     "197.00", False, 2),
    # HIGH TICKET — weight 1
    ("Programa: De Proposito a Prosperidad", "497.00", False, 1),
    ("Coaching Grupal 12 Semanas",          "347.00", False, 1),
    # PREMIUM — weight 0.5
    ("Mentoria 1:1 Premium (3 meses)",      "897.00", False, 0.5),
    ("Aceleradora VIP: Escala Tu Negocio",  "697.00", False, 0.5),
    # PHYSICAL (for shipping_revenue metric)
    ("Kit Branding Fisico + Workbook",      "67.00",  True,  1),
]

# ── Customers — 28 Latin American names, ~80% female ────────────────────
CUSTOMERS = [
    # Female (~22)
    ("María",     "García Flores",    "maria.garcia@example.com",      "+5215551000001"),
    ("Ana Lucía", "Martínez Ríos",    "ana.martinez@example.com",      None),
    ("Sofía",     "Hernández Luna",   "sofia.hernandez@example.com",   None),
    ("Valentina", "Torres Vega",      "valentina.torres@example.com",  None),
    ("Camila",    "Rivera Castillo",  "camila.rivera@example.com",     None),
    ("Isabella",  "Díaz Paredes",     "isabella.diaz@example.com",     "+5215551000011"),
    ("Lucía",     "Jiménez Salazar",  "lucia.jimenez@example.com",     "+5215551000013"),
    ("Fernanda",  "Álvarez Rojas",    "fernanda.alvarez@example.com",  "+5215551000015"),
    ("Gabriela",  "Castro Medina",    "gabriela.castro@example.com",   "+5215551000017"),
    ("Mariana",   "Vargas Peña",      "mariana.vargas@example.com",    None),
    ("Catalina",  "Moreno Quispe",    "catalina.moreno@example.com",   "+5115551000021"),
    ("Daniela",   "Huamán Solís",     "daniela.huaman@example.com",    "+5115551000022"),
    ("Ximena",    "Gutiérrez Paz",    "ximena.gutierrez@example.com",  None),
    ("Renata",    "Mendoza Cruz",     "renata.mendoza@example.com",    "+5725551000024"),
    ("Paula",     "Ospina Restrepo",  "paula.ospina@example.com",      "+5725551000025"),
    ("Alejandra", "Sánchez Duarte",   "alejandra.sanchez@example.com", None),
    ("Natalia",   "Figueroa Lagos",   "natalia.figueroa@example.com",  "+5415551000027"),
    ("Florencia", "Bianchi Romero",   "florencia.bianchi@example.com", "+5415551000028"),
    ("Lorena",    "Palacios Aguilar", "lorena.palacios@example.com",   None),
    ("Andrea",    "Córdoba Navarro",  "andrea.cordoba@example.com",    "+5215551000030"),
    ("Mónica",    "Ramírez Herrera",  "monica.ramirez@example.com",    None),
    ("Paola",     "Vásquez Delgado",  "paola.vasquez@example.com",     "+5725551000032"),
    # Male (~6)
    ("Carlos",    "López Fuentes",    "carlos.lopez@example.com",      "+5215551000002"),
    ("Luis",      "Rodríguez Pinto",  "luis.rodriguez@example.com",    "+5215551000004"),
    ("Diego",     "Ramírez Ochoa",    "diego.ramirez@example.com",     "+5215551000006"),
    ("Andrés",    "Flores Cárdenas",  "andres.flores@example.com",     "+5215551000008"),
    ("Javier",    "Gómez Paredes",    "javier.gomez@example.com",      "+5215551000010"),
    ("Emilio",    "Ortiz Bravo",      "emilio.ortiz@example.com",      "+5215551000018"),
]

# ── Discount codes ──────────────────────────────────────────────────────
DISCOUNT_CODES = [
    # (code, type, value, description)
    ("BIENVENIDA10",  "percentage", 10, "Welcome discount"),
    ("LANZAMIENTO20", "percentage", 20, "Launch promo"),
    ("VIP30",         "percentage", 30, "VIP customer"),
    ("BLACKFRIDAY40", "percentage", 40, "Seasonal sale"),
    ("CUPONREGALO",   "fixed",     20, "Gift voucher — $20 off"),
]

# ── Shipping addresses (Latin America) ──────────────────────────────────
SHIPPING_ADDRESSES = [
    {
        "firstName": "María", "lastName": "García",
        "address1": "Av. Javier Prado Este 4200", "city": "Lima",
        "province": "Lima", "zip": "15023", "countryCode": "PE",
        "phone": "+51999000001",
    },
    {
        "firstName": "Camila", "lastName": "Rivera",
        "address1": "Av. Insurgentes Sur 1602", "city": "Ciudad de México",
        "province": "CDMX", "zip": "03940", "countryCode": "MX",
        "phone": "+52555000002",
    },
    {
        "firstName": "Paula", "lastName": "Ospina",
        "address1": "Carrera 7 #71-21", "city": "Bogotá",
        "province": "Cundinamarca", "zip": "110231", "countryCode": "CO",
        "phone": "+57310000003",
    },
    {
        "firstName": "Florencia", "lastName": "Bianchi",
        "address1": "Av. Santa Fe 1860", "city": "Buenos Aires",
        "province": "Buenos Aires", "zip": "C1123AAQ", "countryCode": "AR",
        "phone": "+54911000004",
    },
]


# ── Helpers ─────────────────────────────────────────────────────────────

def _call_graphql(
    client: httpx.Client,
    shop: str,
    token: str,
    query: str,
    variables: dict | None = None,
) -> dict:
    """Execute a GraphQL mutation/query against the Shopify Admin API."""
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = client.post(
        gql_url(shop),
        headers={
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    body = resp.json()
    if "errors" in body:
        print(f"  [GQL ERROR] {json.dumps(body['errors'], indent=2)}")
    return body


def _random_date(days_back: int = 45) -> str:
    """Return a random ISO-8601 datetime within the last `days_back` days.

    ~30% of dates cluster 7-10 days ago (simulates product launch).
    Minimum offset = 1 day (ensures all orders are in ETL range).
    Rest spreads across 45 days with weekday bias.
    """
    now = datetime.now(timezone.utc)
    for _ in range(50):
        # 30% chance: launch week spike (7-10 days ago)
        if random.random() < 0.30:
            offset = random.uniform(7, 10)
        else:
            offset = random.uniform(1, days_back)

        dt = now - timedelta(days=offset)

        # Bias toward weekdays
        if dt.weekday() >= 5 and random.random() < 0.66:
            continue

        # Random hour 8-23 (business hours bias)
        hour = random.choices(range(8, 24), weights=[1]*4 + [3]*8 + [2]*4, k=1)[0]
        dt = dt.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
        return dt.isoformat()
    return (now - timedelta(days=2)).isoformat()


def _money(amount: str, currency: str = "USD") -> dict:
    return {"shopMoney": {"amount": amount, "currencyCode": currency}}


# ── --from-db credential retrieval ──────────────────────────────────────

def _get_encryption_key_standalone() -> str:
    """Derive Fernet key from API_SECRET_KEY (same as src/core/security.py)."""
    api_secret = os.environ.get("API_SECRET_KEY", "")
    if not api_secret:
        print("ERROR: API_SECRET_KEY env var not set.")
        sys.exit(1)
    digest = hashlib.sha256(api_secret.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode()


def _decrypt_credentials(raw_jsonb: dict) -> dict:
    """Decrypt an EncryptedJSON value (dict with '_encrypted' key)."""
    if isinstance(raw_jsonb, dict) and "_encrypted" in raw_jsonb:
        from cryptography.fernet import Fernet
        key = _get_encryption_key_standalone()
        f = Fernet(key.encode())
        decrypted = f.decrypt(raw_jsonb["_encrypted"].encode()).decode()
        return json.loads(decrypted)
    # Legacy plaintext
    return raw_jsonb


def fetch_credentials_from_db(tenant_slug: str) -> tuple[str, str]:
    """Query channel_connections for Shopify credentials by tenant slug.

    Returns (shop_domain, access_token).
    """
    import psycopg2

    db_host = os.environ.get("POSTGRES_HOST", "postgres")
    db_user = os.environ.get("POSTGRES_USER", "postgres")
    db_pass = os.environ.get("POSTGRES_PASSWORD", "postgres")
    db_name = os.environ.get("POSTGRES_DB", "visionarias_logs")
    db_port = os.environ.get("POSTGRES_PORT", "5432")

    conn = psycopg2.connect(
        host=db_host, port=db_port,
        user=db_user, password=db_pass,
        dbname=db_name,
    )
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT cc.credentials, cc.config
            FROM channel_connections cc
            JOIN tenants t ON cc.tenant_id = t.id
            WHERE t.slug = %s
              AND cc.channel_type = 'shopify'
              AND cc.is_active = true
            LIMIT 1
        """, (tenant_slug,))
        row = cur.fetchone()
        if not row:
            print(f"ERROR: No active Shopify connection for tenant '{tenant_slug}'.")
            sys.exit(1)

        raw_creds, config = row
        # raw_creds is JSONB — could be encrypted or plaintext
        credentials = _decrypt_credentials(raw_creds)

        access_token = credentials.get("access_token", "")
        # shop_domain can be in credentials or config
        shop_domain = (
            credentials.get("shop_domain")
            or credentials.get("shop_url")
            or (config or {}).get("shop_url", "")
        )

        if not access_token:
            print("ERROR: access_token not found in credentials.")
            sys.exit(1)
        if not shop_domain:
            print("ERROR: shop_domain not found in credentials or config.")
            sys.exit(1)

        return shop_domain, access_token
    finally:
        conn.close()


# ── Phase 1: Query existing products ────────────────────────────────────

PRODUCTS_QUERY = """
query {
  products(first: 50) {
    edges {
      node {
        id
        title
        variants(first: 10) {
          edges {
            node {
              id
              price
            }
          }
        }
      }
    }
  }
}
"""


def fetch_existing_products(client: httpx.Client, shop: str, token: str) -> list[dict]:
    """Return list of {id, title, variant_id, price, weight} for all products."""
    data = _call_graphql(client, shop, token, PRODUCTS_QUERY)
    products = []
    # Build a title→weight map from NEW_PRODUCTS
    weight_map = {t: w for t, _, _, w in NEW_PRODUCTS}
    for edge in data.get("data", {}).get("products", {}).get("edges", []):
        node = edge["node"]
        for v_edge in node.get("variants", {}).get("edges", []):
            v = v_edge["node"]
            products.append({
                "product_id": node["id"],
                "title": node["title"],
                "variant_id": v["id"],
                "price": v["price"],
                "weight": weight_map.get(node["title"], 1),
            })
    return products


# ── Phase 2: Create products ────────────────────────────────────────────

PRODUCT_CREATE_MUTATION = """
mutation productCreate($product: ProductCreateInput!) {
  productCreate(product: $product) {
    userErrors { field message }
    product {
      id
      title
      variants(first: 1) {
        edges {
          node {
            id
            price
          }
        }
      }
    }
  }
}
"""

PUBLISH_MUTATION = """
mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $input) {
    userErrors { field message }
  }
}
"""

PUBLICATIONS_QUERY = """
query {
  publications(first: 10) {
    edges {
      node {
        id
        name
      }
    }
  }
}
"""


def get_online_store_publication(client: httpx.Client, shop: str, token: str) -> str | None:
    """Find the Online Store publication ID for publishing products."""
    data = _call_graphql(client, shop, token, PUBLICATIONS_QUERY)
    for edge in data.get("data", {}).get("publications", {}).get("edges", []):
        node = edge["node"]
        if "online store" in node["name"].lower():
            return node["id"]
    edges = data.get("data", {}).get("publications", {}).get("edges", [])
    if edges:
        return edges[0]["node"]["id"]
    return None


def create_products(
    client: httpx.Client,
    shop: str,
    token: str,
    existing: list[dict],
    dry_run: bool = False,
) -> list[dict]:
    """Create new products if needed, then publish them."""
    existing_titles = {p["title"] for p in existing}
    to_create = [(t, p, s, w) for t, p, s, w in NEW_PRODUCTS if t not in existing_titles]

    if not to_create:
        print("  All planned products already exist.")
        return existing

    # Try to get publication for publishing, but don't fail if not available
    pub_id = None
    if not dry_run:
        try:
            pub_id = get_online_store_publication(client, shop, token)
        except Exception as e:
            print(f"  [WARN] Could not get publication ID: {e}")

    all_products = list(existing)
    for title, price, requires_shipping, weight in to_create:
        if dry_run:
            print(f"  [DRY RUN] Would create product: {title} (${price})")
            continue

        variables = {
            "product": {
                "title": title,
                "productType": "Digital Product" if not requires_shipping else "Physical Product",
                "vendor": "Visionarias",
                "status": "ACTIVE",
                "tags": ["seed-data", "test"],
            }
        }

        data = _call_graphql(client, shop, token, PRODUCT_CREATE_MUTATION, variables)
        product_data = (data.get("data") or {}).get("productCreate")
        if product_data is None:
            print(f"  [SKIP] productCreate returned None for '{title}' (access denied?)")
            continue
        errors = product_data.get("userErrors", [])
        if errors:
            print(f"  [WARN] productCreate errors for '{title}': {errors}")
            continue

        product = product_data.get("product", {})
        product_id = product["id"]
        variant_edges = product.get("variants", {}).get("edges", [])
        variant_id = variant_edges[0]["node"]["id"] if variant_edges else None

        if variant_id:
            _set_variant_price(client, shop, token, variant_id, price, requires_shipping)

        entry = {
            "product_id": product_id,
            "title": title,
            "variant_id": variant_id,
            "price": price,
            "weight": weight,
        }
        all_products.append(entry)
        print(f"  ✓ Created: {title} (${price}) → {product_id}")

        if pub_id and product_id:
            _call_graphql(client, shop, token, PUBLISH_MUTATION, {
                "id": product_id,
                "input": [{"publicationId": pub_id}],
            })

        time.sleep(0.5)

    return all_products


VARIANT_UPDATE_MUTATION = """
mutation productVariantUpdate($input: ProductVariantInput!) {
  productVariantUpdate(input: $input) {
    userErrors { field message }
    productVariant { id price }
  }
}
"""


def _set_variant_price(
    client: httpx.Client,
    shop: str,
    token: str,
    variant_id: str,
    price: str,
    requires_shipping: bool,
) -> None:
    """Set price and shipping requirement on a product variant."""
    _call_graphql(client, shop, token, VARIANT_UPDATE_MUTATION, {
        "input": {
            "id": variant_id,
            "price": price,
            "requiresShipping": requires_shipping,
        }
    })


# ── Phase 3: Create customers ──────────────────────────────────────────

CUSTOMER_CREATE_MUTATION = """
mutation customerCreate($input: CustomerInput!) {
  customerCreate(input: $input) {
    userErrors { field message }
    customer { id email }
  }
}
"""


def create_customers(
    client: httpx.Client,
    shop: str,
    token: str,
    dry_run: bool = False,
) -> list[dict]:
    """Create test customers. Returns list of {email, first, last}."""
    created = []
    tags = ["seed-data", "test"]

    for first, last, email, phone in CUSTOMERS:
        if dry_run:
            print(f"  [DRY RUN] Would create customer: {first} {last} <{email}>")
            created.append({"email": email, "first": first, "last": last})
            continue

        inp: dict[str, Any] = {
            "firstName": first,
            "lastName": last,
            "email": email,
            "tags": tags,
        }
        if phone:
            inp["phone"] = phone

        data = _call_graphql(client, shop, token, CUSTOMER_CREATE_MUTATION, {"input": inp})
        cust_data = data.get("data", {}).get("customerCreate", {})
        errors = cust_data.get("userErrors", [])
        if errors:
            if any("taken" in str(e).lower() or "duplicate" in str(e).lower() for e in errors):
                print(f"  ○ Already exists: {first} {last} <{email}>")
            else:
                print(f"  [WARN] customerCreate errors for {email}: {errors}")
        else:
            print(f"  ✓ Created: {first} {last} <{email}>")

        created.append({"email": email, "first": first, "last": last})
        time.sleep(0.3)

    return created


# ── Phase 4: Create orders ──────────────────────────────────────────────

ORDER_CREATE_MUTATION = """
mutation orderCreate($order: OrderCreateOrderInput!) {
  orderCreate(order: $order) {
    userErrors { field message }
    order {
      id
      name
      displayFinancialStatus
      lineItems(first: 10) {
        edges {
          node {
            id
            quantity
          }
        }
      }
      transactions {
        id
        kind
        amountSet {
          shopMoney { amount currencyCode }
        }
      }
    }
  }
}
"""


def _build_line_items(products: list[dict], count: int | None = None) -> tuple[list[dict], float]:
    """Pick weighted random line items. Returns (line_items_input, total_price).

    Uses product `weight` for selection probability.
    Digital products qty=1 (can't buy same course twice).
    Physical products qty 1-2.
    Deduplicates by variant_id (merges into higher qty).
    """
    if count is None:
        count = random.choices([1, 2, 3], weights=[50, 35, 15], k=1)[0]

    weights = [p.get("weight", 1) for p in products]
    chosen = random.choices(products, weights=weights, k=count)

    # Deduplicate by variant_id — merge quantities
    seen: dict[str, dict] = {}
    for p in chosen:
        vid = p.get("variant_id", p["title"])
        if vid in seen:
            # Merge: bump qty (max 3)
            seen[vid]["qty"] = min(seen[vid]["qty"] + 1, 3)
        else:
            is_physical = p.get("requires_shipping", False)
            # Infer physical from title if not in dict
            if "Kit" in p.get("title", "") or "Fisico" in p.get("title", ""):
                is_physical = True
            qty = random.choices([1, 2], weights=[70, 30], k=1)[0] if is_physical else 1
            seen[vid] = {"product": p, "qty": qty}

    items = []
    total = 0.0
    for entry in seen.values():
        p = entry["product"]
        qty = entry["qty"]
        price = float(p["price"])
        total += price * qty

        item: dict[str, Any] = {"quantity": qty}
        if p.get("variant_id"):
            item["variantId"] = p["variant_id"]
        else:
            item["title"] = p["title"]
            item["priceSet"] = _money(f"{price:.2f}")
        items.append(item)

    return items, total


def _build_order(
    products: list[dict],
    customers: list[dict],
    *,
    financial_status: str = "PAID",
    apply_discount: bool = False,
    discount_code_override: tuple | None = None,
    add_shipping: bool = False,
    is_refund: bool = False,
    line_item_count: int | None = None,
    repeat_customer: dict | None = None,
) -> dict:
    """Build an OrderCreateOrderInput dict."""
    line_items, subtotal = _build_line_items(products, count=line_item_count)

    # Discount
    discount_amount = 0.0
    discount_code_input = None
    if apply_discount:
        if discount_code_override:
            code, dtype, value, _ = discount_code_override
        else:
            code, dtype, value, _ = random.choice(DISCOUNT_CODES)

        if dtype == "percentage":
            discount_amount = round(subtotal * value / 100, 2)
            discount_code_input = {
                "itemPercentageDiscountCode": {
                    "code": code,
                    "percentage": value,
                }
            }
        else:
            # fixed amount
            discount_amount = min(float(value), subtotal)
            discount_code_input = {
                "itemFixedDiscountCode": {
                    "code": code,
                    "amount": float(value),
                }
            }

    # Shipping
    shipping_total = 0.0
    shipping_lines = None
    shipping_address = None
    if add_shipping:
        shipping_total = round(random.choice([5.99, 7.99, 9.99]), 2)
        shipping_lines = [{
            "title": "Envio Estandar",
            "priceSet": _money(f"{shipping_total:.2f}"),
        }]
        shipping_address = random.choice(SHIPPING_ADDRESSES)

    # Total after discount
    order_total = round(max(subtotal - discount_amount + shipping_total, 0.01), 2)

    if is_refund:
        financial_status = "REFUNDED"

    # Pick customer
    customer = repeat_customer or random.choice(customers)

    # Tax (8% on subtotal after discount)
    taxable = max(subtotal - discount_amount, 0)
    tax_amount = round(taxable * 0.08, 2)

    processed_at = _random_date()

    order: dict[str, Any] = {
        "lineItems": line_items,
        "customer": {
            "toUpsert": {
                "email": customer["email"],
                "firstName": customer["first"],
                "lastName": customer["last"],
            }
        },
        "financialStatus": financial_status,
        "processedAt": processed_at,
        "currency": "USD",
        "test": True,
        "tags": ["seed-data", "test"],
        "taxLines": [{
            "title": "Sales Tax",
            "priceSet": _money(f"{tax_amount:.2f}"),
            "rate": 0.08,
        }],
        "transactions": [{
            "kind": "SALE",
            "status": "SUCCESS",
            "amountSet": _money(f"{order_total:.2f}"),
        }],
    }

    if discount_code_input:
        order["discountCode"] = discount_code_input

    if shipping_lines:
        order["shippingLines"] = shipping_lines

    if shipping_address:
        order["shippingAddress"] = shipping_address

    if is_refund:
        order["note"] = "Fully refunded"

    return order


def create_orders(
    client: httpx.Client,
    shop: str,
    token: str,
    products: list[dict],
    customers: list[dict],
    dry_run: bool = False,
) -> tuple[dict, list[dict]]:
    """Create ~90 orders in batches of 5 with 62s sleep between batches.

    Returns (stats_dict, list_of_partial_refund_order_data).
    """
    # Select 7 customers who will have multiple orders (repeat buyers)
    repeat_buyers = random.sample(customers, min(7, len(customers)))

    order_specs: list[dict] = []
    # Track which orders are partial refunds (need Phase 5 refundCreate)
    partial_refund_indices: list[int] = []

    # ~55 regular paid orders
    for _ in range(55):
        has_physical = random.random() < 0.35
        spec = _build_order(products, customers, add_shipping=has_physical)
        order_specs.append(spec)

    # ~15 discounted orders (cycle through all 5 codes, rest random)
    for i in range(15):
        code = DISCOUNT_CODES[i % len(DISCOUNT_CODES)]
        spec = _build_order(
            products, customers,
            apply_discount=True,
            discount_code_override=code,
            add_shipping=random.random() < 0.4,
        )
        order_specs.append(spec)

    # ~5 bundle orders (2-3 items from different tiers)
    for _ in range(5):
        spec = _build_order(
            products, customers,
            add_shipping=random.random() < 0.5,
            line_item_count=random.choice([2, 3]),
        )
        order_specs.append(spec)

    # ~8 fully refunded orders (financialStatus: REFUNDED in orderCreate)
    for _ in range(8):
        spec = _build_order(products, customers, is_refund=True)
        order_specs.append(spec)

    # ~7 partial refund orders — created as PAID, refunded in Phase 5
    partial_start = len(order_specs)
    for _ in range(7):
        spec = _build_order(products, customers, add_shipping=random.random() < 0.5)
        order_specs.append(spec)
    partial_refund_indices = list(range(partial_start, len(order_specs)))

    # Overwrite some orders to use repeat buyers (ensure repeat_customers metric)
    # Assign 2-4 extra orders each to 7 repeat buyers (~15 orders total)
    non_partial = [i for i in range(len(order_specs)) if i not in partial_refund_indices]
    repeat_indices = random.sample(non_partial, min(15, len(non_partial)))
    for i, idx in enumerate(repeat_indices):
        buyer = repeat_buyers[i % len(repeat_buyers)]
        order_specs[idx]["customer"] = {
            "toUpsert": {
                "email": buyer["email"],
                "firstName": buyer["first"],
                "lastName": buyer["last"],
            }
        }

    # Shuffle but remember partial refund positions
    # Create index mapping: original_idx -> order_spec
    indexed = list(enumerate(order_specs))
    random.shuffle(indexed)
    shuffled_specs = [spec for _, spec in indexed]
    # Map original partial_refund_indices to new positions
    old_to_new = {old: new for new, (old, _) in enumerate(indexed)}
    new_partial_indices = [old_to_new[i] for i in partial_refund_indices]

    stats = {"paid": 0, "refunded": 0, "discounted": 0, "errors": 0}
    partial_refund_orders: list[dict] = []  # Collect order data for Phase 5
    total = len(shuffled_specs)
    batch_size = 5
    batch_sleep = 62

    print(f"\n  Creating {total} orders in batches of {batch_size}...")
    total_batches = (total + batch_size - 1) // batch_size
    print(f"  Estimated time: ~{total_batches * batch_sleep // 60} minutes\n")

    for i in range(0, total, batch_size):
        batch = shuffled_specs[i : i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  ── Batch {batch_num}/{total_batches} ──")

        for j, order_input in enumerate(batch):
            order_num = i + j + 1
            fin_status = order_input.get("financialStatus", "PAID")
            has_discount = "discountCode" in order_input
            is_partial_target = (i + j) in new_partial_indices

            if dry_run:
                label = fin_status
                if is_partial_target:
                    label += " (→partial refund)"
                print(f"    [DRY RUN] Order #{order_num}: {label}"
                      + (" +discount" if has_discount else ""))
                stats[fin_status.lower()] = stats.get(fin_status.lower(), 0) + 1
                if has_discount:
                    stats["discounted"] += 1
                if is_partial_target:
                    partial_refund_orders.append({"id": f"gid://shopify/Order/{order_num}", "mock": True})
                continue

            data = _call_graphql(client, shop, token, ORDER_CREATE_MUTATION, {"order": order_input})
            order_data = data.get("data", {}).get("orderCreate", {})
            errors = order_data.get("userErrors", [])

            if errors:
                print(f"    ✗ Order #{order_num}: {errors}")
                stats["errors"] += 1
            else:
                order = order_data.get("order", {})
                name = order.get("name", "?")
                display_status = order.get("displayFinancialStatus", fin_status)
                extra = " +discount" if has_discount else ""
                if is_partial_target:
                    extra += " (→partial refund)"
                print(f"    ✓ Order #{order_num} {name}: {display_status}{extra}")
                stats[fin_status.lower()] = stats.get(fin_status.lower(), 0) + 1
                if has_discount:
                    stats["discounted"] += 1

                # Save full order data for Phase 5 partial refunds
                if is_partial_target:
                    partial_refund_orders.append(order)

            time.sleep(0.5)

        if i + batch_size < total:
            remaining_batches = total_batches - batch_num
            print(f"\n  ⏳ Rate limit pause (62s) — {remaining_batches} batches remaining...")
            if not dry_run:
                time.sleep(batch_sleep)
            print()

    return stats, partial_refund_orders


# ── Phase 5: Refund creation (partial refunds) ─────────────────────────

REFUND_CREATE_MUTATION = """
mutation refundCreate($input: RefundInput!) {
  refundCreate(input: $input) {
    userErrors { field message }
    refund {
      id
    }
    order {
      id
      name
      displayFinancialStatus
      currentTotalPriceSet {
        shopMoney { amount currencyCode }
      }
    }
  }
}
"""


def create_partial_refunds(
    client: httpx.Client,
    shop: str,
    token: str,
    partial_refund_orders: list[dict],
    dry_run: bool = False,
) -> dict:
    """Issue refundCreate for partial refund orders.

    This is CRITICAL: only a real refundCreate mutation updates current_total_price.
    The ETL computes partial refund amount as total_price - current_total_price.
    """
    stats = {"refunded": 0, "errors": 0}

    if not partial_refund_orders:
        print("  No partial refund orders to process.")
        return stats

    batch_size = 5
    batch_sleep = 62
    total = len(partial_refund_orders)
    total_batches = (total + batch_size - 1) // batch_size

    print(f"\n  Processing {total} partial refunds in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = partial_refund_orders[i : i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  ── Refund Batch {batch_num}/{total_batches} ──")

        for j, order_data in enumerate(batch):
            order_id = order_data.get("id")
            order_name = order_data.get("name", "?")

            if not order_id or order_data.get("mock"):
                if dry_run:
                    print(f"    [DRY RUN] Would partially refund order {order_name}")
                    stats["refunded"] += 1
                continue

            # Get the sale transaction for the refund
            transactions = order_data.get("transactions", [])
            sale_tx = None
            for tx in transactions:
                if tx.get("kind") == "SALE":
                    sale_tx = tx
                    break

            if not sale_tx:
                print(f"    [WARN] No SALE transaction found for {order_name}, skipping refund.")
                stats["errors"] += 1
                continue

            # Calculate partial refund: 20-60% of order total
            order_amount = float(
                sale_tx.get("amountSet", {}).get("shopMoney", {}).get("amount", "0")
            )
            refund_pct = random.uniform(0.20, 0.60)
            refund_amount = round(order_amount * refund_pct, 2)

            # Build refund line items (refund proportionally across all items)
            line_items = order_data.get("lineItems", {}).get("edges", [])
            refund_line_items = []
            for li_edge in line_items:
                li = li_edge["node"]
                # Refund 1 quantity of each item (partial)
                refund_line_items.append({
                    "lineItemId": li["id"],
                    "quantity": max(1, li["quantity"] // 2),  # refund half qty, at least 1
                })

            refund_input: dict[str, Any] = {
                "orderId": order_id,
                "note": f"Partial refund ({refund_pct:.0%}) — seed data",
                "shipping": {"fullRefund": False},
                "transactions": [{
                    "parentId": sale_tx["id"],
                    "amount": refund_amount,
                    "kind": "REFUND",
                    "gateway": "manual",
                }],
            }

            if refund_line_items:
                refund_input["refundLineItems"] = refund_line_items

            if dry_run:
                print(f"    [DRY RUN] Would partially refund {order_name}: "
                      f"${refund_amount:.2f} ({refund_pct:.0%})")
                stats["refunded"] += 1
                continue

            data = _call_graphql(client, shop, token, REFUND_CREATE_MUTATION, {"input": refund_input})
            refund_data = data.get("data", {}).get("refundCreate", {})
            errors = refund_data.get("userErrors", [])

            if errors:
                print(f"    ✗ Refund for {order_name}: {errors}")
                stats["errors"] += 1
            else:
                updated_order = refund_data.get("order", {})
                new_status = updated_order.get("displayFinancialStatus", "?")
                new_total = (
                    updated_order
                    .get("currentTotalPriceSet", {})
                    .get("shopMoney", {})
                    .get("amount", "?")
                )
                print(f"    ✓ Refund {order_name}: -${refund_amount:.2f} "
                      f"({refund_pct:.0%}) → {new_status} (current=${new_total})")
                stats["refunded"] += 1

            time.sleep(0.5)

        if i + batch_size < total:
            remaining = total_batches - batch_num
            print(f"\n  ⏳ Rate limit pause (62s) — {remaining} batches remaining...")
            if not dry_run:
                time.sleep(batch_sleep)
            print()

    return stats


# ── Summary ─────────────────────────────────────────────────────────────

def print_summary(
    products: list[dict],
    customers: list[dict],
    order_stats: dict,
    refund_stats: dict,
) -> None:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=45)

    print("\n" + "=" * 60)
    print("  SEED DATA SUMMARY")
    print("=" * 60)
    print(f"  Products available:     {len(products)}")
    print(f"  Customers created:      {len(customers)}")
    print(f"  Orders created:")
    print(f"    Paid:                 {order_stats.get('paid', 0)}")
    print(f"    Discounted:           {order_stats.get('discounted', 0)}")
    print(f"    Refunded (full):      {order_stats.get('refunded', 0)}")
    print(f"    Partial refunds:      {refund_stats.get('refunded', 0)}")
    print(f"    Errors:               {order_stats.get('errors', 0) + refund_stats.get('errors', 0)}")
    print(f"  Date range:             {start.date()} → {now.date()}")
    print()
    print("  ETL metrics now testable (12 sales metrics):")
    print("  ─ revenue, order_count, avg_order_value, units_sold")
    print("  ─ total_discounts, total_tax, net_sales")
    print("  ─ refund_amount, refund_count")
    print("  ─ shipping_revenue, repeat_customers, discount_usage_count")
    print("=" * 60)


# ── CLI ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed a Shopify dev store with realistic Visionarias-style test data."
    )
    # Credential source: either --from-db or manual
    parser.add_argument(
        "--from-db",
        action="store_true",
        help="Auto-retrieve credentials from channel_connections DB table.",
    )
    parser.add_argument(
        "--tenant-slug",
        help="Tenant slug to look up (required with --from-db). e.g. visi-test-6",
    )
    parser.add_argument(
        "--shop-domain",
        help="e.g. my-store.myshopify.com (manual mode)",
    )
    parser.add_argument(
        "--access-token",
        help="Shopify Admin API access token (shpat_...) (manual mode)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be created without making API calls.",
    )
    parser.add_argument(
        "--skip-products",
        action="store_true",
        help="Skip product creation (use existing products in the store).",
    )
    parser.add_argument(
        "--skip-customers",
        action="store_true",
        help="Skip customer creation (use customer data from orders directly).",
    )
    args = parser.parse_args()

    # Resolve credentials
    if args.from_db:
        if not args.tenant_slug:
            parser.error("--tenant-slug is required when using --from-db")
        print(f"\n  Fetching Shopify credentials from DB for tenant '{args.tenant_slug}'...")
        shop, token = fetch_credentials_from_db(args.tenant_slug)
        print(f"  ✓ Found: {shop}\n")
    elif args.shop_domain and args.access_token:
        shop = args.shop_domain
        token = args.access_token
    else:
        parser.error("Either --from-db --tenant-slug or --shop-domain --access-token required.")

    shop = shop.replace("https://", "").replace("http://", "").strip("/")

    print(f"{'=' * 60}")
    print(f"  Shopify Test Data Seeder (Visionarias Style)")
    print(f"  Shop: {shop}")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'=' * 60}\n")

    client = httpx.Client()

    # Phase 1: Fetch existing products
    print("Phase 1: Querying existing products...")
    if args.dry_run:
        products = []
        print("  [DRY RUN] Skipping API call, using empty product list.\n")
    else:
        products = fetch_existing_products(client, shop, token)
        print(f"  Found {len(products)} existing product variants.\n")

    # Phase 2: Create additional products
    if args.skip_products:
        print("Phase 2: Skipping product creation (--skip-products).\n")
    else:
        print("Phase 2: Creating products (Visionarias offer ladder)...")
        products = create_products(client, shop, token, products, dry_run=args.dry_run)
    print(f"  Total products: {len(products)}\n")

    if not products and not args.dry_run:
        print("ERROR: No products available. Cannot create orders.")
        sys.exit(1)

    # In dry-run mode, use mock products for order generation
    if not products:
        products = [
            {
                "product_id": f"gid://shopify/Product/{i}",
                "title": t,
                "variant_id": f"gid://shopify/ProductVariant/{i}",
                "price": p,
                "weight": w,
            }
            for i, (t, p, _, w) in enumerate(NEW_PRODUCTS)
        ]

    # Phase 3: Create customers
    if args.skip_customers:
        print("Phase 3: Skipping customer creation (--skip-customers).")
        customers = [{"email": e, "first": f, "last": l} for f, l, e, _ in CUSTOMERS]
        print(f"  Using {len(customers)} customer records for orders.\n")
    else:
        print("Phase 3: Creating customers (28 Latin American)...")
        customers = create_customers(client, shop, token, dry_run=args.dry_run)
        print(f"  Total customers: {len(customers)}\n")

    # Phase 4: Create orders
    print("Phase 4: Creating orders (~90 mixed types)...")
    order_stats, partial_refund_orders = create_orders(
        client, shop, token, products, customers, dry_run=args.dry_run
    )

    # Phase 5: Create partial refunds
    print("\nPhase 5: Creating partial refunds (refundCreate mutations)...")
    refund_stats = create_partial_refunds(
        client, shop, token, partial_refund_orders, dry_run=args.dry_run
    )

    # Summary
    print_summary(products, customers, order_stats, refund_stats)

    client.close()


if __name__ == "__main__":
    main()
