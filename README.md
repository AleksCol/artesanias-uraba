# Artesanías de Urabá

Tienda en línea de artesanías de la subregión de Urabá, Antioquia: catálogo
por categorías, carrito sin cuenta obligatoria y pago con Stripe Checkout.

Stripe corre **en modo de prueba**. No se procesan pagos reales.

## Stack

- Django 5.2 LTS sobre Python 3.14
- PostgreSQL en Neon (`psycopg` 3)
- Stripe Checkout por redirección
- Tailwind CSS 4
- Autenticación y panel de administración nativos de Django

## Apps

| App        | Responsabilidad                                        |
|------------|--------------------------------------------------------|
| `catalogo` | Categorías, productos, listado y detalle                |
| `pedidos`  | Carrito en sesión, pedidos y sus líneas                 |
| `pagos`    | Sesión de Stripe Checkout, webhook y confirmación       |

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate            # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install

cp .env.example .env              # y completar los valores
python manage.py migrate
python manage.py createsuperuser
```

Dos procesos en paralelo durante el desarrollo:

```bash
npm run estilos:watch             # compila static/css/entrada.css -> salida.css
python manage.py runserver
```

`static/css/salida.css` es un artefacto de compilación y no va al repositorio.

## Variables de entorno

Están todas en `.env.example`. Dos detalles que no son obvios:

- Neon expone dos URLs. `DATABASE_URL` es la que usa la aplicación (el endpoint
  con `-pooler`). `DIRECT_DATABASE_URL` es el mismo host sin `-pooler` y es la
  que hay que usar para migraciones. Para no editar el `.env` cada vez, existe
  `USAR_BASE_DIRECTA`:

  ```powershell
  $env:USAR_BASE_DIRECTA=1; python manage.py migrate
  ```
- Las llaves de Stripe deben empezar por `pk_test_` y `sk_test_`.

## Estado

Listo: esqueleto, modelos de catálogo (`Categoria`, `Producto`) con su admin,
listado con filtro por categoría y página de detalle.

Pendiente: carrito en sesión, Stripe Checkout, webhook de confirmación y
página de pago exitoso.

Los precios se guardan **en centavos** (`Producto.precio`), que es la unidad
que espera Stripe. Para mostrarlos hay un filtro de plantilla, `|pesos`, y la
misma función la usa el admin.
