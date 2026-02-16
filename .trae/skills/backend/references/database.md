# Base de Datos y Persistencia

## Stack
- **Base de Datos**: PostgreSQL 15.
- **ORM**: SQLAlchemy (Async).
- **Migraciones**: Alembic.
- **Vector Store**: Qdrant (para RAG).

## Modelado de Datos

Los modelos se definen en `src/services/db/models`. Todos deben heredar de `Base`.
Se debe usar tipado estricto y columnas explícitas.

```python
from sqlalchemy import Column, String, Boolean
from src.services/db/base import Base

class User(Base):
    __tablename__ = "users"
    # Definición de campos
    is_vip = Column(Boolean, default=False)
```

## Patrón Repository

NUNCA acceder a la sesión de DB directamente desde los controladores/endpoints.
Usar Repositorios ubicados en `src/services/db/repositories`.

```python
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        # Implementación
```

## 🛡️ Pipeline de Migración (OBLIGATORIO)

Para cualquier cambio en el esquema, seguir este flujo ESTRICTO.
**PROHIBIDO**: Usar `db.create_all()` o scripts SQL manuales.

### 1. Modificar Modelo
Editar el archivo Python en `src/services/db/models/`.

### 2. Generar Migración
Desde la carpeta raíz del backend:

```bash
cd backend
alembic revision --autogenerate -m "descripcion_del_cambio"
```

### 3. Blindar Migración (Defensive Programming)
**CRÍTICO**: Editar SIEMPRE el archivo generado en `alembic/versions/`.
Las migraciones automáticas NO son seguras para producción. Debes usar el patrón `inspector` para evitar errores si columnas o constraints ya existen.

**Template Obligatorio:**

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # 1. Verificar columnas antes de añadir
    columns = [c['name'] for c in inspector.get_columns('my_table')]
    if 'new_column' not in columns:
        op.add_column('my_table', sa.Column('new_column', sa.String(), nullable=True))

    # 2. Verificar constraints antes de crear
    constraints = [c['name'] for c in inspector.get_unique_constraints('my_table')]
    if 'uq_my_constraint' not in constraints:
        op.create_unique_constraint('uq_my_constraint', 'my_table', ['col1', 'col2'])

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Operaciones inversas también verificadas
    columns = [c['name'] for c in inspector.get_columns('my_table')]
    if 'new_column' in columns:
        op.drop_column('my_table', 'new_column')
```

### 4. Aplicar Migración
```bash
alembic upgrade head
```
