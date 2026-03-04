"""
DroughtAI — API Flask complète
================================
Endpoints :
  GET  /                      → statut
  GET  /api/health            → santé
  POST /api/predict           → prédiction ML depuis formulaire
  POST /api/analyze/image     → analyse YOLO d'une image
  GET  /api/analyze/status    → statut YOLO
  GET  /api/models/info       → infos tous les modèles

Usage:
    python api/app.py
"""

import base64, tempfile, os, sys, json, logging, pickle, time
from pathlib import Path
from functools import wraps

import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

# ── Setup ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("droughtai")

app = Flask(__name__)
CORS(app)

API_KEY      = "droughtai-secret-2024"
YOLO_PATH    = BASE_DIR / "models" / "drought_yolo_best.pt"
ML_PATH      = BASE_DIR / "models" / "drought_ml_best.pkl"
METRICS_PATH = BASE_DIR / "models" / "ml_metrics.json"

_yolo_model = None
_ml_model   = None

# ── Helpers ────────────────────────────────────────────────────────────────
def ok(data, status=200):
    return jsonify({"success": True, "data": data}), status

def err(msg, status=400, detail=""):
    return jsonify({"success": False, "message": msg, "detail": detail}), status

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = (request.headers.get("X-API-Key") or
               request.args.get("api_key") or
               (request.get_json(silent=True) or {}).get("api_key", ""))
        if key != API_KEY:
            return err("Clé API invalide", 401)
        return f(*args, **kwargs)
    return decorated

# ── Charger modèles ────────────────────────────────────────────────────────
def load_ml():
    global _ml_model
    if _ml_model: return _ml_model
    if not ML_PATH.exists():
        logger.warning(f"Modèle ML non trouvé: {ML_PATH}")
        logger.warning("Lance: python ml/train_ml.py")
        return None
    try:
        with open(ML_PATH, "rb") as f:
            _ml_model = pickle.load(f)
        logger.info(f"✅ Modèle ML chargé: {_ml_model.get('model_name','?')} (F1={_ml_model.get('f1',0):.3f})")
        return _ml_model
    except Exception as e:
        logger.error(f"Erreur chargement ML: {e}")
        return None

def load_yolo():
    global _yolo_model
    if _yolo_model: return _yolo_model
    if not YOLO_PATH.exists(): return None
    try:
        from ultralytics import YOLO
        _yolo_model = YOLO(str(YOLO_PATH))
        logger.info(f"✅ Modèle YOLO chargé: {YOLO_PATH.name}")
        return _yolo_model
    except Exception as e:
        logger.error(f"Erreur YOLO: {e}")
        return None

# ── Classes & labels ───────────────────────────────────────────────────────
RISK_LABELS  = ["Aucun", "Faible", "Modere", "Severe", "Extreme"]
RISK_LABELS_FR = ["Aucun", "Faible", "Modéré", "Sévère", "Extrême"]
RISK_COLORS  = {0:"#22c55e", 1:"#eab308", 2:"#f97316", 3:"#ef4444", 4:"#7c3aed"}
RISK_ICONS   = {0:"✅", 1:"⚠️", 2:"🔶", 3:"🚨", 4:"💀"}

YOLO_CLASSES = {0:"Sol Craquelé",1:"Végétation Saine",2:"Stress Hydrique",
                3:"Sol Nu",4:"Eau / Irrigation",5:"Végétation Morte"}

POINTS = ["Rosso","Boghe","Kaedi","NouakchottSud","Matam"]

ML_FEATURES = [
    "month","precipitation","temperature_c","humidity",
    "soil_moisture","evaporation","ndvi","stress_hydrique",
    "point_encoded",
]

# ── /api/predict ───────────────────────────────────────────────────────────

@app.route("/api/predict", methods=["POST"])
@require_api_key
def predict():
    """
    Prédiction ML depuis le formulaire Laravel.

    Body JSON:
    {
        "point":           "Rosso",
        "year":            2024,
        "month":           3,
        "precipitation":   5.0,
        "temperature_c":   38.5,
        "humidity":        22.0,
        "soil_moisture":   0.07,
        "ndvi":            0.09,
        "evaporation":     88.0,      // optionnel
        "stress_hydrique": 0.72       // optionnel
    }
    """
    t0 = time.time()

    ml = load_ml()
    if ml is None:
        return err(
            "Modèle ML non disponible",
            503,
            "Lance: python ml/train_ml.py"
        )

    try:
        data = request.get_json(force=True) or {}
    except:
        return err("JSON invalide")

    # ── Valider les champs requis
    required = ["point","month","precipitation","temperature_c",
                "humidity","soil_moisture","ndvi"]
    missing  = [f for f in required if f not in data]
    if missing:
        return err(f"Champs manquants: {', '.join(missing)}")

    try:
        point         = str(data["point"])
        month         = int(data["month"])
        year          = int(data.get("year", 2024))
        precipitation = float(data["precipitation"])
        temperature_c = float(data["temperature_c"])
        humidity      = float(data["humidity"])
        soil_moisture = float(data["soil_moisture"])
        ndvi          = float(data["ndvi"])
        evaporation   = float(data.get("evaporation", temperature_c * 2.3))
        stress_hydrique = float(data.get("stress_hydrique",
                                max(0, min(1, 1 - soil_moisture / 0.25))))

        # Encoder le point GPS
        le = ml["label_encoder"]
        if point not in le.classes_:
            point = "Kaedi"  # fallback
        point_enc = int(le.transform([point])[0])

        # ── Construire le vecteur de features
        X = np.array([[
            month, precipitation, temperature_c, humidity,
            soil_moisture, evaporation, ndvi, stress_hydrique,
            point_enc,
        ]])

        # ── Prédiction
        model     = ml["model"]
        y_pred    = int(model.predict(X)[0])

        # Probabilités
        probas = {}
        try:
            proba_arr = model.predict_proba(X)[0]
            for i, p in enumerate(proba_arr):
                probas[RISK_LABELS[i]] = round(float(p), 4)
            confidence = float(max(proba_arr))
        except:
            confidence = 0.75
            probas     = {RISK_LABELS[y_pred]: 1.0}

        ms = round((time.time() - t0) * 1000)

        # ── Recommandations selon classe
        reco_map = {
            0: {
                "action":      "Maintenir l'irrigation habituelle",
                "detail":      "Conditions normales. Surveillance météo conseillée.",
                "preventiF":   ["Surveiller l'humidité sol", "Maintenir calendrier d'irrigation"],
            },
            1: {
                "action":      "Augmenter légèrement l'irrigation",
                "detail":      "Faible risque de sécheresse. Surveiller l'évolution.",
                "preventiF":   ["Réduire l'évaporation avec paillage", "Prévoir irrigation supplémentaire"],
            },
            2: {
                "action":      "Irrigation immédiate requise",
                "detail":      "Sécheresse modérée. Intervention dans les 48-72h.",
                "preventiF":   ["Appliquer paillage", "Réduire exposition solaire des cultures"],
            },
            3: {
                "action":      "Intervention urgente — Irrigation dans les 24h",
                "detail":      "Sécheresse sévère. Risque de perte de cultures.",
                "preventiF":   ["Alerter les agriculteurs locaux", "Activer réserves d'eau"],
            },
            4: {
                "action":      "URGENCE — Mesures d'urgence immédiates",
                "detail":      "Sécheresse extrême. Pertes agricoles probables.",
                "preventiF":   ["Évaluer les pertes", "Contacter autorités agricoles", "Aide humanitaire"],
            },
        }

        reco = reco_map[y_pred]

        response = {
            "risk_class":     y_pred,
            "risk_label":     RISK_LABELS[y_pred],
            "risk_label_fr":  RISK_LABELS_FR[y_pred],
            "risk_color":     RISK_COLORS[y_pred],
            "risk_icon":      RISK_ICONS[y_pred],
            "confidence":     round(confidence, 4),
            "probabilities":  probas,
            "model_used":     ml.get("model_name", "gradient_boosting"),
            "model_f1":       round(ml.get("f1", 0), 3),
            "processing_ms":  ms,
            "action":         reco["action"],
            "detail":         reco["detail"],
            "actions_preventives": reco["preventiF"],
            "input": {
                "point":         point,
                "year":          year,
                "month":         month,
                "precipitation": precipitation,
                "temperature_c": temperature_c,
                "humidity":      humidity,
                "soil_moisture": soil_moisture,
                "ndvi":          ndvi,
                "evaporation":   evaporation,
                "stress_hydrique": stress_hydrique,
            },
        }

        logger.info(
            f"[PREDICT] {point} {year}/{month:02d} → "
            f"Classe {y_pred} ({RISK_LABELS[y_pred]}) "
            f"conf={round(confidence*100)}% {ms}ms"
        )
        return ok(response)

    except ValueError as e:
        return err(f"Valeur invalide: {e}")
    except Exception as e:
        logger.error(f"Erreur predict: {e}")
        return err("Erreur interne", 500, str(e))

# ── /api/analyze/image ─────────────────────────────────────────────────────

@app.route("/api/analyze/image", methods=["POST"])
@require_api_key
def analyze_image():
    model = load_yolo()
    if model is None:
        return err("Modèle YOLO non disponible", 503,
                   "Lance: python train.py")
    try:
        data = request.get_json(force=True) or {}
    except:
        return err("JSON invalide")

    if "image_base64" not in data:
        return err("Champ image_base64 manquant")

    try:
        img_bytes = base64.b64decode(data["image_base64"])
        conf      = float(data.get("conf", 0.25))

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        results = model.predict(tmp_path, conf=conf, imgsz=320, verbose=False)
        result  = results[0]
        os.unlink(tmp_path)

        h, w   = result.orig_shape[:2]
        dets   = []
        c_cnt  = {i:0 for i in range(6)}
        c_area = {i:0.0 for i in range(6)}

        for box in result.boxes:
            cls   = int(box.cls[0])
            cf    = float(box.conf[0])
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            area  = ((x2-x1)*(y2-y1))/(w*h)
            c_cnt[cls]  += 1
            c_area[cls] += area
            dets.append({
                "class_id":   cls,
                "class_name": YOLO_CLASSES.get(cls, f"cls_{cls}"),
                "confidence": round(cf, 3),
                "bbox":       [x1,y1,x2-x1,y2-y1],
                "area_pct":   round(area*100, 1),
            })

        risk = _calc_yolo_risk(c_area)
        return ok({**risk,
            "source": "yolo_droughtai", "model": YOLO_PATH.name,
            "n_detections": len(dets), "detections": dets,
            "class_counts": {YOLO_CLASSES.get(i,f"cls_{i}"): c_cnt[i] for i in range(6)},
            "class_areas":  {YOLO_CLASSES.get(i,f"cls_{i}"): round(c_area[i]*100,1) for i in range(6)},
        })
    except Exception as e:
        logger.error(f"YOLO error: {e}")
        return err("Erreur YOLO", 500, str(e))

def _calc_yolo_risk(ca):
    cr=ca.get(0,0); hl=ca.get(1,0); st=ca.get(2,0)
    br=ca.get(3,0); wt=ca.get(4,0); dd=ca.get(5,0)
    ds = min(100,max(0,int(cr*180+br*120+dd*150+st*60-hl*80-wt*40)))
    rc = 4 if ds>=80 or dd>0.3 else (3 if ds>=60 or cr>0.35 else
         (2 if ds>=40 or br>0.40 else (1 if ds>=20 or st>0.20 else 0)))
    urg=["Faible","Moyenne","Élevée","Critique","Critique"][rc]
    dom=max(ca,key=ca.get) if any(v>0 for v in ca.values()) else 1
    resume=(f"YOLO: {YOLO_CLASSES.get(dom,'?')} dominant. "
            f"Risque {RISK_LABELS[rc]} (score {ds}/100).")
    neg=[f"Sol craquelé {round(cr*100)}%" if cr>0.1 else None,
         f"Sol nu {round(br*100)}%"       if br>0.2 else None,
         f"Végétation morte {round(dd*100)}%" if dd>0.05 else None]
    pos=[f"Végétation saine {round(hl*100)}%" if hl>0.1 else None,
         f"Eau visible {round(wt*100)}%"      if wt>0.05 else None]
    neg=[x for x in neg if x] or ["Aucun indicateur critique"]
    pos=[x for x in pos if x] or ["Aucun indicateur positif"]
    return {
        "risk_class":rc,"risk_label":RISK_LABELS[rc],
        "risk_label_fr":RISK_LABELS_FR[rc],"risk_color":RISK_COLORS[rc],
        "drought_score":ds,"score_sante":max(5,100-rc*20),
        "urgence":urg,"confidence":round(max(ca.values(),default=0),3),
        "resume_global":resume,"resume":resume,
        "alerte":f"Classe {rc} — {RISK_LABELS[rc]} · YOLO",
        "indicateurs_negatifs":neg,"indicateurs_positifs":pos,
        "actions_immediates":{4:["Irrigation urgente","Alerter autorités"],
            3:["Irriguer 24h","Protéger cultures"],
            2:["Irriguer 48-72h","Appliquer paillage"],
            1:["Surveiller sol","Préparer irrigation"],
            0:["Surveillance normale"]}[rc],
        "actions_preventives":["Installer station météo","Rotation cultures","Réserves eau"],
        "gaspillage_eau":{"detecte":wt>0.15,"niveau":"Modéré" if wt>0.15 else "Faible","score":int(wt*100),"details":f"Eau visible {round(wt*100)}%"},
        "stress_hydrique":{"detecte":rc>=1,"niveau":RISK_LABELS[rc],"score":min(100,int((st+cr)*80+rc*10)),"details":f"Sol craquelé {round(cr*100)}% · Stress {round(st*100)}%"},
        "risque_secheresse":{"classe":rc,"label":RISK_LABELS[rc],"score":ds,"details":f"Sol nu {round(br*100)}% · Mort {round(dd*100)}%"},
        "anomalies_plantes":{"detectee":st>0.05 or dd>0.05,"type":"Stress sévère" if dd>0.1 else ("Modéré" if st>0.1 else "Normal"),"score":int((st+dd)*100),"details":f"Saine {round(hl*100)}% · Stressée {round(st*100)}%"},
    }

# ── Routes utilitaires ─────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return ok({
        "name": "DroughtAI API", "version": "2.0.0",
        "ml_model":   ML_PATH.name   if ML_PATH.exists()   else "non entraîné",
        "yolo_model": YOLO_PATH.name if YOLO_PATH.exists() else "non entraîné",
        "endpoints": [
            "POST /api/predict          → prédiction ML",
            "POST /api/analyze/image   → analyse YOLO",
            "GET  /api/analyze/status  → statut YOLO",
            "GET  /api/models/info     → infos modèles",
            "GET  /api/health          → santé API",
        ]
    })

@app.route("/api/health", methods=["GET"])
def health():
    return ok({"status":"ok","ml":ML_PATH.exists(),"yolo":YOLO_PATH.exists()})

@app.route("/api/analyze/status", methods=["GET"])
@require_api_key
def yolo_status():
    return ok({
        "yolo_available": YOLO_PATH.exists(),
        "model_path":     str(YOLO_PATH),
        "classes":        YOLO_CLASSES,
    })

@app.route("/api/models/info", methods=["GET"])
@require_api_key
def models_info():
    info = {"ml": None, "yolo": None}
    if ML_PATH.exists() and METRICS_PATH.exists():
        with open(METRICS_PATH) as f:
            info["ml"] = json.load(f)
    if YOLO_PATH.exists():
        info["yolo"] = {
            "path": str(YOLO_PATH),
            "size_mb": round(YOLO_PATH.stat().st_size/1e6, 1),
        }
    return ok(info)

@app.route("/api/timeseries", methods=["GET"])
@require_api_key
def timeseries():
    """Données fictives pour les graphiques Laravel."""
    import random
    point    = request.args.get("point", "Rosso")
    variable = request.args.get("variable", "predicted_risk")
    data = []
    for year in range(2018, 2024):
        for month in range(1, 13):
            data.append({
                "point": point, "year": year, "month": month,
                "value": round(random.uniform(0, 3), 2),
                "label": variable,
            })
    return ok({"variable": variable, "point": point, "series": data})

@app.route("/api/stats", methods=["GET"])
@require_api_key
def stats():
    return ok({
        "total_predictions": 0,
        "points": POINTS,
        "risk_distribution": {RISK_LABELS[i]: 0 for i in range(5)},
    })

# ── Lancement ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("DroughtAI API v2.0")
    print("=" * 55)
    print(f"ML Model  : {'✅ ' + ML_PATH.name if ML_PATH.exists() else '❌ non trouvé — lance: python ml/train_ml.py'}")
    print(f"YOLO Model: {'✅ ' + YOLO_PATH.name if YOLO_PATH.exists() else '❌ non trouvé'}")

    load_ml()
    load_yolo()

    print(f"\n🚀 http://127.0.0.1:5000")
    print(f"API Key : {API_KEY}")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=False)
