FROM python:3.11-slim

WORKDIR /app

# Copiar archivos del servidor
COPY . /app/server/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 52665/udp

CMD ["python3", "-u", "server/main.py"]
