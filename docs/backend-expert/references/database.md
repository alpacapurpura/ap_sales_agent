# Base de Datos y Persistencia

## Stack Tecnológico
- **Base de Datos**: PostgreSQL 15.
- **ORM**: SQLAlchemy (Async) + Alembic (Migraciones).
- **Vector Store**: Qdrant (para RAG y Búsqueda Semántica).
- **Cache**: Redis (para sesiones y estados efímeros).

## 🏗️ Modelado de Datos (Modular)

En la arquitectura **Modular Monolith**, cada módulo gestiona sus propias tablas y modelos.

### Ubicación de Modelos
Los modelos de base de datos (SQLAlchemy) se definen en:
`src/modules/{nombre_modulo}/infrastructure/models/`

Todos los modelos deben heredar de `Base` (importado de `src/shared/infrastructure/db/base_model.py` o similar).

```python
# Ejemplo: src/modules/iam/infrastructure/models/user_model.py
from sqlalchemy import Column, String, Boolean
from src.shared.infrastructure.db.base_model import Base

class UserModel(Base):
    __tablename__ = "iam_users"  # Prefijo del módulo recomendado
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
```

### Reglas de Modelado
1.  **Prefijos de Tabla**: Usar el nombre del módulo como prefijo para evitar colisiones (e.g., `iam_users`, `sales_deals`).
2.  **Tipado Estricto**: Definir tipos de columnas explícitos.
3.  **Relaciones**: Definir relaciones (Foreign Keys) SOLO dentro del mismo módulo.
    -   **Prohibido**: Relaciones directas (SQL JOINs) entre tablas de diferentes módulos.
    -   **Alternativa**: Almacenar IDs externos (e.g., `customer_id` en `OrderModel`) y resolver la entidad en la capa de aplicación.

---

## 🛡️ Patrón Repository

El acceso a datos se abstrae mediante Repositorios.
**Ubicación**: `src/modules/{nombre_modulo}/infrastructure/repositories/`

El repositorio implementa una interfaz definida en el Dominio (`domain/interfaces.py`).

```python
# Ejemplo: src/modules/iam/infrastructure/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.iam.domain.interfaces import IUserRepository
from src.modules.iam.domain.entities import User
from src.modules.iam.infrastructure.models.user_model import UserModel

class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            return User.model_validate(model) # Conversión a Entidad de Dominio
        return None
```

---

## 🔄 Migraciones (Alembic)

Para cualquier cambio en el esquema de base de datos, sigue este flujo estricto:

1.  **Modificar Modelo**: Editar el archivo Python en `infrastructure/models/`.
2.  **Generar Migración**:
    Desde la carpeta raíz del backend (`backend/`):
    ```bash
    alembic revision --autogenerate -m "feat: add user active flag"
    ```
3.  **Verificar Migración**:
    Revisar el archivo generado en `alembic/versions/`. Asegurarse de que detectó los cambios correctamente.
    
    **Defensive Programming (Opcional pero Recomendado)**:
    Si es una migración crítica en producción, usar el patrón `inspector` para verificar existencia de columnas antes de añadir/borrar.

4.  **Aplicar Migración**:
    ```bash
    alembic upgrade head
    ```

**Nota Importante**: Asegúrate de que el nuevo modelo esté importado en `backend/src/main.py` o en `alembic/env.py` para que Alembic lo detecte al autogenerar.
