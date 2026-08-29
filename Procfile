web: gunicorn upwork_assistant.wsgi:application --timeout 60 --bind 0.0.0.0:$PORT
release: python manage.py migrate --noinput
