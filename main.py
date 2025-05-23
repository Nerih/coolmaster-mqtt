import asyncio
from datetime import datetime
from math import isnan

from config import COOLMASTER_HOST, COOLMASTER_PORT, POLL_INTERVAL, USE_BATCH_POLLING
from coolmaster.client import CoolMasterClient
from mqtt.publisher import MQTTPublisher

def log(msg):
    print(f"{datetime.now().strftime('%H:%M:%S')} 🧠 {msg}")

def clean(value):
    """Sanitize value for safe comparison and caching."""
    try:
        if value is None:
            return None
        if isinstance(value, float):
            if isnan(value):
                return None
            return round(value, 2)
        return value
    except Exception:
        return None

async def main():
    log("CoolMaster → MQTT bridge starting...")

    client = CoolMasterClient(COOLMASTER_HOST, COOLMASTER_PORT)
    loop = asyncio.get_running_loop()
    mqtt = MQTTPublisher(client, loop)
    last_status = {}
    unit_ids = await client.get_units()
    log(f"📡 Discovered CoolMasterNet units: {unit_ids}")

    if USE_BATCH_POLLING:
        log("📥 Using batch polling for all units")

    for uid in unit_ids:
        mqtt.publish_climate_config(uid)

    while True:
        if USE_BATCH_POLLING:
            try:
                current_statuses = await client.get_status()

                for uid, status in current_statuses.items():
                    current = {k: clean(v) for k, v in status.items()}
                    last = last_status.get(uid, {})
                    changed = {}

                    for key, value in current.items():
                        if last.get(key) != value:
                            changed[key] = {"from": last.get(key), "to": value}

                    if changed:
                        log(f"🔄 {uid} → " + ', '.join(f"{k} {v['from']}→{v['to']}" for k, v in changed.items()))

                        # MQTT
                        try:
                            mqtt.publish_climate_state(status)
                        except Exception as e:
                            log(f"❌ MQTT publish error for {uid}: {e}")

                        # Cache updated state
                        last_status[uid] = current

            except Exception as e:
                log(f"❌ Polling error: {e} — will retry after {POLL_INTERVAL}s")
        else:
            log("⚠️ Use BATCH POLLING, Single unit polling not supported")

        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("🛑 Stopped by user.")
