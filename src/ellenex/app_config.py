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


class EllenexProcessorConfig(config.Schema):
    subscription = ManySubscriptionConfig(default=["on_tts_event"], hidden=True)
    position = config.ApplicationPosition()

    sensor_type = config.Enum(
        "Sensor Type",
        choices=SensorType,
        default=SensorType.PLS3_L,
        description="Which Ellenex level sensor model is reporting on this device.",
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
