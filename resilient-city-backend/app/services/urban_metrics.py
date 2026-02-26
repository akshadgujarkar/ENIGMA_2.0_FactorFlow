def calculate_heat_index(data):
    total_temp = 0
    count = 0

    for feature in data["features"]:
        total_temp += feature["properties"].get("temperature", 0)
        count += 1

    return total_temp / count if count else 0