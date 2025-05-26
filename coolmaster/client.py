import asyncio
import re
import socket
from datetime import datetime

class CoolMasterClient:
    def __init__(self, host, port=10102, timeout=3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.reader = None
        self.writer = None
        self.lock = asyncio.Lock()

    async def _ensure_connected(self):
        """Ensure the Telnet connection is open and valid."""
        try:
            if self.writer is None or self.writer.is_closing():
                print(f"{datetime.now().strftime('%H:%M:%S')}🔌 Connecting to CoolMasterNet at {self.host}:{self.port}...")
                self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
                print(f"{datetime.now().strftime('%H:%M:%S')} ✅ CoolMasterNet connected")
        except (OSError, socket.gaierror) as e:
            raise ConnectionError(f"{datetime.now().strftime('%H:%M:%S')} ❌ Failed to connect to CoolMasterNet: {e}")

    async def _make_request(self, command):
        """Send a command and return the cleaned response, retrying on connection failure."""
        while True:
            async with self.lock:
                try:
                    await self._ensure_connected()
                    self.writer.write((command + "\n").encode())
                    await self.writer.drain()

                    response = await asyncio.wait_for(self.reader.readuntil(b"\n>"), timeout=self.timeout)
                    text = response.decode().strip().strip(">").replace("OK", "").strip()
                    return text

                except asyncio.TimeoutError:
                    raise TimeoutError(f"❌ Timeout waiting for response to command: {command}")

                except (ConnectionResetError, BrokenPipeError):
                    print(f"{datetime.now().strftime('%H:%M:%S')} ⚠️ Connection lost, retrying immediately...")
                    await self._reset_connection()
                    continue

                except ConnectionError as e:
                    print(f"{datetime.now().strftime('%H:%M:%S')} ❌ Connection error: {e}")
                    await self._reset_connection()
                    print(f"{datetime.now().strftime('%H:%M:%S')} ⏳ Waiting 10 seconds before retrying...")
                    await asyncio.sleep(10)
                    continue

                except Exception as e:
                    raise RuntimeError(f"❌ Unexpected error during command '{command}': {e}")


    async def _reset_connection(self):
        """Tear down and rebuild the connection."""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
        self.reader = None
        self.writer = None
        await asyncio.sleep(1)

    async def close(self):
        """Cleanly close the Telnet connection."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def get_units(self):
        """Return a list of unit IDs like ['L1.001', 'L2.003']"""
        raw = await self._make_request("ls")
        return [line.split()[0] for line in raw.splitlines() if line]
        
    async def get_status(self, uid: str = None):
        """
        Get status for a single UID or all units.
        If `uid` is provided, runs `ls2 {uid}`, otherwise `ls2`.
        Returns:
            - dict of {uid: status_dict} if `uid` is None
            - status_dict directly if `uid` is provided
        """
        command = f"ls2 {uid}" if uid else "ls2"
        raw = await self._make_request(command)
        lines = raw.strip().splitlines()

        # Handle single line for individual unit
        if uid:
            lines = [raw.strip()]

        units = {}

        for line in lines:
            fields = re.split(r"\s+", line.strip())
            if len(fields) < 8:
                print(f"⚠️ Skipping malformed line: {line}")
                continue

            unit_id = fields[0]
            try:
                error_field = fields[6]
                if error_field == "-":
                    error_status = "OK"
                    has_error = False
                else:
                    error_status = error_field
                    has_error = True

                hvac_state = "cooling" if fields[-1] == "1" else "idle"

                unit_data = {
                    "uid": unit_id,
                    "is_on": fields[1] == "ON",
                    "thermostat": float(fields[2][:-1]),
                    "temperature": float(fields[3][:-1]),
                    "fan_mode": fields[4].lower(),
                    "hvac_mode": fields[5].lower(),
                    "status": error_status,
                    "has_error": has_error,
                    "state": hvac_state,
                }

                units[unit_id] = unit_data

            except Exception as e:
                print(f"❌ Error parsing line for {unit_id}: {e}")
                continue

        return units[uid] if uid else units
  

    async def set_thermostat(self, uid: str, value: float):
        try:
            print(f"{datetime.now().strftime('%H:%M:%S')} 🌡️ Setting {uid} setpoint to {value}°C")
            await self._make_request(f"temp {uid} {value}")
        except Exception as e:
            print(f"❌ Failed to set temperature for {uid}: {e}")

    async def set_mode(self, uid: str, mode: str):
        try:
            if mode.lower() == "off":
                print(f"{datetime.now().strftime('%H:%M:%S')} ❄️ Turning OFF {uid}")
                await self._make_request(f"off {uid}")
            elif mode.lower() in ["cool", "auto", "heat", "dry", "fan"]:
                print(f"{datetime.now().strftime('%H:%M:%S')} ❄️ Setting {uid} mode to {mode}")
                #ensure unit is turned on in addition to setting the mode to cool/auto/heat etc.
                await self._make_request(f"on {uid}")
                await self._make_request(f"{mode.lower()} {uid}")
            else:
                print(f"⚠️ Ignoring unknown mode '{mode}' for {uid}")
        except Exception as e:
            print(f"❌ Failed to set mode for {uid}: {e}")

    async def set_fan_speed(self, uid: str, speed: str):
        try:
            valid_speeds = ["low", "medium", "high", "auto"]
            if speed.lower() not in valid_speeds:
                print(f"⚠️ Invalid fan speed '{speed}' for {uid}")
                return
            print(f"{datetime.now().strftime('%H:%M:%S')} 💨 Setting {uid} fan speed to {speed}")
            await self._make_request(f"fspeed {uid} {speed.lower()}")
            
        except Exception as e:
            print(f"❌ Failed to set fan speed for {uid}: {e}")

