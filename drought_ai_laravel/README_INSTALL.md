# DroughtAI Laravel 11 — Installation complète

## Prérequis
- PHP 8.2+  →  `php -v`
- Composer  →  `composer self-update`
- API Flask démarrée sur ton PC

---

## Installation — 4 commandes

```bash
cd drought_ai_laravel
composer install
php artisan key:generate
php artisan storage:link
php artisan serve
```

Ouvrir → http://localhost:8000

---

## Lancer les deux serveurs (2 terminaux)

**Terminal 1 — Flask API :**
```bash
cd C:\Users\Mohame Lemine\Desktop\drought_ai_project\drought_ai
python api\app.py
```

**Terminal 2 — Laravel :**
```bash
cd drought_ai_laravel
php artisan serve
```

---

## Fonctionnement de l'analyse photo

```
Photo uploadée
      │
      ▼
PHP GD extrait les features visuelles :
  • % pixels verts  → NDVI estimé, végétation
  • % pixels bruns  → sol nu, sécheresse
  • % pixels gris   → sol craquelé
  • % pixels bleus  → eau visible
  • luminosité      → température estimée
      │
      ▼
/api/predict Flask → Gradient Boosting F1=86.6%
      │
      ▼
Résultat réel avec classe de risque 0-4
```

**Aucune clé API externe requise.**

---

## Si l'IP Flask change

```bash
ipconfig  # trouver ton IP
```

Modifier `.env` :
```env
DROUGHTAI_URL=http://TON_IP:5000
```

Puis :
```bash
php artisan config:clear
php artisan cache:clear
```

---

## Pages disponibles

| Page | URL | Description |
|---|---|---|
| Tableau de bord | / | Carte Leaflet, graphiques, stats 2018–2023 |
| Prédiction | /predict | Formulaire → modèle Flask |
| Analyse Photo | /analysis | Upload image → features visuelles → Flask |

