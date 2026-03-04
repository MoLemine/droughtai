<?php $__env->startSection('title','Tableau de Bord'); ?>
<?php $__env->startSection('content'); ?>

<div class="ph">
  <h1>📊 Tableau de bord</h1>
  <p>Sécheresse agricole — Mauritanie & Vallée du Fleuve Sénégal · 2018–2023</p>
</div>

<?php if(!$online): ?>
<div class="offline">⚠️ <div><strong>API Flask hors ligne.</strong> Lancez <code style="background:#fee2e2;padding:1px 5px;border-radius:3px">python api\app.py</code> sur 192.168.100.37:5000</div></div>
<?php endif; ?>

<div class="g4" style="margin-bottom:1.25rem">
  <div class="stat" style="--c:#15803d"><div class="sl">Risque moyen</div><div class="sv"><?php echo e(number_format($globalStats['mean_risk']??0.91,2)); ?></div><div class="ss">Classes 0–3 · 2018–2023</div></div>
  <div class="stat" style="--c:#ea580c"><div class="sl">Modéré+</div><div class="sv"><?php echo e($globalStats['pct_moderate']??24); ?><span style="font-size:1.1rem">%</span></div><div class="ss">Observations ≥ classe 2</div></div>
  <div class="stat" style="--c:#dc2626"><div class="sl">Sévère</div><div class="sv"><?php echo e($globalStats['pct_severe']??2); ?><span style="font-size:1.1rem">%</span></div><div class="ss">Observations ≥ classe 3</div></div>
  <div class="stat" style="--c:#2563eb"><div class="sl">Observations</div><div class="sv"><?php echo e($globalStats['total']??355); ?></div><div class="ss">5 points GPS · 6 ans</div></div>
</div>

<div class="g2" style="margin-bottom:1.25rem">
  <div class="card">
    <div class="ch"><div class="ci" style="background:#dcfce7">🗺️</div><h3>Carte des risques — 2023</h3></div>
    <div id="lmap" style="height:300px;border-radius:0"></div>
  </div>
  <div class="card">
    <div class="ch"><div class="ci" style="background:#dbeafe">📈</div><h3>Évolution du risque par localité</h3></div>
    <div class="cb"><canvas id="ch-ts" style="max-height:255px"></canvas></div>
  </div>
</div>

<div class="g2" style="margin-bottom:1.25rem">
  <div class="card">
    <div class="ch"><div class="ci" style="background:#ffedd5">📍</div><h3>Risque moyen par localité</h3></div>
    <div class="cb">
      <?php $__empty_1 = true; $__currentLoopData = $byPoint; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $pt): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); $__empty_1 = false; ?>
      <?php $r=$pt['mean_risk']??0;$pct=min(100,round($r/3*100));$c=$r>=2?'#dc2626':($r>=1.2?'#ea580c':($r>=0.7?'#d97706':'#15803d'));$bi=$r>=2?'b3':($r>=1.2?'b2':($r>=0.7?'b1':'b0')); ?>
      <div style="margin-bottom:.85rem">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.28rem">
          <span style="font-size:.85rem;font-weight:600"><?php echo e($pt['name']??''); ?></span>
          <span class="badge <?php echo e($bi); ?>"><?php echo e(number_format($r,2)); ?></span>
        </div>
        <div class="pb"><div class="pf" style="width:<?php echo e($pct); ?>%;background:<?php echo e($c); ?>"></div></div>
      </div>
      <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); if ($__empty_1): ?>
      <p style="color:var(--mu);text-align:center;padding:2rem 0;font-size:.85rem">API hors ligne — données indisponibles</p>
      <?php endif; ?>
    </div>
  </div>

  <div class="card">
    <div class="ch"><div class="ci" style="background:#fef9c3">📊</div><h3>Distribution des classes</h3></div>
    <div class="cb" style="display:flex;align-items:center;gap:1.4rem">
      <canvas id="ch-dist" style="max-width:185px;max-height:185px;flex-shrink:0"></canvas>
      <div style="flex:1">
        <?php $rc=['#22c55e','#eab308','#f97316','#ef4444','#7c3aed'] ?>
        <?php $__currentLoopData = $distribution; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $i=>$d): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">
          <div style="display:flex;align-items:center;gap:7px">
            <span style="width:8px;height:8px;border-radius:50%;background:<?php echo e($rc[$i]??'#ccc'); ?>;display:inline-block;flex-shrink:0"></span>
            <span style="font-size:.81rem"><?php echo e($d['label']); ?></span>
          </div>
          <span style="font-family:var(--mo);font-weight:700;font-size:.81rem"><?php echo e($d['count']); ?></span>
        </div>
        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
      </div>
    </div>
  </div>
</div>

<div class="card">
  <div class="ch"><div class="ci" style="background:#f0fdf4">📅</div><h3>Tendance annuelle 2018–2023</h3></div>
  <table style="width:100%;border-collapse:collapse;font-size:.83rem">
    <thead><tr style="background:#f8fafc">
      <th style="padding:.65rem .9rem;text-align:left;font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--mu);border-bottom:2px solid var(--bd)">Année</th>
      <th style="padding:.65rem .9rem;text-align:left;font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--mu);border-bottom:2px solid var(--bd)">Risque moyen</th>
      <th style="padding:.65rem .9rem;text-align:left;font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--mu);border-bottom:2px solid var(--bd)">Précipitations</th>
      <th style="padding:.65rem .9rem;text-align:left;font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--mu);border-bottom:2px solid var(--bd)">NDVI</th>
      <th style="padding:.65rem .9rem;text-align:left;font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--mu);border-bottom:2px solid var(--bd)">Tendance</th>
    </tr></thead>
    <tbody>
      <?php $prev=null ?>
      <?php $__currentLoopData = $byYear; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $yr): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
      <?php $r=$yr['mean_risk']??0;$a=$prev===null?'—':($r>$prev?'↑':($r<$prev?'↓':'→'));$ac=$a==='↑'?'#dc2626':($a==='↓'?'#16a34a':'#64748b');$prev=$r;$bi=$r>=2?'b3':($r>=1.2?'b2':($r>=0.7?'b1':'b0')); ?>
      <tr>
        <td style="padding:.65rem .9rem;border-bottom:1px solid #f1f5f9;font-weight:700"><?php echo e($yr['year']); ?></td>
        <td style="padding:.65rem .9rem;border-bottom:1px solid #f1f5f9"><span class="badge <?php echo e($bi); ?>"><?php echo e(number_format($r,3)); ?></span></td>
        <td style="padding:.65rem .9rem;border-bottom:1px solid #f1f5f9;font-family:var(--mo)"><?php echo e(number_format($yr['mean_precipitation']??0,1)); ?> mm</td>
        <td style="padding:.65rem .9rem;border-bottom:1px solid #f1f5f9;font-family:var(--mo)"><?php echo e(number_format($yr['mean_ndvi']??0,4)); ?></td>
        <td style="padding:.65rem .9rem;border-bottom:1px solid #f1f5f9;font-size:1.2rem;font-weight:800;color:<?php echo e($ac); ?>"><?php echo e($a); ?></td>
      </tr>
      <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
    </tbody>
  </table>
</div>

<?php $__env->stopSection(); ?>
<?php $__env->startPush('scripts'); ?>
<script>
const features=<?php echo json_encode($map['features']??[], 15, 512) ?>;
const map=L.map('lmap').setView([16.8,-14.5],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap',maxZoom:18}).addTo(map);
features.forEach(f=>{
  const p=f.properties,c=p.risk_color||'#22c55e',r=Math.max(14,p.mean_risk*20);
  L.circleMarker([f.geometry.coordinates[1],f.geometry.coordinates[0]],{radius:r,fillColor:c,color:'#fff',weight:2.5,fillOpacity:.88})
   .addTo(map).bindPopup(`<div style="font-family:'Plus Jakarta Sans',sans-serif;min-width:145px"><strong>${p.name}</strong><br><span style="color:${c};font-weight:700">${p.risk_label||'—'}</span><hr style="border:none;border-top:1px solid #e2e8f0;margin:.35rem 0"><div style="font-size:.77rem;line-height:1.7">Risque: <b>${p.mean_risk}</b><br>Précip.: <b>${p.mean_precipitation} mm</b><br>NDVI: <b>${p.mean_ndvi}</b></div></div>`);
});
const leg=L.control({position:'bottomright'});leg.onAdd=()=>{const d=L.DomUtil.create('div');d.style.cssText='background:#fff;padding:7px 11px;border-radius:8px;font-size:.71rem;box-shadow:0 2px 8px rgba(0,0,0,.1)';d.innerHTML='<b style="display:block;margin-bottom:4px">Risque</b>'+[['#22c55e','Aucun'],['#eab308','Faible'],['#f97316','Modéré'],['#ef4444','Sévère']].map(([c,l])=>`<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px"><span style="width:8px;height:8px;border-radius:50%;background:${c};display:inline-block"></span>${l}</div>`).join('');return d;};leg.addTo(map);

const ts=<?php echo json_encode($timeseriesData??[], 15, 512) ?>,pts=Object.keys(ts),cols=['#16a34a','#2563eb','#f97316','#dc2626','#7c3aed'];
const dates=[...new Set(pts.flatMap(p=>ts[p].map(s=>s.date)))].sort();
new Chart(document.getElementById('ch-ts'),{type:'line',data:{labels:dates,datasets:pts.map((p,i)=>({label:p,data:dates.map(d=>{const s=ts[p]?.find(x=>x.date===d);return s?s.value:null;}),borderColor:cols[i%5],backgroundColor:cols[i%5]+'18',borderWidth:2,pointRadius:1.5,tension:.4,fill:false,spanGaps:true}))},options:{responsive:true,plugins:{legend:{position:'bottom',labels:{font:{size:10},boxWidth:10}}},scales:{x:{ticks:{maxTicksLimit:7,font:{size:9}},grid:{color:'#f1f5f9'}},y:{min:0,max:3.2,ticks:{stepSize:.5,font:{size:9}},grid:{color:'#f1f5f9'},title:{display:true,text:'Classe risque',font:{size:9}}}}}});

const dist=<?php echo json_encode($distribution??[], 15, 512) ?>;
new Chart(document.getElementById('ch-dist'),{type:'doughnut',data:{labels:dist.map(d=>d.label),datasets:[{data:dist.map(d=>d.count),backgroundColor:['#22c55e','#eab308','#f97316','#ef4444','#7c3aed'],borderWidth:2,borderColor:'#fff'}]},options:{responsive:true,cutout:'62%',plugins:{legend:{display:false}}}});
</script>
<?php $__env->stopPush(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH C:\Users\Mohame Lemine\Desktop\drought_yolo\drought_ai_laravel\resources\views/dashboard/index.blade.php ENDPATH**/ ?>