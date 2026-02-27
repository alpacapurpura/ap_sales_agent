# Python Expert Best Practices

High-priority rules for writing production-grade Python code in Visionarias Brain.

## 1. Error Handling (CRITICAL)

### Explicit Exception Handling
**Never** use bare `except:` or `except Exception:`. It hides bugs and makes debugging impossible.

```python
# ❌ BAD
try:
    process_payment()
except:
    pass

# ✅ GOOD
try:
    process_payment()
except PaymentFailedError as e:
    logger.error("Payment failed", error=e)
    raise HTTPException(status_code=402, detail="Payment required")
```

### Dictionary Access
Use `d[key]` when the key **must** exist (fail fast). Use `d.get(key)` only when `None` is a valid state.

```python
# ❌ BAD: Silently fails if 'id' is missing
user_id = data.get("id")
if user_id: ...

# ✅ GOOD: Fails immediately if 'id' is missing (Contract violation)
user_id = data["id"]
```

## 2. Common Bugs & Antipatterns

### Mutable Default Arguments
**Never** use mutable objects (`list`, `dict`) as default arguments. They are shared across all calls.

```python
# ❌ BAD
def add_item(item, items=[]):
    items.append(item)
    return items

# ✅ GOOD
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### Type Safety & Pydantic
Visionarias Brain uses Pydantic V2. Enforce strict typing.

-   **Use `ConfigDict(extra='forbid')`** to prevent unexpected fields.
-   **Avoid `Any`**: Always try to define a specific type or a Union.
-   **Return Types**: Always annotate function return types.

## 3. Code Clarity & Style

### List Comprehensions
Use them for **creating new lists**, not for side effects.

```python
# ❌ BAD
[print(x) for x in items]

# ✅ GOOD
for x in items:
    print(x)

# ✅ GOOD (Creating a list)
squares = [x**2 for x in items]
```

### Early Returns (Guard Clauses)
Avoid deep nesting (`if/else` hell) by returning early.

```python
# ❌ BAD
if user:
    if user.is_active:
        if user.has_permission:
            do_action()

# ✅ GOOD
if not user or not user.is_active:
    return
if not user.has_permission:
    raise PermissionError()
do_action()
```

## 4. Performance

### Global Variables
Avoid global state. It breaks concurrency and makes testing hard.

### Heavy Operations
Don't block the Async Event Loop. CPU-bound operations should run in a threadpool or separate process.
