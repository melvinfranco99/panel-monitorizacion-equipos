# Imagen del panel. Se usa en el laboratorio (lab/) y sirve para desplegar en un servidor.
FROM python:3.12-slim

# ping no viene en la imagen slim
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV MONITOR_DB=/app/instance/monitor.db
EXPOSE 5000
# Un único proceso (-w 1) con varios hilos: así solo hay UN monitor.
CMD ["gunicorn", "-w", "1", "--threads", "8", "-b", "0.0.0.0:5000", "wsgi:app"]
