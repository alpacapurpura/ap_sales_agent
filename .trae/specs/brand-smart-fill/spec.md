# Brand Smart Fill Spec

## Why
Los nuevos usuarios del Brand Studio enfrentan una barrera de entrada alta al tener que llenar manualmente múltiples campos. El objetivo es facilitar la carga inicial mediante un "Llenado Inteligente" que extraiga y estructure automáticamente esta información desde su web (incluyendo subpáginas) y documentos. Además, permitir actualizaciones posteriores para refinar la información existente.

## What Changes
### Frontend
- **Nuevo Componente `SmartFillCard`**:
  - **Modo Inicial**:
    - Input para URL y Textarea (Documentos/Contexto).
    - Mensaje claro: "Web y Documentos son complementarios. Más información ayuda, pero no es obligatoria."
    - Advertencia: "Información sensible (Legal, RUC) requerirá verificación manual."
  - **Modo Actualización (2da vez en adelante)**:
    - UI diferenciada ("Refinar Información").
    - Input opcional para describir qué actualizar (ej: "Actualizar solo la historia").
    - Lógica de "Comparar y Mejorar" en el backend.
  - **Feedback y Bloqueo**:
    - Bloqueo de UI durante la extracción (puede tardar).
    - Barra de progreso o pasos visuales ("Analizando Home", "Buscando Equipo", "Generando Estrategia...").
  - **Resumen Final**:
    - Modal o reporte al finalizar: "Se han llenado X campos. Por favor revisa Y y Z."

### Backend
- **Endpoint `/api/tools/extract-full-brand` (Actualizado)**:
  - Acepta `url`, `context_text`, `mode` ("initial" | "update"), y `update_instructions` (opcional).
  - **Deep Crawling**: El extractor debe navegar links relevantes (`/about`, `/team`, `/contact`, `/story`) para obtener contexto completo.
  - **Multi-Step Extraction**:
    - Paso 1: Crawling y Análisis de estructura.
    - Paso 2: Extracción de Identidad y Visuales.
    - Paso 3: Generación de Estrategia y Historia (calidad > velocidad).
    - Paso 4: Extracción de Equipo y Testimonios.
  - **Lógica de Actualización**:
    - En modo "update", el prompt recibe la data actual + nueva info y decide qué mejorar/reemplazar.
  - **Persistencia**: Guardado automático en DB tras la extracción inicial.
  - **Prompts**: Todos los prompts deben residir en `backend/src/core/prompts/brand_extraction/`.

## Impact
- **Affected Specs**: Brand Studio.
- **Affected Code**:
  - `frontend/src/features/brand/components/container/brand-studio-layout.tsx`
  - `backend/src/core/agents/web_extractor/` (Graph logic upgrade).
  - `backend/src/core/prompts/` (New folder).

## ADDED Requirements
### Requirement: Deep Crawling
El sistema DEBE ser capaz de "nadar" en los links del sitio web (About Us, Team, Contacto) para extraer información que no está en el Home.

### Requirement: Quality & Conciseness
- La extracción se prioriza por CALIDAD, permitiendo múltiples llamadas al LLM si es necesario.
- Los campos de texto (Historia, Misión) deben ser CONCISOS (max ~300-500 caracteres por sección clave) y directos.

### Requirement: Update Mode
- Si ya existe información, el sistema entra en "Modo Actualización".
- El prompt de actualización debe considerar: `Current Data` + `New Data` + `User Instructions` -> `Improved Data`.

### Requirement: Progress Feedback
- El usuario debe ver el progreso paso a paso.
- La interfaz debe bloquearse para evitar inconsistencias durante la escritura.

## MODIFIED Requirements
### Requirement: Prompts Storage
Todos los prompts de extracción y generación deben estar centralizados en archivos `.txt` o `.py` dentro de `backend/src/core/prompts/`.
