# Arquitectura Backend: Monolito Modular (DDD)

El proyecto Visionarias Brain sigue una arquitectura de **Monolito Modular** estrictamente alineada con los principios de **Domain-Driven Design (DDD)** y **Clean Architecture**.

El objetivo es mantener la agilidad de un monolito (despliegue unico, base de codigo unificada) pero con la separacion de responsabilidades y escalabilidad logica de los microservicios.

## Estructura de Directorios

La raiz del codigo fuente es `backend/src/`.

### 1. Modulos de Negocio (`src/modules/`)
Cada carpeta dentro de `modules` representa un **Bounded Context** (Contexto Delimitado) autonomo.

#### Estructura Interna de un Modulo
Cada modulo DEBE seguir esta estructura de capas:

```text
src/modules/{nombre_modulo}/
+-- api/                  # CAPA DE INTERFAZ (Transporte)
|   +-- router.py         # Router principal (o multiples archivos por recurso)
|   +-- dependencies.py   # Inyeccion de dependencias (opcional)
|   +-- dto/              # Carpeta para esquemas Pydantic (Request/Response)
|
+-- application/          # CAPA DE APLICACION (Casos de Uso)
|   +-- services/         # Logica de negocio (o archivos *_service.py)
|   +-- agents/           # Agentes de IA (LangGraph) especificos del modulo
|   +-- orchestrators/    # Coordinadores de flujos complejos
|
+-- domain/               # CAPA DE DOMINIO (Reglas de Negocio Puras)
|   +-- entities.py       # Modelos de Dominio (Pydantic, NO ORM)
|   +-- enums.py          # Enumeraciones y constantes
|   +-- exceptions.py     # Excepciones especificas del dominio
|   +-- schemas.py        # Definiciones de tipos/interfaces adicionales
|
+-- infrastructure/       # CAPA DE INFRAESTRUCTURA (Implementacion Tecnica)
|   +-- models/           # Modelos de Base de Datos (SQLAlchemy)
|   +-- repositories/     # Implementacion de Repositorios (SQLAlchemy)
|   +-- external/         # Clientes HTTP, Adaptadores de servicios externos
|
+-- tests/                # Tests aislados del modulo (Unitarios/Integracion)
```

### 2. Nucleo Compartido (`src/shared/`)
Codigo reutilizable que NO pertenece a ningun dominio especifico.
- `application/`: Utilidades de aplicacion generales.
- `core/`: Configuracion global, Logging (`structlog`), Excepciones base.
- `domain/`: Tipos basicos, Interfaces genericas.
- `infrastructure/`: Configuracion de DB (`session.py`), Cliente HTTP base, Seguridad.
- `utils/`: Herramientas auxiliares (fechas, hashing).

## Flujo de Datos (Request-Response)

1. **Request**: Llega a `api/routers.py`. Se valida con DTOs.
2. **Delegacion**: El router llama al Servicio de Aplicacion (`application/services/`).
3. **Orquestacion**: El servicio aplica reglas de negocio.
   - Si necesita datos, llama al Repositorio (inyectado como interfaz).
   - Si necesita IA, llama al Agente o Servicio de IA.
4. **Persistencia**: El Repositorio (`infrastructure/repositories/`) traduce la entidad de Dominio a Modelo ORM y ejecuta la query.
5. **Retorno**: Los datos fluyen de vuelta hacia arriba, siempre convertidos a Entidades de Dominio o DTOs antes de salir de la capa correspondiente.

## Reglas de Arquitectura

1. **Regla de Dependencia**: Las capas internas (Dominio) NO deben conocer a las externas (Infraestructura, API).
   - *Correcto*: `Infrastructure` importa `Domain`.
   - *Incorrecto*: `Domain` importa `SQLAlchemy`.
2. **Aislamiento de Modulos**:
   - Un modulo NO puede importar directamente codigo de otro modulo (excepto interfaces publicas o DTOs compartidos, aunque se prefiere evitar).
   - La comunicacion entre modulos debe ser via **Eventos** (Asincrono) o llamadas a **Servicios Publicos** explicitos.
   - **NUNCA** hacer JOINS entre tablas de diferentes modulos.
3. **State Management (IA)**:
   - El estado de los agentes (LangGraph) se gestiona como parte de la infraestructura de IA, pero las definiciones de estado pueden vivir en `application` o `domain` segun su complejidad.
