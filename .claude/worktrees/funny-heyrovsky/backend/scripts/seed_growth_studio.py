"""Seed Growth Studio data for Visionarias tenant.

Populates all 7 funnel stages with coherent, realistic data simulating
30 days of real extraction from connected sources.

Tables seeded:
- extraction_runs (ETL run records)
- official_metrics (daily metric data)
- metric_aggregations (pre-computed rollups for dashboard)
- customer_profiles (lifecycle progression)
- lifecycle_transitions (stage transitions)
- journey_events (email, checkout, meeting, SDR events)
- sales (revenue by offer/tier)
- channel_cost_settings (monthly costs)
- referral_codes, nps_surveys, nps_responses (evangelization)

Usage: docker exec -it visionarias_brain_dev python scripts/seed_growth_studio.py
"""
import uuid
import random
from datetime import datetime, timedelta, timezone, date

# -- Config --
TENANT_ID = "6347e21e-8112-4aa1-80d3-6adaa73bf6f9"
NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=30)
TODAY = date.today()
START_DATE = TODAY - timedelta(days=30)

# Products (from DB)
PRODUCTS = {
    "N0_FREE": {"id": "217ff363-8e96-4132-9542-935499bc7efc", "name": "Guía: Liberar la Mente", "price": 0, "currency": "USD"},
    "N1_TRIPWIRE": {"id": "5cbae26f-0e52-4795-8edd-b8e4518e27de", "name": "Pack Meditaciones: Abundancia", "price": 27, "currency": "USD"},
    "N2_GROUP": {"id": "46ad9d44-1ff0-47d0-a623-30e196b89013", "name": "Programa: De Propósito a Prosperidad", "price": 497, "currency": "PEN"},
    "N3_MENTOR": {"id": "42704d9b-6e35-47b8-b09f-bb9ec1942542", "name": "Mentoría Privada: Visión Clara", "price": 2500, "currency": "USD"},
    "N4_SERVICE": {"id": "0ae6fca2-126b-4ae2-9231-1a14bf76cacd", "name": "Agencia Visionarias DFY", "price": 5000, "currency": "USD"},
    "N5_MASTERMIND": {"id": "929828ac-6e48-4416-9849-196d306250d4", "name": "Círculo Visionarias Elite", "price": 10000, "currency": "USD"},
    "N5_RETREAT": {"id": "5bf98020-e366-4ce5-86e2-80cb34b5eef4", "name": "Retiro Visionarias: Tulum 2026", "price": 8000, "currency": "USD"},
}

# Connected providers
PROVIDERS = ["meta", "google_analytics", "youtube", "mailerlite"]

# Funnel numbers (coherent drop-off)
VISITORS = 18500
LEADS = 620
MQLS = 185
SQLS = 72
CUSTOMERS = 38
RETAINED = 28
EVANGELISTS = 12

# Lead source distribution
LEAD_SOURCES = {
    "ig-dm": 180,
    "whatsapp-inbound": 140,
    "fb-messenger": 45,
    "landing-form": 160,
    "mailerlite": 95,
}

LIFECYCLE_STAGES = ["SUBSCRIBER", "LEAD", "MQL", "SQL", "OPPORTUNITY", "CUSTOMER", "EVANGELIST"]


def gen_uuid():
    return str(uuid.uuid4())


def random_date(start_dt, end_dt):
    delta = end_dt - start_dt
    total_secs = int(delta.total_seconds())
    if total_secs <= 0:
        return start_dt
    random_seconds = random.randint(0, total_secs)
    return start_dt + timedelta(seconds=random_seconds)


def build_sql():
    """Build all INSERT statements as a single SQL script."""
    stmts = []
    stmts.append(f"-- Growth Studio Seed Data for Visionarias ({TODAY})")
    stmts.append(f"-- Tenant: {TENANT_ID}")
    stmts.append("")

    # =============================================
    # 0. CLEANUP existing seed data
    # =============================================
    stmts.append("-- Cleanup previous seed data")
    for table in [
        "nps_responses", "nps_surveys", "referral_codes",
        "sales", "lifecycle_transitions", "journey_events",
        "metric_aggregations", "official_metrics", "staging_metrics",
        "extraction_runs", "channel_cost_settings",
    ]:
        stmts.append(f"DELETE FROM {table} WHERE tenant_id = '{TENANT_ID}';")

    # Don't delete existing customer_profiles, but update them
    stmts.append("")

    # =============================================
    # 1. EXTRACTION RUNS (successful runs per provider)
    # =============================================
    stmts.append("-- Extraction Runs")
    extraction_run_ids = {}
    for provider in PROVIDERS:
        run_id = gen_uuid()
        extraction_run_ids[provider] = run_id
        started = NOW - timedelta(hours=random.randint(1, 4))
        duration = round(random.uniform(3.5, 15.0), 2)
        completed = started + timedelta(seconds=duration)
        metrics_count = random.randint(50, 200)
        stmts.append(
            f"INSERT INTO extraction_runs (id, tenant_id, provider, status, started_at, completed_at, "
            f"metrics_count, duration_seconds, rows_extracted, rate_limit_headroom, created_at) VALUES ("
            f"'{run_id}', '{TENANT_ID}', '{provider}', 'success', "
            f"'{started.isoformat()}', '{completed.isoformat()}', "
            f"{metrics_count}, {duration}, {metrics_count}, {round(random.uniform(0.4, 0.9), 2)}, "
            f"'{started.isoformat()}');"
        )
    stmts.append("")

    # =============================================
    # 2. OFFICIAL METRICS (daily data, 30 days)
    # =============================================
    stmts.append("-- Official Metrics (daily)")

    # Attraction channels with realistic daily values
    attraction_channels = {
        "ig-organic": {"provider": "meta", "metrics": {"reach": (800, 2200), "engagement": (40, 180)}, "cost_type": "neutral"},
        "yt-organic": {"provider": "youtube", "metrics": {"reach": (400, 1200), "engagement": (20, 80)}, "cost_type": "neutral"},
        "fb-organic": {"provider": "meta", "metrics": {"reach": (300, 900), "engagement": (15, 60)}, "cost_type": "neutral"},
        "google-organic": {"provider": "google_analytics", "metrics": {"sessions": (80, 250), "users": (60, 200)}, "cost_type": "neutral"},
        "direct": {"provider": "google_analytics", "metrics": {"sessions": (30, 100), "users": (25, 80)}, "cost_type": "neutral"},
        "meta-ads": {"provider": "meta", "metrics": {"reach": (2000, 6000), "clicks": (120, 380), "conversions": (8, 25), "spend": (30, 85)}, "cost_type": "investment"},
        "google-ads": {"provider": "google_analytics", "metrics": {"reach": (1200, 3500), "clicks": (60, 200), "conversions": (4, 15), "spend": (20, 60)}, "cost_type": "investment"},
    }

    # Nurture retargeting channels
    nurture_channels = {
        "meta-retargeting": {"provider": "meta", "metrics": {"reach": (500, 1500), "clicks": (30, 90), "spend": (10, 30)}, "cost_type": "investment"},
    }

    all_metric_channels = {**attraction_channels, **nurture_channels}

    for d in range(30):
        metric_date = START_DATE + timedelta(days=d)
        # Weekday boost factor (less on weekends)
        weekday = metric_date.weekday()
        boost = 1.0 if weekday < 5 else 0.65

        for slug, config in all_metric_channels.items():
            provider = config["provider"]
            cost_type = config["cost_type"]
            run_id = extraction_run_ids.get(provider, extraction_run_ids["meta"])

            for metric_name, (low, high) in config["metrics"].items():
                value = round(random.uniform(low, high) * boost, 2)
                unit = "currency" if metric_name == "spend" else "count"
                currency = "'USD'" if metric_name == "spend" else "NULL"
                spend_json = f"'{{\"{metric_name}\": {value}}}'" if metric_name == "spend" else "NULL"

                stmts.append(
                    f"INSERT INTO official_metrics (id, tenant_id, provider, channel_slug, metric_name, "
                    f"value, unit, currency, metric_date, spend, cost_type, extra, "
                    f"source_extraction_run_id, created_at) VALUES ("
                    f"'{gen_uuid()}', '{TENANT_ID}', '{provider}', '{slug}', '{metric_name}', "
                    f"{value}, '{unit}', {currency}, '{metric_date}', {spend_json}, '{cost_type}', "
                    f"'{{}}', '{run_id}', '{NOW.isoformat()}');"
                )
    stmts.append("")

    # =============================================
    # 3. METRIC AGGREGATIONS (last_30_days rollups)
    # =============================================
    stmts.append("-- Metric Aggregations (last_30_days period)")

    for slug, config in all_metric_channels.items():
        run_id = extraction_run_ids.get(config["provider"], extraction_run_ids["meta"])
        cost_type = config["cost_type"]

        for metric_name, (low, high) in config["metrics"].items():
            # Sum 30 days with ~0.85 avg factor for weekends
            total = round(sum(random.uniform(low, high) * (1.0 if (START_DATE + timedelta(days=d)).weekday() < 5 else 0.65) for d in range(30)), 2)
            unit = "currency" if metric_name == "spend" else "count"
            currency = "'USD'" if metric_name == "spend" else "NULL"

            stmts.append(
                f"INSERT INTO metric_aggregations (id, tenant_id, channel_slug, metric_name, "
                f"period_type, period_start, period_end, value, unit, currency, cost_type, "
                f"computed_at, extraction_run_id) VALUES ("
                f"'{gen_uuid()}', '{TENANT_ID}', '{slug}', '{metric_name}', "
                f"'last_30_days', '{START_DATE}', '{TODAY}', {total}, '{unit}', {currency}, "
                f"'{cost_type}', '{NOW.isoformat()}', '{run_id}');"
            )
    stmts.append("")

    # =============================================
    # 4. CUSTOMER PROFILES (new leads with lifecycle progression)
    # =============================================
    stmts.append("-- Customer Profiles (new leads + lifecycle)")

    # First update existing 61 subscribers to have lead_source and is_inactive
    stmts.append(
        f"UPDATE customer_profiles SET is_inactive = false, lead_source = 'ig-dm' "
        f"WHERE tenant_id = '{TENANT_ID}' AND lead_source IS NULL;"
    )

    profile_ids = []
    profile_stages = {}  # profile_id -> final stage

    # Build realistic funnel: 620 leads, 185 MQL, 72 SQL, 38 customers, 12 evangelists
    stage_counts = {
        "LEAD": LEADS - MQLS,         # 435 stay as LEAD
        "MQL": MQLS - SQLS,           # 113 stay as MQL
        "SQL": SQLS - CUSTOMERS,      # 34 stay as SQL
        "CUSTOMER": CUSTOMERS - EVANGELISTS,  # 26 become CUSTOMER
        "EVANGELIST": EVANGELISTS,     # 12 become EVANGELIST
    }

    first_names = [
        "María", "Ana", "Carla", "Sofía", "Valentina", "Lucía", "Isabella", "Daniela",
        "Camila", "Paula", "Andrea", "Gabriela", "Fernanda", "Natalia", "Diana",
        "Laura", "Claudia", "Rosa", "Carmen", "Elena", "Mariana", "Adriana",
        "Patricia", "Catalina", "Jimena", "Alejandra", "Mónica", "Verónica",
        "Jessica", "Lorena", "Paola", "Silvia", "Beatriz", "Teresa", "Gloria",
    ]
    last_names = [
        "García", "López", "Martínez", "González", "Rodríguez", "Hernández",
        "Pérez", "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
        "Díaz", "Cruz", "Morales", "Reyes", "Gutiérrez", "Ortiz", "Castillo",
        "Vargas", "Romero", "Mendoza", "Ruiz", "Álvarez", "Jiménez", "Medina",
    ]

    lead_source_list = []
    for src, count in LEAD_SOURCES.items():
        lead_source_list.extend([src] * count)
    random.shuffle(lead_source_list)

    idx = 0
    for final_stage, count in stage_counts.items():
        for _ in range(count):
            pid = gen_uuid()
            profile_ids.append(pid)
            profile_stages[pid] = final_stage

            src = lead_source_list[idx % len(lead_source_list)]
            idx += 1

            first_seen = random_date(START, NOW - timedelta(days=2))
            last_seen = random_date(first_seen + timedelta(hours=1), NOW)
            last_activity = random_date(first_seen, NOW)
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            email = f"{fname.lower().replace('í','i').replace('é','e').replace('ó','o').replace('á','a').replace('ú','u')}.{lname.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}{random.randint(1,999)}@gmail.com"

            is_inactive = "false"
            lifetime_value = 0
            first_conversion = "NULL"
            lead_score = round(random.uniform(10, 95), 1)

            if final_stage == "CUSTOMER":
                lifetime_value = random.choice([27, 27, 497, 497, 2500, 5000])
                first_conversion = f"'{random_date(first_seen + timedelta(days=3), NOW).isoformat()}'"
                lead_score = round(random.uniform(70, 95), 1)
            elif final_stage == "EVANGELIST":
                lifetime_value = random.choice([2500, 5000, 10000, 8000, 497])
                first_conversion = f"'{random_date(first_seen + timedelta(days=2), NOW).isoformat()}'"
                lead_score = round(random.uniform(85, 99), 1)
            elif final_stage == "SQL":
                lead_score = round(random.uniform(55, 80), 1)
            elif final_stage == "MQL":
                lead_score = round(random.uniform(35, 65), 1)

            stmts.append(
                f"INSERT INTO customer_profiles (id, tenant_id, lifecycle_stage, first_seen_at, "
                f"last_seen_at, total_sessions, total_ltv, properties, tags, computed_traits, "
                f"full_name, primary_email, lead_score, lead_source, is_inactive, "
                f"lifetime_value, last_activity_at, first_conversion_at, created_at) VALUES ("
                f"'{pid}', '{TENANT_ID}', '{final_stage}', '{first_seen.isoformat()}', "
                f"'{last_seen.isoformat()}', {random.randint(1, 15)}, {lifetime_value}, "
                f"'{{}}', ARRAY[]::varchar[], '{{}}', "
                f"'{fname} {lname}', '{email}', {lead_score}, '{src}', {is_inactive}, "
                f"{lifetime_value}, '{last_activity.isoformat()}', {first_conversion}, "
                f"'{first_seen.isoformat()}');"
            )
    stmts.append("")

    # =============================================
    # 5. LIFECYCLE TRANSITIONS
    # =============================================
    stmts.append("-- Lifecycle Transitions")

    stage_order = {"LEAD": 1, "MQL": 2, "SQL": 3, "OPPORTUNITY": 3, "CUSTOMER": 4, "EVANGELIST": 5}
    transition_pairs = {
        "LEAD": [("SUBSCRIBER", "LEAD")],
        "MQL": [("SUBSCRIBER", "LEAD"), ("LEAD", "MQL")],
        "SQL": [("SUBSCRIBER", "LEAD"), ("LEAD", "MQL"), ("MQL", "SQL")],
        "CUSTOMER": [("SUBSCRIBER", "LEAD"), ("LEAD", "MQL"), ("MQL", "SQL"), ("SQL", "CUSTOMER")],
        "EVANGELIST": [("SUBSCRIBER", "LEAD"), ("LEAD", "MQL"), ("MQL", "SQL"), ("SQL", "CUSTOMER"), ("CUSTOMER", "EVANGELIST")],
    }

    for pid, final_stage in profile_stages.items():
        pairs = transition_pairs.get(final_stage, [])
        base_time = random_date(START, NOW - timedelta(days=5))
        for i, (from_s, to_s) in enumerate(pairs):
            t = base_time + timedelta(days=i * random.randint(1, 4), hours=random.randint(0, 12))
            if t > NOW:
                t = NOW - timedelta(hours=random.randint(1, 24))

            reasons = {
                "LEAD": "form_submission",
                "MQL": "lead_score_threshold",
                "SQL": "meeting_booked",
                "CUSTOMER": "payment_completed",
                "EVANGELIST": "nps_promoter",
            }
            triggers = {
                "LEAD": "capture_automation",
                "MQL": "scoring_engine",
                "SQL": "sales_agent",
                "CUSTOMER": "payment_webhook",
                "EVANGELIST": "nps_survey",
            }

            stmts.append(
                f"INSERT INTO lifecycle_transitions (id, profile_id, tenant_id, from_stage, to_stage, "
                f"reason, triggered_by, score_at_transition, occurred_at) VALUES ("
                f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', '{from_s}', '{to_s}', "
                f"'{reasons.get(to_s, 'system')}', '{triggers.get(to_s, 'system')}', "
                f"{round(random.uniform(20, 95), 1)}, '{t.isoformat()}');"
            )
    stmts.append("")

    # =============================================
    # 6. JOURNEY EVENTS
    # =============================================
    stmts.append("-- Journey Events")

    # Get customer and evangelist profile IDs
    customer_ids = [pid for pid, s in profile_stages.items() if s in ("CUSTOMER", "EVANGELIST")]
    mql_ids = [pid for pid, s in profile_stages.items() if s in ("MQL", "SQL", "CUSTOMER", "EVANGELIST")]
    all_lead_ids = list(profile_stages.keys())

    # 6a. Message received events (capture - conversations by channel)
    messaging_channels = ["ig-dm", "whatsapp-inbound", "fb-messenger"]
    for pid in random.sample(all_lead_ids, min(350, len(all_lead_ids))):
        channel = random.choice(messaging_channels)
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'messaging', 'message_received', "
            f"'{channel}', '{{\"channel_slug\": \"{channel}\"}}', '{t.isoformat()}', '{t.isoformat()}');"
        )

    # 6b. Email events (nurture)
    email_profiles = random.sample(all_lead_ids, min(400, len(all_lead_ids)))
    for pid in email_profiles:
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'email', 'email_sent', "
            f"'mailerlite', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )
    # Opens (45% rate)
    for pid in random.sample(email_profiles, int(len(email_profiles) * 0.45)):
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'email', 'email_opened', "
            f"'mailerlite', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )
    # Clicks (12% rate)
    for pid in random.sample(email_profiles, int(len(email_profiles) * 0.12)):
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'email', 'email_clicked', "
            f"'mailerlite', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )

    # 6c. SDR followup events (nurture)
    sdr_profiles = random.sample(mql_ids, min(120, len(mql_ids)))
    for pid in sdr_profiles:
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'sdr', 'sdr_followup_sent', "
            f"'ai-sdr', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )
    # 35% replied
    for pid in random.sample(sdr_profiles, int(len(sdr_profiles) * 0.35)):
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'sdr', 'sdr_followup_replied', "
            f"'ai-sdr', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )

    # 6d. Checkout events (opportunity)
    sql_and_customer_ids = [pid for pid, s in profile_stages.items() if s in ("SQL", "CUSTOMER", "EVANGELIST")]
    checkout_profiles = random.sample(sql_and_customer_ids, min(55, len(sql_and_customer_ids)))
    for pid in checkout_profiles:
        t = random_date(START, NOW)
        price = random.choice([27, 27, 497, 2500])
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'checkout', 'checkout_initiated', "
            f"'shopify', '{{\"total_price\": \"{price}\"}}', '{t.isoformat()}', '{t.isoformat()}');"
        )

    # Cart abandoned (~35% of checkouts)
    abandoned_profiles = random.sample(checkout_profiles, int(len(checkout_profiles) * 0.35))
    for pid in abandoned_profiles:
        t = random_date(START, NOW)
        price = random.choice([27, 497, 2500])
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'checkout', 'cart_abandoned', "
            f"'shopify', '{{\"total_price\": \"{price}\"}}', '{t.isoformat()}', '{t.isoformat()}');"
        )

    # 6e. Meeting events (opportunity - qualification)
    meeting_profiles = random.sample(sql_and_customer_ids, min(40, len(sql_and_customer_ids)))
    for pid in meeting_profiles:
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'meeting', 'meeting_booked', "
            f"'scheduling', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )
    # 70% completed
    for pid in random.sample(meeting_profiles, int(len(meeting_profiles) * 0.70)):
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'meeting', 'meeting_completed', "
            f"'scheduling', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )
    # 15% no-show
    no_show_profiles = [p for p in meeting_profiles if p not in random.sample(meeting_profiles, int(len(meeting_profiles) * 0.70))]
    for pid in random.sample(meeting_profiles, max(1, int(len(meeting_profiles) * 0.15))):
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'meeting', 'meeting_no_show', "
            f"'scheduling', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )
    # 10% rescheduled
    for pid in random.sample(meeting_profiles, max(1, int(len(meeting_profiles) * 0.10))):
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'meeting', 'meeting_rescheduled', "
            f"'scheduling', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )

    # 6f. Payment link events (opportunity)
    payment_profiles = random.sample(sql_and_customer_ids, min(25, len(sql_and_customer_ids)))
    for pid in payment_profiles:
        t = random_date(START, NOW)
        stmts.append(
            f"INSERT INTO journey_events (id, profile_id, tenant_id, event_type, event_name, "
            f"channel, properties, occurred_at, created_at) VALUES ("
            f"'{gen_uuid()}', '{pid}', '{TENANT_ID}', 'payment', 'payment_link_sent', "
            f"'sales-agent', '{{}}', '{t.isoformat()}', '{t.isoformat()}');"
        )

    stmts.append("")

    # =============================================
    # 7. SALES (revenue by offer)
    # =============================================
    stmts.append("-- Sales")

    # Realistic sales distribution across offers
    sales_config = [
        # (product_key, count, stage, source)
        ("N1_TRIPWIRE", 18, "CONVERSION", "SHOPIFY"),
        ("N2_GROUP", 8, "CONVERSION", "SALES_AGENT"),
        ("N3_MENTOR", 5, "CONVERSION", "SALES_AGENT"),
        ("N4_SERVICE", 3, "CONVERSION", "SALES_AGENT"),
        ("N5_MASTERMIND", 2, "CONVERSION", "SALES_AGENT"),
        ("N5_RETREAT", 2, "CONVERSION", "MANUAL"),
        # Expansion (renewals/upsells from existing customers)
        ("N2_GROUP", 3, "EXPANSION", "SALES_AGENT"),
        ("N3_MENTOR", 2, "EXPANSION", "SALES_AGENT"),
    ]

    sale_idx = 0
    for product_key, count, stage, source in sales_config:
        product = PRODUCTS[product_key]
        for _ in range(count):
            cid = customer_ids[sale_idx % len(customer_ids)]
            sale_idx += 1
            t = random_date(START + timedelta(days=5), NOW)
            amount = product["price"] * random.uniform(0.9, 1.1)  # slight variance
            payment = random.choice(["STRIPE", "CREDIT_CARD", "PAYPAL", "MANUAL"])

            stmts.append(
                f"INSERT INTO sales (id, tenant_id, customer_id, offer_id, transaction_id, "
                f"amount, currency, status, stage, source, payment_method, occurred_at, created_at) VALUES ("
                f"'{gen_uuid()}', '{TENANT_ID}', '{cid}', '{product['id']}', "
                f"'TXN-{gen_uuid()[:8].upper()}', "
                f"{round(amount, 2)}, '{product['currency']}', 'COMPLETED', '{stage}', "
                f"'{source}', '{payment}', '{t.isoformat()}', '{t.isoformat()}');"
            )
    stmts.append("")

    # =============================================
    # 8. CHANNEL COST SETTINGS
    # =============================================
    stmts.append("-- Channel Cost Settings")

    costs = [
        ("meta-ads", "platform", 1800, "USD", "paid_management"),
        ("google-ads", "platform", 1200, "USD", "paid_management"),
        ("mailerlite", "tool", 49, "USD", "organic_management"),
        ("meta-retargeting", "platform", 450, "USD", "paid_management"),
        ("ig-organic", "agency", 300, "USD", "organic_management"),
        ("fb-organic", "agency", 150, "USD", "organic_management"),
        ("yt-organic", "agency", 200, "USD", "organic_management"),
    ]

    for slug, cost_type, amount, currency, proration in costs:
        stmts.append(
            f"INSERT INTO channel_cost_settings (id, tenant_id, channel_slug, cost_type, "
            f"monthly_amount, currency, proration_category, is_active, created_at) VALUES ("
            f"'{gen_uuid()}', '{TENANT_ID}', '{slug}', '{cost_type}', "
            f"{amount}, '{currency}', '{proration}', true, '{NOW.isoformat()}');"
        )
    stmts.append("")

    # =============================================
    # 9. REFERRAL CODES + NPS (Evangelization)
    # =============================================
    stmts.append("-- Evangelization: Referral Codes")

    evangelist_ids = [pid for pid, s in profile_stages.items() if s == "EVANGELIST"]
    referral_codes = []
    for pid in evangelist_ids:
        code = f"VIS-{gen_uuid()[:6].upper()}"
        referral_codes.append((pid, code))
        stmts.append(
            f"INSERT INTO referral_codes (id, tenant_id, customer_id, code, source, is_active, created_at) VALUES ("
            f"'{gen_uuid()}', '{TENANT_ID}', '{pid}', '{code}', 'internal', true, '{NOW.isoformat()}');"
        )

    stmts.append("")
    stmts.append("-- Evangelization: NPS Surveys & Responses")

    # Create NPS surveys for all customers + evangelists
    nps_customer_ids = [pid for pid, s in profile_stages.items() if s in ("CUSTOMER", "EVANGELIST")]
    for pid in nps_customer_ids:
        survey_id = gen_uuid()
        token = f"nps-{gen_uuid()[:12]}"
        sent_at = random_date(START + timedelta(days=10), NOW)
        expires = sent_at + timedelta(days=14)

        stmts.append(
            f"INSERT INTO nps_surveys (id, tenant_id, token, customer_id, delivery_channel, "
            f"status, created_at, sent_at, expires_at) VALUES ("
            f"'{survey_id}', '{TENANT_ID}', '{token}', '{pid}', 'universal_link', "
            f"'completed', '{sent_at.isoformat()}', '{sent_at.isoformat()}', '{expires.isoformat()}');"
        )

        # 75% response rate
        if random.random() < 0.75:
            # Promoters (9-10): 60%, Passives (7-8): 25%, Detractors (0-6): 15%
            r = random.random()
            if r < 0.60:
                score = random.choice([9, 10])
                feedback = random.choice([
                    "Excelente programa, me cambió la vida!",
                    "Increíble mentoría, super recomendado",
                    "Las mejores herramientas para crecer mi negocio",
                    "Transformador. Resultados reales.",
                ])
            elif r < 0.85:
                score = random.choice([7, 8])
                feedback = random.choice([
                    "Buen contenido, me gustaría más seguimiento",
                    "Útil pero podría mejorar los materiales",
                    "Buena experiencia en general",
                ])
            else:
                score = random.randint(3, 6)
                feedback = random.choice([
                    "No cumplió del todo mis expectativas",
                    "Necesita mejorar la comunicación",
                ])

            responded = random_date(sent_at + timedelta(hours=2), min(sent_at + timedelta(days=7), NOW))
            consent = "true" if score >= 9 else "false"

            stmts.append(
                f"INSERT INTO nps_responses (id, tenant_id, survey_id, customer_id, score, "
                f"feedback_text, consent_public_use, responded_at) VALUES ("
                f"'{gen_uuid()}', '{TENANT_ID}', '{survey_id}', '{pid}', {score}, "
                f"'{feedback}', {consent}, '{responded.isoformat()}');"
            )

    stmts.append("")

    return "\n".join(stmts)


if __name__ == "__main__":
    sql = build_sql()

    # Write to file for execution
    output_path = "/tmp/seed_growth_studio.sql"
    with open(output_path, "w") as f:
        f.write("BEGIN;\n\n")
        f.write(sql)
        f.write("\n\nCOMMIT;\n")

    print(f"SQL written to {output_path}")
    print(f"Lines: {len(sql.splitlines())}")
    print("Run: psql -U postgres -d visionarias_logs -f /tmp/seed_growth_studio.sql")
