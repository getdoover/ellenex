import base64
import logging
import math

from pydoover.processor import Application
from pydoover.models import MessageCreateEvent

from .app_config import EllenexProcessorConfig
from .app_tags import EllenexTags
from .app_ui import EllenexUI
from . import decoder

log = logging.getLogger(__name__)


class EllenexProcessor(Application):
    config_cls = EllenexProcessorConfig
    ui_cls = EllenexUI
    tags_cls = EllenexTags

    config: EllenexProcessorConfig
    tags: EllenexTags
    ui: EllenexUI

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
        decoded = decoder.decode(payload, port, sensor_type)
        if not decoded:
            log.warning("Ellenex port=%s len=%s did not match expected format", port, len(payload))
            return

        log.info("Ellenex (%s) decoded: %s", sensor_type, decoded)

        raw_level = decoded["raw_level"]
        raw_battery = decoded["raw_battery_v"]

        await self.tags.raw_level.set(raw_level)
        await self.tags.raw_battery_v.set(raw_battery)

        level_pct = self._compute_level_pct(raw_level)
        battery_pct = round(self._batt_volts_to_percent(raw_battery) * 100)

        if level_pct is not None:
            await self.tags.level_pct.set(level_pct)
        await self.tags.battery_pct.set(battery_pct)

        await self._assess_warnings(level_pct, battery_pct)

    def _compute_level_pct(self, raw_level: float | None) -> float | None:
        if raw_level is None:
            return None

        zero_cal = self._param("input_zero_cal", 0)
        scaling_cal = self._param("input_scaling_cal", 1)
        sensor_max = self._param("input_max", 250)
        tank_type = self._param("tank_type", "Flat Bottom")

        processed = (raw_level + zero_cal) * scaling_cal
        if not sensor_max:
            return None
        pct = round((processed / sensor_max) * 100, 1)

        if tank_type == "Horizontal Cylinder":
            # Horizontal cylinder cross-section area mapping (legacy formula)
            r = 50.0
            h = max(0.0, min(pct, 100.0))
            try:
                pct = math.acos((r - h) / r) * (r * r) - (r - h) * math.sqrt(2 * r * h - h * h)
            except ValueError:
                pass

        return pct

    def _param(self, name: str, default):
        try:
            element = getattr(self.ui.details, name, None) or getattr(self.ui, name, None)
            if element is None:
                return default
            value = element.value
            return value if value is not None else default
        except Exception:
            return default

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
        level_alarm = self._param("input_low_level", None)
        batt_alarm = self._param("batt_alarm_level", None)

        new_level_warn = (
            level_alarm is not None and level_pct is not None and level_pct < level_alarm
        )
        new_batt_warn = (
            batt_alarm is not None and battery_pct is not None and battery_pct < batt_alarm
        )

        prev_level_warn = await self.tags.level_low_warning.get()
        prev_batt_warn = await self.tags.batt_low_warning.get()

        await self.tags.level_low_warning.set(new_level_warn)
        await self.tags.batt_low_warning.set(new_batt_warn)

        if new_level_warn and not prev_level_warn:
            await self._notify("Level is getting low")
        if new_batt_warn and not prev_batt_warn:
            await self._notify("Battery is getting low")

    async def _notify(self, message: str):
        log.info("Ellenex notification: %s", message)
        await self.api.create_message("significantEvent", message)
        await self.api.create_message("activity_logs", {"activity_log": {"action_string": message}})
