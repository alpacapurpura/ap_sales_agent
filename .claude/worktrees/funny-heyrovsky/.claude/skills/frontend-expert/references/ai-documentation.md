# AI-First Documentation Standards

Para maximizar la eficiencia de agentes AI trabajando en este codebase, todo el codigo debe documentarse con "AI Intent" en mente.

## 1. The "Why" over "What"
Los agentes AI pueden leer el codigo para saber *que* hace. Necesitan comentarios para entender *por que* existe y *como* encaja en el sistema.

**Malo:**
```typescript
// Returns the user
function getUser(id: string) { ... }
```

**Bueno:**
```typescript
/**
 * [AI Context] Retrieves the full system user profile enriched with Tenant information.
 * Used primarily in the Dashboard Layout to determine permissions.
 * [Constraints] Returns 404 if the user is not linked to the current Tenant.
 */
function getUser(id: string) { ... }
```

## 2. Component Documentation
Cada componente exportado en `src/features` o `src/components` DEBE tener un bloque TSDoc.

**Template:**
```typescript
/**
 * [Component Name]
 * [AI Context] Brief description of business purpose.
 * [Props] Key props that drive logic (optional if Typed clearly).
 * [UI Behavior] What user interaction does this handle?
 * [Dependencies] Key hooks or contexts used.
 */
```

## 3. Hook Documentation
Custom hooks contienen el "Cerebro" de la aplicacion. Documentar el flujo logico.

**Template:**
```typescript
/**
 * [Hook Name]
 * [AI Context] What logic does this encapsulate?
 * [Input] Parameters.
 * [Output] Returned state and methods.
 * [Invariant] What condition is always true?
 */
```

## 4. "AI-Stop" Comments
Si un bloque de codigo es fragil o tiene edge cases no obvios, usar un warning `AI-Stop`.

```typescript
// ! AI-STOP: Do not refactor this useEffect.
// The dependency array is intentionally empty to prevent infinite loops caused by
// the external widget's poor reference stability.
useEffect(() => { ... }, []);
```
