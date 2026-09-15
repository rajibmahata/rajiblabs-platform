FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r mcp && useradd -r -g mcp -d /app -s /sbin/nologin mcp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R mcp:mcp /app

USER mcp

EXPOSE 8100

CMD ["python", "-m", "uvicorn", "app.rest:app", "--host", "0.0.0.0", "--port", "8100"]
