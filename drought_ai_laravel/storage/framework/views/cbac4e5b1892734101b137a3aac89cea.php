<?php $__env->startSection('title','Prédiction'); ?>
<?php $__env->startSection('content'); ?>

<div class="ph">
  <h1>🎯 Prédiction de sécheresse</h1>
  <p>Entrez les données climatiques d'une localité pour une prédiction instantanée</p>
</div>

<div class="g2">

  
  <div>
    <div class="card">
      <div class="ch"><div class="ci" style="background:#f0fdf4">📋</div><h3>Données climatiques</h3></div>
      <div class="cb">

        <?php if($errors->any()): ?>
        <div class="alert a-err">⚠️<div><?php $__currentLoopData = $errors->all(); $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $e): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?><div><?php echo e($e); ?></div><?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?></div></div>
        <?php endif; ?>

        <form method="POST" action="<?php echo e(route('predict.post')); ?>" id="pform">
          <?php echo csrf_field(); ?>
          <div class="g2">
            <div class="fg">
              <label class="lbl">📍 Localité</label>
              <select name="point" class="inp" required>
                <?php $__currentLoopData = \App\Services\DroughtAiService::points(); $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $pt): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                <option value="<?php echo e($pt); ?>" <?php echo e(old('point',$input['point']??'Rosso')===$pt?'selected':''); ?>><?php echo e($pt); ?></option>
                <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
              </select>
            </div>
            <div class="fg">
              <label class="lbl">📅 Mois</label>
              <select name="month" class="inp" required>
                <?php $__currentLoopData = ['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre']; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $i=>$m): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                <option value="<?php echo e($i+1); ?>" <?php echo e(old('month',$input['month']??date('n'))==($i+1)?'selected':''); ?>><?php echo e($m); ?></option>
                <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
              </select>
            </div>
          </div>
          <div class="fg">
            <label class="lbl">📆 Année</label>
            <select name="year" class="inp" required>
              <?php $__currentLoopData = range(2018,date('Y')+1); $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $y): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
              <option value="<?php echo e($y); ?>" <?php echo e(old('year',$input['year']??date('Y'))==$y?'selected':''); ?>><?php echo e($y); ?></option>
              <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
            </select>
          </div>
          <div class="divider"></div>
          <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--mu);margin-bottom:.8rem">Variables climatiques</div>
          <div class="g2">
            <div class="fg">
              <label class="lbl">💧 Précipitations (mm)</label>
              <input type="number" name="precipitation" class="inp" step="0.1" min="0" max="500" required value="<?php echo e(old('precipitation',$input['precipitation']??'15')); ?>">
              <div class="hint">Saison sèche ≈ 0 · pluies ≈ 35–80 mm</div>
            </div>
            <div class="fg">
              <label class="lbl">🌡️ Température (°C)</label>
              <input type="number" name="temperature_c" class="inp" step="0.1" min="10" max="55" required value="<?php echo e(old('temperature_c',$input['temperature_c']??'32')); ?>">
              <div class="hint">Typique : 26–42 °C</div>
            </div>
            <div class="fg">
              <label class="lbl">💦 Humidité relative (%)</label>
              <input type="number" name="humidity" class="inp" step="0.1" min="0" max="100" required value="<?php echo e(old('humidity',$input['humidity']??'35')); ?>">
              <div class="hint">Sèche ≈ 15–25% · pluies ≈ 55–75%</div>
            </div>
            <div class="fg">
              <label class="lbl">🌍 Humidité sol (m³/m³)</label>
              <input type="number" name="soil_moisture" class="inp" step="0.001" min="0" max="1" required value="<?php echo e(old('soil_moisture',$input['soil_moisture']??'0.08')); ?>">
              <div class="hint">Sec ≈ 0.04 · normal ≈ 0.12–0.20</div>
            </div>
            <div class="fg">
              <label class="lbl">🌿 NDVI (végétation)</label>
              <input type="number" name="ndvi" class="inp" step="0.001" min="0" max="1" required value="<?php echo e(old('ndvi',$input['ndvi']??'0.10')); ?>">
              <div class="hint">Nu ≈ 0.07 · vert dense ≈ 0.22–0.28</div>
            </div>
            <div style="display:flex;align-items:flex-end;padding-bottom:1rem">
              <div style="background:#f8fafc;border:1px solid var(--bd);border-radius:9px;padding:.7rem;font-size:.73rem;color:var(--mu);line-height:1.7;width:100%">
                📌 <strong>Rappel</strong><br>
                Saison sèche → NDVI bas, précip=0<br>
                Saison pluies → NDVI élevé, précip>30
              </div>
            </div>
          </div>
          <button type="submit" class="btn btn-g btn-w btn-lg" id="sbtn">🎯 Lancer la prédiction</button>
        </form>
      </div>
    </div>
  </div>

  
  <div>
    <?php if(isset($result) && $result): ?>
    <?php
      $rc=$result['risk_class']??0;
      $cls=\App\Services\DroughtAiService::riskClasses()[$rc]??['icon'=>'✅','fr'=>'Aucun','color'=>'#22c55e'];
      $conf=round(($result['confidence']??0)*100);
      $cc=$conf>=75?'#16a34a':($conf>=50?'#d97706':'#dc2626');
      $probas=$result['probabilities']??[];
      $rcols=['#22c55e','#eab308','#f97316','#ef4444','#7c3aed'];
    ?>
    <div class="card" style="border-top:4px solid <?php echo e($cls['color']); ?>">
      <div class="ch">
        <div class="ci" style="background:<?php echo e($cls['color']); ?>22">🎯</div>
        <h3>Résultat de la prédiction</h3>
        <span class="badge" style="background:<?php echo e($cls['color']); ?>18;color:<?php echo e($cls['color']); ?>"><?php echo e($result['model_used']??'GB'); ?> · <?php echo e($result['processing_ms']??'?'); ?>ms</span>
      </div>
      <div class="cb">
        <div style="display:flex;align-items:center;gap:1.2rem;padding:1rem;background:<?php echo e($cls['color']); ?>0d;border-radius:12px;border:1.5px solid <?php echo e($cls['color']); ?>33;margin-bottom:1.2rem">
          <span style="font-size:2.8rem;line-height:1"><?php echo e($cls['icon']); ?></span>
          <div style="flex:1">
            <div style="font-size:1.5rem;font-weight:800;color:<?php echo e($cls['color']); ?>"><?php echo e($cls['fr']); ?></div>
            <div style="font-size:.77rem;color:var(--mu);margin-top:.1rem">
              <?php echo e($result['input']['point']??'—'); ?> · <?php echo e($result['input']['year']??''); ?>/<?php echo e(sprintf('%02d',$result['input']['month']??0)); ?>

            </div>
          </div>
          <div style="text-align:center">
            <div style="font-family:var(--mo);font-size:1.8rem;font-weight:800;color:<?php echo e($cc); ?>"><?php echo e($conf); ?>%</div>
            <div style="font-size:.63rem;color:var(--mu)">confiance</div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.55rem;margin-bottom:1.1rem">
          <?php $__currentLoopData = [['Point',$result['input']['point']??'—'],['Classe',($rc).'/3'],['Modèle',ucwords(str_replace('_',' ',$result['model_used']??''))]]; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as [$l,$v]): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
          <div style="background:#f8fafc;border-radius:8px;padding:.55rem;text-align:center">
            <div style="font-size:.63rem;color:var(--mu);margin-bottom:.15rem;text-transform:uppercase"><?php echo e($l); ?></div>
            <div style="font-weight:700;font-size:.88rem"><?php echo e($v); ?></div>
          </div>
          <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
        </div>

        <?php if($probas): ?>
        <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--mu);margin-bottom:.55rem">Probabilités par classe</div>
        <?php $__currentLoopData = $probas; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $lbl=>$p): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
        <?php $pct=round($p*100);$li=array_search($lbl,['Aucun','Faible','Modere','Severe','Extreme']);$col=$rcols[$li!==false?$li:0]; ?>
        <div style="margin-bottom:.45rem">
          <div style="display:flex;justify-content:space-between;margin-bottom:.18rem;font-size:.77rem">
            <span><?php echo e($lbl); ?></span><span style="font-family:var(--mo);font-weight:600"><?php echo e($pct); ?>%</span>
          </div>
          <div class="pb"><div class="pf" style="width:<?php echo e($pct); ?>%;background:<?php echo e($col); ?>"></div></div>
        </div>
        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
        <?php endif; ?>

        <div style="margin-top:1.1rem">
          <a href="<?php echo e(route('analysis')); ?>" class="btn btn-o btn-w">📷 Analyser une photo de cette zone →</a>
        </div>
      </div>
    </div>
    <?php else: ?>
    <div class="card" style="display:flex;align-items:center;justify-content:center;min-height:400px">
      <div style="text-align:center;padding:2rem">
        <div style="font-size:4rem;margin-bottom:1rem">🌾</div>
        <div style="font-size:1.05rem;font-weight:700;margin-bottom:.4rem">Prêt à analyser</div>
        <div style="font-size:.83rem;color:var(--mu);max-width:230px;margin:0 auto;line-height:1.6">Remplissez le formulaire et cliquez sur <strong>Lancer la prédiction</strong></div>
        <div style="margin-top:1.4rem;display:inline-flex;flex-direction:column;gap:.4rem;text-align:left">
          <?php $__currentLoopData = [['#22c55e','✅','Aucun — Conditions normales'],['#eab308','⚠️','Faible — Surveillance conseillée'],['#f97316','🔶','Modéré — Irrigation requise'],['#ef4444','🚨','Sévère — Action urgente']]; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as [$c,$ic,$d]): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
          <div style="display:flex;align-items:center;gap:7px;font-size:.78rem">
            <span><?php echo e($ic); ?></span><span style="color:<?php echo e($c); ?>;font-weight:600"><?php echo e($d); ?></span>
          </div>
          <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
        </div>
      </div>
    </div>
    <?php endif; ?>
  </div>

</div>
<?php $__env->stopSection(); ?>
<?php $__env->startPush('scripts'); ?>
<script>
document.getElementById('pform').addEventListener('submit',function(){
  const b=document.getElementById('sbtn');b.innerHTML='⏳ Analyse en cours...';b.disabled=true;
});
</script>
<?php $__env->stopPush(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH C:\Users\Mohame Lemine\Desktop\drought_yolo\drought_ai_laravel\resources\views/predict/index.blade.php ENDPATH**/ ?>