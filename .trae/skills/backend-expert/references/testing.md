# Testing Backend

* El backend usa `pytest` y `pytest-asyncio`.  
* Cobertura exigida: Lógica crítica de negocio (Capa de Aplicación y Dominio) debe estar probada.  
* **Capa de Aplicación:** Usa `unittest.mock.Mock` o `AsyncMock` para simular los repositorios y servicios externos. No uses la base de datos real para testear la lógica de negocio pura.  
* **Capa API (Integración):** Usa `TestClient` o `AsyncClient` de `httpx` junto con una base de datos temporal (Test DB) o sobrescribiendo la dependencia de la base de datos (`app.dependency_overrides`).  
* **Nombres de Tests:** Formato `test_[nombre_funcion]_[condicion]_[resultado_esperado]`. Ejemplo: `test_create_offer_with_invalid_data_raises_error`.


### 1. Ubicación de los Tests

- **Tests de Módulo (Unitarios e Integración Aislada)**:
    - Ubicación: `src/modules/{nombre_modulo}/tests/`
    - **Unit Tests**: Pruebas de Servicios de Dominio, Entidades y Casos de Uso aislados (mocking de repositorios).
    - **Integration Tests**: Pruebas de Repositorios contra una DB real (usando contenedores de prueba) o pruebas de API del módulo específico.

- **Tests de Sistema (End-to-End / Cross-Module)**:
    - Ubicación: `backend/tests/integration/`
    - Pruebas que involucran múltiples módulos o flujos completos de usuario que atraviesan todo el sistema.


### 2. Ejecución de Tests

Los tests deben ejecutarse **dentro del contenedor Docker** para garantizar consistencia de entorno (especialmente para acceso a DB y dependencias de sistema).

```bash
# Ejecutar todos los tests del proyecto
docker exec -t visionarias_brain_dev pytest

# Ejecutar tests de un módulo específico
docker exec -t visionarias_brain_dev pytest src/modules/iam/tests

# Ejecutar un test específico con logs (-s)
docker exec -t visionarias_brain_dev pytest src/modules/iam/tests/unit/test_auth_service.py -s
```

### 3. Fixtures y Configuración (`conftest.py`)

- **Global**: `backend/tests/conftest.py` (Configuración de DB compartida, cliente HTTP global).
- **Módulo**: `src/modules/{modulo}/tests/conftest.py` (Fixtures específicos del módulo, e.g., `mock_user`, `mock_order`).

### 4. Guía para Escribir Tests

#### Unit Tests (Servicios)
Usar `pytest-mock` o `unittest.mock` para aislar la lógica de negocio de la infraestructura.

```python
# Ejemplo: test_user_service.py
def test_create_user_success(mock_user_repo):
    service = UserService(repo=mock_user_repo)
    user = service.create_user(email="test@example.com")
    assert user.email == "test@example.com"
    mock_user_repo.save.assert_called_once()
```

#### Integration Tests (Repositorios/API)
Usar la base de datos de prueba (limpiada después de cada test).

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

---

## 🛑 Reglas de Oro
1.  **No Mockear lo que no posees**: En tests de integración, usa la implementación real (DB en Docker). En unitarios, mockea interfaces propias.
2.  **Limpieza de Datos**: Asegurar que cada test deje la DB en un estado limpio (usar transacciones rollback en `conftest.py`).
3.  **Velocidad**: Los tests unitarios deben correr en milisegundos. Si tocan DB, son de integración.
