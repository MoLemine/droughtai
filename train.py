"""
DroughtAI YOLO — Entraînement rapide CPU
=========================================
Optimisé pour CPU — durée : 30-60 minutes
"""

import shutil
from pathlib import Path

print("=" * 60)
print("DroughtAI YOLO — Mode CPU rapide")
print("=" * 60)

try:
    from ultralytics import YOLO
    print("✅ ultralytics OK")
except ImportError:
    print("❌ Lance : pip install ultralytics")
    exit(1)

# Vérifier dataset
data_yaml  = Path("data/final/data.yaml")
train_imgs = list(Path("data/final/images/train").glob("*"))
val_imgs   = list(Path("data/final/images/val").glob("*"))

if not data_yaml.exists():
    print("❌ Lance d'abord : python prepare_kaggle.py")
    exit(1)

if len(train_imgs) < 50:
    print(f"❌ Seulement {len(train_imgs)} images — lance prepare_kaggle.py")
    exit(1)

print(f"✅ Dataset : {len(train_imgs)} train | {len(val_imgs)} val")
print(f"⚠️  Mode CPU — durée estimée : 30-60 min")
print()

# ── Paramètres MINIMAUX pour CPU ─────────────────────────────────────────
#
#  yolov8n.pt → nano = 3M params (le plus léger)
#  imgsz=320  → 4x plus rapide que 640
#  epochs=15  → suffisant pour un premier modèle fonctionnel
#  batch=4    → CPU ne supporte pas plus
#  workers=0  → obligatoire Windows pour éviter erreurs
#  mosaic=0   → désactivé (trop lent sur CPU)
#  mixup=0    → désactivé
#  cache=False→ False si RAM < 8GB

model = YOLO("yolov8n.pt")

print("🚀 Entraînement démarré...")
print("   Modèle : yolov8n.pt (nano — le plus rapide)")
print("   Epochs : 15")
print("   Taille : 320px")
print("   Batch  : 4")
print()

results = model.train(
    data          = str(data_yaml),
    epochs        = 5,
    imgsz         = 320,
    batch         = 4,
    workers       = 0,
    device        = "cpu",
    patience      = 10,
    lr0           = 0.01,
    lrf           = 0.001,
    momentum      = 0.937,
    weight_decay  = 0.0005,
    warmup_epochs = 1,
    augment       = True,
    hsv_h         = 0.015,
    hsv_s         = 0.7,
    hsv_v         = 0.4,
    flipud        = 0.0,
    fliplr        = 0.5,
    mosaic        = 0.0,
    mixup         = 0.0,
    copy_paste    = 0.0,
    name          = "drought_yolo_v1",
    project       = "results",
    exist_ok      = True,
    verbose       = True,
    save          = True,
    save_period   = 5,
    val           = True,
    plots         = True,
    cache         = False,
)

# ── Sauvegarder ──────────────────────────────────────────────────────────
Path("models").mkdir(exist_ok=True)

best = Path("results/drought_yolo_v1/weights/best.pt")
last = Path("results/drought_yolo_v1/weights/last.pt")

if best.exists():
    shutil.copy2(best, "models/drought_yolo_best.pt")
    print("\n✅ Modèle → models/drought_yolo_best.pt")
elif last.exists():
    shutil.copy2(last, "models/drought_yolo_best.pt")
    print("\n✅ Modèle (last) → models/drought_yolo_best.pt")

# ── Résultats ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("📊 RÉSULTATS")
print("=" * 60)
try:
    m     = results.results_dict
    map50 = m.get("metrics/mAP50(B)", 0)
    prec  = m.get("metrics/precision(B)", 0)
    rec   = m.get("metrics/recall(B)", 0)
    print(f"  mAP50     : {map50:.3f}  {'✅ Bon' if map50 > 0.4 else '⚠️ Passable — normal pour 15 epochs CPU'}")
    print(f"  Precision : {prec:.3f}")
    print(f"  Recall    : {rec:.3f}")
    print()
    print("  Note : mAP50 > 0.40 est suffisant pour démarrer.")
    print("  Pour améliorer plus tard : epochs=100 + imgsz=640 (avec GPU)")
except Exception as e:
    print(f"  (métriques: {e})")

print("\n" + "=" * 60)
print("✅ TERMINÉ")
print("=" * 60)
print("\n➡️  Tester sur une photo :")
print("   python scripts/3_evaluate.py --image ta_photo.jpg")
print("\n➡️  Intégrer dans Flask :")
print("   python scripts/5_patch_app_py.py")