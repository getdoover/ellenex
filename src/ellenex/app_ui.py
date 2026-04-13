from pathlib import Path

from pydoover import ui

from .app_tags import EllenexTags


class EllenexUI(ui.UI, hidden="$config.app().hide_ui"):
    level = ui.NumericVariable(
        "Level (%)",
        value=EllenexTags.level_pct,
        precision=1,
        form="radialGauge",
        ranges=[
            ui.Range("Low", 0, 40, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Half", 40, 80, ui.Colour.blue, show_on_graph=True),
            ui.Range("Full", 80, 100, ui.Colour.green, show_on_graph=True),
        ],
    )

    battery_level = ui.NumericVariable(
        "Battery (%)",
        value=EllenexTags.battery_pct,
        precision=0,
        ranges=[
            ui.Range("Low", 0, 30, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Half", 30, 80, ui.Colour.blue, show_on_graph=True),
            ui.Range("Full", 80, 100, ui.Colour.green, show_on_graph=True),
        ],
    )

    level_low_warning = ui.WarningIndicator(
        "Level Low",
        hidden="!$tag.app().level_low_warning",
    )
    batt_low_warning = ui.WarningIndicator(
        "Battery Low",
        hidden="!$tag.app().batt_low_warning",
    )

    details = ui.Submodule(
        "Details",
        children=[
            ui.Select(
                "Tank Type",
                options=[ui.Option("Flat Bottom"), ui.Option("Horizontal Cylinder")],
                name="tank_type",
            ),
            ui.FloatInput("Max Level (cm)", min_val=0, max_val=999, name="input_max"),
            ui.FloatInput("Low level alarm (%)", min_val=0, max_val=99, name="input_low_level"),
            ui.FloatInput("Zero Calibration (cm)", min_val=-999, max_val=999, name="input_zero_cal"),
            ui.FloatInput("Scaling Calibration (x multiply)", min_val=-999, max_val=999, name="input_scaling_cal"),
            ui.FloatInput("Battery Alarm (%)", min_val=0, max_val=100, name="batt_alarm_level"),
            ui.NumericVariable(
                "Raw Reading",
                value=EllenexTags.raw_level,
                precision=2,
                name="raw_level",
            ),
            ui.NumericVariable(
                "Battery (V)",
                value=EllenexTags.raw_battery_v,
                precision=2,
                name="raw_battery_v",
            ),
        ],
    )


def export():
    EllenexUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "ellenex_lorawan",
    )
