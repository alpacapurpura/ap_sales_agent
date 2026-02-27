## 1. Configurar Componente SignIn
- Editar `frontend/src/app/sign-in/[[...sign-in]]/page.tsx`:
  - Añadir props al componente `<SignIn />` para fijar su comportamiento:
    - `routing="path"`
    - `path="/sign-in"`
    - `signUpUrl="/sign-up"`
    - `forceRedirectUrl="/" ` (para asegurar que tras el login vaya al dashboard)

## 2. Configurar Componente SignUp
- Editar `frontend/src/app/sign-up/[[...sign-up]]/page.tsx` (si existe, o verificar su existencia):
  - Aplicar la misma configuración: `routing="path"`, `path="/sign-up"`, `signInUrl="/sign-in"`.

## 3. Verificación
- El usuario deberá recargar `http://salesagent.local/sign-in`.
- El error `ERR_ABORTED` debería desaparecer al estabilizarse la lógica de enrutamiento del componente.