FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    fonts-dejavu-core fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
COPY requirements/production.txt requirements/production.txt
RUN pip install --no-cache-dir -r requirements/production.txt
COPY . .
RUN useradd --create-home app && chown -R app:app /app
USER app
ENV DJANGO_SETTINGS_MODULE=config.settings.production
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-"]
