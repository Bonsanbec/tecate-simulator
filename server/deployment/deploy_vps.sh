#!/usr/bin/env bash
# ==============================================================================
# Script de Aprovisionamiento y Despliegue en VPS Ubuntu (bonsanbec.dev)
# ==============================================================================

set -euo pipefail

echo "===== INICIANDO DESPLIEGUE DE TECATE SIMULATOR SERVER (TKT/1) ====="

# 1. Actualización básica de paquetes y verificación de Python 3
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip

# 2. Configurar puerto
PORT="${SERVER_PORT:-52665}"

# 3. Preparar directorio de ejecución
TARGET_DIR="/opt/tecate-simulator"
echo "[VPS] Sincronizando archivos a ${TARGET_DIR}..."
sudo mkdir -p "${TARGET_DIR}"
sudo chown -R www-data:www-data "${TARGET_DIR}"
sudo -u www-data git clone --no-checkout https://github.com/Bonsanbec/tecate-simulator "${TARGET_DIR}"
cd ${TARGET_DIR}
sudo -u www-data git sparse-checkout init
sudo -u www-data git sparse-checkout set server
sudo -u www-data git checkout master

# 4. Asegurar existencia de archivo .env
if [ ! -f "${TARGET_DIR}/server/.env" ]; then
    echo "[VPS] Copiando plantilla .env.example -> .env..."
    sudo cp "${TARGET_DIR}/server/.env.example" "${TARGET_DIR}/server/.env"
fi

# 5. Instalar servicio systemd
SERVICE_FILE="${TARGET_DIR}/server/deployment/tecate-server.service"
if [ -f "${SERVICE_FILE}" ]; then
    echo "[VPS] Instalando unidad de servicio systemd..."
    sudo cp "${SERVICE_FILE}" /etc/systemd/system/tecate-server.service
    sudo systemctl daemon-reload
    sudo systemctl enable tecate-server
    sudo systemctl restart tecate-server
    echo "[VPS] Estado del servicio tecate-server:"
    sudo systemctl status tecate-server --no-pager
fi

echo "===== DESPLIEGUE FINALIZADO EXITOSAMENTE ====="
echo "Servidor escuchando en UDP/${PORT}"
