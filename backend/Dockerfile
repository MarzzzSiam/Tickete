FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libjpeg62-turbo \
    libopenjp2-7 fonts-dejavu-core fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements/ requirements/
RUN pip install -r requirements/production.txt
COPY . .
RUN useradd --create-home tickete && chown -R tickete:tickete /app
USER tickete
ENV DJANGO_SETTINGS_MODULE=config.settings.production
CMD ["python", "deploy.py"]
