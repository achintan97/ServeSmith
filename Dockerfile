FROM python:3.12-slim-bookworm

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
COPY ui/ ui/
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "servesmith.server:app", "--host", "0.0.0.0", "--port", "8000"]
