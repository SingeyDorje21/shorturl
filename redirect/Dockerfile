FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY shared/ ./shared/
COPY redirect/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY redirect/ ./redirect/

ENV PYTHONPATH=/app

EXPOSE 8002
CMD ["uvicorn", "redirect.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
