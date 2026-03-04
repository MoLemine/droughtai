"""
DroughtAI — Collecte données réelles NASA POWER
================================================
Télécharge les vraies données climatiques 2018-2023
pour 5 points GPS en Mauritanie.

Source : NASA POWER API (gratuit, sans clé API)
https://power.larc.nasa.gov/

Variables collectées :
  T2M       → Température 2m (°C)
  PRECTOTCORR → Précipitations (mm/jour)
  RH2M      → Humidité relative (%)
  EVLAND    → Évapotranspiration (mm/jour)
  ALLSKY_SFC_SW_DWN → Rayonnement solaire

Usage:
    pip install requests pandas numpy
    python ml/1_collect_nasa.py
"""

import requests
import pandas as pd
import numpy as np
import time
import json
from pathlib import Path
from datetime import datetime

# ── Points GPS Mauritanie ─────────────────────────────────────────────────
POINTS = {
    "Rosso":         {"lat": 16.51, "lon": -15.80},
    "Boghe":         {"lat": 17.03, "lon": -14.28},
    "Kaedi":         {"lat": 16.15, "lon": -13.50},
    "NouakchottSud": {"lat": 18.00, "lon": -15.95},
    "Matam":         {"lat": 15.66, "lon": -13.26},
}

# ── Paramètres NASA POWER ─────────────────────────────────────────────────
NASA_URL   = "https://power.larc.nasa.gov/api/temporal/monthly/point"
START_YEAR = 2018
END_YEAR   = 2023

PARAMETERS = ",".join([
    "T2M",            # Température 2m (°C)
    "T2M_MAX",        # Température max
    "T2M_MIN",        # Température min
    "PRECTOTCORR",    # Précipitations corrigées (mm/jour)
    "RH2M",           # Humidité relative 2m (%)
    "EVLAND",         # Évapotranspiration (mm/jour)
    "ALLSKY_SFC_SW_DWN",  # Rayonnement solaire
    "WS2M",           # Vitesse vent 2m (m/s)
    "GWETROOT",       # Humidité sol racines (0-1)
    "GWETPROF",       # Humidité sol profil (0-1)
])


def fetch_nasa_point(name: str, lat: float, lon: float) -> pd.DataFrame | None:
    """Télécharge les données NASA POWER pour un point GPS."""
    
    params = {
        "parameters": PARAMETERS,
        "community":  "AG",           # Agriculture
        "longitude":  lon,
        "latitude":   lat,
        "start":      START_YEAR,
        "end":        END_YEAR,
        "format":     "JSON",
    }
    
    print(f"  📡 {name} ({lat}, {lon})...", end=" ", flush=True)
    
    try:
        r = requests.get(NASA_URL, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        
        properties = data.get("properties", {}).get("parameter", {})
        if not properties:
            print("❌ Données vides")
            return None
        
        rows = []
        for year in range(START_YEAR, END_YEAR + 1):
            for month in range(1, 13):
                key = f"{year}{month:02d}"
                row = {
                    "point": name,
                    "lat":   lat,
                    "lon":   lon,
                    "year":  year,
                    "month": month,
                }
                
                for param, values in properties.items():
                    val = values.get(key, -999)
                    # NASA utilise -999 pour les valeurs manquantes
                    row[param] = np.nan if val <= -998 else val
                
                rows.append(row)
        
        df = pd.DataFrame(rows)
        print(f"✅ {len(df)} mois")
        return df
        
    except requests.exceptions.Timeout:
        print("❌ Timeout — réessaie plus tard")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Pas de connexion internet")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def add_ndvi_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule un proxy NDVI depuis les variables NASA.
    NDVI réel nécessite MODIS, mais on peut l'estimer depuis
    précipitations + humidité sol + saison.
    """
    df = df.copy()
    
    # NDVI proxy basé sur humidité sol + précipitations + saison
    def calc_ndvi(row):
        precip      = row.get("PRECTOTCORR", 0) * 30  # mm/jour → mm/mois
        soil        = row.get("GWETROOT", 0.1)
        month       = row["month"]
        
        # Saison des pluies juillet-septembre = NDVI plus haut
        season_bonus = 0.08 if month in [7, 8, 9] else (
                       0.04 if month in [6, 10] else 0.0)
        
        base  = 0.07
        ndvi  = base + min(0.20, precip / 120) + min(0.10, soil * 0.4) + season_bonus
        noise = np.random.normal(0, 0.012)
        return round(max(0.04, min(0.50, ndvi + noise)), 3)
    
    df["ndvi"] = df.apply(calc_ndvi, axis=1)
    return df


def clean_and_rename(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme et nettoie les colonnes."""
    df = df.copy()
    
    rename = {
        "T2M":              "temperature_c",
        "PRECTOTCORR":      "precip_daily",     # mm/jour
        "RH2M":             "humidity",
        "EVLAND":           "evap_daily",        # mm/jour
        "GWETROOT":         "soil_moisture",
        "GWETPROF":         "soil_moisture_deep",
        "ALLSKY_SFC_SW_DWN":"solar_radiation",
        "WS2M":             "wind_speed",
        "T2M_MAX":          "temp_max",
        "T2M_MIN":          "temp_min",
    }
    df.rename(columns=rename, inplace=True)
    
    # Convertir précipitations : mm/jour → mm/mois
    if "precip_daily" in df.columns:
        df["precipitation"] = (df["precip_daily"] * 30).round(1)
        df.drop(columns=["precip_daily"], inplace=True)
    
    if "evap_daily" in df.columns:
        df["evaporation"] = (df["evap_daily"] * 30).round(1)
        df.drop(columns=["evap_daily"], inplace=True)
    
    # Stress hydrique calculé depuis humidité sol
    if "soil_moisture" in df.columns:
        df["stress_hydrique"] = (1 - df["soil_moisture"] / 0.30).clip(0, 1).round(3)
    
    # Supprimer valeurs aberrantes
    if "temperature_c" in df.columns:
        df.loc[df["temperature_c"] > 55, "temperature_c"] = np.nan
        df.loc[df["temperature_c"] < 10, "temperature_c"] = np.nan
    
    if "humidity" in df.columns:
        df.loc[df["humidity"] > 100, "humidity"] = 100
        df.loc[df["humidity"] < 0,   "humidity"] = 0
    
    if "precipitation" in df.columns:
        df.loc[df["precipitation"] < 0, "precipitation"] = 0
    
    # Interpoler les NaN
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method="linear", limit=2)
    df.dropna(subset=["temperature_c", "precipitation", "humidity"], inplace=True)
    
    return df


def assign_risk_class(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assigne la classe de risque basée sur les indices réels :
    SPI (Standardized Precipitation Index) simplifié + humidité sol.
    """
    df = df.copy()
    
    # Normaliser les précipitations par point et mois (SPI simplifié)
    df["precip_zscore"] = df.groupby(["point", "month"])["precipitation"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-6)
    )
    
    # Score de sécheresse composite
    def drought_score(row):
        score = 0
        
        # SPI (précipitations normalisées)
        spi = row.get("precip_zscore", 0)
        if spi < -2.0:   score += 4
        elif spi < -1.5: score += 3
        elif spi < -1.0: score += 2
        elif spi < -0.5: score += 1
        
        # Humidité sol
        sm = row.get("soil_moisture", 0.15)
        if sm < 0.05:   score += 3
        elif sm < 0.08: score += 2
        elif sm < 0.12: score += 1
        
        # NDVI
        ndvi = row.get("ndvi", 0.15)
        if ndvi < 0.07:   score += 3
        elif ndvi < 0.10: score += 2
        elif ndvi < 0.15: score += 1
        
        # Température très haute
        temp = row.get("temperature_c", 30)
        if temp > 42:   score += 2
        elif temp > 38: score += 1
        
        # Humidité air très basse
        rh = row.get("humidity", 40)
        if rh < 15:   score += 2
        elif rh < 25: score += 1
        
        return score
    
    df["drought_score"] = df.apply(drought_score, axis=1)
    
    # Convertir score → classe 0-4
    df["risk_class"] = pd.cut(
        df["drought_score"],
        bins=[-1, 2, 4, 6, 9, 100],
        labels=[0, 1, 2, 3, 4]
    ).astype(int)
    
    return df


def main():
    print("=" * 60)
    print("DroughtAI — Collecte NASA POWER")
    print(f"Période : {START_YEAR}–{END_YEAR}")
    print(f"Points  : {len(POINTS)}")
    print("=" * 60)
    print()
    
    Path("ml").mkdir(exist_ok=True)
    all_dfs = []
    
    for name, coords in POINTS.items():
        df = fetch_nasa_point(name, coords["lat"], coords["lon"])
        if df is not None:
            all_dfs.append(df)
        time.sleep(1.5)  # Respecter les limites NASA API
    
    if not all_dfs:
        print("\n❌ Aucune donnée collectée.")
        print("   Vérifie ta connexion internet.")
        return
    
    print(f"\n✅ {len(all_dfs)}/{len(POINTS)} points collectés")
    
    # Fusionner
    df = pd.concat(all_dfs, ignore_index=True)
    
    # Nettoyer et renommer
    print("\n🔧 Nettoyage des données...")
    df = clean_and_rename(df)
    
    # Ajouter NDVI proxy
    print("🌿 Calcul NDVI proxy...")
    df = add_ndvi_proxy(df)
    
    # Assigner classes de risque
    print("🎯 Calcul des classes de risque...")
    df = assign_risk_class(df)
    
    # Sauvegarder données brutes
    raw_path = Path("ml/nasa_raw.csv")
    df.to_csv(raw_path, index=False)
    print(f"✅ Données brutes: {raw_path} ({len(df)} lignes)")
    
    # Sauvegarder dataset final pour ML
    ml_cols = [
        "point", "year", "month",
        "precipitation", "temperature_c", "humidity",
        "soil_moisture", "evaporation", "ndvi",
        "stress_hydrique", "risk_class"
    ]
    available = [c for c in ml_cols if c in df.columns]
    df_ml = df[available].dropna()
    
    ml_path = Path("ml/drought_dataset.csv")
    df_ml.to_csv(ml_path, index=False)
    
    # Statistiques
    print(f"\n📊 Dataset final : {len(df_ml)} lignes")
    print(f"\nDistribution des classes de risque :")
    labels = ["Aucun","Faible","Modéré","Sévère","Extrême"]
    for i in range(5):
        n   = (df_ml["risk_class"] == i).sum()
        pct = n / len(df_ml) * 100 if len(df_ml) > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {i} {labels[i]:10s}: {n:4d} ({pct:5.1f}%) {bar}")
    
    print(f"\nColonnes disponibles :")
    for c in df_ml.columns:
        print(f"  • {c}: min={df_ml[c].min():.2f}, max={df_ml[c].max():.2f}, "
              f"mean={df_ml[c].mean():.2f}")
    
    # Sauvegarder aussi les métadonnées
    meta = {
        "source":     "NASA POWER API",
        "url":        "https://power.larc.nasa.gov/",
        "period":     f"{START_YEAR}-{END_YEAR}",
        "points":     list(POINTS.keys()),
        "n_rows":     len(df_ml),
        "collected_at": datetime.now().isoformat(),
        "parameters": PARAMETERS,
    }
    with open("ml/data_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    
    print(f"\n✅ Métadonnées: ml/data_metadata.json")
    print(f"\n➡️  Étape suivante: python ml/2_train_compare.py")


if __name__ == "__main__":
    main()
