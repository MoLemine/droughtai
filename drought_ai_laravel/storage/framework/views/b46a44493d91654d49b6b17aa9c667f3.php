<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="csrf-token" content="<?php echo e(csrf_token()); ?>">
<title><?php echo $__env->yieldContent('title','DroughtAI'); ?> — Prédiction Sécheresse</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{
  --g:#15803d;--g2:#16a34a;--gl:#f0fdf4;--gxl:#dcfce7;--gd:#14532d;
  --y:#d97706;--yl:#fffbeb;--o:#ea580c;--ol:#fff7ed;
  --r:#dc2626;--rl:#fef2f2;--b:#2563eb;--bl:#eff6ff;
  --bg:#f8fafc;--w:#fff;--bd:#e2e8f0;--bd2:#cbd5e1;
  --tx:#0f172a;--tx2:#334155;--mu:#64748b;--mu2:#94a3b8;
  --fn:'Plus Jakarta Sans',sans-serif;--mo:'JetBrains Mono',monospace;
  --rd:12px;--sh:0 1px 2px rgba(0,0,0,.05),0 4px 12px rgba(0,0,0,.06);
}
html{font-size:15px;scroll-behavior:smooth}
body{font-family:var(--fn);background:var(--bg);color:var(--tx);min-height:100vh;display:flex;flex-direction:column;line-height:1.55}

/* NAV */
nav{background:var(--gd);height:62px;display:flex;align-items:center;padding:0 1.5rem;gap:.5rem;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.2)}
.logo{display:flex;align-items:center;gap:9px;color:#fff;font-size:1.1rem;font-weight:800;text-decoration:none;margin-right:.5rem}
.logo-tag{background:#4ade80;color:#14532d;font-size:.62rem;font-weight:800;padding:2px 7px;border-radius:5px}
.nav-a{display:flex;align-items:center;gap:6px;color:rgba(255,255,255,.7);text-decoration:none;padding:7px 13px;border-radius:8px;font-size:.84rem;font-weight:500;transition:.15s}
.nav-a:hover{background:rgba(255,255,255,.1);color:#fff}
.nav-a.on{background:rgba(255,255,255,.15);color:#fff;font-weight:600}
.ml-a{margin-left:auto}
.api-status{display:flex;align-items:center;gap:6px;font-size:.74rem;font-weight:600;padding:5px 11px;border-radius:20px;color:#fff}
.api-status.online{background:rgba(74,222,128,.2)}.api-status.offline{background:rgba(248,113,113,.2)}
.api-status .dot{width:6px;height:6px;border-radius:50%;background:currentColor}
.api-status.online .dot{animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

/* MAIN */
main{flex:1;max-width:1260px;width:100%;margin:0 auto;padding:2rem 1.5rem}

/* PAGE HEADER */
.ph{margin-bottom:1.7rem}
.ph h1{font-size:1.65rem;font-weight:800;letter-spacing:-.5px}
.ph p{font-size:.875rem;color:var(--mu);margin-top:3px}

/* CARD */
.card{background:var(--w);border:1px solid var(--bd);border-radius:var(--rd);box-shadow:var(--sh);overflow:hidden}
.ch{padding:.95rem 1.3rem;border-bottom:1px solid var(--bd);display:flex;align-items:center;gap:9px}
.ch h3{font-size:.93rem;font-weight:700;flex:1;color:var(--tx)}
.cb{padding:1.2rem 1.3rem}
.ci{width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0}

/* GRIDS */
.g2{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:1.1rem}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}

/* STAT */
.stat{background:var(--w);border:1px solid var(--bd);border-left:4px solid var(--c,var(--g2));border-radius:var(--rd);padding:1.1rem 1.3rem;box-shadow:var(--sh)}
.sl{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--mu);margin-bottom:.3rem}
.sv{font-size:2rem;font-weight:800;font-family:var(--mo);line-height:1}
.ss{font-size:.7rem;color:var(--mu);margin-top:.3rem}

/* BADGES */
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:.71rem;font-weight:700}
.b0{background:#dcfce7;color:#14532d}.b1{background:#fef9c3;color:#854d0e}
.b2{background:#ffedd5;color:#9a3412}.b3{background:#fee2e2;color:#991b1b}.b4{background:#ede9fe;color:#5b21b6}

/* FORM */
.fg{margin-bottom:.95rem}
.lbl{display:block;font-size:.81rem;font-weight:600;color:var(--tx2);margin-bottom:.35rem}
.inp{width:100%;padding:.62rem .88rem;border:1.5px solid var(--bd2);border-radius:9px;font-family:var(--fn);font-size:.875rem;color:var(--tx);background:#fff;transition:.2s;outline:none}
.inp:focus{border-color:var(--g2);box-shadow:0 0 0 3px rgba(21,128,61,.1)}
.hint{font-size:.7rem;color:var(--mu);margin-top:.28rem}

/* BUTTONS */
.btn{display:inline-flex;align-items:center;gap:7px;padding:.62rem 1.25rem;border-radius:9px;font-family:var(--fn);font-size:.875rem;font-weight:600;border:none;cursor:pointer;transition:.15s;text-decoration:none}
.btn-g{background:var(--g);color:#fff}.btn-g:hover{background:var(--gd);box-shadow:0 4px 12px rgba(21,128,61,.3);transform:translateY(-1px)}
.btn-o{background:transparent;color:var(--g);border:1.5px solid var(--g)}.btn-o:hover{background:var(--gxl)}
.btn-w{width:100%;justify-content:center}.btn-lg{padding:.82rem 1.55rem;font-size:.93rem}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none!important;box-shadow:none!important}

/* ALERTS */
.alert{display:flex;gap:8px;padding:.82rem 1.1rem;border-radius:9px;font-size:.82rem;margin-bottom:.9rem}
.a-err{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}
.a-demo{background:#fffbeb;border:1px solid #fde68a;color:#92400e;font-size:.76rem}

/* UPLOAD / DROP */
.dz{position:relative;border:2.5px dashed var(--bd2);border-radius:var(--rd);padding:2.4rem 1.5rem;text-align:center;cursor:pointer;transition:.2s;background:#fafcff}
.dz:hover,.dz.over{border-color:var(--g2);background:var(--gl)}
.dz input{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
.dz-icon{font-size:2.6rem;display:block;margin-bottom:.65rem;line-height:1}
.dz-title{font-size:.98rem;font-weight:700;margin-bottom:.25rem}
.dz-sub{font-size:.77rem;color:var(--mu)}
.dz-prev{margin-top:.9rem;display:none}
.dz-prev img,.dz-prev video{max-height:175px;max-width:100%;border-radius:10px;object-fit:cover}
.dz-fname{font-size:.74rem;color:var(--mu);margin-top:.4rem;font-family:var(--mo)}

/* TYPE PICKER */
.tpicker{display:grid;grid-template-columns:repeat(5,1fr);gap:.5rem;margin-bottom:1.1rem}
.tp{border:2px solid var(--bd);border-radius:10px;padding:.62rem .4rem;text-align:center;cursor:pointer;transition:.15s;background:#fff;user-select:none;position:relative}
.tp:hover{border-color:var(--g2);background:var(--gl)}
.tp input[type=radio]{position:absolute;opacity:0;pointer-events:none}
.tp.picked{border-color:var(--g2);background:var(--gxl)}
.tp-i{font-size:1.35rem;display:block;margin-bottom:.25rem}
.tp-l{font-size:.65rem;font-weight:700;line-height:1.3;color:var(--tx2)}

/* PROGRESS */
.pb{height:7px;background:#e2e8f0;border-radius:6px;overflow:hidden}
.pf{height:100%;border-radius:6px;transition:width 1.2s ease}

/* SCORE RING */
.sring{width:70px;height:70px;border-radius:50%;border:5px solid;display:flex;align-items:center;justify-content:center;flex-direction:column;flex-shrink:0}
.snum{font-family:var(--mo);font-size:1.1rem;font-weight:800;line-height:1}
.smax{font-size:.5rem;font-weight:600}

/* ACTIONS */
.acts{list-style:none;display:flex;flex-direction:column;gap:.4rem}
.acts li{display:flex;gap:8px;font-size:.82rem;padding:.48rem .68rem;background:#f8fafc;border-radius:7px;border-left:3px solid var(--g2)}
.acts li::before{content:'→';color:var(--g2);font-weight:700;flex-shrink:0}

/* DIVIDER */
.divider{height:1px;background:var(--bd);margin:1rem 0}

/* OFFLINE */
.offline{background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:.82rem 1.1rem;margin-bottom:1.2rem;display:flex;align-items:center;gap:9px;color:#991b1b;font-size:.82rem}

/* RESPONSIVE */
@media(max-width:900px){.g3,.g4{grid-template-columns:1fr 1fr}.tpicker{grid-template-columns:repeat(3,1fr)}}
@media(max-width:640px){.g2,.g3,.g4{grid-template-columns:1fr}.tpicker{grid-template-columns:repeat(2,1fr)}.nav-a span:not(.nicon){display:none}}
</style>
<?php echo $__env->yieldPushContent('head'); ?>
</head>
<body>

<nav>
  <a href="<?php echo e(route('dashboard')); ?>" class="logo">
    🌵 DroughtAI <span class="logo-tag">v2.0</span>
  </a>
  <a href="<?php echo e(route('dashboard')); ?>"  class="nav-a <?php echo e(request()->routeIs('dashboard') ?'on':''); ?>"><span class="nicon">📊</span><span>Tableau de bord</span></a>
  <a href="<?php echo e(route('predict')); ?>"    class="nav-a <?php echo e(request()->routeIs('predict*')  ?'on':''); ?>"><span class="nicon">🎯</span><span>Prédiction</span></a>
  <a href="<?php echo e(route('analysis')); ?>"   class="nav-a <?php echo e(request()->routeIs('analysis*') ?'on':''); ?>"><span class="nicon">📷</span><span>Analyse Photo/Vidéo</span></a>
  <div class="ml-a">
    <div class="api-status <?php echo e(isset($online)&&$online ? 'online':'offline'); ?>">
      <span class="dot"></span>
      API <?php echo e(isset($online)&&$online ? 'En ligne':'Hors ligne'); ?>

    </div>
  </div>
</nav>

<main><?php echo $__env->yieldContent('content'); ?></main>

<footer style="text-align:center;padding:1.1rem;font-size:.72rem;color:var(--mu);border-top:1px solid var(--bd);background:var(--w)">
  DroughtAI v2.0 · Mauritanie & Vallée du Fleuve Sénégal · Gradient Boosting F1=86.6% · <a href="http://192.168.100.37:5000/api/health" target="_blank" style="color:var(--g)">API Flask</a>
</footer>

<?php echo $__env->yieldPushContent('scripts'); ?>
</body>
</html>
<?php /**PATH C:\Users\Mohame Lemine\Desktop\drought_yolo\drought_ai_laravel\resources\views/layouts/app.blade.php ENDPATH**/ ?>