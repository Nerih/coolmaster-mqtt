# CoolMaster → MQTT Bridge

This project bridges a CoolMasterNet HVAC system with MQTT, enabling Home Assistant (or other MQTT consumers) to monitor and control HVAC units in real-time.

## 📦 Features

- Connects to CoolMasterNet via Telnet
- Publishes and subscribes to MQTT topics using Home Assistant-compatible payloads
- Supports batch polling of all HVAC units
- Reports HVAC state, temperature, mode, fan speed, and error status

## 🐳 Docker-based Development

### 🛠 Prerequisites

- WSL2 with Docker Engine installed (no Docker Desktop)
- VS Code with Remote - WSL extension (optional but recommended)

### 🔧 Configuration

Edit `config.py`:

```python
COOLMASTER_HOST = "192.168.0.252"
COOLMASTER_PORT = 10102
MQTT_HOST = "192.168.0.253"
MQTT_PORT = 1883
MQTT_USERNAME = "your-user"
MQTT_PASSWORD = "your-pass"
MQTT_TOPIC_PREFIX = "homeassistant/climate"
POLL_INTERVAL = 2
USE_BATCH_POLLING = True


🐳 Run in Docker
Build the image:

bash
Copy
Edit
docker build -t coolmaster-bridge .
Run the container:

bash
Copy
Edit
docker run --rm -it \
  -v "$PWD":/app \
  -w /app \
  --network=host \
  coolmaster-bridge
--network=host is important if you're connecting to LAN devices from WSL2.

📂 Project Structure
arduino
Copy
Edit
.
├── app.py
├── config.py
├── mqtt/
│   └── publisher.py
├── coolmaster/
│   └── client.py
├── requirements.txt
└── Dockerfile
🧪 Development Tips
Logs show MQTT connection, message flow, and CoolMaster commands

Use Home Assistant Developer Tools to inspect entities under climate.

