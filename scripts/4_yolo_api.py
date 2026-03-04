"""
DroughtAI YOLO — Endpoint Flask
================================
Ajoute /api/analyze/image à ton API Flask existante.
Copie ce fichier dans ton dossier api/ et importe-le dans app.py
"""

import base64
import tempfile
import os
from pathlib import Path
from flask import request, jsonify

# Import du script d'évaluation
import sys
sys.path.insert(0, str(Path(__file__).parent))
from scripts.3_evaluate import predict_image, load_model, CLASS_NAMES

_yolo_model = None

def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        model_path = Path("models/drought_yolo_best.pt")
        if model_path.exists():
            from ultralytics import YOLO
            _yolo_model = YOLO(str(model_path))
    return _yolo_model


def register_yolo_routes(app, require_api_key, ok, err, logger):
    """
    Enregistre les routes YOLO dans l'app Flask existante.
    
    Appel depuis app.py:
        from api.yolo_api import register_yolo_routes
        register_yolo_routes(app, require_api_key, ok, err, logger)
    """

    @app.route("/api/analyze/image", methods=["POST"])
    @require_api_key
    def analyze_image():
        """
        Analyse une image avec YOLO.
        
        Body JSON:
        {
            "image_base64": "...",    // Image encodée en base64
            "type": "full",           // full | drought_risk | water_stress | water_waste | pesticide
            "conf": 0.25              // Seuil confiance 0.0-1.0
        }
        """
        try:
            data = request.get_json(force=True)
        except:
            return err("Corps JSON invalide")

        if "image_base64" not in data:
            return err("Champ image_base64 manquant")

        model = get_yolo_model()
        if model is None:
            return err(
                "Modèle YOLO non disponible. "
                "Lance: python scripts/2_train_yolo.py",
                503
            )

        try:
            # Décoder l'image base64
            img_data = base64.b64decode(data["image_base64"])
            
            # Sauvegarder temporairement
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp.write(img_data)
                tmp_path = tmp.name

            conf = float(data.get("conf", 0.25))
            result = predict_image(tmp_path, conf=conf, save=False)
            os.unlink(tmp_path)

            logger.info(
                f"[YOLO] risk={result.get('risk_label','?')} "
                f"detections={result.get('n_detections', 0)}"
            )
            return ok(result)

        except Exception as e:
            logger.error(f"YOLO analyze error: {e}")
            return err("Erreur analyse YOLO", 500, str(e))

    @app.route("/api/analyze/status", methods=["GET"])
    @require_api_key
    def yolo_status():
        """Vérifie si le modèle YOLO est disponible."""
        model_path = Path("models/drought_yolo_best.pt")
        return ok({
            "yolo_available": model_path.exists(),
            "model_path":     str(model_path),
            "classes":        CLASS_NAMES,
        })
