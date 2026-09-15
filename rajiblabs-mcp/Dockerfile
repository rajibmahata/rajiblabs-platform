FROM python:3.12-slim
RUN groupadd -r mcp && useradd -r -g mcp -d /app -s /sbin/nologin mcp
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    chown -R mcp:mcp /app
COPY --chown=mcp:mcp app ./app
USER mcp
EXPOSE 8100
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
