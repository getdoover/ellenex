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
        form=ui.Widget.radial,
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
            ui.FloatInput(
                "Uplink Interval",
                units="min",
                default=240,
                min_val=1,
                max_val=1440,
                precision=0,
                name="uplink_interval",
            ),
        ],
    )

    async def setup(self):
        # Build volume gauge ranges from the configured storage curve.
        # Thresholds mirror the % gauge: 40% / 80% of max sensor depth,
        # looked up through the curve to get absolute ML values.
        curve = sorted(
            (
                (p.level_m.value, p.volume_ml.value)
                for p in self.config.storage_curve.value
                if p.level_m.value is not None and p.volume_ml.value is not None
            ),
            key=lambda p: p[0],
        )
        if len(curve) < 2:
            return

        max_depth = self.config.max_level.value or curve[-1][0]
        max_volume = curve[-1][1]

        def volume_at(depth: float) -> float:
            for (x1, y1), (x2, y2) in zip(curve, curve[1:]):
                if x1 <= depth <= x2:
                    return y1 + (depth - x1) * (y2 - y1) / (x2 - x1)
            return max_volume if depth > curve[-1][0] else curve[0][1]

        low = int(volume_at(max_depth * 0.4))
        high = int(volume_at(max_depth * 0.8))
        self.level_volume.ranges = [
            ui.Range("Low", 0, low, ui.Colour.yellow),
            ui.Range("Half", low, high, ui.Colour.blue),
            ui.Range("Full", high, int(max_volume), ui.Colour.green),
        ]


def export():
    EllenexUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "ellenex_lorawan",
    )
