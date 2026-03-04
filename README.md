# DroughtAI YOLO — Détection Agricole

Modèle YOLOv8 entraîné pour détecter 6 classes de conditions agricoles
dans les zones sahéliennes (Mauritanie, Sénégal).

## Classes détectées

| ID | Classe | Description |
|----|--------|-------------|
| 0 | sol_craquele | Sol craquelé — sécheresse sévère |
| 1 | vegetation_saine | Végétation verte saine |
| 2 | stress_hydrique | Végétation jaunissante / stressée |
| 3 | sol_nu | Sol nu brun — désertification |
| 4 | eau_irrigation | Eau / irrigation visible |
| 5 | vegetation_morte | Végétation morte / desséchée |

---

## Installation

```bash
pip install ultralytics opencv-python torch roboflow
```

---

## Pipeline complet

### Étape 1 — Télécharger les datasets

```bash
# Éditer ROBOFLOW_KEY dans le script (clé gratuite sur roboflow.com)
python scripts/1_download_datasets.py
```

**Datasets gratuits utilisés :**
- Roboflow Universe — Drought Land Detection
- Roboflow Universe — Cracked Soil Detection
- Roboflow Universe — Plant Stress Detection
- Kaggle — Soil Types Dataset

### Étape 2 — Entraîner YOLO

```bash
python scripts/2_train_yolo.py
```

Durée : ~30 min (GPU) ou ~4h (CPU) pour 100 epochs.
Le meilleur modèle est sauvegardé dans `models/drought_yolo_best.pt`.

### Étape 3 — Évaluer

```bash
# Sur le test set
python scripts/3_evaluate.py

# Sur une image
python scripts/3_evaluate.py --image ma_photo.jpg

# Sur un dossier
python scripts/3_evaluate.py --folder ./mes_photos
```

### Étape 4 — Intégrer dans Flask

```bash
# Copier le dossier drought_yolo dans ton projet
cp -r drought_yolo/ C:\Users\Mohame Lemine\Desktop\drought_ai_project\drought_ai\

# Patcher app.py automatiquement
cd C:\Users\Mohame Lemine\Desktop\drought_ai_project\drought_ai
python drought_yolo/scripts/5_patch_app_py.py
```

Puis relancer Flask :
```bash
python api\app.py
```

---

## Nouveaux endpoints Flask

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/analyze/image` | POST | Analyse YOLO d'une image (base64) |
| `/api/analyze/status` | GET | Statut du modèle YOLO |

---

## Flux complet après intégration

```
Photo uploadée (Laravel)
        │
        ▼
POST /api/analyze/image (Flask)
        │
        ▼
YOLOv8 détecte :
  ├── sol_craquele  → 45% surface
  ├── sol_nu        → 30% surface
  ├── stress_hydrique → 15% surface
  └── vegetation_saine → 10% surface
        │
        ▼
Calcul risque global → Classe 3 Sévère
        │
        ▼
Résultat complet → Laravel → Vue
```

---

## Datasets recommandés pour améliorer le modèle

| Source | Lien | Contenu |
|--------|------|---------|
| Roboflow Universe | universe.roboflow.com | 200k+ datasets annotés |
| CHIRPS | chirps.ucsb.edu | Précipitations 1981–2024 |
| MODIS NDVI | lpdaac.usgs.gov | NDVI satellite mensuel |
| Kaggle | kaggle.com/datasets | Soil, plant disease datasets |
| Google Earth Engine | earthengine.google.com | Images satellite gratuites |

---

## Structure des fichiers

```
drought_yolo/
├── data/
│   ├── drought.yaml          # Config dataset YOLO
│   ├── images/
│   │   ├── train/            # Images entraînement
│   │   ├── val/              # Images validation
│   │   └── test/             # Images test
│   └── labels/
│       ├── train/            # Annotations YOLO (.txt)
│       ├── val/
│       └── test/
├── models/
│   └── drought_yolo_best.pt  # Meilleur modèle entraîné
├── scripts/
│   ├── 1_download_datasets.py
│   ├── 2_train_yolo.py
│   ├── 3_evaluate.py
│   ├── 4_yolo_api.py         # Endpoints Flask
│   └── 5_patch_app_py.py     # Patch automatique app.py
├── results/                  # Métriques, courbes, prédictions
├── requirements.txt
└── README.md
```
