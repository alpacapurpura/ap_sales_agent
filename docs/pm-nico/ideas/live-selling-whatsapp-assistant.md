# live-selling-whatsapp-assistant

> Raw idea — capturada 2026-05-01 por /pm. No validada.

## Input verbatim (Chris)

"Brindarle a toda persona que haga un en vivo mi 'Número whatsapp', y que ese número de whatsapp actúe como si fuera un asistente virtual real. No quiero interfaces web, nada, solo un número de whatsapp con el que un microempresario se contacte y recargue 'por uso' donde el uso es el acompañamiento a un 'live' de tiktok.

El usuario nos pasa el link de la sesión o pone videollamada al numero, la cosa es que mientras hace el envivo, nosotros lo 'veamos' como si fuera un asistente y conforme el va promocionando y dando información, nosotros podamos no solo guardar el precio sino también la suficiente información como para que cuando los que esten viendo el en vivo puedan mandar screenshot de qué producto les gusta y el agente IA lo reciba al whatsapp que se le haya asociado, y que entregue la información del producto y pida el pago para gestionarlo y conforme van pagando vaya 'avisando' al que hace el en vivo 'venta realizada' de X producto y se vaya debitando del stock del en vivo.

Terminado el en vivo no hay memoria nada, es solo un asistente que ayuda por cada sesión.

Pienso cobrar por eso 20 a 50 soles dependiendo de la cantidad de productos / tiempo, como si fuera una persona solo que más fiable y atenta."

## Observaciones PM (raw)

- **Canal:** WhatsApp único — sin app, sin web, sin dashboard para el vendedor (raw idea; podría evolucionar).
- **Trigger:** En vivo TikTok (link o videollamada al número).
- **Core loop:**
  1. Vendedor inicia sesión → comparte catálogo/ephemeral stock.
  2. Espectadores ven producto → screenshot por WhatsApp al número.
  3. IA reconoce producto (visión?) → ofrece info + pago.
  4. Pago confirmado → notificación al vendedor + stock decrementado.
  5. Fin en vivo → memoria wiped (sesión efímera).
- **Pricing:** 20-50 PEN por sesión, variable por # productos / duración.
- **Target:** Microempresarios LATAM (Perú implícito por soles).
- **Sin memoria post-sesión:** interesante constraint — reduce compliance, simplifica infra.
- **Tecnología implícita:** WhatsApp Business API, visión por screenshot (classify image), pagos (Stripe/Yape/Plin?), TTS o notificación al vendedor en vivo.

## Preguntas JTBD pendientes (para validar)

1. ¿Job real del vendedor? "Vender más durante en vivo sin distracción" o "No perder ventas por no atender chat"?
2. ¿Job del comprador? "Comprar rápido sin salir de WhatsApp" o "No perderse ofertas del live"?
3. ¿Cómo asocia el screenshot al producto exacto? ¿Visión + OCR + matching contra ephemeral catalog?
4. ¿El vendedor configura stock antes o durante el live?
5. ¿Qué pasa si 2 personas compran última unidad simultáneamente?
6. ¿Recarga "por uso" = prepaid credits? ¿Stripe? ¿Yape/Plin local?

## Diferenciadores hipotéticos vs mercado

- **ZIG** = AI co-host para TikTok Live (monitorea chat, insights, NO WhatsApp checkout).
- **Popcorn AI / bitChat / Raimond / Incepticore / Wapikit** = WhatsApp AI sales agent 24/7 para e-commerce (NO ephemeral live-session, NO screenshot-to-buy).
- **Hello24 / Wazzy** = WhatsApp commerce con checkout integrado (NO vinculación a livestream real-time).

Diferenciador potencial: **sesión efímera vinculada a livestream + screenshot compra + notificación real-time al vendedor + pricing micro por uso**. Ninguno encontrado hace exactamente esto.

## Research de mercado (2026-05-01)

### TikTok Shop en Perú

- **TikTok Shop NO disponible en Perú** (a feb 2026). Llegó a México en enero 2025 como primer país LATAM. No hay fecha oficial para Perú (Acción Popular, El Comercio, Gestión, Seotical).
- **Modelo dominante hoy:** Emprendedores peruanos usan TikTok Live como descubrimiento + cierre por WhatsApp + Yape/Plin/transferencia. Es el estándar de facto.
- Los lives generan 3-5x más conversión que contenido estático. Mejores horarios: 8-10 pm L-V, 3-6 pm fines de semana (testimonios Lima).
- Existe riesgo de estafas por pagos fuera de app — confianza es pain point explícito.

### WhatsApp In-App Browser (Webviews) — Meta 2025-2026

- Meta lanzó **In-App Browser (IAB)** para WhatsApp Business API. Links en CTA buttons de templates abren **dentro de WhatsApp**, no en Chrome/Safari.
- **Soporta pagos** directamente. Usuario cierra con "X" y vuelve al chat.
- Requisito: negocio con **≥1,000 conversaciones iniciadas por día** (Wati.io, YCloud).
- Pasan contexto (teléfono como session identifier, cart details, tokens).
- **Esto habilita tu requisito "no salir de WhatsApp"** sin depender de app propia.

### Pagos en WhatsApp — Perú

| Opción | Qué es | Costo | Nota |
|---|---|---|---|
| **Plin WhatsApp** (Interbank, oct 2025) | Bot verificado de Interbank para plinear desde chat | Gratis | Límite S/100/tx, S/2000/día. Solo clientes Interbank. Envía audio/texto. Prueba de concepto real. |
| **Yape/Plin vía link de pago** | Culqi, ITPago, PayRequest generan links con checkout Yape/Plin | ~3.5-4% + S/1 por tx | Cliente paga en app bancaria, comprobante automático. |
| **ITPago** | Plataforma peruana todo-en-uno: catálogo + link pago + inventario | Planes desde ~S/50-200/mo | Caso real: cafetería en Lima redujo procesamiento de 8 min a 90 seg, ventas WhatsApp +240% Q1. |
| **PayRequest / Whinta** | Links de pago genéricos con 20+ métodos | Free tier + % por tx | No Yape/Plin nativo, tarjetas sí. |

**Insight:** Plin WhatsApp de Interbank demuestra que **el canal es viable y deseado** en Perú. Tu idea sería "Plin WhatsApp para emprendedores de TikTok Live".

### AI Visual Search / Reconocimiento de producto por screenshot

| Solución | Precio | Accuracy | Nota |
|---|---|---|---|
| **Google Vision API Product Search** | Free tier $300, luego por uso | Alta para catálogo pre-indexado | Requiere crear catalog+product set+index. Soporta homegoods, apparel, toys, packaged goods, general. |
| **Wizzy.ai Visual Search** | Desde $149/mo | 94% claim | Shopify-focused. Soporta screenshots de social media. |
| **AlFinder** | Custom | >95% | Soporta multi-object detection (outfit completo). Screenshots con UI overlays/watermarks OK. |
| **Pic2Product** | Free trial + API keys | 95%+ | Fashion, home decor, electronics. RESTful API. |
| **SnapMatch (Shopify)** | $19-199/mo | — | Google AI powered. 1,000-25,000 searches/mo. |
| **nyris** | Enterprise | 95%+ | B2B/industrial focus. Object detection + segmentation + OCR. |
| **SightScout** | $24.99-299.99/mo | — | Text + semantic + visual unified. Generous free tier. |

**Viabilidad técnica:** Reconocer producto por screenshot contra catálogo de 50 ítems es **trivial** con Google Vision API o modelos open-source (CLIP). No necesitas enterprise tier. El challenge no es la visión — es **matching preciso cuando el screenshot tiene UI overlay de TikTok** (comentarios, corazones, usuario). Necesita:
1. Object detection primero (¿dónde está el producto en la imagen?)
2. OCR para extraer texto visible en screenshot (precio, nombre)
3. Matching contra ephemeral catalog (50 SKUs)

Para 50 productos por sesión, ni siquiera necesitas vector DB — un catálogo en memoria con embeddings CLIP es suficiente.

### Competidores directos e indirectos

| Competidor | Qué hace | Diferenciador de tu idea |
|---|---|---|
| **ZIG** ($20-50/mo) | AI co-host para TikTok Live — monitorea chat, insights | NO WhatsApp, NO checkout, NO ephemeral session |
| **Popcorn AI** ($149-299/mo) | WhatsApp sales agent 24/7 con catálogo Shopify | NO livestream binding, NO screenshot-to-buy, NO wipe post-session |
| **bitChat / Raimond / Incepticore** | WhatsApp commerce general | Mismo gap: no livestream ephemeral |
| **ITPago** | Links de pago + catálogo + inventario para WhatsApp | NO AI asistente contextual al live, NO screenshot matching, NO notificación real-time al vendedor |
| **Plin WhatsApp** (Interbank) | Transferencias P2P desde WhatsApp | NO comercio, NO catálogo, NO asistente de ventas |

**Conclusión:** No existe competidor directo. Hay **competidores parciales** en cada capa (chat insights, WhatsApp commerce, links de pago). Tu diferenciador compuesto = **livestream context + ephemeral session + screenshot buy + real-time seller notification**.

## Viabilidad técnica — resumen

| Componente | Viabilidad | Complejidad | Opciones |
|---|---|---|---|
| WhatsApp Business API | ✅ Alta | Media | Baileys (open source, no puppeteer), Wati, 360dialog, o WhatsApp Cloud API directo |
| Reconocimiento screenshot → producto | ✅ Alta | Baja-Media | Google Vision API Product Search, CLIP + Pinecone/Qdrant local, o simplemente OCR + fuzzy match para 50 SKUs |
| Checkout in-WhatsApp | ✅ Alta | Media | WhatsApp Webviews (Meta IAB) para templates, o link Culqi/Yape que abre en in-app browser |
| Notificación real-time al vendedor | ✅ Alta | Baja | WebSocket/WhatsApp message al número del vendedor |
| Pagos Yape/Plin | ✅ Alta | Media | Culqi/ITPago links con Yape QR. Plin WhatsApp aún no tiene API pública para comercios. |
| Stock efímero por sesión | ✅ Alta | Baja | Redis / Postgres session-scoped. Wipe al finalizar live. |
| Precio variable 20-50 PEN por sesión | ✅ Alta | Baja | Stripe/Culqi con monto dinámico, o prepaid credits system |

**No hay componente imposible.** La complejidad está en **orquestación en tiempo real** (livestream → WhatsApp → AI → pago → notificación → stock) y en **UX sin fricción** (screenshot debe ser suficiente, sin que el comprador escriba nada).

## Riesgos identificados

1. **WhatsApp Business API session stability** — wwebjs tiene reportes masivos de desconexiones cada 2-3 días. Baileys (WebSocket nativo) es más estable. Si usas WhatsApp Cloud API oficial (Meta), es estable pero tiene costo por conversación.
2. **Plin/Yape como método de pago** — Yape no tiene API oficial para comercios (solo P2P). Culqi/ITPago simulan link con QR Yape/Plin. El comprador debe salir brevemente a su app bancaria, escanear QR, y volver. Con IAB (in-app browser) esto es "dentro de WhatsApp".
3. **Screenshot quality** — TikTok UI overlay (comentarios, botones) puede confundir visión. Necesita pre-processing (crop, object detection) o fallback a "¿te refieres a [producto X]?" con 2-3 opciones.
4. **Concurrencia** — Si 500 personas ven el live y 20 mandan screenshot simultáneo, el bot debe escalar. WhatsApp Cloud API maneja rate limits; Baileys en self-hosted requiere cuidado.
5. **Legal/Compliance** — Procesar pagos en Perú requiere RUC, facturación electrónica (Sunat). Si cobras 20-50 PEN por sesión, eres pasarela de pagos? O servicio de software? Revisar con abogado local.

## Estado

**Idea validada como realizable.** Ningún componente bloqueante. Ningún competidor directo.

**Próximo paso:** Si Chris quiere avanzar → migrar a `opportunities/` con JTBD + OST + soluciones alternativas + RICE/WSJF vs otros proyectos. Si no → queda en `ideas/`.
