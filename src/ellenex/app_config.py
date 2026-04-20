import enum
from pathlib import Path

from pydoover import config
from pydoover.processor import ManySubscriptionConfig


class SensorType(enum.Enum):
    PLS2_L = "pls2-l"
    PLS3_L = "pls3-l"
    PLV3_L = "plv3-l"
    DUS2_L = "dus2-l"
    DRC3_L = "drc3-l"


class TankType(enum.Enum):
    NA = "N/A"
    FLAT_BOTTOM = "Flat Bottom"
    HORIZONTAL_CYLINDER = "Horizontal Cylinder"


class StorageCurvePoint(config.Object):
    level_m = config.Number("Level (m)", description="Sensor level reading in metres.")
    volume_ml = config.Number("Volume (ML)", description="Stored volume at this level in megalitres.")


class EllenexProcessorConfig(config.Schema):
    subscription = ManySubscriptionConfig(default=["on_tts_event", "ui_cmds"], hidden=True)
    position = config.ApplicationPosition()

    sensor_type = config.Enum(
        "Sensor Type",
        choices=SensorType,
        default=SensorType.PLS3_L,
        description="Which Ellenex level sensor model is reporting on this device.",
    )

    tank_type = config.Enum(
        "Tank Type",
        choices=TankType,
        default=TankType.FLAT_BOTTOM,
        description="Tank geometry — used to translate depth to percentage full.",
    )
    max_level = config.Number(
        "Max Level (m)",
        default=2.5,
        description="Sensor reading (in metres) that corresponds to 100% full.",
    )
    zero_calibration = config.Number(
        "Zero Calibration (m)",
        default=0.0,
        description="Offset (in metres) added to every raw sensor reading before scaling.",
    )
    scaling_calibration = config.Number(
        "Scaling Calibration",
        default=1.0,
        description="Multiplier applied after the zero offset.",
    )
    low_level_alarm = config.Number(
        "Low Level Alarm (%)",
        default=None,
        description="Trigger a low-level warning when the tank drops below this percentage.",
    )
    battery_alarm = config.Number(
        "Battery Alarm (%)",
        default=None,
        description="Trigger a low-battery warning when battery drops below this percentage.",
    )
    storage_curve = config.Array(
        "Storage Curve",
        element=StorageCurvePoint("Point"),
        description=(
            "Optional lookup table mapping sensor level (m) to stored volume (ML). "
            "When provided, volume is reported alongside percentage."
        ),
    )

    hide_ui = config.Boolean(
        "Hide Default UI",
        description="Whether to hide the default UI. Useful if you have a custom UI application.",
        default=False,
    )


def export():
    EllenexProcessorConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "ellenex_lorawan",
    )
