# CoolMaster ↔ MQTT Bridge

This project connects a **CoolMasterNet HVAC controller** to **Home Assistant** (or other MQTT consumers) via a fast, reliable MQTT bridge.

The reason this exists, is becuase of the lack of local push (i.e. real time) updates for Coolmaster, this bridge emulates near real time by frequent polling. It polls the CoolMasterNet system over Telnet and publishes real-time climate state, sensor data, and control topics via MQTT using Home Assistant's discovery format.

The Bridge/Docker should run on the same physical local network as the Coolmaster, as the statuses are updated at intervals of 2 seconds (configurable via POLL_INTERVAL). I would only run 1 instance of the bridge per Coolmaster to avoid taxing the device, although it is unlikely this level of polling will cause any issues. 

---

## 🧠 How It Works

- Connects to **CoolMasterNet** via TCP 
- Publishes and subscribes to **MQTT** 
- Periodically polls all discovered HVAC units (default: 2 seconds)
- Automatically:
  - Registers devices with Home Assistant on /homeassistant/climate (configurable)
  - Publishes temperature, fan mode, mode, and error state
  - Responds to MQTT control topics (`set/temperature`, `set/mode`, `set/fan_mode`)

---

## 🐳 Running with Docker (WSL or Linux)

### 📦 1. Build the image

```bash
docker build -t coolmaster-mqtt-bridge .
▶️ 2. Run the container
bash
Copy
Edit
docker run --rm -it \
  --env-file .env \
  -v "$PWD":/app \
  -w /app \
  --network=host \
  coolmaster-mqtt-bridge
✅ Important flags:

--env-file .env loads your runtime config (see below)

--network=host is required to access LAN devices from WSL/Linux Docker

-v "$PWD":/app mounts your code so changes reflect live (great for dev)

⚙️ Environment Variables
The app is configured via environment variables (in a .env file):

env
Copy
Edit
# CoolMasterNet connection
COOLMASTER_HOST=192.168.1.50
COOLMASTER_PORT=10102

# MQTT broker connection
MQTT_HOST=192.168.1.60
MQTT_PORT=1883
MQTT_USERNAME=your_user
MQTT_PASSWORD=your_pass

# MQTT topic root
MQTT_TOPIC_PREFIX=homeassistant/climate

# Polling behavior
POLL_INTERVAL=2
USE_BATCH_POLLING=true
You can copy this into a file named .env in your project root.

🏠 Home Assistant Integration
This system is fully compatible with Home Assistant MQTT Discovery.

Devices show up under climate.coolmaster_*

Includes sensors for:

Current temperature

HVAC state

Error status

Supports:

mode_command_topic

fan_mode_command_topic

temperature_command_topic

🛠 Folder Structure
bash
Copy
Edit
.
├── main.py                  # Main entrypoint
├── config.py                # Environment loader
├── mqtt/
│   └── publisher.py         # MQTT publishing logic
├── coolmaster/
│   └── client.py            # Telnet control + polling
├── requirements.txt
├── Dockerfile
└── .env                     # Runtime configuration (not committed)
🧼 License
MIT

