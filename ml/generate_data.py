"""
Génère un dataset réaliste pour la Mauritanie
basé sur les vraies conditions climatiques 2018-2023.
"""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

# ── Paramètres climatiques réels par point GPS ────────────────────────────
POINTS = {
    "Rosso": {
        "lat": 16.51, "lon": -15.80,
        "temp_base": 30, "temp_amp": 8,
        "precip_annual": 280,
        "soil_base": 0.12,
    },
    "Boghe": {
        "lat": 17.03, "lon": -14.28,
        "temp_base": 31, "temp_amp": 9,
        "precip_annual": 240,
        "soil_base": 0.10,
    },
    "Kaedi": {
        "lat": 16.15, "lon": -13.50,
        "temp_base": 32, "temp_amp": 9,
        "precip_annual": 200,
        "soil_base": 0.09,
    },
    "NouakchottSud": {
        "lat": 18.00, "lon": -15.95,
        "temp_base": 28, "temp_amp": 6,
        "precip_annual": 100,
        "soil_base": 0.06,
    },
    "Matam": {
        "lat": 15.66, "lon": -13.26,
        "temp_base": 33, "temp_amp": 10,
        "precip_annual": 350,
        "soil_base": 0.13,
    },
}

# Distribution mensuelle des précipitations (% du total annuel)
MONTHLY_RAIN = {
    1:0.002, 2:0.003, 3:0.003, 4:0.005,
    5:0.010, 6:0.050, 7:0.150, 8:0.350,
    9:0.280, 10:0.100, 11:0.030, 12:0.005,
}

def get_ndvi(precip, soil_moisture, month):
    """NDVI basé sur précipitations et saison."""
    base = 0.07
    rain_effect = min(0.25, precip / 150)
    soil_effect = min(0.10, soil_moisture * 0.8)
    season = 0.05 if month in [7,8,9] else 0.0
    ndvi = base + rain_effect + soil_effect + season
    return round(min(0.50, ndvi + np.random.normal(0, 0.015)), 3)

def get_risk_class(ndvi, soil_moisture, precip, temp, humidity, point_name):
    """Calcule la classe de risque réelle (0-4)."""
    p = POINTS[point_name]

    # Score de sécheresse (plus c'est haut, plus c'est sec)
    drought_score = 0

    # NDVI très bas → grande sécheresse
    if ndvi < 0.08:   drought_score += 3
    elif ndvi < 0.12: drought_score += 2
    elif ndvi < 0.18: drought_score += 1

    # Sol très sec
    if soil_moisture < 0.05:  drought_score += 3
    elif soil_moisture < 0.08: drought_score += 2
    elif soil_moisture < 0.12: drought_score += 1

    # Précipitations nulles
    if precip < 2:   drought_score += 3
    elif precip < 8:  drought_score += 2
    elif precip < 20: drought_score += 1

    # Température très haute
    if temp > 42:   drought_score += 2
    elif temp > 38: drought_score += 1

    # Humidité très basse
    if humidity < 15: drought_score += 2
    elif humidity < 25: drought_score += 1

    # Zone désertique (NouakchottSud) → +1
    if point_name == "NouakchottSud": drought_score += 1

    # Convertir en classe 0-4
    if drought_score >= 10: return 4   # Extrême
    elif drought_score >= 7: return 3  # Sévère
    elif drought_score >= 4: return 2  # Modéré
    elif drought_score >= 2: return 1  # Faible
    else: return 0                      # Aucun

def generate_dataset(n_samples=5000):
    records = []
    years   = list(range(2018, 2024))
    months  = list(range(1, 13))
    point_names = list(POINTS.keys())

    for _ in range(n_samples):
        point_name = np.random.choice(point_names)
        p     = POINTS[point_name]
        year  = np.random.choice(years)
        month = np.random.choice(months)

        # Température mensuelle réaliste
        temp_seasonal = p["temp_base"] + p["temp_amp"] * np.sin((month - 4) * np.pi / 6)
        temp  = round(temp_seasonal + np.random.normal(0, 2), 1)
        temp  = max(20, min(50, temp))

        # Précipitations mensuelles
        rain_ratio = MONTHLY_RAIN[month]
        precip_mean = p["precip_annual"] * rain_ratio
        precip = round(max(0, np.random.exponential(max(0.1, precip_mean))), 1)
        precip = min(200, precip)

        # Humidité
        humidity_base = 20 + (precip / 5) + (month in [7,8,9]) * 25
        humidity = round(max(5, min(95, humidity_base + np.random.normal(0, 6))), 1)

        # Humidité sol
        soil_base = p["soil_base"] + (precip / 300)
        soil_moisture = round(max(0.02, min(0.40, soil_base + np.random.normal(0, 0.02))), 3)

        # Évaporation
        evaporation = round(temp * 2.3 + np.random.normal(0, 3), 1)
        evaporation = max(5, min(120, evaporation))

        # Stress hydrique
        stress = round(max(0, min(1, 1 - soil_moisture / 0.25)), 3)

        # NDVI
        ndvi = get_ndvi(precip, soil_moisture, month)

        # Classe de risque
        risk_class = get_risk_class(ndvi, soil_moisture, precip, temp, humidity, point_name)

        records.append({
            "point":           point_name,
            "year":            year,
            "month":           month,
            "precipitation":   precip,
            "temperature_c":   temp,
            "humidity":        humidity,
            "soil_moisture":   soil_moisture,
            "evaporation":     evaporation,
            "ndvi":            ndvi,
            "stress_hydrique": stress,
            "risk_class":      risk_class,
        })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    Path("ml").mkdir(exist_ok=True)
    df = generate_dataset(6000)
    df.to_csv("ml/drought_dataset.csv", index=False)

    print(f"✅ Dataset: {len(df)} lignes")
    print(f"\nDistribution des classes:")
    labels = ["Aucun","Faible","Modéré","Sévère","Extrême"]
    for i in range(5):
        n   = (df['risk_class']==i).sum()
        pct = n/len(df)*100
        bar = "█" * int(pct/2)
        print(f"  {i} {labels[i]:10s}: {n:4d} ({pct:.1f}%) {bar}")

    print(f"\nSaved: ml/drought_dataset.csv")
