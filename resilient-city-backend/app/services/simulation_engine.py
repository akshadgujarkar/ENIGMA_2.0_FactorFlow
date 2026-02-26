def simulate(data, green_increase, rainfall):
    for feature in data["features"]:
        props = feature["properties"]

        ndvi = props.get("ndvi", 0.3)
        temperature = props.get("temperature", 30)
        impervious = props.get("impervious", 0.5)
        elevation = props.get("elevation", 10)

        # Increase vegetation
        ndvi = ndvi * (1 + green_increase / 100)

        # Reduce heat island effect
        temperature = temperature - (green_increase * 0.15)

        # Flood risk calculation
        flood_risk = (rainfall * impervious) / max(elevation, 1)

        props["ndvi"] = ndvi
        props["temperature"] = temperature
        props["flood_risk"] = flood_risk

    return data