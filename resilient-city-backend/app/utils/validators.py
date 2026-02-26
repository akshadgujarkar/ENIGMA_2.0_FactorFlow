def validate_scenario(scenario):
    if "green_increase" not in scenario or "rainfall" not in scenario:
        raise ValueError("Missing scenario parameters")