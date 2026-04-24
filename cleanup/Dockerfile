FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY shared/ ./shared/
COPY cleanup/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY cleanup/ ./cleanup/

ENV PYTHONPATH=/app

EXPOSE 8003
CMD ["uvicorn", "cleanup.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
