FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright browsers and dependencies
RUN playwright install --with-deps chromium

COPY meal_calculate /app

RUN mkdir -p /app/staticfiles

CMD ["gunicorn", "meal_project.wsgi:application", "--bind", "0.0.0.0:8000"]
