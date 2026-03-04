"""
DroughtAI — Entraînement Multi-Modèles ML
==========================================
Entraîne et compare : Random Forest, Gradient Boosting, XGBoost, SVM, KNN
Sauvegarde le meilleur modèle dans models/drought_ml_best.pkl

Usage:
    python ml/train_ml.py
"""

import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Imports ML ────────────────────────────────────────────────────────────
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (classification_report, confusion_matrix,
                              accuracy_score, f1_score)
from sklearn.pipeline import Pipeline

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️  XGBoost non installé — ignoré (pip install xgboost)")

# ── Config ────────────────────────────────────────────────────────────────
FEATURES = [
    "month", "precipitation", "temperature_c", "humidity",
    "soil_moisture", "evaporation", "ndvi", "stress_hydrique",
    "point_encoded",
]
TARGET   = "risk_class"
LABELS   = ["Aucun", "Faible", "Modere", "Severe", "Extreme"]
MODELS_DIR = Path("models")


def load_data():
    csv_path = Path("ml/drought_dataset.csv")
    if not csv_path.exists():
        print("Dataset non trouvé — génération automatique...")
        from ml.generate_data import generate_dataset
        df = generate_dataset(6000)
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    print(f"✅ Dataset chargé: {len(df)} lignes, {df['risk_class'].nunique()} classes")
    return df


def prepare_features(df):
    # Encoder les points GPS
    le = LabelEncoder()
    df = df.copy()
    df["point_encoded"] = le.fit_transform(df["point"])

    X = df[FEATURES].values
    y = df[TARGET].values

    return X, y, le


def train_all_models(X_train, y_train, X_test, y_test):
    """Entraîne tous les modèles et retourne les résultats."""

    models = {
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        ),
        "svm": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SVC(
                kernel="rbf",
                C=10,
                gamma="scale",
                probability=True,
                class_weight="balanced",
                random_state=42,
            )),
        ]),
        "knn": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", KNeighborsClassifier(
                n_neighbors=7,
                weights="distance",
                metric="euclidean",
            )),
        ]),
    }

    if HAS_XGB:
        models["xgboost"] = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
        )

    results = {}
    print("\n" + "=" * 60)
    print("Entraînement des modèles...")
    print("=" * 60)

    for name, model in models.items():
        print(f"\n🔄 {name}...", end=" ", flush=True)
        t0 = datetime.now()

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc  = accuracy_score(y_test, y_pred)
        f1   = f1_score(y_test, y_pred, average="weighted")
        dur  = (datetime.now() - t0).total_seconds()

        results[name] = {
            "model":    model,
            "accuracy": acc,
            "f1":       f1,
            "duration": dur,
            "y_pred":   y_pred,
        }

        status = "✅" if f1 >= 0.70 else ("⚠️" if f1 >= 0.50 else "❌")
        print(f"{status} Accuracy={acc:.3f} F1={f1:.3f} ({dur:.1f}s)")

    return results


def print_comparison(results):
    """Affiche le tableau comparatif."""
    print("\n" + "=" * 60)
    print("📊 COMPARAISON DES MODÈLES")
    print("=" * 60)
    print(f"  {'Modèle':22s} {'Accuracy':>10s} {'F1':>10s} {'Durée':>8s}")
    print("  " + "-" * 55)

    sorted_results = sorted(results.items(), key=lambda x: x[1]["f1"], reverse=True)
    for i, (name, r) in enumerate(sorted_results):
        medal = ["🥇","🥈","🥉"][i] if i < 3 else "  "
        print(f"  {medal} {name:20s} {r['accuracy']:10.3f} {r['f1']:10.3f} {r['duration']:7.1f}s")

    best_name, best_r = sorted_results[0]
    print(f"\n🏆 Meilleur modèle : {best_name} (F1={best_r['f1']:.3f})")
    return best_name


def save_best_model(best_name, results, le):
    """Sauvegarde le meilleur modèle."""
    MODELS_DIR.mkdir(exist_ok=True)
    best_model = results[best_name]["model"]

    artifact = {
        "model":       best_model,
        "model_name":  best_name,
        "label_encoder": le,
        "features":    FEATURES,
        "labels":      LABELS,
        "accuracy":    results[best_name]["accuracy"],
        "f1":          results[best_name]["f1"],
        "trained_at":  datetime.now().isoformat(),
    }

    # Sauvegarder tous les modèles + le meilleur séparément
    pkl_path = MODELS_DIR / "drought_ml_best.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(artifact, f)
    print(f"\n✅ Meilleur modèle sauvegardé: {pkl_path}")

    # Sauvegarder aussi tous les modèles
    all_models = {}
    for name, r in results.items():
        all_models[name] = {
            "model":    r["model"],
            "accuracy": r["accuracy"],
            "f1":       r["f1"],
        }
    all_models["label_encoder"] = le
    all_models["features"]      = FEATURES
    all_models["labels"]        = LABELS

    all_path = MODELS_DIR / "drought_ml_all.pkl"
    with open(all_path, "wb") as f:
        pickle.dump(all_models, f)
    print(f"✅ Tous les modèles: {all_path}")

    # Métriques JSON
    metrics = {
        "best_model": best_name,
        "models": {
            name: {"accuracy": r["accuracy"], "f1": r["f1"]}
            for name, r in results.items()
        },
        "trained_at": datetime.now().isoformat(),
    }
    with open(MODELS_DIR / "ml_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Métriques: models/ml_metrics.json")


def print_detail(best_name, results, y_test):
    """Affiche le rapport détaillé du meilleur modèle."""
    r      = results[best_name]
    y_pred = r["y_pred"]

    print(f"\n📊 Rapport détaillé — {best_name}")
    print("=" * 60)
    present = sorted(set(y_test) | set(y_pred))
    target_names = [LABELS[i] for i in present]
    print(classification_report(y_test, y_pred,
                                  labels=present,
                                  target_names=target_names,
                                  zero_division=0))


# ── MAIN ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("DroughtAI — Entraînement Multi-Modèles ML")
    print("=" * 60)

    # 1. Charger les données
    df = load_data()
    X, y, le = prepare_features(df)

    print(f"\nFeatures utilisées ({len(FEATURES)}):")
    for f in FEATURES:
        print(f"  • {f}")

    # 2. Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"\nSplit: {len(X_train)} train | {len(X_test)} test")

    # 3. Entraîner tous les modèles
    results = train_all_models(X_train, y_train, X_test, y_test)

    # 4. Comparer et choisir le meilleur
    best_name = print_comparison(results)

    # 5. Rapport détaillé
    print_detail(best_name, results, y_test)

    # 6. Sauvegarder
    save_best_model(best_name, results, le)

    print("\n" + "=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)
    print("➡️  Redémarre l'API Flask : python api/app.py")
    print("    Le modèle ML sera chargé automatiquement.")
