from pydoover.tags import Tag, Tags


class EllenexTags(Tags):
    # Computed values shown in main UI
    level_pct = Tag("number", default=None)
    battery_pct = Tag("number", default=None)

    # Raw values from the sensor
    raw_level = Tag("number", default=None)
    raw_battery_v = Tag("number", default=None)

    # Warning state (drives WarningIndicator visibility)
    level_low_warning = Tag("boolean", default=False)
    batt_low_warning = Tag("boolean", default=False)
