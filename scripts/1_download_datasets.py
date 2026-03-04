"""
DroughtAI YOLO — Téléchargement automatique des datasets
=========================================================
Sources gratuites utilisées :
  1. Roboflow Universe — Drought Detection (CC BY 4.0)
  2. Roboflow Universe — Cracked Soil Detection
  3. Roboflow Universe — Plant Disease / Stress Detection
  4. Kaggle — Soil Types Dataset
  5. NASA EarthData NDVI images (optionnel)

Usage:
    pip install roboflow kaggle requests tqdm
    python scripts/1_download_datasets.py
"""

import os
import json
import shutil
import random
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
SPLITS   = ["train", "val", "test"]

def setup_dirs():
    for split in SPLITS:
        (DATA_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)
    print("Dossiers créés.")


def download_roboflow(api_key: str, workspace: str, project: str, version: int, target_dir: Path):
    """Télécharge un dataset Roboflow au format YOLOv8."""
    try:
        from roboflow import Roboflow
        rf      = Roboflow(api_key=api_key)
        project = rf.workspace(workspace).project(project)
        dataset = project.version(version).download("yolov8", location=str(target_dir))
        print(f"✅ Roboflow {project}/{version} → {target_dir}")
        return True
    except Exception as e:
        print(f"❌ Roboflow {workspace}/{project}: {e}")
        return False


def download_datasets_roboflow(api_key: str):
    """
    Télécharge les datasets depuis Roboflow Universe.
    Clé API gratuite sur : https://roboflow.com (compte requis)
    """
    datasets = [
        # (workspace, project, version, local_name, class_mapping)
        ("drought-detection", "drought-land",       1, "drought_land",
         {0: 0, 1: 3}),   # drought→sol_craquele, normal→sol_nu
        
        ("soil-crack",        "cracked-soil-det",   2, "cracked_soil",
         {0: 0}),           # crack→sol_craquele
        
        ("plant-disease",     "plant-disease-nymph", 3, "plant_stress",
         {0: 2, 1: 1, 2: 5}),  # diseased→stress, healthy→sain, dead→morte
        
        ("irrigation",        "water-detection",     1, "water_detect",
         {0: 4}),           # water→eau_irrigation
    ]
    
    for workspace, project_name, version, local_name, class_map in datasets:
        target = DATA_DIR / "raw" / local_name
        success = download_roboflow(api_key, workspace, project_name, version, target)
        if success:
            merge_dataset(target, class_map)


def download_kaggle_datasets():
    """
    Télécharge depuis Kaggle.
    Prérequis: kaggle.json dans ~/.kaggle/
    https://www.kaggle.com/settings → API → Create New Token
    """
    kaggle_datasets = [
        ("prasanshasatpathy/soil-types",        "soil_types"),
        ("ravirajsinh45/real-life-industrial-dataset", "industrial"),
    ]
    
    try:
        import kaggle
        for dataset_id, local_name in kaggle_datasets:
            target = DATA_DIR / "raw" / local_name
            target.mkdir(parents=True, exist_ok=True)
            print(f"📥 Kaggle: {dataset_id}")
            kaggle.api.dataset_download_files(
                dataset_id, path=str(target), unzip=True
            )
            print(f"✅ {dataset_id} → {target}")
    except Exception as e:
        print(f"❌ Kaggle: {e}")
        print("   → Installe: pip install kaggle")
        print("   → Configure: https://www.kaggle.com/settings → API")


def merge_dataset(source_dir: Path, class_mapping: dict):
    """
    Fusionne un dataset téléchargé dans la structure principale.
    Réattribue les classes selon class_mapping.
    """
    source_dir = Path(source_dir)
    if not source_dir.exists():
        return
    
    for split in SPLITS:
        img_src = source_dir / split / "images"
        lbl_src = source_dir / split / "labels"
        
        if not img_src.exists():
            # Chercher les images à la racine
            img_src = source_dir / "images"
            lbl_src = source_dir / "labels"
        
        if not img_src.exists():
            continue
            
        img_dst = DATA_DIR / "images" / split
        lbl_dst = DATA_DIR / "labels" / split
        
        # Copier images
        for img_path in img_src.glob("*.[jJpP][pPnN][gGeE]*"):
            shutil.copy2(img_path, img_dst / img_path.name)
        
        # Copier et remapper labels
        if lbl_src.exists():
            for lbl_path in lbl_src.glob("*.txt"):
                content = lbl_path.read_text().strip()
                new_lines = []
                for line in content.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split()
                    old_class = int(parts[0])
                    new_class = class_mapping.get(old_class, old_class)
                    new_lines.append(f"{new_class} {' '.join(parts[1:])}")
                
                (lbl_dst / lbl_path.name).write_text("\n".join(new_lines))
    
    print(f"✅ Fusionné: {source_dir.name}")


def generate_synthetic_annotations():
    """
    Génère des annotations synthétiques pour les images existantes
    sans label, basé sur l'analyse des couleurs (similaire à GD PHP).
    Utile pour auto-labeler rapidement un petit dataset.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("⚠️ cv2 non disponible. Installer: pip install opencv-python")
        return
    
    print("\n🤖 Génération d\'annotations synthétiques...")
    
    for split in SPLITS:
        img_dir = DATA_DIR / "images" / split
        lbl_dir = DATA_DIR / "labels" / split
        
        for img_path in img_dir.glob("*.[jJpP][pPnN][gGeE]*"):
            lbl_path = lbl_dir / (img_path.stem + ".txt")
            if lbl_path.exists():
                continue  # déjà annoté
            
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            
            h, w = img.shape[:2]
            annotations = []
            
            # Analyse par zones de 4x4
            zone_h, zone_w = h // 4, w // 4
            for row in range(4):
                for col in range(4):
                    y1 = row * zone_h
                    x1 = col * zone_w
                    zone = img[y1:y1+zone_h, x1:x1+zone_w]
                    
                    mean_b = np.mean(zone[:,:,0])
                    mean_g = np.mean(zone[:,:,1])
                    mean_r = np.mean(zone[:,:,2])
                    
                    # Déterminer la classe
                    if mean_g > mean_r * 1.15 and mean_g > 60:
                        cls = 1  # vegetation_saine
                    elif mean_r > mean_g * 1.1 and mean_r > 80:
                        cls = 3  # sol_nu
                    elif abs(mean_r-mean_g) < 25 and mean_r < 160 and mean_r > 60:
                        cls = 0  # sol_craquele
                    elif mean_b > mean_r * 1.1 and mean_b > 70:
                        cls = 4  # eau_irrigation
                    elif mean_g < 50 and mean_r < 80:
                        cls = 5  # vegetation_morte
                    else:
                        cls = 2  # stress_hydrique (défaut)
                    
                    # Format YOLO: class cx cy w h (normalisé)
                    cx = (x1 + zone_w/2) / w
                    cy = (y1 + zone_h/2) / h
                    bw = zone_w / w
                    bh = zone_h / h
                    annotations.append(f"{cls} {cx:.4f} {cy:.4f} {bw:.4f} {bh:.4f}")
            
            if annotations:
                lbl_path.write_text("\n".join(annotations))
    
    print("✅ Annotations synthétiques générées.")


def count_dataset():
    """Affiche les statistiques du dataset."""
    print("\n📊 Statistiques dataset:")
    total_images = 0
    for split in SPLITS:
        imgs = list((DATA_DIR / "images" / split).glob("*.[jJpP][pPnN][gGeE]*"))
        lbls = list((DATA_DIR / "labels" / split).glob("*.txt"))
        total_images += len(imgs)
        print(f"  {split:8s}: {len(imgs):4d} images | {len(lbls):4d} labels")
    print(f"  {'TOTAL':8s}: {total_images:4d} images")


# ── MAIN ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("DroughtAI YOLO — Téléchargement des datasets")
    print("=" * 60)
    
    setup_dirs()
    
    # Option 1 : Roboflow (clé API gratuite)
    ROBOFLOW_KEY = "ZdUSoXz0Q7Y935l5Zvuc"  # ← Mettre ta clé ici: https://roboflow.com
    if ROBOFLOW_KEY:
        download_datasets_roboflow(ROBOFLOW_KEY)
    else:
        print("\n⚠️  ROBOFLOW_KEY non défini.")
        print("   1. Crée un compte sur https://roboflow.com (gratuit)")
        print("   2. Va dans Settings → API Keys")
        print("   3. Copie ta clé dans ce fichier : ROBOFLOW_KEY = 'ta_cle'")
    
    # Option 2 : Kaggle
    download_kaggle_datasets()
    
    # Option 3 : Auto-labeling des images existantes
    generate_synthetic_annotations()
    
    count_dataset()
    print("\n✅ Prêt pour l\'entraînement → python scripts/2_train_yolo.py")
