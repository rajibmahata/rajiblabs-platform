FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r orchestrator && useradd -r -g orchestrator -d /app -s /sbin/nologin orchestrator

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R orchestrator:orchestrator /app

USER orchestrator

EXPOSE 8200

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
