# Reglas de Diseño Orientado a Dominio (DDD)

Para garantizar la mantenibilidad y escalabilidad del Monolito Modular, se aplican estrictamente las siguientes reglas:

## 1. Separación Estricta: Dominio vs Infraestructura

### 🛑 Regla de Oro
**La capa de Dominio (`domain/`) JAMÁS debe conocer la Infraestructura.**

- **Prohibido**: Importar `sqlalchemy`, `fastapi` o cualquier librería externa de infraestructura en `domain/`.
- **Prohibido**: Heredar modelos de dominio de `Base` (SQLAlchemy).
- **Permitido**: Usar `Pydantic` (esquemas puros), tipos nativos de Python (`dataclasses`, `enums`, `typing`).

### ¿Por qué?
Si tu lógica de negocio depende de la base de datos, no puedes probarla sin una base de datos, y cambiar de base de datos implica reescribir tu negocio.

---

## 2. Modelado de Entidades

### Entidades de Dominio (Pydantic)
Ubicación: `src/modules/{modulo}/domain/`

Son objetos ricos que encapsulan datos y reglas de negocio.
```python
# ✅ CORRECTO
from pydantic import BaseModel, Field

class User(BaseModel):
    id: str
    email: str
    is_active: bool = True

    def activate(self):
        self.is_active = True
```

```python
# ❌ INCORRECTO
from src.shared.infrastructure.db.base_model import Base # ERROR: Acoplamiento a DB

class User(Base):
    __tablename__ = "users"
    ...
```

### Modelos de Persistencia (SQLAlchemy)
Ubicación: `src/modules/{modulo}/infrastructure/models/`

Son representaciones de las tablas de la base de datos. Solo deben usarse en la capa de infraestructura (Repositorios).

```python
# ✅ CORRECTO
from sqlalchemy import Column, String, Boolean
from src.shared.infrastructure.db.base_model import Base

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
```

---

## 3. El Rol del Repositorio

El Repositorio es el **traductor** entre el mundo del Dominio y el mundo de la Persistencia.

- **Input**: Recibe entidades de Dominio o IDs.
- **Proceso**: Convierte Dominio -> Modelo DB (para guardar) o Modelo DB -> Dominio (para leer).
- **Output**: Devuelve siempre entidades de Dominio.

**Ejemplo de Flujo:**
1. `Service` llama a `repo.get_user(id)`.
2. `Repository` hace query a `UserModel` (SQLAlchemy).
3. `Repository` convierte `UserModel` -> `User` (Pydantic).
4. `Repository` devuelve `User`.
5. `Service` trabaja con `User` puro.

---

## 4. Comunicación entre Módulos

Los módulos son independientes y no deben compartir tablas ni modelos.

- **Prohibido**: Hacer `JOIN` entre tablas de diferentes módulos.
- **Prohibido**: Importar un `Repository` de otro módulo directamente.
- **Correcto**:
    - **Síncrono**: Llamar a la capa `Application` (Servicio) del otro módulo.
    - **Asíncrono (Preferido)**: Emitir un Evento de Dominio (`UserCreated`) que el otro módulo escucha.
