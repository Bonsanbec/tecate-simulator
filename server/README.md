# Servidor de Juego Tecate Simulator — Protocolo TKT/1

Servidor asíncrono y ligero para la sincronización multijugador del mundo compartido de Tecate Simulator, implementado bajo la especificación [`docs/multijugador.md`](../docs/multijugador.md).

El servidor es una autoridad ligera sobre el estado compartido (sesiones, entidades dinámicas, posiciones, velocidades y chat). No requiere mallas 3D, escenas de Godot ni datos del mapa estático.

---

## 1. Configuración (`.env`)

Todas las opciones de red y simulación se configuran mediante el archivo `.env` ubicado en la raíz del servidor:

```env
SERVER_BIND_HOST=0.0.0.0
SERVER_PORT=52665

PUBLIC_DOMAIN=bonsanbec.dev
PUBLIC_SUBDOMAIN=api.tecate
PUBLIC_HOST=api.tecate.bonsanbec.dev

TICK_RATE=30
SESSION_TIMEOUT_SECONDS=10.0
MAX_CLIENTS=64
SPATIAL_GRID_CELL_SIZE=150.0
BROADCAST_RADIUS_CELLS=1
LOG_LEVEL=INFO
```

---

## 2. Ejecución Local

Para pruebas locales en desarrollo:

```bash
python3 server/main.py
```

Para ejecutar las pruebas unitarias y de integración:

```bash
python3 -m unittest discover -s server/tests -v
```

---

## 3. Despliegue en VPS Ubuntu (`*.bonsanbec.dev`)

### Paso 1: Configuración de DNS
En tu panel de DNS para el dominio `bonsanbec.dev`:
- Crear un registro **A** apuntando el subdominio `api.tecate.bonsanbec.dev` a la dirección IP pública del VPS Ubuntu.

### Paso 2: Clonar el Repositorio en el VPS
```bash
git clone https://github.com/Bonsanbec/tecate-simulator.git /opt/tecate-simulator
cd /opt/tecate-simulator/server
```

### Paso 3: Ejecutar el Script de Aprovisionamiento
```bash
./deployment/deploy_vps.sh
```
El script automáticamente:
1. Instala dependencias del sistema.
2. Abre el puerto `UDP/52665` en el cortafuegos `ufw`.
3. Registra e inicia el servicio `systemd` (`tecate-server.service`).

### Comandos de Administración del Servicio
- Ver registros en tiempo real: `sudo journalctl -u tecate-server -f`
- Reiniciar el servicio: `sudo systemctl restart tecate-server`
- Detener el servicio: `sudo systemctl stop tecate-server`
- Comprobar estado: `sudo systemctl status tecate-server`
