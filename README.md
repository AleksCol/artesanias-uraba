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

Sobre un catálogo que ya existe, el comando actualiza nombres y descripciones
pero **no toca precio ni existencias**: volver a correrlo no puede deshacer una
venta ni revertir un precio cambiado desde el admin. Y `--borrar-todo` falla
con un mensaje claro si algún producto ya fue comprado, porque `ItemPedido` lo
protege.

Dos procesos en paralelo durante el desarrollo:

```bash
npm run estilos:watch             # compila static/css/entrada.css -> salida.css
python manage.py runserver
```

`static/css/salida.css` es un artefacto de compilación y no va al repositorio.

## Fotos de producto

`Producto.imagen` es un `ImageField` común. Dónde aterriza el archivo lo decide
una sola variable:

- **Con `CLOUDINARY_URL`**: sube a Cloudinary.
- **Sin ella**: se guarda en `media/` del disco local.

El disco local alcanza para desarrollo, pero no para producción: en un host de
sistema de archivos efímero (Railway, entre otros) las fotos se pierden en cada
despliegue. Los modelos, las plantillas y el admin no cambian entre un modo y
el otro; solo cambia el backend en `STORAGES`.

Para empujar a Cloudinary las fotos de un catálogo que ya existe:

```bash
python manage.py cargar_datos_de_ejemplo --refrescar-fotos
```

El comando borra la foto anterior antes de subir la nueva. Hace falta: el
wrapper sube con `use_filename` pero sin `overwrite`, así que Cloudinary asigna
un nombre único en cada subida y, sin ese borrado, cada refresco dejaría ocho
archivos huérfanos ocupando el plan gratis para siempre. Verificado: dos
refrescos seguidos dejan ocho archivos, no dieciséis.

Una nota sobre la dependencia: `django-cloudinary-storage` está sin
mantenimiento desde 2020, aunque funciona bien sobre Django 5.2 y Python 3.14
(probado). El SDK oficial `cloudinary` sí está mantenido pero no trae backend
de `Storage`. Si el wrapper llegara a romperse, reemplazarlo por un backend
propio sobre el SDK son unas cincuenta líneas y no obliga a tocar los modelos.

## Despliegue en Render

Render no usa `Procfile`: separa el despliegue en **build** y **start**. Ambos
están declarados en `render.yaml`, así que el servicio se crea como Blueprint
y no hay que llenar campos a mano.

- **Build** (`./build.sh`): instala dependencias, corre `collectstatic` y
  migra. Va acá y no en el arranque porque en Render el build produce el
  sistema de archivos que después se ejecuta: no se repite en cada reinicio ni
  se pisa entre instancias.
- **Start**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`. Render
  exige escuchar en `0.0.0.0` y define `PORT` (10000 por defecto).

`collectstatic` no es opcional: el almacenamiento de estáticos usa manifiesto y
sin ese paso cada página responde 500 con `Missing staticfiles manifest entry`.
Por lo mismo `static/css/salida.css` se versiona — el build de Render no corre
Tailwind. Acordate de `npm run estilos` y commitear el resultado al tocar
plantillas. El fuente vive en `assets/css/entrada.css`, fuera de `static/`,
porque `collectstatic` no puede post-procesar un archivo con
`@import "tailwindcss"` y aborta el build entero si lo encuentra.

`.python-version` pide 3.13. Render toma ese archivo y hoy su default es
3.14.3, pero `gunicorn` 26 declara soporte hasta 3.13 — y gunicorn es
justamente lo único que no se puede probar en local desde Windows.

### Variables a configurar

Las declara `render.yaml` con `sync: false`, así que Render las pide al crear
el servicio y ninguna queda en el repositorio.

| Variable | Nota |
| --- | --- |
| `DJANGO_SECRET_KEY` | Generar una nueva, distinta a la de desarrollo |
| `DATABASE_URL` | Neon, endpoint **con** `-pooler` |
| `DIRECT_DATABASE_URL` | Neon, el mismo host **sin** `-pooler` |
| `CLOUDINARY_URL` | Sin esta variable las fotos irían al disco efímero |
| `STRIPE_PUBLISHABLE_KEY` | `pk_test_...` |
| `STRIPE_SECRET_KEY` | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | El del endpoint público, no el del `stripe listen` |

`DJANGO_DEBUG=False` y `STRIPE_MONEDA=cop` ya vienen con valor en el blueprint.
`DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS` son opcionales: el
dominio de `RENDER_EXTERNAL_HOSTNAME` se agrega solo a las dos. Hacen falta
únicamente para un dominio propio.

### Después del primer despliegue

1. Crear el endpoint de webhook en Stripe apuntando a
   `https://<dominio>/pagos/webhook/`, con el evento
   `checkout.session.completed`. Copiar su `whsec_...` a
   `STRIPE_WEBHOOK_SECRET` y **volver a desplegar**: las variables se leen al
   importar los settings, cambiarlas no basta.
2. Crear el superusuario desde la shell del servicio.
3. Opcional, con el HTTPS ya firme: activar HSTS con `DJANGO_HSTS_SEGUNDOS`,
   subiendo por etapas (3600, después 31536000). Arranca apagado a propósito:
   el navegador recuerda la directiva todo el plazo y no se deshace desde el
   servidor.

### Lo que trae el plan gratis

El servicio se duerme tras 15 minutos sin tráfico y tarda cerca de un minuto en
volver, mostrando una pantalla de carga. Para un portafolio significa que quien
abra el enlace en frío espera ese minuto. Hay 750 horas de instancia por mes.

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

### Probarlo en local

Hay que reenviar los eventos al servidor de desarrollo con el CLI de Stripe:

```bash
stripe listen --forward-to localhost:8000/pagos/webhook/
```

Ese comando imprime un `whsec_...` que va en `STRIPE_WEBHOOK_SECRET`. Sin esa
variable el webhook responde 503 a propósito, en vez de aceptar eventos sin
verificar la firma.

**Después de escribir el secreto en el `.env` hay que reiniciar `runserver`.**
Las variables se leen una sola vez, al importar los settings; un servidor que
ya estaba corriendo sigue con el valor viejo y rechaza los eventos con 503.

### Dos cosas de Stripe que costaron descubrir

**Managed Payments hay que apagarlo.** Viene activo por defecto en la cuenta y
solo admite productos digitales: la documentación lista "physical goods" entre
las categorías no soportadas, y sus códigos de impuesto elegibles son todos de
software, libros, cursos o streaming. Una tienda de cestería y barro no puede
calificar, así que la sesión se crea con `managed_payments={"enabled": False}`.
Sin eso, Stripe rechaza la solicitud pidiendo un código de impuesto que no
existe para bienes físicos.

**El peso colombiano lleva dos decimales.** Se confirmó contra una sesión real:
`unit_amount` de 18500000 se muestra en Stripe como COP 185,000.00. Es decir,
los montos van en centavos, igual que `Producto.precio`. Si COP hubiera sido
moneda de cero decimales, el mismo número habría cobrado cien veces de más.

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
