import base64
import logging
import math

from pydoover.processor import Application
from pydoover.models import MessageCreateEvent
from pydoover.models.data import ConnectionConfig, ConnectionType
from pydoover.ui import handler

from .app_config import EllenexProcessorConfig, TankType
from .app_tags import EllenexTags
from .app_ui import EllenexUI
from .decoder import decode

log = logging.getLogger(__name__)


class EllenexProcessor(Application):
    config_cls = EllenexProcessorConfig
    ui_cls = EllenexUI
    tags_cls = EllenexTags

    config: EllenexProcessorConfig
    tags: EllenexTags
    ui: EllenexUI

    async def setup(self):
        await self._update_connection_info(self.ui_manager.get_value("uplink_interval"))

    async def _update_connection_info(self, minutes: int):
        desired = ConnectionConfig(
            connection_type=ConnectionType.periodic,
            expected_interval=minutes * 60,
            offline_after=minutes * 60 * 3,
        )
        if self.connection_config == desired:
            return
        await self.api.update_connection_config(desired)

    async def on_message_create(self, event: MessageCreateEvent):
        if event.channel.name != "on_tts_event":
            return

        uplink = event.message.data.get("uplink_message")
        if not uplink:
            return

        port = uplink.get("f_port")
        frm = uplink.get("frm_payload")
        if port is None or not frm:
            return

        try:
            payload = base64.b64decode(frm)
        except Exception:
            log.exception("Failed to base64-decode frm_payload: %r", frm)
            return

        sensor_type = self.config.sensor_type.value.value
        decoded = decode(payload, port, sensor_type)
        if not decoded:
            log.warning("Ellenex port=%s len=%s did not match expected format", port, len(payload))
            return

        log.info("Ellenex (%s) decoded: %s", sensor_type, decoded)

        raw_level = decoded["raw_level"]
        raw_battery = decoded["raw_battery_v"]

        await self.tags.raw_level.set(raw_level)
        await self.tags.raw_battery_v.set(raw_battery)

        calibrated_level = self._calibrate(raw_level)
        level_pct = self._compute_level_pct(calibrated_level)
        battery_pct = round(self._batt_volts_to_percent(raw_battery) * 100)

        if level_pct is not None:
            await self.tags.level_pct.set(level_pct)
            await self.tags.level_volume.set(self._compute_volume(calibrated_level))
        await self.tags.battery_pct.set(battery_pct)

        volume_enabled = len(self._storage_curve()) >= 2
        await self.tags.level_pct_hidden.set(volume_enabled)
        await self.tags.level_volume_hidden.set(not volume_enabled)

        await self._assess_warnings(level_pct, battery_pct)

    def _calibrate(self, raw_level: float | None) -> float | None:
        if raw_level is None:
            return None
        zero_cal = self.config.zero_calibration.value
        scaling_cal = self.config.scaling_calibration.value
        return (raw_level + zero_cal) * scaling_cal

    def _compute_level_pct(self, calibrated_level: float | None) -> float | None:
        if calibrated_level is None:
            return None

        sensor_max = self.config.max_level.value
        tank_type = self.config.tank_type.value

        if not sensor_max:
            return None
        pct = round((calibrated_level / sensor_max) * 100, 1)

        if tank_type is TankType.HORIZONTAL_CYLINDER:
            # Horizontal cylinder cross-section area mapping (legacy formula)
            r = 50.0
            h = max(0.0, min(pct, 100.0))
            try:
                pct = math.acos((r - h) / r) * (r * r) - (r - h) * math.sqrt(2 * r * h - h * h)
            except ValueError:
                pass

        return pct

    def _storage_curve(self) -> list[tuple[float, float]]:
        points = []
        for point in self.config.storage_curve.value:
            level_m = point.level_m.value
            volume_ml = point.volume_ml.value
            if level_m is None or volume_ml is None:
                continue
            points.append((float(level_m), float(volume_ml)))
        points.sort(key=lambda p: p[0])
        return points

    def _compute_volume(self, level_m: float | None) -> float | None:
        if level_m is None:
            return None
        curve = self._storage_curve()
        if len(curve) < 2:
            return None

        for (x1, y1), (x2, y2) in zip(curve, curve[1:]):
            if x1 <= level_m <= x2:
                return y1 + (level_m - x1) * (y2 - y1) / (x2 - x1)

        # Extrapolate outside the range using the nearest two points.
        if level_m < curve[0][0]:
            (x1, y1), (x2, y2) = curve[0], curve[1]
        else:
            (x1, y1), (x2, y2) = curve[-2], curve[-1]
        return y1 + (level_m - x1) * (y2 - y1) / (x2 - x1)

    @staticmethod
    def _batt_volts_to_percent(volts: float | None) -> float:
        if volts is None:
            return 0.0
        if volts < 2.8:
            out = 0.0
        elif volts < 3.1:
            out = (volts - 3.1) * (1 / 3)
        else:
            out = 0.1 + (volts - 3.1) * 1.5
        return max(0.0, min(out, 1.0))

    async def _assess_warnings(self, level_pct: float | None, battery_pct: float | None):
        level_alarm = self.config.low_level_alarm.value
        batt_alarm = self.config.battery_alarm.value

        new_level_warn = (
            level_alarm is not None and level_pct is not None and level_pct < level_alarm
        )
        new_batt_warn = (
            batt_alarm is not None and battery_pct is not None and battery_pct < batt_alarm
        )

        prev_level_warn = self.tags.level_low_warning.value
        prev_batt_warn = self.tags.batt_low_warning.value

        await self.tags.level_low_warning.set(new_level_warn)
        await self.tags.batt_low_warning.set(new_batt_warn)
        await self.tags.level_low_warning_hidden.set(not new_level_warn)
        await self.tags.batt_low_warning_hidden.set(not new_batt_warn)

        if new_level_warn and not prev_level_warn:
            await self._notify("Level is getting low")
        if new_batt_warn and not prev_batt_warn:
            await self._notify("Battery is getting low")

    @handler("uplink_interval", parser=int)
    async def on_uplink_interval(self, ctx, payload: int):
        # Ellenex "change sampling rate" downlink: [0x10, 0x01, high, low]
        # on fPort 1. 0x10 = command, 0x01 = unit (minute), then minutes
        # as a 16-bit big-endian integer.
        minutes = max(1, min(int(payload), 0xFFFF))
        frm = base64.b64encode(bytes([0x10, 0x01, (minutes >> 8) & 0xFF, minutes & 0xFF])).decode()
        log.info("Sending downlink to set uplink interval to %s min", minutes)
        await self.api.create_message(
            "tts_downlink",
            {"f_port": 1, "frm_payload": frm},
        )
        await self._update_connection_info(minutes)

    async def _notify(self, message: str):
        log.info("Ellenex notification: %s", message)
        await self.api.create_message("notifications", {"message": message})
        await self.api.create_message("activity_logs", {"activity_log": {"action_string": message}})
