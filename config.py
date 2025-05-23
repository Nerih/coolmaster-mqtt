import os

COOLMASTER_HOST = os.getenv("COOLMASTER_HOST", "")
COOLMASTER_PORT = int(os.getenv("COOLMASTER_PORT", 10102))

MQTT_HOST = os.getenv("MQTT_HOST", "")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "homeassistant/climate")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 2))
USE_BATCH_POLLING = os.getenv("USE_BATCH_POLLING", "true").lower() in ("1", "true", "yes")
