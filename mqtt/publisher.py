import paho.mqtt.client as mqtt
import json
from config import MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD
from datetime import datetime
import asyncio
from coolmaster.client import CoolMasterClient

class MQTTPublisher:
    def __init__(self, coolmaster_client,loop):
        self.coolmaster = coolmaster_client  # ✅ store reference
        self.loop = loop
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.will_set(
            topic="homeassistant/climate/coolmaster/status",  # availability topic
            payload="offline",                                        # will payload
            qos=0,
            retain=True                                               # retain so HA sees it on restart
        )

        try:
            print(f"{datetime.now().strftime('%H:%M:%S')}🔌 Connecting to MQTT at {MQTT_HOST}:{MQTT_PORT}...")
            self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print(f"{datetime.now().strftime('%H:%M:%S')} ❌ MQTT TCP connect error: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"{datetime.now().strftime('%H:%M:%S')} ✅ MQTT connected successfully")
            #subscribe to the climate entities command topics.
            self.client.subscribe("homeassistant/climate/+/set/temperature")
            self.client.subscribe("homeassistant/climate/+/set/mode")
            self.client.subscribe("homeassistant/climate/+/set/fan_mode")
            self.client.on_message = self._on_message

            #Tell everyone where are Online
            self.client.publish("homeassistant/climate/coolmaster/status", "online", retain=True)
            print(f"{datetime.now().strftime('%H:%M:%S')} ✅ Published availability → 'online' (retain=True)")

       
        elif rc == 4:
            print(f"{datetime.now().strftime('%H:%M:%S')} ❌ MQTT authentication failed (bad username/password)")
        else:
            print(f"{datetime.now().strftime('%H:%M:%S')} ❌ MQTT connection failed with result code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"{datetime.now().strftime('%H:%M:%S')} ⚠️ Disconnected from MQTT (code {rc})")

    def get_known_unit_ids(self):
        # If you've already discovered them during init, store them
        # Else you can just re-call get_units()
        return getattr(self, "_unit_ids", [])


    def publish_climate_state(self, unit):
        safe_uid = unit['uid'].replace('.', '_')
        topic = f"homeassistant/climate/coolmaster_{safe_uid}/state"

        payload = {
            "temperature": unit["thermostat"],             # setpoint
            "current_temperature": unit["temperature"],    # actual room temp
           "hvac_mode": "off" if not unit["is_on"] else unit["hvac_mode"],
            "fan_mode": unit["fan_mode"],
           # "state": "cooling" if unit["is_on"] else "off",
            "status": unit["status"],
            "state": unit["state"]
        }

        self.client.publish(topic, json.dumps(payload), retain=True).wait_for_publish()

        #update icon
        error_icon = "mdi:alert-circle" if unit["has_error"] else "mdi:check"       
        error_topic = f"homeassistant/sensor/coolmaster_{safe_uid}_status/config"
        error_payload = {
            "name": f"Status",
            "unique_id": f"coolmaster_{safe_uid}_status",
            "state_topic": f"homeassistant/climate/coolmaster_{safe_uid}/state",
            "availability_topic" : "homeassistant/climate/coolmaster/status" ,
            "value_template": "{{ value_json.status }}",
            "icon" : error_icon, 
            "device": {
                "identifiers": [f"coolmaster_{safe_uid}"],
                "name": f"CoolMaster HVAC {safe_uid}",
                "manufacturer": "CoolAutomation",
                "model": "CoolMasterNet",
                "sw_version": "Coolmaster-MQTT Bridge 1.0"
            }
        }  

        # Publish main climate state
        self.client.publish(error_topic, json.dumps(error_payload), retain=True).wait_for_publish()



    def publish_climate_config(self, uid):
        safe_uid = uid.replace('.', '_')
        object_id = f"coolmaster_{safe_uid}"

        error_topic = f"homeassistant/sensor/{object_id}_status/config"
        error_payload = {
                "name": f"Status",
                "unique_id": f"coolmaster_{safe_uid}_status",
                "state_topic": f"homeassistant/climate/coolmaster_{safe_uid}/state",
                "value_template": "{{ value_json.status }}",
                "availability_topic" : "homeassistant/climate/coolmaster/status" ,
                "icon" : "mdi:check", 
                "device": {
                    "identifiers": [f"coolmaster_{safe_uid}"],
                    "name": f"CoolMaster HVAC {safe_uid}",
                    "manufacturer": "CoolAutomation",
                    "model": "CoolMasterNet",
                    "sw_version": "Coolmaster-MQTT Bridge 1.0"
                }
            }
        self.client.publish(error_topic, json.dumps(error_payload),0,True).wait_for_publish()


        temp_topic = f"homeassistant/sensor/{object_id}_temp/config"
        temp_payload = {
                "name": f"Current Temperature",
                "unique_id": f"coolmaster_{safe_uid}_temp",
                "state_topic": f"homeassistant/climate/coolmaster_{safe_uid}/state",
                "value_template": "{{ value_json.current_temperature }}",
                "availability_topic" : "homeassistant/climate/coolmaster/status" ,
                "icon" : "mdi:thermometer", 
                "device_class" : "temperature",
                "unit_of_measurement": "°C" ,
                "device": {
                    "identifiers": [f"coolmaster_{safe_uid}"],
                    "name": f"CoolMaster HVAC {safe_uid}",
                    "manufacturer": "CoolAutomation",
                    "model": "CoolMasterNet",
                    "sw_version": "Coolmaster-MQTT Bridge 1.0"
                }
            }
        self.client.publish(temp_topic, json.dumps(temp_payload),0,True).wait_for_publish()


        state_topic = f"homeassistant/sensor/{object_id}_state/config"
        state_payload = {
                "name": f"HVAC State",
                "unique_id": f"coolmaster_{safe_uid}_state",
                "state_topic": f"homeassistant/climate/coolmaster_{safe_uid}/state",
                "availability_topic" : "homeassistant/climate/coolmaster/status" ,
                "value_template": "{{ value_json.state }}",
                "icon" : "mdi:weather-dust", 
                "device": {
                    "identifiers": [f"coolmaster_{safe_uid}"],
                    "name": f"CoolMaster HVAC {safe_uid}",
                    "manufacturer": "CoolAutomation",
                    "model": "CoolMasterNet",
                    "sw_version": "Coolmaster-MQTT Bridge 1.0"
                }
            }
        self.client.publish(state_topic, json.dumps(state_payload),0,True).wait_for_publish()


        topic = f"homeassistant/climate/{object_id}/config"
        payload = {
            "name": f"CoolMaster {uid}",
            "unique_id": object_id,
            "availability_topic" : "homeassistant/climate/coolmaster/status" ,
            "state_topic": f"homeassistant/climate/coolmaster_{safe_uid}/state",
            "current_temperature_topic": f"homeassistant/climate/coolmaster_{safe_uid}/state",
            "current_temperature_template": "{{ value_json.current_temperature }}",
            "temperature_command_topic": f"homeassistant/climate/coolmaster_{safe_uid}/set/temperature",
            "temperature_state_topic" :  f"homeassistant/climate/coolmaster_{safe_uid}/state",
            "temperature_state_template" : "{{ value_json.temperature }}",
            "mode_command_topic": f"homeassistant/climate/coolmaster_{safe_uid}/set/mode",
            "mode_state_topic" :  f"homeassistant/climate/coolmaster_{safe_uid}/state",
            "mode_state_template" : "{{ value_json.hvac_mode }}",
            "fan_mode_command_topic": f"homeassistant/climate/coolmaster_{safe_uid}/set/fan_mode",
            "fan_mode_state_topic": f"homeassistant/climate/coolmaster_{safe_uid}/state",
            "fan_mode_state_template": "{{ value_json.fan_mode }}",
            "modes": ["off", "cool"],
            "fan_modes": ["auto", "low", "medium", "high"],
            "temperature_unit": "C",
            "min_temp": 16,
            "max_temp": 28,
            "retain": False,
            "device": {
                "identifiers": [f"coolmaster_{safe_uid}"],
                "name": f"CoolMaster HVAC {safe_uid}",
                "manufacturer": "CoolAutomation",
                "model": "CoolMasterNet",
                "sw_version": "Coolmaster-MQTT Bridge 1.0"
            }
        }

        self.client.publish(topic, json.dumps(payload),0,True).wait_for_publish()

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"{datetime.now().strftime('%H:%M:%S')} 📨 MQTT command: {topic} = {payload}")

        try:
            parts = topic.split("/")
            if len(parts) >= 5 and parts[2].startswith("coolmaster_"):
                uid = parts[2].replace("coolmaster_", "").replace("_", ".")
                command_type = parts[4]  # "temperature", "mode", "fan_mode"

                asyncio.run_coroutine_threadsafe(
                    self.handle_command(uid, command_type, payload),
                    self.loop
                )
                
            else:
                print(f"{datetime.now().strftime('%H:%M:%S')} ⚠️ Ignored unmatched topic: {topic}")
        except Exception as e:
            print(f"{datetime.now().strftime('%H:%M:%S')} ❌ Failed to handle command: {e}")


    async def handle_command(self, uid: str, command_type: str, value: str):
        try:
            if command_type == "temperature":
                temp = float(value)
                print(f"{datetime.now().strftime('%H:%M:%S')} 🌡️ Set {uid} temperature → {temp}")
                await self.coolmaster.set_thermostat(uid, temp)

            elif command_type == "mode":
                print(f"{datetime.now().strftime('%H:%M:%S')} ❄️ Set {uid} mode → {value}")
                await self.coolmaster.set_mode(uid, value)

            elif command_type == "fan_mode":
                print(f"{datetime.now().strftime('%H:%M:%S')} 💨 Set {uid} fan → {value}")
                await self.coolmaster.set_fan_speed(uid, value)

            else:
                print(f"{datetime.now().strftime('%H:%M:%S')} ⚠️ Unknown command type: {command_type}")

        except Exception as e:
            print(f"{datetime.now().strftime('%H:%M:%S')} ❌ Command failed [{uid}, {command_type}, {value}]: {e}")

