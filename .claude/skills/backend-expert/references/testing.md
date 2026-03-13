# Testing Backend

El backend usa `pytest` y `pytest-asyncio`.
Cobertura exigida: Logica critica de negocio (Capa de Aplicacion y Dominio) debe estar probada.

- **Capa de Aplicacion:** Usar `unittest.mock.Mock` o `AsyncMock` para simular los repositorios y servicios externos. No usar la base de datos real para testear la logica de negocio pura.
- **Capa API (Integracion):** Usar `TestClient` o `AsyncClient` de `httpx` junto con una base de datos temporal (Test DB) o sobrescribiendo la dependencia de la base de datos (`app.dependency_overrides`).
- **Nombres de Tests:** Formato `test_[nombre_funcion]_[condicion]_[resultado_esperado]`. Ejemplo: `test_create_offer_with_invalid_data_raises_error`.

### 1. Ubicacion de los Tests

- **Tests de Modulo (Unitarios e Integracion Aislada)**:
    - Ubicacion: `src/modules/{nombre_modulo}/tests/`
    - **Unit Tests**: Pruebas de Servicios de Dominio, Entidades y Casos de Uso aislados (mocking de repositorios).
    - **Integration Tests**: Pruebas de Repositorios contra una DB real (usando contenedores de prueba) o pruebas de API del modulo especifico.

- **Tests de Sistema (End-to-End / Cross-Module)**:
    - Ubicacion: `backend/tests/integration/`
    - Pruebas que involucran multiples modulos o flujos completos de usuario que atraviesan todo el sistema.

### 2. Ejecucion de Tests

Los tests deben ejecutarse **dentro del contenedor Docker** para garantizar consistencia de entorno (especialmente para acceso a DB y dependencias de sistema).

```bash
# Ejecutar todos los tests del proyecto
docker exec -t visionarias_brain_dev pytest

# Ejecutar tests de un modulo especifico
docker exec -t visionarias_brain_dev pytest src/modules/iam/tests

# Ejecutar un test especifico con logs (-s)
docker exec -t visionarias_brain_dev pytest src/modules/iam/tests/unit/test_auth_service.py -s
```

### 3. Fixtures y Configuracion (`conftest.py`)

- **Global**: `backend/tests/conftest.py` (Configuracion de DB compartida, cliente HTTP global).
- **Modulo**: `src/modules/{modulo}/tests/conftest.py` (Fixtures especificos del modulo, e.g., `mock_user`, `mock_order`).

### 4. Guia para Escribir Tests

#### Unit Tests (Servicios)
Usar `pytest-mock` o `unittest.mock` para aislar la logica de negocio de la infraestructura.

```python
# Ejemplo: test_user_service.py
def test_create_user_success(mock_user_repo):
    service = UserService(repo=mock_user_repo)
    user = service.create_user(email="test@example.com")
    assert user.email == "test@example.com"
    mock_user_repo.save.assert_called_once()
```

#### Integration Tests (Repositorios/API)
Usar la base de datos de prueba (limpiada despues de cada test).

```python
# Ejemplo: test_user_repo.py
@pytest.mark.asyncio
async def test_save_user(db_session):
    repo = UserRepository(db_session)
    user = User(email="real@db.com")
    await repo.save(user)

    saved = await repo.get_by_email("real@db.com")
    assert saved is not None
```

## Reglas de Oro
1. **No Mockear lo que no posees**: En tests de integracion, usar la implementacion real (DB en Docker). En unitarios, mockear interfaces propias.
2. **Limpieza de Datos**: Asegurar que cada test deje la DB en un estado limpio (usar transacciones rollback en `conftest.py`).
3. **Velocidad**: Los tests unitarios deben correr en milisegundos. Si tocan DB, son de integracion.
