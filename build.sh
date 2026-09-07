#!/usr/bin/env bash
# Se ejecuta en cada despliegue de Render, antes de arrancar el servidor.
# A diferencia de un Procfile, acá el trabajo pesado va en la fase de build:
# no se repite en cada reinicio ni corre dos veces si hay varias instancias.
set -o errexit

pip install --upgrade pip
pip install --requirement requirements.txt

# El almacenamiento de estáticos usa manifiesto. Sin este paso, cada página
# falla con "Missing staticfiles manifest entry": no es un 404 silencioso.
python manage.py collectstatic --no-input

# Por el endpoint directo de Neon, no por el pooler: PgBouncer en modo
# transacción no lleva bien las migraciones. Si DIRECT_DATABASE_URL no está
# configurada, los settings degradan solos al endpoint normal.
USAR_BASE_DIRECTA=1 python manage.py migrate --no-input
