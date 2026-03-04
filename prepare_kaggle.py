"""
DroughtAI YOLO — Préparation dataset Kaggle
============================================
Convertit les datasets Kaggle/GitHub → format YOLO
et fusionne tout dans data/final/

Datasets supportés :
  - new-plant-diseases-dataset (Kaggle) → 87k images
  - soil-types (Kaggle)
  - PlantDoc-Dataset (GitHub)

Usage:
    python prepare_kaggle.py
"""

import os
import shutil
import random
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────
random.seed(42)
SPLITS    = {"train": 0.75, "val": 0.15, "test": 0.10}
IMG_EXTS  = {".jpg", ".jpeg", ".png", ".JPG", ".PNG", ".JPEG"}
FINAL_DIR = Path("data/final")

# ── Mapping maladies → 6 classes DroughtAI ───────────────────────────────
#
#   0 = sol_craquele      (sol fissuré, sec)
#   1 = vegetation_saine  (plante saine)
#   2 = stress_hydrique   (jaunissement, flétrissement)
#   3 = sol_nu            (sol nu brun)
#   4 = eau_irrigation    (eau visible)
#   5 = vegetation_morte  (nécrose, pourriture)
#
DISEASE_TO_CLASS = {
    # ── Saine ──────────────────────────────────────────────
    "healthy":                      1,

    # ── Stress hydrique (jaunissement, flétrissement) ──────
    "bacterial_spot":               2,
    "early_blight":                 2,
    "septoria_leaf_spot":           2,
    "spider_mites":                 2,
    "target_spot":                  2,
    "mosaic_virus":                 2,
    "yellow_leaf_curl_virus":       2,
    "leaf_scorch":                  2,
    "cercospora_leaf_spot":         2,
    "common_rust":                  2,
    "angular_leaf_spot":            2,
    "leaf_spot":                    2,
    "brown_spot":                   2,
    "gray_leaf_spot":               2,
    "anthracnose":                  2,

    # ── Végétation morte (nécrose, pourriture sévère) ──────
    "late_blight":                  5,
    "leaf_mold":                    5,
    "black_rot":                    5,
    "northern_leaf_blight":         5,
    "haunglongbing":                5,
    "powdery_mildew":               5,
    "downy_mildew":                 5,
    "fire_blight":                  5,
    "fusarium":                     5,
    "blight":                       5,
    "rot":                          5,
    "scab":                         5,
    "rust":                         5,
}

SOIL_TO_CLASS = {
    "alluvial":   1,   # sol fertile → vegetation_saine
    "black":      3,   # sol noir nu → sol_nu
    "clay":       3,   # sol argileux → sol_nu
    "red":        0,   # sol rouge sec → sol_craquele
    "sandy":      0,   # sol sableux → sol_craquele
    "cracked":    0,   # sol craquelé → sol_craquele
    "laterite":   3,   # latérite → sol_nu
    "dry":        3,   # sec → sol_nu
    "wet":        4,   # humide → eau_irrigation
    "loamy":      1,   # limoneux → vegetation_saine
}


# ── Helpers ───────────────────────────────────────────────────────────────

def setup_dirs():
    """Crée la structure finale."""
    for split in SPLITS:
        (FINAL_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (FINAL_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)
    print("✅ Dossiers data/final/ créés")


def get_split() -> str:
    """Retourne un split aléatoire selon les ratios."""
    r = random.random()
    if r < SPLITS["train"]:
        return "train"
    elif r < SPLITS["train"] + SPLITS["val"]:
        return "val"
    return "test"


def yolo_label(class_id: int) -> str:
    """Label YOLO bbox = image entière."""
    return f"{class_id} 0.5 0.5 1.0 1.0"


def copy_image(src: Path, class_id: int, prefix: str, counter: int) -> bool:
    """Copie une image + crée son label YOLO."""
    try:
        split    = get_split()
        new_name = f"{prefix}_{counter}{src.suffix.lower()}"
        lbl_name = f"{prefix}_{counter}.txt"

        shutil.copy2(src, FINAL_DIR / "images" / split / new_name)
        (FINAL_DIR / "labels" / split / lbl_name).write_text(yolo_label(class_id))
        return True
    except Exception as e:
        return False


def detect_class_from_name(name: str, mapping: dict, default: int = 2) -> int:
    """Détecte la classe depuis un nom de dossier."""
    name_lower = name.lower().replace("-", "_").replace(" ", "_")
    for keyword, cls in mapping.items():
        if keyword in name_lower:
            return cls
    return default


# ── Dataset 1 : new-plant-diseases-dataset ───────────────────────────────

def process_plant_diseases() -> int:
    """
    Structure Kaggle :
      data/kaggle/plant_diseases/
        New Plant Diseases Dataset(Augmented)/
          train/
            Apple___Apple_scab/  *.jpg
            Apple___healthy/     *.jpg
            ...
          valid/
            ...
    """
    base = Path("data/kaggle/plant_diseases")
    if not base.exists():
        print("⚠️  plant_diseases non trouvé — vérifie le téléchargement Kaggle")
        return 0

    # Chercher le bon sous-dossier
    roots = []
    for p in base.rglob("train"):
        if p.is_dir():
            roots.append(p.parent)
            break

    if not roots:
        # Structure plate
        roots = [base]

    count = 0
    for root in roots:
        for split_name in ["train", "valid", "test", "Train", "Valid"]:
            split_path = root / split_name
            if not split_path.exists():
                continue

            for class_dir in sorted(split_path.iterdir()):
                if not class_dir.is_dir():
                    continue

                # Nom du dossier ex: "Apple___Early_blight"
                class_id = detect_class_from_name(
                    class_dir.name, DISEASE_TO_CLASS, default=2
                )

                images = [f for f in class_dir.iterdir() if f.suffix in IMG_EXTS]
                random.shuffle(images)
                # Max 150 images par classe pour équilibrer
                images = images[:150]

                for img in images:
                    if copy_image(img, class_id, "plant", count):
                        count += 1

    print(f"✅ Plant Diseases  : {count:5d} images")
    return count


# ── Dataset 2 : soil-types ────────────────────────────────────────────────

def process_soil_types() -> int:
    """
    Structure Kaggle :
      data/kaggle/soil_types/
        Alluvial Soil/   *.jpg
        Black Soil/      *.jpg
        Clay Soil/       *.jpg
        Red Soil/        *.jpg
    """
    base = Path("data/kaggle/soil_types")
    if not base.exists():
        print("⚠️  soil_types non trouvé")
        return 0

    count = 0
    # Chercher tous les dossiers contenant des images
    for folder in base.rglob("*"):
        if not folder.is_dir():
            continue

        class_id = detect_class_from_name(folder.name, SOIL_TO_CLASS, default=3)
        images   = [f for f in folder.iterdir() if f.suffix in IMG_EXTS]

        for img in images:
            if copy_image(img, class_id, "soil", count):
                count += 1

    print(f"✅ Soil Types      : {count:5d} images")
    return count


# ── Dataset 3 : PlantDoc GitHub ───────────────────────────────────────────

def process_plantdoc() -> int:
    """
    Structure GitHub :
      data/github/plantdoc/
        TRAIN/
          Apple Scab Leaf/    *.jpg
          Apple leaf/         *.jpg
          ...
        TEST/
          ...
    """
    base = Path("data/github/plantdoc")
    if not base.exists():
        print("⚠️  PlantDoc GitHub non trouvé — lance: git clone https://github.com/pratikkayal/PlantDoc-Dataset data/github/plantdoc")
        return 0

    count = 0
    for split_name in ["TRAIN", "TEST", "train", "test"]:
        split_path = base / split_name
        if not split_path.exists():
            continue

        for class_dir in sorted(split_path.iterdir()):
            if not class_dir.is_dir():
                continue

            name = class_dir.name.lower()
            if "healthy" in name or "leaf" in name and "blight" not in name:
                class_id = 1   # vegetation_saine
            elif "blight" in name or "rot" in name or "scab" in name:
                class_id = 5   # vegetation_morte
            elif "spot" in name or "mildew" in name or "rust" in name:
                class_id = 2   # stress_hydrique
            else:
                class_id = 2   # stress_hydrique par défaut

            for img in class_dir.iterdir():
                if img.suffix in IMG_EXTS:
                    if copy_image(img, class_id, "plantdoc", count):
                        count += 1

    print(f"✅ PlantDoc GitHub : {count:5d} images")
    return count


# ── data.yaml ─────────────────────────────────────────────────────────────

def write_yaml():
    yaml = """# DroughtAI YOLO — Dataset Final
# Généré par prepare_kaggle.py

path: ./data/final
train: images/train
val:   images/val
test:  images/test

nc: 6
names:
  0: sol_craquele
  1: vegetation_saine
  2: stress_hydrique
  3: sol_nu
  4: eau_irrigation
  5: vegetation_morte
"""
    (FINAL_DIR / "data.yaml").write_text(yaml)
    print("✅ data/final/data.yaml créé")


# ── Statistiques ──────────────────────────────────────────────────────────

def print_stats():
    print("\n📊 Dataset final :")
    print(f"  {'Split':8s} {'Images':>8s} {'Labels':>8s}")
    print("  " + "-" * 28)
    total_imgs = 0
    for split in ["train", "val", "test"]:
        imgs = len(list((FINAL_DIR / "images" / split).glob("*")))
        lbls = len(list((FINAL_DIR / "labels" / split).glob("*.txt")))
        total_imgs += imgs
        print(f"  {split:8s} {imgs:8d} {lbls:8d}")
    print("  " + "-" * 28)
    print(f"  {'TOTAL':8s} {total_imgs:8d}")

    # Compter par classe
    print("\n📊 Distribution des classes :")
    class_names = {
        0: "sol_craquele",
        1: "vegetation_saine",
        2: "stress_hydrique",
        3: "sol_nu",
        4: "eau_irrigation",
        5: "vegetation_morte",
    }
    class_counts = {i: 0 for i in range(6)}
    for split in ["train", "val", "test"]:
        for lbl_file in (FINAL_DIR / "labels" / split).glob("*.txt"):
            content = lbl_file.read_text().strip()
            if content:
                cls = int(content.split()[0])
                class_counts[cls] = class_counts.get(cls, 0) + 1

    for cls_id, name in class_names.items():
        bar = "█" * (class_counts[cls_id] // 50)
        print(f"  {cls_id} {name:20s}: {class_counts[cls_id]:5d} {bar}")

    return total_imgs


# ── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("DroughtAI — Préparation dataset YOLO")
    print("=" * 60)

    setup_dirs()
    print()

    t  = process_plant_diseases()
    t += process_soil_types()
    t += process_plantdoc()

    write_yaml()
    total = print_stats()

    print()
    if total < 100:
        print("⚠️  Moins de 100 images détectées.")
        print("   Vérifie que les datasets sont bien téléchargés dans :")
        print("   - data/kaggle/plant_diseases/")
        print("   - data/kaggle/soil_types/")
        print("   - data/github/plantdoc/")
    else:
        print(f"✅ {total} images prêtes pour l'entraînement !")
        print("➡️  Lance maintenant : python train.py")