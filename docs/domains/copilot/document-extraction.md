# Document Extraction Pipeline

Anchor referencia para `[COPILOT-DOC-EXTRACTION-SSOT]` y `[COPILOT-DOC-EXTRACTION-PIPELINE]`.

## Objetivo

Cuando el usuario sube un documento (brief, brand book, perfil de avatar) el copilot debe:

1. Mapear el contenido a los **campos editables** del módulo destino (brand / offer / buyer_persona).
2. **Nunca** inventar paths que no existen en el catálogo.
3. Devolver un `preview_update` para que el usuario apruebe los cambios via `propose_field_updates`.

## Single Source of Truth

```
src/modules/copilot/domain/extraction_domain_registry.py
```

`ExtractionDomainConfig` por dominio: `template_name`, `persister_key`, `response_value_kind`. Todo el pipeline lee de aquí — no más duplicación entre `tools/guided/extract.py` y `tools/extract_from_doc.py`.

## Pipeline runtime

```
extract_document_to_fields(asset_id, domain)
  ↓ get_extraction_config(domain)  ← registry
  ↓ DocumentProcessor.extract_from_text(text, domain, …)
      ↓ build_field_paths_hint(domain)  ← deriva paths del catálogo editable
      ↓ prompt_loader.render(config.template_name, document_text, existing_data, field_paths_hint)
      ↓ ai_service.run_structured_action(action_name=f"{domain}_doc_extraction", response_model=DocumentExtractionResponse)
      ↓ DocumentExtractionResponse.extracted_fields: dict[str, Any]
        — acepta strings, listas, dicts (BuyerPersona pain_points = list[dict])
  ↓ ui_action: preview_update | clarify_card (recovery cuando falla)
```

## Templates

Convención: `interview/{domain}_doc_extraction.j2`. Cada template recibe:

- `document_text`: contenido extraído del asset.
- `existing_data`: mapa actual de la entidad (los campos llenos no se sobrescriben).
- `field_paths_hint`: bloque markdown auto-generado del catálogo editable + dict-parents dinámicos.

El template **no hardcodea paths**. Si cambias el catálogo `editable_fields_*.py`, el hint se actualiza automáticamente.

## Recovery UX

`extract_document_to_fields` nunca devuelve `extraction_failed` como texto crudo. Cuando falla:

```json
{
  "text": "Hubo un problema procesando el documento.",
  "error": "extraction_failed",
  "ui_action": {
    "type": "clarify_card",
    "clarify_items": [{
      "field_path": "{domain}.__doc_recovery__",
      "issue": "¿Qué quieres hacer?",
      "options": ["Reintentar", "Subir otro documento", "Llenar manualmente"]
    }]
  }
}
```

El `system prompt` (`copilot_system.j2` → "Manejo de errores de herramientas") instruye al LLM a NO regurgitar el JSON al chat — debe usar la card.

## Registrar un nuevo dominio

1. Agregar entrada a `EXTRACTION_DOMAINS` en `extraction_domain_registry.py`.
2. Crear `interview/{domain}_doc_extraction.j2`.
3. Registrar persister en `persister_registry.py` con la misma `persister_key`.
4. (Opcional) Si el catálogo editable distingue listas vs scalars, agregar al map `_LIST_PATHS` en `field_paths_hint.py`.
5. Tests: `test_extraction_domain_registry.py` debe contemplar el nuevo dominio.
