"""Ellenex level/distance sensor LoRaWAN payload decoder.

Supports the v3 fixed-layout sensors (PLS2-L, PLS3-L, PLV3-L, DUS2-L) and
the v6 CBOR-encoded sensors (DRC3-L).

v3 layout (8 bytes on FPort 1/15):
    bytes[3..4] = sensor reading (signed int16, big-endian)
    bytes[5..6] = temperature reading (signed int16, big-endian)
    bytes[7]    = battery voltage (1 LSB = 0.1 V)

v6 layout (CBOR map on FPort 1/15) — see Ellenex DRC3-L.js.
"""
from __future__ import annotations

import struct

VALID_PORTS = (1, 15)
V3_LENGTH = 8
DRC3_RANGE_CM = 1000  # 10 m sensor range, mirrors the DUS2-L convention

_K = 0.01907
_M = 0.007
_B = -0.35


def _read_i16(b1: int, b2: int) -> int:
    raw = (b1 << 8) | b2
    return raw - 0x10000 if b1 & 0x80 else raw


def decode(payload: bytes, port: int, sensor_type: str, liquid_density: float = 1.0) -> dict | None:
    if port not in VALID_PORTS:
        return None

    if sensor_type == "drc3-l":
        return _decode_drc3(payload)

    if len(payload) != V3_LENGTH:
        return None

    sensor_reading = _read_i16(payload[3], payload[4])
    temperature_reading = _read_i16(payload[5], payload[6])
    battery_v = payload[7] * 0.1

    if sensor_type == "pls2-l":
        # PLS2-L returns sensor reading directly as mm; UI works in cm.
        level_mm = sensor_reading / liquid_density
        raw_level = round(level_mm / 10)
    elif sensor_type == "dus2-l":
        # DUS2-L is an ultrasonic distance sensor with a 10 m (10000 mm) range.
        # Reading is distance from the sensor; subtract from range for fill height.
        sensor_range_mm = 10000
        raw_level = round((sensor_range_mm - sensor_reading) / 10)
    elif sensor_type == "pls3-l":
        sensor_range = 3  # metres
        l1 = ((temperature_reading - 1638.3) * sensor_range) / 13106.4
        l2 = (_K * sensor_reading * _M) + _B
        level_m = (l1 - l2 * 10) / liquid_density
        # PLS3-L UI works in cm
        raw_level = round(level_m * 100)
    elif sensor_type == "plv3-l":
        sensor_range = 20  # metres
        battery_v *= 1.125  # legacy compensation
        l1 = ((temperature_reading - 4000) * sensor_range) / 16000
        l2 = (_K * sensor_reading * _M) + _B
        raw_level = (l1 - l2 * 10) / liquid_density  # metres
    else:
        return None

    return {
        "raw_level": raw_level,
        "raw_battery_v": round(battery_v, 2),
        "sensor_reading": sensor_reading,
        "temperature_reading": temperature_reading,
    }


def _decode_drc3(payload: bytes) -> dict | None:
    try:
        obj = _cbor_loads(payload)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None

    distance_m = obj.get("D")
    battery_mv = obj.get("v")
    if distance_m is None or battery_mv is None:
        return None

    distance_cm = float(distance_m) * 100
    # Match the DUS2-L convention: report fill height (cm) using the sensor
    # max range as the empty reference. Tank height calibration is applied
    # downstream via inputMax / inputZeroCal / inputScalingCal.
    raw_level = round(DRC3_RANGE_CM - distance_cm)
    return {
        "raw_level": raw_level,
        "raw_battery_v": round(float(battery_mv) / 1000, 3),
        "distance_m": float(distance_m),
    }


def _cbor_loads(buf: bytes):
    """Minimal CBOR decoder — supports the subset emitted by Ellenex v6 sensors.

    Handles unsigned/negative ints, byte strings, text strings, arrays, maps,
    booleans/null, and float16/32/64. Indefinite-length items are not used by
    Ellenex but are supported for safety.
    """
    pos = [0]

    def read_byte() -> int:
        b = buf[pos[0]]
        pos[0] += 1
        return b

    def read_n(n: int) -> bytes:
        s = buf[pos[0]:pos[0] + n]
        pos[0] += n
        return s

    def read_length(ai: int) -> int:
        if ai < 24:
            return ai
        if ai == 24:
            return read_byte()
        if ai == 25:
            return int.from_bytes(read_n(2), "big")
        if ai == 26:
            return int.from_bytes(read_n(4), "big")
        if ai == 27:
            return int.from_bytes(read_n(8), "big")
        if ai == 31:
            return -1
        raise ValueError(f"Unsupported length encoding: {ai}")

    def parse_item():
        initial = read_byte()
        major = initial >> 5
        ai = initial & 0x1F

        if major == 0:
            return read_length(ai)
        if major == 1:
            return -1 - read_length(ai)
        if major == 2:
            length = read_length(ai)
            return bytes(read_n(length))
        if major == 3:
            length = read_length(ai)
            return read_n(length).decode("utf-8")
        if major == 4:
            length = read_length(ai)
            arr = []
            if length == -1:
                while buf[pos[0]] != 0xFF:
                    arr.append(parse_item())
                pos[0] += 1
            else:
                for _ in range(length):
                    arr.append(parse_item())
            return arr
        if major == 5:
            length = read_length(ai)
            obj: dict = {}
            if length == -1:
                while buf[pos[0]] != 0xFF:
                    k = parse_item()
                    obj[k] = parse_item()
                pos[0] += 1
            else:
                for _ in range(length):
                    k = parse_item()
                    obj[k] = parse_item()
            return obj
        if major == 7:
            if ai == 20:
                return False
            if ai == 21:
                return True
            if ai in (22, 23):
                return None
            if ai == 25:
                return _float16(read_n(2))
            if ai == 26:
                return struct.unpack(">f", read_n(4))[0]
            if ai == 27:
                return struct.unpack(">d", read_n(8))[0]
            return ai
        raise ValueError(f"Unsupported major type: {major}")

    return parse_item()


def _float16(b: bytes) -> float:
    half = (b[0] << 8) | b[1]
    exp = (half & 0x7C00) >> 10
    frac = half & 0x03FF
    if exp == 0:
        val = (frac / 1024) * (2 ** -14)
    elif exp == 31:
        val = float("nan") if frac else float("inf")
    else:
        val = (1 + frac / 1024) * (2 ** (exp - 15))
    return -val if (half & 0x8000) else val
