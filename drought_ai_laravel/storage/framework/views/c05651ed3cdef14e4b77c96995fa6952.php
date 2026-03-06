
<?php $__env->startSection('title','Tableau de Bord'); ?>
<?php $__env->startSection('content'); ?>

<div class="ph">
  <h1>📊 Tableau de bord</h1>
  <p>Sécheresse agricole — Mauritanie & Vallée du Fleuve Sénégal · 2018–2027</p>
</div>

<?php if(!$online): ?>
<div class="offline">⚠️ <div><strong>API Flask hors ligne.</strong> Dashboard fonctionnel en mode local. Lancez <code style="background:#fee2e2;padding:1px 5px;border-radius:3px">python api\app.py</code></div></div>
<?php endif; ?>


<div style="display:flex;align-items:center;gap:.7rem;margin-bottom:1.2rem;flex-wrap:wrap">
  <span style="font-size:.82rem;font-weight:700;color:var(--mu)">📅 Année :</span>
  <?php $__currentLoopData = $allYears; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $yr): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
    <?php $isPred = in_array($yr, $predictionYears); ?>
    <a href="?year=<?php echo e($yr); ?>"
       style="padding:.3rem .8rem;border-radius:20px;font-size:.82rem;font-weight:700;text-decoration:none;
              <?php echo e($selectedYear == $yr
                  ? 'background:'.($isPred?'#7c3aed':'#2563eb').';color:#fff;border:2px solid '.($isPred?'#7c3aed':'#2563eb')
                  : 'background:#f1f5f9;color:var(--tx);border:2px solid #e2e8f0'); ?>">
      <?php echo e($isPred ? '🔮 '.$yr : $yr); ?>

    </a>
  <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
</div>

<?php if($isPrediction): ?>
<div style="background:#faf5ff;border:1.5px solid #c4b5fd;border-radius:10px;padding:.75rem 1rem;margin-bottom:1.2rem;display:flex;align-items:center;gap:.7rem;font-size:.83rem">
  <span style="font-size:1.3rem">🔮</span>
  <div>
    <strong style="color:#7c3aed">Projection <?php echo e($selectedYear); ?></strong> —
    Basée sur la tendance 2018–2023 (régression linéaire + saisonnalité).
    <span style="color:#9333ea">Incertitude ±0.3 classes.</span>
  </div>
</div>
<?php endif; ?>


<div class="g4" style="margin-bottom:1.25rem">
  <div class="stat" style="--c:#15803d"><div class="sl">Risque moyen</div><div class="sv"><?php echo e(number_format($globalStats['mean_risk'],2)); ?></div><div class="ss">Toutes années · 5 points</div></div>
  <div class="stat" style="--c:#ea580c"><div class="sl">Modéré+</div><div class="sv"><?php echo e($globalStats['pct_moderate']); ?><span style="font-size:1.1rem">%</span></div><div class="ss">Observations ≥ classe 2</div></div>
  <div class="stat" style="--c:#dc2626"><div class="sl">Sévère</div><div class="sv"><?php echo e($globalStats['pct_severe']); ?><span style="font-size:1.1rem">%</span></div><div class="ss">Observations ≥ classe 3</div></div>
  <div class="stat" style="--c:#2563eb"><div class="sl">Observations</div><div class="sv"><?php echo e($globalStats['total']); ?></div><div class="ss">5 points GPS · 6 ans réels</div></div>
</div>


<div class="g2" style="margin-bottom:1.25rem">
  <div class="card">
    <div class="ch"><div class="ci" style="background:#dcfce7">🗺️</div><h3>Carte des risques — <?php echo e($selectedYear); ?><?php echo e($isPrediction ? ' 🔮' : ''); ?></h3></div>
    <div id="leaflet-map" style="height:310px;border-radius:0"></div>
  </div>
  <div class="card">
    <div class="ch"><div class="ci" style="background:#dbeafe">📈</div><h3>Évolution 2018–2027 <span style="font-size:.72rem;color:var(--mu)">— pointillés = projections</span></h3></div>
    <div class="cb"><canvas id="ch-ts" style="max-height:260px"></canvas></div>
  </div>
</div>


<div class="g2" style="margin-bottom:1.25rem">
  <div class="card">
    <div class="ch"><div class="ci" style="background:#ffedd5">📍</div><h3>Risque par localité — <?php echo e($selectedYear); ?><?php echo e($isPrediction ? ' 🔮' : ''); ?></h3></div>
    <div class="cb">
      <?php $__empty_1 = true; $__currentLoopData = $byPoint; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $pt): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); $__empty_1 = false; ?>
        <?php
          $r   = $pt['mean_risk'];
          $pct = min(100, round($r / 4 * 100));
          $c   = $pt['risk_color'];
          $bi  = $pt['risk_class'] >= 3 ? 'b3' : ($pt['risk_class'] >= 2 ? 'b2' : ($pt['risk_class'] >= 1 ? 'b1' : 'b0'));
        ?>
        <div style="margin-bottom:.9rem">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.28rem">
            <div style="display:flex;align-items:center;gap:.5rem">
              <span style="font-size:.85rem;font-weight:700"><?php echo e($pt['name']); ?></span>
              <span style="font-size:.71rem;color:var(--mu)">💧<?php echo e($pt['mean_precipitation']); ?>mm · 🌿<?php echo e($pt['mean_ndvi']); ?></span>
            </div>
            <span class="badge <?php echo e($bi); ?>" style="background:<?php echo e($c); ?>18;color:<?php echo e($c); ?>;border:1px solid <?php echo e($c); ?>44">
              <?php echo e($pt['risk_label']); ?> · <?php echo e(number_format($r,2)); ?>

            </span>
          </div>
          <div class="pb"><div class="pf" style="width:<?php echo e($pct); ?>%;background:<?php echo e($c); ?>"></div></div>
        </div>
      <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); if ($__empty_1): ?>
        <p style="color:var(--mu);text-align:center;padding:2rem">Aucune donnée pour <?php echo e($selectedYear); ?></p>
      <?php endif; ?>
    </div>
  </div>

  <div class="card">
    <div class="ch"><div class="ci" style="background:#fef9c3">📊</div><h3>Distribution des classes — <?php echo e($selectedYear); ?><?php echo e($isPrediction ? ' 🔮' : ''); ?></h3></div>
    <div class="cb" style="display:flex;align-items:center;gap:1.4rem">
      <canvas id="ch-dist" style="max-width:185px;max-height:185px;flex-shrink:0"></canvas>
      <div style="flex:1">
        <?php $__currentLoopData = $distribution; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $d): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
          <?php if($d['count'] > 0): ?>
          <div style="margin-bottom:.5rem">
            <div style="display:flex;justify-content:space-between;margin-bottom:.18rem">
              <div style="display:flex;align-items:center;gap:7px">
                <span style="width:8px;height:8px;border-radius:50%;background:<?php echo e($d['color']); ?>;display:inline-block"></span>
                <span style="font-size:.8rem;font-weight:600"><?php echo e($d['label']); ?></span>
              </div>
              <span style="font-size:.8rem;font-weight:700;color:<?php echo e($d['color']); ?>">
                <?php echo e($d['count']); ?> <span style="color:var(--mu);font-weight:400">(<?php echo e($d['pct']); ?>%)</span>
              </span>
            </div>
            <div class="pb"><div class="pf" style="width:<?php echo e($d['pct']); ?>%;background:<?php echo e($d['color']); ?>"></div></div>
          </div>
          <?php endif; ?>
        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
      </div>
    </div>
  </div>
</div>


<div class="card">
  <div class="ch"><div class="ci" style="background:#f0fdf4">📅</div><h3>Tendance 2018–2027 <span style="font-size:.72rem;color:#7c3aed">🔮 = projection</span></h3></div>
  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:.83rem">
      <thead>
        <tr style="background:#f8fafc">
          <?php $__currentLoopData = ['Année','Risque moyen','Précipitations','NDVI','Tendance','Type']; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $h): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
            <th style="padding:.65rem .9rem;text-align:left;font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--mu);border-bottom:2px solid var(--bd)"><?php echo e($h); ?></th>
          <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
        </tr>
      </thead>
      <tbody>
        <?php $prev = null; ?>
        <?php $__currentLoopData = $byYear; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $yr): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
          <?php
            $r      = $yr['mean_risk'];
            $arr    = $prev === null ? '—' : ($r > $prev + 0.02 ? '↑' : ($r < $prev - 0.02 ? '↓' : '→'));
            $ac     = $arr === '↑' ? '#dc2626' : ($arr === '↓' ? '#16a34a' : '#64748b');
            $bi     = $r >= 3 ? 'b3' : ($r >= 2 ? 'b2' : ($r >= 1 ? 'b1' : 'b0'));
            $pred   = $yr['predicted'];
            $prev   = $r;
          ?>
          <tr style="border-bottom:1px solid #f1f5f9;<?php echo e($pred ? 'background:#faf5ff' : ''); ?>">
            <td style="padding:.65rem .9rem;font-weight:800;color:<?php echo e($pred ? '#7c3aed' : 'inherit'); ?>"><?php echo e($pred ? '🔮 ' : ''); ?><?php echo e($yr['year']); ?></td>
            <td style="padding:.65rem .9rem"><span class="badge <?php echo e($bi); ?>"><?php echo e(number_format($r,3)); ?></span></td>
            <td style="padding:.65rem .9rem;font-family:var(--mo)"><?php echo e(number_format($yr['mean_precipitation'],1)); ?> mm</td>
            <td style="padding:.65rem .9rem;font-family:var(--mo)"><?php echo e(number_format($yr['mean_ndvi'],4)); ?></td>
            <td style="padding:.65rem .9rem;font-size:1.1rem;font-weight:800;color:<?php echo e($ac); ?>"><?php echo e($arr); ?></td>
            <td style="padding:.65rem .9rem">
              <?php if($pred): ?>
                <span style="background:#f3e8ff;color:#7c3aed;padding:.2rem .6rem;border-radius:12px;font-size:.72rem;font-weight:700">Projection</span>
              <?php else: ?>
                <span style="background:#f0fdf4;color:#16a34a;padding:.2rem .6rem;border-radius:12px;font-size:.72rem;font-weight:700">Historique</span>
              <?php endif; ?>
            </td>
          </tr>
        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
      </tbody>
    </table>
  </div>
</div>


<div class="card" style="margin-top:1rem">
  <div class="cb">
    <div style="font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--mu);margin-bottom:.7rem">📖 Légende — Classes de risque</div>
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:.6rem">
      <?php $__currentLoopData = [
        ['#22c55e','✅','Aucun','Conditions normales. Irrigation non requise.'],
        ['#eab308','⚠️','Faible','Tension hydrique légère. Surveillance.'],
        ['#f97316','🔶','Modéré','Déficit pluviométrique. Irrigation 72h.'],
        ['#ef4444','🚨','Sévère','Sol très sec. Risque perte récolte.'],
        ['#7c3aed','💀','Extrême','Sécheresse catastrophique.'],
      ]; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as [$col,$ic,$lbl,$desc]): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
        <div style="background:<?php echo e($col); ?>0d;border:1.5px solid <?php echo e($col); ?>33;border-radius:10px;padding:.7rem;text-align:center">
          <div style="font-size:1.4rem"><?php echo e($ic); ?></div>
          <div style="font-weight:800;color:<?php echo e($col); ?>;font-size:.85rem"><?php echo e($lbl); ?></div>
          <div style="font-size:.71rem;color:var(--mu);margin-top:.25rem;line-height:1.4"><?php echo e($desc); ?></div>
        </div>
      <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
    </div>
  </div>
</div>

<?php $__env->stopSection(); ?>
<?php $__env->startPush('scripts'); ?>
<script>

const geoFeatures  = <?php echo json_encode($geoJson['features'] ?? [], 15, 512) ?>;
const tsSeries     = <?php echo json_encode($timeseriesData ?? [], 15, 512) ?>;
const distData     = <?php echo json_encode($distribution ?? [], 15, 512) ?>;
const selYear      = <?php echo e($selectedYear); ?>;
const isProjection = <?php echo e($isPrediction ? 'true' : 'false'); ?>;

const leafletMap = L.map('leaflet-map').setView([16.8, -14.5], 7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap', maxZoom: 18
}).addTo(leafletMap);

geoFeatures.forEach(f => {
    const p = f.properties;
    const c = p.risk_color || '#22c55e';
    const r = Math.max(16, p.mean_risk * 22);
    L.circleMarker([f.geometry.coordinates[1], f.geometry.coordinates[0]], {
        radius: r, fillColor: c, color: '#fff', weight: 2.5, fillOpacity: 0.88
    }).addTo(leafletMap).bindPopup(
        `<div style="font-family:sans-serif;min-width:150px">
            <strong>${p.name}</strong>
            ${isProjection ? ' <span style="background:#f3e8ff;color:#7c3aed;padding:1px 6px;border-radius:8px;font-size:.72rem">🔮 Proj.</span>' : ''}
            <br><span style="color:${c};font-weight:800;font-size:1rem">${p.risk_label}</span>
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:.35rem 0">
            <div style="font-size:.77rem;line-height:1.8">
                📊 Risque: <b>${p.mean_risk}</b><br>
                💧 Précip.: <b>${p.mean_precipitation} mm</b><br>
                🌿 NDVI: <b>${p.mean_ndvi}</b>
            </div>
        </div>`
    );
});

const legend = L.control({position: 'bottomright'});
legend.onAdd = () => {
    const d = L.DomUtil.create('div');
    d.style.cssText = 'background:#fff;padding:8px 12px;border-radius:8px;font-size:.72rem;box-shadow:0 2px 8px rgba(0,0,0,.12)';
    d.innerHTML = '<b style="display:block;margin-bottom:4px">Risque</b>'
        + [['#22c55e','Aucun'],['#eab308','Faible'],['#f97316','Modéré'],['#ef4444','Sévère'],['#7c3aed','Extrême']]
          .map(([c,l]) => `<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px"><span style="width:8px;height:8px;border-radius:50%;background:${c};display:inline-block"></span>${l}</div>`)
          .join('');
    return d;
};
legend.addTo(leafletMap);

// ── Timeseries ────────────────────────────────────────────────────────────
const tsPoints = Object.keys(tsSeries);
const tsColors = ['#16a34a','#2563eb','#f97316','#dc2626','#7c3aed'];
const allDates = [...new Set(tsPoints.flatMap(p => tsSeries[p].map(s => s.date)))].sort();

const tsDatasets = tsPoints.flatMap((p, i) => {
    const col = tsColors[i % 5];
    return [
        {
            label: p,
            data: allDates.map(d => { const s = tsSeries[p]?.find(x => x.date === d); return (!s || s.predicted) ? null : s.value; }),
            borderColor: col, borderWidth: 2, pointRadius: 1.5,
            tension: 0.4, fill: false, spanGaps: true,
        },
        {
            label: p + '_proj',
            data: allDates.map(d => { const s = tsSeries[p]?.find(x => x.date === d); return (!s || !s.predicted) ? null : s.value; }),
            borderColor: col, borderWidth: 2, borderDash: [6, 3],
            pointRadius: 1, tension: 0.4, fill: false, spanGaps: true,
        }
    ];
});

new Chart(document.getElementById('ch-ts'), {
    type: 'line',
    data: { labels: allDates, datasets: tsDatasets },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: { font: { size: 10 }, boxWidth: 10, filter: item => !item.text.endsWith('_proj') }
            }
        },
        scales: {
            x: { ticks: { maxTicksLimit: 10, font: { size: 9 } }, grid: { color: '#f1f5f9' } },
            y: { min: 0, max: 3.5, ticks: { stepSize: 0.5, font: { size: 9 } }, grid: { color: '#f1f5f9' },
                 title: { display: true, text: 'Classe risque', font: { size: 9 } } }
        }
    }
});

// ── Doughnut ──────────────────────────────────────────────────────────────
const activeDist = distData.filter(d => d.count > 0);
new Chart(document.getElementById('ch-dist'), {
    type: 'doughnut',
    data: {
        labels: activeDist.map(d => d.label),
        datasets: [{ data: activeDist.map(d => d.count), backgroundColor: activeDist.map(d => d.color), borderWidth: 3, borderColor: '#fff' }]
    },
    options: { responsive: true, cutout: '62%', plugins: { legend: { display: false } } }
});
</script>
<?php $__env->stopPush(); ?>
<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH C:\Users\Mohame Lemine\Desktop\drought_yolo\drought_ai_laravel\resources\views/dashboard.blade.php ENDPATH**/ ?>