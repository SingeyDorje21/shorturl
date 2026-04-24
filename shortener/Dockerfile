FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY shared/ ./shared/
COPY shortener/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shortener/ ./shortener/

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "shortener.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
