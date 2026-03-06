# 🌾 DroughtAI — Système de Détection de Sécheresse Agricole

> Système complet d'analyse et de prédiction de la sécheresse agricole pour la Mauritanie et la Vallée du Fleuve Sénégal — combinant Computer Vision (YOLOv8) et Machine Learning (LightGBM).

---

## 📸 Aperçu

```
Photo satellite/terrain    Données climatiques
        │                         │
        ▼                         ▼
   YOLOv8 YOLO              LightGBM ML
   (détection objets)       (prédiction risque)
        │                         │
        └──────────┬──────────────┘
                   ▼
           Flask REST API
                   │
                   ▼
         Laravel 11 Dashboard
         (carte + graphiques + historique)
```

---

## 🚀 Fonctionnalités

### 📊 Tableau de bord
- Carte interactive Leaflet des 5 points GPS en Mauritanie
- Évolution du risque de sécheresse 2018–2023 par localité
- Distribution des classes de risque (graphique doughnut)
- Tendance annuelle avec indicateurs ↑↓

### 🤖 Analyse d'image (YOLOv8)
- Upload d'une photo de terrain (JPG/PNG/WebP)
- Détection automatique de 6 classes :
  - 🟤 Sol craquelé
  - 🟢 Végétation saine
  - 🟡 Stress hydrique
  - 🟠 Sol nu
  - 🔵 Eau / irrigation
  - ⚫ Végétation morte
- Score de sécheresse 0–100
- Recommandations d'intervention immédiates

### 🎯 Prédiction ML (formulaire)
- Saisie de données climatiques (précipitations, température, NDVI, humidité sol...)
- Prédiction par **7 algorithmes** comparés :
  | Algorithme | F1 Score |
  |---|---|
  | 🥇 LightGBM | **0.9875** |
  | 🥈 Gradient Boosting | 0.9816 |
  | 🥉 XGBoost | 0.9808 |
  | 4 Random Forest | 0.9665 |
  | 5 SVM (RBF) | 0.8635 |
  | 6 KNN (k=7) | 0.8380 |
  | 7 Logistic Regression | 0.8096 |
- 5 classes de risque : Aucun / Faible / Modéré / Sévère / Extrême
- Probabilités par classe + recommandations

### 📋 Historique MySQL
- Toutes les prédictions sauvegardées en base de données
- Filtres par point, risque, date
- Historique des analyses d'images avec miniatures

---

## 🗂️ Structure du projet

```
drought_yolo/
├── api/
│   └── app.py                  ← API Flask (ML + YOLO)
├── ml/
│   ├── 1_collect_nasa.py       ← Collecte données NASA POWER
│   └── 2_train_compare.py      ← Comparaison 7 algorithmes ML
├── scripts/
│   ├── 1_download_datasets.py
│   ├── 2_train_yolo.py
│   ├── 3_evaluate.py           ← Test sur images
│   └── 5_patch_app_py.py
├── data/
│   └── drought.yaml            ← Config dataset YOLO
├── drought_ai_laravel/         ← Application Laravel 11
│   ├── app/
│   │   ├── Http/Controllers/
│   │   │   ├── DashboardController.php
│   │   │   ├── PredictController.php
│   │   │   └── AnalysisController.php
│   │   ├── Models/
│   │   │   ├── Prediction.php
│   │   │   └── ImageAnalysis.php
│   │   └── Services/
│   │       ├── DroughtAiService.php
│   │       └── ImageAnalysisService.php
│   ├── database/migrations/
│   ├── resources/views/
│   └── routes/web.php
├── train.py                    ← Entraînement YOLO (CPU optimisé)
├── prepare_kaggle.py           ← Préparation datasets
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Prérequis
- Python 3.10+
- PHP 8.2+, Composer
- MySQL 8.0+
- XAMPP (Windows) ou équivalent

### 1. Cloner le projet
```bash
git clone https://github.com/Molemine/droughtai.git
cd droughtai
```

### 2. Environnement Python
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 3. Entraîner les modèles

**Données NASA POWER (réelles) :**
```bash
python ml/1_collect_nasa.py
```

**Comparer 7 algorithmes ML :**
```bash
python ml/2_train_compare.py
```

**Télécharger datasets YOLO :**
```bash
kaggle datasets download -d vipoooool/new-plant-diseases-dataset -p data/kaggle/plant_diseases --unzip
python prepare_kaggle.py
```

**Entraîner YOLO :**
```bash
python train.py
```

### 4. Lancer l'API Flask
```bash
python api\app.py
# → http://127.0.0.1:5000
```

### 5. Installer Laravel
```bash
cd drought_ai_laravel
composer install
cp .env.example .env
php artisan key:generate
```

Configurer `.env` :
```env
DB_DATABASE=droughtai
DB_USERNAME=root
DB_PASSWORD=

DROUGHTAI_URL=http://127.0.0.1:5000
DROUGHTAI_KEY=droughtai-secret-2024
```

```bash
php artisan migrate
php artisan storage:link
php artisan serve
# → http://localhost:8000
```

---

## 📡 API Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Statut API |
| GET | `/api/health` | Santé API |
| POST | `/api/predict` | Prédiction ML depuis données climatiques |
| POST | `/api/analyze/image` | Analyse YOLO d'une image (base64) |
| GET | `/api/analyze/status` | Statut modèle YOLO |
| GET | `/api/models/info` | Infos tous les modèles |

**Exemple prédiction :**
```bash
curl -X POST http://127.0.0.1:5000/api/predict \
  -H "X-API-Key: droughtai-secret-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "point": "Kaedi",
    "month": 3,
    "year": 2024,
    "precipitation": 2.0,
    "temperature_c": 40.5,
    "humidity": 18.0,
    "soil_moisture": 0.05,
    "ndvi": 0.08
  }'
```

---

## 🗺️ Points GPS couverts

| Localité | Latitude | Longitude | Précipitations annuelles |
|---|---|---|---|
| Rosso | 16.51°N | 15.80°O | ~280 mm |
| Boghe | 17.03°N | 14.28°O | ~240 mm |
| Kaedi | 16.15°N | 13.50°O | ~200 mm |
| NouakchottSud | 18.00°N | 15.95°O | ~100 mm |
| Matam | 15.66°N | 13.26°O | ~350 mm |

---

<!-- ## ❓ Pourquoi les modèles (.pt, .pkl) ne sont pas sur GitHub ?

Les fichiers modèles sont **exclus du dépôt** pour 3 raisons :

1. **Taille** : `drought_yolo_best.pt` ≈ 22 MB, `drought_ml_all.pkl` ≈ 50 MB → GitHub limite à 100 MB par fichier et recommande < 50 MB.

2. **Reproductibilité** : Les modèles doivent être **entraînés sur les données réelles** de chaque utilisateur. Quelqu'un qui clone le projet doit lancer `python ml/2_train_compare.py` pour avoir un modèle adapté à ses données locales.

3. **Sécurité** : Un modèle `.pkl` peut contenir du code arbitraire — ne jamais faire confiance à un `.pkl` téléchargé d'une source inconnue.

**Pour partager les modèles**, utilise [Hugging Face Hub](https://huggingface.co) ou [GitHub Releases](https://github.com/TON_USERNAME/droughtai/releases). -->

---

## 🛠️ Technologies utilisées

| Composant | Technologie |
|---|---|
| Computer Vision | YOLOv8n (Ultralytics) |
| Machine Learning | LightGBM, XGBoost, scikit-learn |
| API Backend | Flask 3.0 + Flask-CORS |
| Frontend | Laravel 11 + Blade |
| Base de données | MySQL 8.0 |
| Carte | Leaflet.js + OpenStreetMap |
| Graphiques | Chart.js |
| Données | NASA POWER API, Kaggle, PlantDoc |

---

## 📊 Résultats modèles

**YOLO (5 epochs CPU) :**
- mAP50 : **0.957**
- mAP50-95 : **0.936**
- Recall : 0.903

**LightGBM (meilleur ML) :**
- F1 Score : **0.9875**
- Accuracy : 0.9875
- CV F1 : 0.9823 ± 0.0037

---

## 👤 Auteur

**Mohame Lemine Tah & Elhafed Khatri** — Projet DroughtAI  
Mauritanie 🇲🇷

---

## 📄 Licence

MIT License — libre d'utilisation pour usage académique et non-commercial.
