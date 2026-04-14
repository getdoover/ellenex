from pydoover.tags import Tag, Tags


class EllenexTags(Tags):
    # Computed values shown in main UI
    level_pct = Tag("number", default=None)
    level_volume = Tag("number", default=None)
    battery_pct = Tag("number", default=None)

    # Raw values from the sensor
    raw_level = Tag("number", default=None)
    raw_battery_v = Tag("number", default=None)

    # Warning state (drives WarningIndicator visibility).
    # `*_hidden` tags are the inverse — UI `hidden=` needs a plain tag, no negation.
    level_low_warning = Tag("boolean", default=False)
    batt_low_warning = Tag("boolean", default=False)
    level_low_warning_hidden = Tag("boolean", default=True)
    batt_low_warning_hidden = Tag("boolean", default=True)

    # Drive % vs volume UI visibility — kept as opposites.
    # When a storage curve is configured, hide level_pct and show level_volume.
    level_pct_hidden = Tag("boolean", default=False)
    level_volume_hidden = Tag("boolean", default=True)
