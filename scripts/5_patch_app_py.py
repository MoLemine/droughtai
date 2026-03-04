"""
DroughtAI — Patch app.py pour intégrer YOLO
=============================================
Ce script modifie automatiquement ton app.py Flask
pour ajouter les endpoints YOLO.

Usage:
    cd C:\\Users\\Mohame Lemine\\Desktop\\drought_ai_project\\drought_ai
    python drought_yolo/scripts/5_patch_app_py.py
"""

from pathlib import Path
import re

APP_PY = Path("api/app.py")

IMPORT_LINE  = "from api.yolo_api import register_yolo_routes"
REGISTER_LINE = "    register_yolo_routes(app, require_api_key, ok, err, logger)"

def patch():
    if not APP_PY.exists():
        print(f"ERREUR: {APP_PY} non trouvé.")
        return
    
    content = APP_PY.read_text(encoding="utf-8")
    
    # 1. Ajouter l'import
    if IMPORT_LINE in content:
        print("Import YOLO déjà présent.")
    else:
        content = content.replace(
            "from pathlib import Path",
            "from pathlib import Path\n" + IMPORT_LINE
        )
        print("✅ Import YOLO ajouté.")
    
    # 2. Enregistrer les routes (après load_models())
    if REGISTER_LINE in content:
        print("Routes YOLO déjà enregistrées.")
    else:
        content = content.replace(
            "    load_models()",
            "    load_models()\n" + REGISTER_LINE
        )
        print("✅ Routes YOLO enregistrées.")
    
    APP_PY.write_text(content, encoding="utf-8")
    print("\n✅ app.py patché avec succès!")
    print("\nNouveaux endpoints disponibles:")
    print("  POST /api/analyze/image  → Analyse YOLO d\'une image")
    print("  GET  /api/analyze/status → Statut du modèle YOLO")

if __name__ == "__main__":
    patch()
