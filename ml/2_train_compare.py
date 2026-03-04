"""
DroughtAI — Comparaison 7 Algorithmes ML
==========================================
Algorithms testés :
  1. Random Forest
  2. Gradient Boosting
  3. XGBoost
  4. LightGBM
  5. SVM (RBF)
  6. KNN
  7. Logistic Regression (baseline)

Usage:
    pip install scikit-learn xgboost lightgbm pandas numpy matplotlib seaborn
    python ml/2_train_compare.py
"""

import pickle, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from time import time

warnings.filterwarnings("ignore")

# ── Sklearn ────────────────────────────────────────────────────────────────
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import (train_test_split, cross_val_score,
                                      StratifiedKFold)
from sklearn.metrics import (classification_report, confusion_matrix,
                              accuracy_score, f1_score, precision_score,
                              recall_score)
from sklearn.pipeline import Pipeline

# ── XGBoost ────────────────────────────────────────────────────────────────
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️  XGBoost non dispo — pip install xgboost")

# ── LightGBM ───────────────────────────────────────────────────────────────
try:
    from lightgbm import LGBMClassifier
    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    print("⚠️  LightGBM non dispo — pip install lightgbm")

# ── Config ─────────────────────────────────────────────────────────────────
FEATURES = [
    "month", "precipitation", "temperature_c", "humidity",
    "soil_moisture", "evaporation", "ndvi", "stress_hydrique",
    "point_encoded",
]
TARGET     = "risk_class"
LABELS     = ["Aucun", "Faible", "Modere", "Severe", "Extreme"]
MODELS_DIR = Path("models")
ML_DIR     = Path("ml")
CV_FOLDS   = 5


# ── Chargement données ─────────────────────────────────────────────────────

def load_data():
    csv = ML_DIR / "drought_dataset.csv"
    if not csv.exists():
        print(f"❌ {csv} non trouvé")
        print("   Lance d'abord: python ml/1_collect_nasa.py")
        exit(1)

    df = pd.read_csv(csv)
    print(f"✅ Dataset chargé: {len(df)} lignes")
    print(f"   Source: {'NASA POWER réel' if (ML_DIR/'data_metadata.json').exists() else 'Données générées'}")

    # Encoder point GPS
    le = LabelEncoder()
    df["point_encoded"] = le.fit_transform(df["point"])

    # Vérifier colonnes manquantes
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        print(f"⚠️  Colonnes manquantes: {missing}")
        for col in missing:
            df[col] = 0

    X = df[FEATURES].values
    y = df[TARGET].values.astype(int)

    return X, y, le, df


# ── Définir les modèles ────────────────────────────────────────────────────

def get_models():
    models = {}

    # 1. Random Forest
    models["Random Forest"] = RandomForestClassifier(
        n_estimators=200, max_depth=15,
        min_samples_split=5, min_samples_leaf=2,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )

    # 2. Gradient Boosting
    models["Gradient Boosting"] = GradientBoostingClassifier(
        n_estimators=200, max_depth=6,
        learning_rate=0.05, subsample=0.8,
        random_state=42,
    )

    # 3. SVM
    models["SVM (RBF)"] = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", SVC(
            kernel="rbf", C=10, gamma="scale",
            probability=True, class_weight="balanced", random_state=42,
        )),
    ])

    # 4. KNN
    models["KNN (k=7)"] = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", KNeighborsClassifier(
            n_neighbors=7, weights="distance", metric="euclidean",
        )),
    ])

    # 5. Logistic Regression (baseline)
    models["Logistic Regression"] = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=1000, class_weight="balanced",
            random_state=42,
        )),
    ])

    # 6. XGBoost
    if HAS_XGB:
        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=6,
            learning_rate=0.05, subsample=0.8,
            colsample_bytree=0.8, eval_metric="mlogloss",
            random_state=42, n_jobs=-1, verbosity=0,
        )

    # 7. LightGBM
    if HAS_LGB:
        models["LightGBM"] = LGBMClassifier(
            n_estimators=200, max_depth=6,
            learning_rate=0.05, subsample=0.8,
            class_weight="balanced", random_state=42,
            n_jobs=-1, verbose=-1,
        )

    return models


# ── Entraînement + évaluation ──────────────────────────────────────────────

def train_and_evaluate(models, X_train, X_test, y_train, y_test):
    results = {}
    cv      = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=42)

    print(f"\n{'Modèle':25s} {'Acc':>7s} {'F1':>7s} {'Prec':>7s} {'Rec':>7s} {'CV F1':>8s} {'Temps':>6s}")
    print("─" * 75)

    for name, model in models.items():
        t0 = time()

        # Entraînement
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        # Métriques test
        acc  = accuracy_score(y_test, y_pred)
        f1   = f1_score(y_test, y_pred, average="weighted", zero_division=0)
        prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        rec  = recall_score(y_test, y_pred, average="weighted", zero_division=0)

        # Cross-validation F1
        try:
            cv_scores = cross_val_score(model, X_train, y_train,
                                        cv=cv, scoring="f1_weighted", n_jobs=-1)
            cv_f1 = cv_scores.mean()
            cv_std = cv_scores.std()
        except:
            cv_f1 = f1
            cv_std = 0

        dur = time() - t0

        results[name] = {
            "model":     model,
            "accuracy":  acc,
            "f1":        f1,
            "precision": prec,
            "recall":    rec,
            "cv_f1":     cv_f1,
            "cv_std":    cv_std,
            "duration":  dur,
            "y_pred":    y_pred,
        }

        # Icône selon performance
        icon = "🏆" if f1 >= 0.85 else ("✅" if f1 >= 0.70 else
               ("⚠️ " if f1 >= 0.50 else "❌"))
        print(f"{icon} {name:22s} {acc:7.3f} {f1:7.3f} {prec:7.3f} {rec:7.3f} "
              f"{cv_f1:6.3f}±{cv_std:.2f} {dur:5.1f}s")

    return results


# ── Visualisations ─────────────────────────────────────────────────────────

def plot_comparison(results):
    """Bar chart comparant tous les modèles."""
    names  = list(results.keys())
    f1s    = [r["f1"]    for r in results.values()]
    accs   = [r["accuracy"] for r in results.values()]
    cv_f1s = [r["cv_f1"] for r in results.values()]

    # Trier par F1
    sorted_idx = np.argsort(f1s)[::-1]
    names  = [names[i]  for i in sorted_idx]
    f1s    = [f1s[i]    for i in sorted_idx]
    accs   = [accs[i]   for i in sorted_idx]
    cv_f1s = [cv_f1s[i] for i in sorted_idx]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("DroughtAI — Comparaison des algorithmes ML", fontsize=14, fontweight="bold")

    # Plot 1: F1 Score comparaison
    colors = ["#2563eb" if i == 0 else "#93c5fd" for i in range(len(names))]
    bars = axes[0].barh(names, f1s, color=colors, edgecolor="white", height=0.6)
    axes[0].set_xlabel("F1 Score (weighted)")
    axes[0].set_title("F1 Score sur test set")
    axes[0].set_xlim(0, 1.05)
    axes[0].axvline(x=0.7, color="orange", linestyle="--", alpha=0.7, label="Seuil 0.70")
    axes[0].axvline(x=0.85, color="green", linestyle="--", alpha=0.7, label="Seuil 0.85")
    axes[0].legend(fontsize=8)
    for bar, val in zip(bars, f1s):
        axes[0].text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                    f"{val:.3f}", va="center", fontsize=9, fontweight="bold")

    # Plot 2: F1 vs CV F1
    x   = np.arange(len(names))
    w   = 0.35
    axes[1].bar(x - w/2, f1s,    w, label="F1 Test",  color="#2563eb", alpha=0.8)
    axes[1].bar(x + w/2, cv_f1s, w, label="F1 CV",    color="#16a34a", alpha=0.8)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(names, rotation=35, ha="right", fontsize=9)
    axes[1].set_ylabel("F1 Score")
    axes[1].set_title("F1 Test vs Cross-Validation")
    axes[1].legend()
    axes[1].set_ylim(0, 1.1)

    plt.tight_layout()
    out = ML_DIR / "model_comparison.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Graphique: {out}")


def plot_confusion_matrix(best_name, results, y_test):
    """Matrice de confusion du meilleur modèle."""
    y_pred = results[best_name]["y_pred"]
    present = sorted(set(y_test) | set(y_pred))
    cm   = confusion_matrix(y_test, y_pred, labels=present)
    lbls = [LABELS[i] for i in present]

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=lbls, yticklabels=lbls, ax=ax)
    ax.set_xlabel("Prédit")
    ax.set_ylabel("Réel")
    ax.set_title(f"Matrice de confusion — {best_name}")
    plt.tight_layout()

    out = ML_DIR / "confusion_matrix_best.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Matrice confusion: {out}")


def plot_feature_importance(best_name, results):
    """Importance des features pour les modèles qui le supportent."""
    model = results[best_name]["model"]

    try:
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "named_steps"):
            clf = model.named_steps.get("clf")
            if hasattr(clf, "feature_importances_"):
                importances = clf.feature_importances_
            else:
                return
        else:
            return

        fig, ax = plt.subplots(figsize=(8, 5))
        idx = np.argsort(importances)[::-1]
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(FEATURES)))[::-1]
        ax.bar(range(len(FEATURES)),
               importances[idx],
               color=colors[idx])
        ax.set_xticks(range(len(FEATURES)))
        ax.set_xticklabels([FEATURES[i] for i in idx],
                           rotation=40, ha="right", fontsize=9)
        ax.set_ylabel("Importance")
        ax.set_title(f"Importance des features — {best_name}")
        plt.tight_layout()

        out = ML_DIR / "feature_importance.png"
        plt.savefig(out, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"✅ Feature importance: {out}")
    except Exception as e:
        print(f"⚠️  Feature importance non disponible: {e}")


# ── Sauvegarde ─────────────────────────────────────────────────────────────

def save_all(results, best_name, le):
    MODELS_DIR.mkdir(exist_ok=True)

    # Sauvegarder le meilleur modèle
    best = results[best_name]
    artifact = {
        "model":         best["model"],
        "model_name":    best_name.lower().replace(" ", "_"),
        "label_encoder": le,
        "features":      FEATURES,
        "labels":        LABELS,
        "accuracy":      best["accuracy"],
        "f1":            best["f1"],
        "cv_f1":         best["cv_f1"],
        "trained_at":    datetime.now().isoformat(),
    }
    with open(MODELS_DIR / "drought_ml_best.pkl", "wb") as f:
        pickle.dump(artifact, f)
    print(f"✅ Meilleur modèle: models/drought_ml_best.pkl")

    # Sauvegarder tous les modèles
    all_models = {
        name: {
            "model":    r["model"],
            "accuracy": r["accuracy"],
            "f1":       r["f1"],
            "cv_f1":    r["cv_f1"],
        }
        for name, r in results.items()
    }
    all_models["_meta"] = {"label_encoder": le, "features": FEATURES, "labels": LABELS}
    with open(MODELS_DIR / "drought_ml_all.pkl", "wb") as f:
        pickle.dump(all_models, f)
    print(f"✅ Tous les modèles: models/drought_ml_all.pkl")

    # Métriques JSON
    metrics = {
        "best_model":  best_name,
        "best_f1":     best["f1"],
        "best_cv_f1":  best["cv_f1"],
        "trained_at":  datetime.now().isoformat(),
        "models": {
            name: {
                "accuracy":  r["accuracy"],
                "f1":        r["f1"],
                "precision": r["precision"],
                "recall":    r["recall"],
                "cv_f1":     r["cv_f1"],
                "duration_s":round(r["duration"], 1),
            }
            for name, r in results.items()
        },
    }
    with open(MODELS_DIR / "ml_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"✅ Métriques JSON: models/ml_metrics.json")


# ── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 75)
    print("DroughtAI — Comparaison 7 Algorithmes ML")
    print("=" * 75)

    # 1. Données
    X, y, le, df = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Split: {len(X_train)} train | {len(X_test)} test")
    print(f"Classes: { {i: int((y==i).sum()) for i in range(5)} }")

    # 2. Modèles
    models = get_models()
    print(f"\n{len(models)} algorithmes à comparer: {', '.join(models.keys())}")

    # 3. Entraînement
    print(f"\n{'─'*75}")
    results = train_and_evaluate(models, X_train, X_test, y_train, y_test)

    # 4. Classement
    sorted_r = sorted(results.items(), key=lambda x: x[1]["f1"], reverse=True)
    best_name, best_r = sorted_r[0]

    print(f"\n{'='*75}")
    print(f"🏆 MEILLEUR MODÈLE : {best_name}")
    print(f"   F1 Score  : {best_r['f1']:.4f}")
    print(f"   Accuracy  : {best_r['accuracy']:.4f}")
    print(f"   CV F1     : {best_r['cv_f1']:.4f} ± {best_r['cv_std']:.4f}")
    print(f"{'='*75}")

    # 5. Rapport détaillé
    print(f"\n📊 Rapport détaillé — {best_name}:")
    present = sorted(set(y_test) | set(best_r["y_pred"]))
    print(classification_report(
        y_test, best_r["y_pred"],
        labels=present,
        target_names=[LABELS[i] for i in present],
        zero_division=0
    ))

    # 6. Visualisations
    print("📊 Génération des graphiques...")
    try:
        plot_comparison(results)
        plot_confusion_matrix(best_name, results, y_test)
        plot_feature_importance(best_name, results)
    except Exception as e:
        print(f"⚠️  Graphiques: {e}")

    # 7. Sauvegarder
    print("\n💾 Sauvegarde des modèles...")
    save_all(results, best_name, le)

    # 8. Tableau récap final
    print(f"\n{'─'*75}")
    print(f"{'#':3s} {'Modèle':25s} {'F1':>8s} {'Accuracy':>10s} {'CV F1':>8s}")
    print(f"{'─'*75}")
    medals = ["🥇","🥈","🥉","4️⃣ ","5️⃣ ","6️⃣ ","7️⃣ "]
    for i, (name, r) in enumerate(sorted_r):
        print(f"{medals[i]} {name:24s} {r['f1']:8.4f} {r['accuracy']:10.4f} {r['cv_f1']:8.4f}")

    print(f"\n✅ TERMINÉ")
    print(f"➡️  Modèle sauvegardé → models/drought_ml_best.pkl")
    print(f"➡️  Graphiques        → ml/model_comparison.png")
    print(f"➡️  Relance Flask     → python api/app.py")
