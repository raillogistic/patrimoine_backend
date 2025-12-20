#!/bin/sh

echo "running container"
cd /home/app


# python manage.py flush --no-input
python manage.py makemigrations
python manage.py migrate


exec "$@"