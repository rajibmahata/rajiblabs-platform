FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY scripts ./scripts
# Resume seed PDF (init_db copies it to UPLOAD_DIR/resumes on first boot;
# without it the resume seed is skipped and /api/resume/current 404s)
COPY data/Rajib-Mahata-Resume-2026.pdf ./data/Rajib-Mahata-Resume-2026.pdf
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
