"""
DroughtAI YOLO — Entraînement YOLOv8
======================================
Entraîne un modèle YOLOv8 de détection de sécheresse agricole.

Usage:
    pip install ultralytics torch torchvision
    python scripts/2_train_yolo.py

Modèles disponibles (du plus léger au plus précis):
    yolov8n.pt  → nano   (3M params)  rapide, mobile
    yolov8s.pt  → small  (11M params) bon équilibre  ← RECOMMANDÉ
    yolov8m.pt  → medium (26M params) meilleure précision
    yolov8l.pt  → large  (44M params) très précis, GPU requis
"""

import os
import yaml
import shutil
from pathlib import Path
from datetime import datetime

try:
    from ultralytics import YOLO
except ImportError:
    print("ERREUR: ultralytics non installé.")
    print("Installer: pip install ultralytics")
    exit(1)

# ── Config entraînement ───────────────────────────────────────────────────
CONFIG = {
    "model":       "yolov8s.pt",   # Téléchargé automatiquement
    "data":        "data/drought.yaml",
    "epochs":      100,            # 100 suffit, augmenter si dataset grand
    "imgsz":       640,            # Taille image standard YOLO
    "batch":       16,             # Réduire à 8 si manque de RAM
    "workers":     4,
    "patience":    20,             # Early stopping
    "lr0":         0.01,           # Learning rate initial
    "lrf":         0.001,          # Learning rate final
    "momentum":    0.937,
    "weight_decay":0.0005,
    "warmup_epochs":3.0,
    "box":         7.5,            # Poids box loss
    "cls":         0.5,            # Poids classification loss
    "device":      "",             # "" = auto (GPU si disponible, sinon CPU)
    "augment":     True,           # Augmentation données
    "hsv_h":       0.015,          # Variation teinte (utile pour végétation)
    "hsv_s":       0.7,
    "hsv_v":       0.4,
    "flipud":      0.2,            # Flip vertical (utile pour sol)
    "fliplr":      0.5,            # Flip horizontal
    "mosaic":      1.0,            # Mosaic augmentation
    "mixup":       0.1,
    "copy_paste":  0.1,
    "name":        f"drought_yolo_{datetime.now().strftime('%Y%m%d_%H%M')}",
    "project":     "results",
    "exist_ok":    True,
    "verbose":     True,
    "save":        True,
    "save_period": 10,             # Sauvegarder tous les 10 epochs
    "val":         True,
    "plots":       True,
}


def check_dataset():
    """Vérifie que le dataset est prêt."""
    data_yaml = Path(CONFIG["data"])
    if not data_yaml.exists():
        print(f"ERREUR: {data_yaml} non trouvé.")
        print("Lance d\'abord: python scripts/1_download_datasets.py")
        return False
    
    train_imgs = list(Path("data/images/train").glob("*.[jJpP][pPnN][gGeE]*"))
    val_imgs   = list(Path("data/images/val").glob("*.[jJpP][pPnN][gGeE]*"))
    
    print(f"Dataset: {len(train_imgs)} train | {len(val_imgs)} val")
    
    if len(train_imgs) < 10:
        print("AVERTISSEMENT: Moins de 10 images d\'entraînement.")
        print("Recommandé: minimum 100 images par classe.")
        print("Lance: python scripts/1_download_datasets.py")
        return False
    
    return True


def train():
    """Lance l\'entraînement YOLO."""
    print("=" * 60)
    print("DroughtAI YOLO — Entraînement")
    print("=" * 60)
    
    if not check_dataset():
        print("\nDataset insuffisant. Utilisation du mode démo.")
        print("Le modèle sera quand même créé mais peu précis.")
    
    print(f"\nModèle de base : {CONFIG['model']}")
    print(f"Epochs         : {CONFIG['epochs']}")
    print(f"Image size     : {CONFIG['imgsz']}px")
    print(f"Batch size     : {CONFIG['batch']}")
    
    # Charger modèle pré-entraîné (téléchargé automatiquement si absent)
    model = YOLO(CONFIG["model"])
    
    # Lancer entraînement
    results = model.train(
        data        = CONFIG["data"],
        epochs      = CONFIG["epochs"],
        imgsz       = CONFIG["imgsz"],
        batch       = CONFIG["batch"],
        workers     = CONFIG["workers"],
        patience    = CONFIG["patience"],
        lr0         = CONFIG["lr0"],
        lrf         = CONFIG["lrf"],
        momentum    = CONFIG["momentum"],
        weight_decay= CONFIG["weight_decay"],
        warmup_epochs=CONFIG["warmup_epochs"],
        box         = CONFIG["box"],
        cls         = CONFIG["cls"],
        device      = CONFIG["device"],
        augment     = CONFIG["augment"],
        hsv_h       = CONFIG["hsv_h"],
        hsv_s       = CONFIG["hsv_s"],
        hsv_v       = CONFIG["hsv_v"],
        flipud      = CONFIG["flipud"],
        fliplr      = CONFIG["fliplr"],
        mosaic      = CONFIG["mosaic"],
        mixup       = CONFIG["mixup"],
        copy_paste  = CONFIG["copy_paste"],
        name        = CONFIG["name"],
        project     = CONFIG["project"],
        exist_ok    = CONFIG["exist_ok"],
        verbose     = CONFIG["verbose"],
        save        = CONFIG["save"],
        save_period = CONFIG["save_period"],
        val         = CONFIG["val"],
        plots       = CONFIG["plots"],
    )
    
    # Copier le meilleur modèle dans models/
    best_model = Path(CONFIG["project"]) / CONFIG["name"] / "weights" / "best.pt"
    if best_model.exists():
        dest = Path("models/drought_yolo_best.pt")
        shutil.copy2(best_model, dest)
        print(f"\n✅ Meilleur modèle sauvegardé: {dest}")
    
    # Afficher les métriques finales
    print("\n📊 Résultats finaux:")
    try:
        metrics = results.results_dict
        print(f"  mAP50     : {metrics.get('metrics/mAP50(B)', 0):.3f}")
        print(f"  mAP50-95  : {metrics.get('metrics/mAP50-95(B)', 0):.3f}")
        print(f"  Precision : {metrics.get('metrics/precision(B)', 0):.3f}")
        print(f"  Recall    : {metrics.get('metrics/recall(B)', 0):.3f}")
    except:
        pass
    
    print(f"\n✅ Entraînement terminé: results/{CONFIG['name']}/")
    print("➡️  Étape suivante: python scripts/3_evaluate.py")
    
    return results


def validate_existing():
    """Valide un modèle déjà entraîné."""
    model_path = Path("models/drought_yolo_best.pt")
    if not model_path.exists():
        print("Aucun modèle entraîné. Lance d\'abord: python scripts/2_train_yolo.py")
        return
    
    model   = YOLO(str(model_path))
    metrics = model.val(data=CONFIG["data"], imgsz=CONFIG["imgsz"])
    print("Validation terminée.")


if __name__ == "__main__":
    import sys
    if "--val" in sys.argv:
        validate_existing()
    else:
        train()
