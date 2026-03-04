"""
DroughtAI YOLO — Évaluation et test du modèle
==============================================
Usage:
    python scripts/3_evaluate.py                    # Évalue sur test set
    python scripts/3_evaluate.py --image photo.jpg  # Teste sur une image
    python scripts/3_evaluate.py --folder ./photos  # Teste un dossier
"""

import sys
import json
from pathlib import Path
import argparse

try:
    from ultralytics import YOLO
    import cv2
    import numpy as np
except ImportError as e:
    print(f"Installer: pip install ultralytics opencv-python")
    exit(1)

MODEL_PATH = Path("models/drought_yolo_best.pt")
DATA_YAML  = Path("data/drought.yaml")

CLASS_NAMES = {
    0: "Sol Craquelé",
    1: "Végétation Saine",
    2: "Stress Hydrique",
    3: "Sol Nu",
    4: "Eau / Irrigation",
    5: "Végétation Morte",
}

CLASS_COLORS = {
    0: (0,  0,   200),   # Rouge  — sol craquelé
    1: (0,  200, 50),    # Vert   — végétation saine
    2: (0,  200, 255),   # Jaune  — stress hydrique
    3: (100,150, 200),   # Marron — sol nu
    4: (200, 50,  50),   # Bleu   — eau
    5: (50,  50, 150),   # Bordeaux — végétation morte
}

RISK_MAP = {
    0: {"risk_class": 3, "risk_label": "Severe",   "urgence": "Élevée"},
    1: {"risk_class": 0, "risk_label": "Aucun",    "urgence": "Faible"},
    2: {"risk_class": 2, "risk_label": "Modere",   "urgence": "Moyenne"},
    3: {"risk_class": 2, "risk_label": "Modere",   "urgence": "Moyenne"},
    4: {"risk_class": 1, "risk_label": "Faible",   "urgence": "Faible"},
    5: {"risk_class": 4, "risk_label": "Extreme",  "urgence": "Critique"},
}


def load_model():
    if not MODEL_PATH.exists():
        print(f"ERREUR: Modèle non trouvé: {MODEL_PATH}")
        print("Lance d\'abord: python scripts/2_train_yolo.py")
        exit(1)
    return YOLO(str(MODEL_PATH))


def evaluate_on_test():
    """Évalue le modèle sur le test set."""
    model   = load_model()
    metrics = model.val(data=str(DATA_YAML), split="test", imgsz=640)
    
    print("\n📊 Métriques sur le test set:")
    print(f"  mAP50     : {metrics.box.map50:.3f}")
    print(f"  mAP50-95  : {metrics.box.map:.3f}")
    print(f"  Precision : {metrics.box.mp:.3f}")
    print(f"  Recall    : {metrics.box.mr:.3f}")
    
    print("\n📊 Par classe:")
    for i, name in CLASS_NAMES.items():
        if i < len(metrics.box.ap50):
            print(f"  {name:22s}: AP50={metrics.box.ap50[i]:.3f}")


def predict_image(image_path: str, conf: float = 0.25, save: bool = True) -> dict:
    """
    Prédit les classes sur une image et retourne un résultat
    compatible avec le format attendu par Laravel/Flask.
    """
    model      = load_model()
    img_path   = Path(image_path)
    
    if not img_path.exists():
        return {"success": False, "error": f"Image non trouvée: {image_path}"}
    
    results    = model.predict(str(img_path), conf=conf, imgsz=640, verbose=False)
    result     = results[0]
    
    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]
    
    detections    = []
    class_counts  = {i: 0 for i in range(6)}
    total_area    = 0
    class_area    = {i: 0.0 for i in range(6)}
    
    for box in result.boxes:
        cls   = int(box.cls[0])
        conf_ = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        area  = ((x2-x1) * (y2-y1)) / (w * h)
        
        class_counts[cls] += 1
        class_area[cls]   += area
        total_area        += area
        
        det = {
            "class_id":    cls,
            "class_name":  CLASS_NAMES[cls],
            "confidence":  round(conf_, 3),
            "bbox":        [x1, y1, x2-x1, y2-y1],
            "area_pct":    round(area * 100, 1),
        }
        detections.append(det)
        
        # Dessiner sur image
        color = CLASS_COLORS[cls]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{CLASS_NAMES[cls]} {conf_:.2f}"
        cv2.putText(img, label, (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Calculer le risque global basé sur les détections
    risk = calculate_risk(class_area, class_counts)
    
    # Sauvegarder image annotée
    if save:
        out_path = img_path.parent / f"{img_path.stem}_yolo{img_path.suffix}"
        cv2.imwrite(str(out_path), img)
        print(f"✅ Image annotée: {out_path}")
    
    return {
        "success":      True,
        "source":       "yolo_model",
        "demo":         False,
        "model":        str(MODEL_PATH.name),
        "detections":   detections,
        "n_detections": len(detections),
        "class_counts": {CLASS_NAMES[i]: class_counts[i] for i in range(6)},
        "class_areas":  {CLASS_NAMES[i]: round(class_area[i] * 100, 1) for i in range(6)},
        **risk,
    }


def calculate_risk(class_area: dict, class_counts: dict) -> dict:
    """
    Calcule le risque global et les 4 indicateurs
    à partir des détections YOLO.
    """
    # Poids des surfaces détectées
    cracked  = class_area[0]   # sol_craquele
    healthy  = class_area[1]   # vegetation_saine
    stressed = class_area[2]   # stress_hydrique
    bare     = class_area[3]   # sol_nu
    water    = class_area[4]   # eau_irrigation
    dead     = class_area[5]   # vegetation_morte
    
    # Score sécheresse 0–100
    drought_score = min(100, int(
        cracked * 180 + bare * 120 + dead * 150 + stressed * 60
        - healthy * 80 - water * 40
    ))
    drought_score = max(0, drought_score)
    
    # Classe de risque
    if drought_score >= 80 or dead > 0.3:
        risk_class, risk_label = 4, "Extreme"
    elif drought_score >= 60 or cracked > 0.35:
        risk_class, risk_label = 3, "Severe"
    elif drought_score >= 40 or bare > 0.40:
        risk_class, risk_label = 2, "Modere"
    elif drought_score >= 20 or stressed > 0.20:
        risk_class, risk_label = 1, "Faible"
    else:
        risk_class, risk_label = 0, "Aucun"
    
    RISK_COLORS_HEX = {0:"#22c55e", 1:"#eab308", 2:"#f97316", 3:"#ef4444", 4:"#7c3aed"}
    
    urgence = ["Faible","Moyenne","Élevée","Critique","Critique"][risk_class]
    
    health_score = max(5, 100 - risk_class * 20 - int(drought_score / 5))
    
    indicators = {
        "gaspillage_eau": {
            "detecte": water > 0.15,
            "niveau":  "Modéré" if water > 0.15 else "Faible",
            "score":   int(water * 100),
            "details": f"Eau visible : {round(water*100)}% de la surface",
        },
        "stress_hydrique": {
            "detecte": stressed > 0.05 or risk_class >= 1,
            "niveau":  risk_label,
            "score":   min(100, int((stressed + cracked) * 80 + risk_class * 10)),
            "details": f"Sol craquelé {round(cracked*100)}% · Stress {round(stressed*100)}%",
        },
        "risque_secheresse": {
            "classe":  risk_class,
            "label":   risk_label,
            "score":   drought_score,
            "details": f"Sol nu {round(bare*100)}% · Végétation morte {round(dead*100)}%",
        },
        "anomalies_plantes": {
            "detectee": stressed > 0.05 or dead > 0.05,
            "type":     "Stress hydrique sévère" if dead > 0.1
                        else ("Stress modéré" if stressed > 0.1 else "Normal"),
            "score":    int((stressed + dead) * 100),
            "details":  f"Saine {round(healthy*100)}% · Stressée {round(stressed*100)}% · Morte {round(dead*100)}%",
        },
    }
    
    # Actions selon risque
    actions = {
        4: ["Urgence : irrigation immédiate", "Alerter autorités agricoles", "Évaluer replantation d\'urgence"],
        3: ["Irrigation dans les 24h", "Protéger les cultures restantes", "Contacter service météo"],
        2: ["Irriguer dans les 48-72h", "Appliquer paillage", "Surveiller quotidiennement"],
        1: ["Surveiller l\'humidité du sol", "Préparer irrigation préventive"],
        0: ["Maintenir l\'irrigation habituelle", "Surveillance normale"],
    }
    
    neg = []
    pos = []
    if cracked > 0.1: neg.append(f"Sol craquelé détecté : {round(cracked*100)}%")
    if bare > 0.2:    neg.append(f"Sol nu : {round(bare*100)}%")
    if dead > 0.05:   neg.append(f"Végétation morte : {round(dead*100)}%")
    if stressed > 0.1: neg.append(f"Stress hydrique : {round(stressed*100)}%")
    if healthy > 0.1:  pos.append(f"Végétation saine : {round(healthy*100)}%")
    if water > 0.05:   pos.append(f"Eau disponible : {round(water*100)}%")
    if not neg: neg = ["Aucun indicateur critique détecté"]
    if not pos: pos = ["Aucun indicateur positif détecté"]
    
    resume = (
        f"YOLO détecte : {CLASS_NAMES[max(class_area, key=class_area.get)]} dominant. "
        f"Risque {risk_label} (score {drought_score}/100). "
        f"{'Intervention recommandée.' if risk_class >= 2 else 'Situation sous contrôle.'}"
    )
    
    return {
        "risk_class":            risk_class,
        "risk_label":            risk_label,
        "risk_label_fr":         ["Aucun","Faible","Modéré","Sévère","Extrême"][risk_class],
        "risk_color":            RISK_COLORS_HEX[risk_class],
        "confidence":            round(max((v for v in class_area.values() if v > 0), default=0), 3),
        "drought_score":         drought_score,
        "score_sante":           health_score,
        "urgence":               urgence,
        "resume_global":         resume,
        "resume":                resume,
        "alerte":                f"Classe {risk_class} — {risk_label} · YOLO DroughtAI",
        "indicateurs_negatifs":  neg,
        "indicateurs_positifs":  pos,
        "actions_immediates":    actions[risk_class],
        "actions_preventives":   ["Installer station météo", "Rotation des cultures", "Réserves d\'eau"],
        "gaspillage_eau":        indicators["gaspillage_eau"],
        "stress_hydrique":       indicators["stress_hydrique"],
        "risque_secheresse":     indicators["risque_secheresse"],
        "anomalies_plantes":     indicators["anomalies_plantes"],
    }


def predict_folder(folder: str, conf: float = 0.25):
    """Prédit sur toutes les images d\'un dossier."""
    folder_path = Path(folder)
    images = list(folder_path.glob("*.[jJpP][pPnN][gGeE]*"))
    print(f"\n📂 {len(images)} images trouvées dans {folder}")
    
    all_results = []
    for img_path in images:
        print(f"  Analyse: {img_path.name}")
        result = predict_image(str(img_path), conf=conf)
        all_results.append({"file": img_path.name, **result})
    
    # Sauvegarder résultats JSON
    output = Path("results/predictions.json")
    output.parent.mkdir(exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Résultats sauvegardés: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DroughtAI YOLO — Évaluation")
    parser.add_argument("--image",  type=str, help="Tester sur une image")
    parser.add_argument("--folder", type=str, help="Tester sur un dossier")
    parser.add_argument("--conf",   type=float, default=0.25, help="Seuil confiance")
    args = parser.parse_args()
    
    if args.image:
        result = predict_image(args.image, conf=args.conf)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.folder:
        predict_folder(args.folder, conf=args.conf)
    else:
        evaluate_on_test()
