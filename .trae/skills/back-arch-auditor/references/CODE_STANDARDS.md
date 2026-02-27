# Lista de Convenciones de Código (Code Standards)

Estas reglas de estilo son **MANDATORIAS** y no negociables para mantener la coherencia y calidad del código backend.

## 1. Naming Conventions (Estricto)

### Archivos y Carpetas: `snake_case`
Todo nombre de archivo o directorio debe estar en minúsculas y usar guiones bajos como separadores.
- ✅ `user_service.py`, `sales/`, `api_client.py`
- ❌ `UserService.py`, `Sales/`, `APIClient.py`

### Clases y Tipos: `PascalCase`
Los nombres de Clases, Pydantic Models, Exceptions y TypeAliases deben usar Capitalización Pascal.
- ✅ `class UserRepository:`, `class UserDTO(BaseModel):`
- ❌ `class user_repository:`, `class userDTO:`

### Funciones, Métodos y Variables: `snake_case`
Todo nombre de función, método o variable local debe estar en minúsculas con guiones bajos.
- ✅ `def get_user_by_id():`, `user_name = "John"`
- ❌ `def getUserById():`, `userName = "John"`

### Constantes: `UPPER_CASE`
Las variables globales constantes deben estar en mayúsculas sostenidas con guiones bajos.
- ✅ `MAX_RETRIES = 5`, `DEFAULT_TIMEOUT = 30`
- ❌ `MaxRetries = 5`, `defaultTimeout = 30`

### Miembros Privados: `_leading_underscore`
Métodos o atributos internos de una clase/módulo deben prefijarse con un guión bajo.
- ✅ `def _internal_helper(self):`
- ❌ `def internalHelper(self):`

## 2. Typing (Estricto)
- **Todas las funciones públicas** deben tener anotaciones de tipo completas (argumentos y retorno).
- Usar `Optional[T]` o `T | None` para valores que pueden ser nulos.
- Usar `List[T]`, `Dict[K, V]` o las versiones genéricas `list[T]`, `dict[K, V]` (Python 3.9+).

```python
# ✅ CORRECTO
def calculate_total(items: list[Product], discount: float | None = None) -> float:
    ...

# ❌ INCORRECTO
def calculate_total(items, discount=None):
    ...
```

## 3. Manejo de Errores
- Usar excepciones personalizadas de dominio (`DomainError`) definidas en `src/modules/{name}/domain/exceptions.py`.
- **Nunca** retornar `None` para indicar error; levantar una excepción.
- Capturar excepciones específicas en la capa de aplicación y transformarlas en `HTTPException` en la capa API si es necesario, pero preferiblemente dejar que el middleware global maneje errores no controlados.

## 4. Estructura de Archivos
- **Orden de Imports**:
    1. Librerías estándar (`os`, `sys`).
    2. Librerías de terceros (`fastapi`, `sqlalchemy`).
    3. Módulos locales (`src.shared...`, `src.modules...`).
- **Definiciones**: Constantes primero, luego Clases/Funciones.
