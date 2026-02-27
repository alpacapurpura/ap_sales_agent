# Plan Final: Sistema Híbrido de WhatsApp (Validado 2026)

He realizado la investigación actualizada a **Febrero 2026** y confirmo que la estrategia híbrida sigue siendo la óptima.

### 🔍 Hallazgos Clave (Estado del Arte 2026)
1.  **Evolution API (QR)**: Sigue siendo el estándar *open-source* líder para integraciones "tipo usuario" (Scan & Go). Es la base de muchas soluciones SaaS modernas por su flexibilidad.
2.  **Meta Cloud API (Oficial)**: Meta ha facilitado el onboarding ("Embedded Signup"), pero la **verificación de negocio** sigue siendo una barrera para usuarios pequeños.
3.  **Coexistencia**: Aunque Meta ha mejorado la coexistencia (usar App + API), sigue siendo complejo y riesgoso para el usuario promedio configurarlo sin ayuda técnica.

### 🚀 Propuesta UX Refinada (Pantalla de Selección)
Diseñaremos una pantalla de "Elección de Camino" clara y honesta:

*   **Camino A: "Modo Personal / Startup" (QR)** ⚡ *Tu elección inicial*
    *   **Ventaja:** Escaneas y funcionas en 1 minuto.
    *   **App Móvil:** ✅ Sigues usando tu WhatsApp normal en tu celular.
    *   **Riesgo:** Si envías spam masivo, Meta puede desconectarte (tecnología basada en WhatsApp Web).
    *   **Tecnología:** Evolution API (Self-hosted).

*   **Camino B: "Modo Empresarial" (Oficial)** 🏢 *Para escalar*
    *   **Ventaja:** Estabilidad total y "Green Tick" posible.
    *   **App Móvil:** ⚠️ El número pasa a la nube. Pierdes el acceso directo desde la App de WhatsApp (usarías nuestro Dashboard).
    *   **Requisito:** Verificación de Facebook Business Manager.
    *   **Tecnología:** Meta Cloud API.

---

### 🛠️ Plan de Implementación Inmediata (Opción A - QR)

Una vez apruebes este plan, comenzaré con la implementación del **Modo QR** (Evolution API) para cumplir con tu requisito de "solución más sencilla".

1.  **Infraestructura**: Desplegar `evolution-api` v2 en Docker.
2.  **Backend**: Crear `WhatsAppService` para gestionar la sesión y el QR.
3.  **Frontend**: Implementar la **Pantalla de Selección** (dejando la Opción B inhabilitada o como "Próximamente" por ahora) y el **Escáner QR**.

¿Autorizas el inicio de la implementación del **Modo QR**?