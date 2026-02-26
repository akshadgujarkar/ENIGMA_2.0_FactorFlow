def calculate_sdg(data):
    total_temp = 0
    total_ndvi = 0
    total_flood = 0
    count = 0

    for feature in data["features"]:
        props = feature["properties"]
        total_temp += props.get("temperature", 0)
        total_ndvi += props.get("ndvi", 0)
        total_flood += props.get("flood_risk", 0)
        count += 1

    if count == 0:
        return 0

    avg_temp = total_temp / count
    avg_ndvi = total_ndvi / count
    avg_flood = total_flood / count

    score = 100 - (avg_temp + avg_flood) + (avg_ndvi * 50)

    return round(max(min(score, 100), 0), 2)