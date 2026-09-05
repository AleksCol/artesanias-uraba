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

`Pedido` e `ItemPedido` viven en `pedidos`; `pagos` solo habla con Stripe.

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate            # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install

cp .env.example .env              # y completar los valores
python manage.py migrate
python manage.py createsuperuser
python manage.py cargar_datos_de_ejemplo
```

`cargar_datos_de_ejemplo` crea cuatro categorías y ocho productos de muestra y
baja las fotos de Pexels (licencia libre, uso comercial sin atribución). Son
fotos de referencia, no de piezas reales. Acepta `--borrar-todo` para empezar
de cero y `--sin-fotos` para trabajar sin conexión. Como `media/` no va al
repositorio, en una clonada nueva hay que correrlo para tener imágenes.

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

## Pagos

El cobro es Stripe Checkout por redirección. La aplicación nunca ve un dato de
tarjeta: se arma una sesión de pago, se manda al comprador a Stripe y se vuelve.

**El pago lo confirma el webhook, no el regreso del navegador.** Volver a
`/pagos/listo/` solo significa que alguien volvió: esa URL se puede escribir a
mano y se pierde si cierran la pestaña. Por eso esa vista no cambia el estado
del pedido, y si el webhook todavía no llegó lo dice en pantalla en vez de
afirmar un pago que nadie confirmó. El inventario también baja ahí, no antes.

El webhook es idempotente: Stripe reintenta los eventos, y `_confirmar_pago`
solo actúa sobre pedidos en `pendiente`, así que un evento repetido no descuenta
el inventario dos veces.

Para probarlo en local hace falta reenviar los eventos al servidor de
desarrollo, con el CLI de Stripe:

```bash
stripe listen --forward-to localhost:8000/pagos/webhook/
```

Ese comando imprime un `whsec_...` que va en `STRIPE_WEBHOOK_SECRET`. Sin esa
variable el webhook responde 503 a propósito, en vez de aceptar eventos sin
verificar la firma.

## Estado

Listo: catálogo con su admin, carrito en sesión, checkout con Stripe, webhook
de confirmación, página de resultado y pedidos en el admin.

Pendiente: correo de confirmación al comprador y despliegue.

El carrito no exige cuenta: vive en la sesión y guarda solo cantidades. El
precio se lee de la base y se congela en `ItemPedido.precio_unitario` al crear
el pedido, así que subir un precio no reescribe lo que ya se cobró. Las
cantidades se recortan a las existencias en el servidor, no solo en el `max`
del formulario, y al cobrar se vuelven a verificar con las filas bloqueadas.

Agregar al carrito funciona sin JavaScript (POST y redirección). Con
JavaScript se envía por `fetch` y la foto viaja hasta el contador del
encabezado; ese recorrido se omite con `prefers-reduced-motion`.

Los precios se guardan **en centavos** (`Producto.precio`), que es la unidad
que espera Stripe. Para mostrarlos hay un filtro de plantilla, `|pesos`, y la
misma función la usa el admin.
