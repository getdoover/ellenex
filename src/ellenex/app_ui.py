from pathlib import Path

from pydoover import ui

from .app_tags import EllenexTags


class EllenexUI(ui.UI, hidden="$config.app().hide_ui"):
    level = ui.NumericVariable(
        "Level",
        units="%",
        value=EllenexTags.level_pct,
        precision=1,
        form=ui.Widget.radial,
        ranges=[
            ui.Range("Low", 0, 40, ui.Colour.yellow),
            ui.Range("Half", 40, 80, ui.Colour.blue),
            ui.Range("Full", 80, 100, ui.Colour.green),
        ],
        hidden=EllenexTags.level_pct_hidden,
    )

    level_volume = ui.NumericVariable(
        "Volume",
        units="ML",
        value=EllenexTags.level_volume,
        precision=2,
        hidden=EllenexTags.level_volume_hidden,
    )

    battery_level = ui.NumericVariable(
        "Battery",
        units="%",
        value=EllenexTags.battery_pct,
        precision=0,
        ranges=[
            ui.Range("Low", 0, 30, ui.Colour.yellow),
            ui.Range("Half", 30, 80, ui.Colour.blue),
            ui.Range("Full", 80, 100, ui.Colour.green),
        ],
    )

    level_low_warning = ui.WarningIndicator(
        "Level Low",
        hidden=EllenexTags.level_low_warning_hidden,
    )
    batt_low_warning = ui.WarningIndicator(
        "Battery Low",
        hidden=EllenexTags.batt_low_warning_hidden,
    )

    details = ui.Submodule(
        "Details",
        children=[
            ui.NumericVariable(
                "Raw Reading",
                value=EllenexTags.raw_level,
                precision=2,
                name="raw_level",
            ),
            ui.NumericVariable(
                "Battery",
                units="V",
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
