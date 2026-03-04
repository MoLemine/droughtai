@extends('layouts.app')
@section('title','Prédiction')
@section('content')

<div class="ph">
  <h1>🎯 Prédiction de sécheresse</h1>
  <p>Entrez les données climatiques d'une localité pour une prédiction instantanée</p>
</div>

<div class="g2">

  {{-- FORMULAIRE --}}
  <div>
    <div class="card">
      <div class="ch"><div class="ci" style="background:#f0fdf4">📋</div><h3>Données climatiques</h3></div>
      <div class="cb">

        @if($errors->any())
        <div class="alert a-err">⚠️<div>@foreach($errors->all() as $e)<div>{{ $e }}</div>@endforeach</div></div>
        @endif

        <form method="POST" action="{{ route('predict.post') }}" id="pform">
          @csrf
          <div class="g2">
            <div class="fg">
              <label class="lbl">📍 Localité</label>
              <select name="point" class="inp" required>
                @foreach(\App\Services\DroughtAiService::points() as $pt)
                <option value="{{ $pt }}" {{ old('point',$input['point']??'Rosso')===$pt?'selected':'' }}>{{ $pt }}</option>
                @endforeach
              </select>
            </div>
            <div class="fg">
              <label class="lbl">📅 Mois</label>
              <select name="month" class="inp" required>
                @foreach(['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre'] as $i=>$m)
                <option value="{{ $i+1 }}" {{ old('month',$input['month']??date('n'))==($i+1)?'selected':'' }}>{{ $m }}</option>
                @endforeach
              </select>
            </div>
          </div>
          <div class="fg">
            <label class="lbl">📆 Année</label>
            <select name="year" class="inp" required>
              @foreach(range(2018,date('Y')+1) as $y)
              <option value="{{ $y }}" {{ old('year',$input['year']??date('Y'))==$y?'selected':'' }}>{{ $y }}</option>
              @endforeach
            </select>
          </div>
          <div class="divider"></div>
          <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--mu);margin-bottom:.8rem">Variables climatiques</div>
          <div class="g2">
            <div class="fg">
              <label class="lbl">💧 Précipitations (mm)</label>
              <input type="number" name="precipitation" class="inp" step="0.1" min="0" max="500" required value="{{ old('precipitation',$input['precipitation']??'15') }}">
              <div class="hint">Saison sèche ≈ 0 · pluies ≈ 35–80 mm</div>
            </div>
            <div class="fg">
              <label class="lbl">🌡️ Température (°C)</label>
              <input type="number" name="temperature_c" class="inp" step="0.1" min="10" max="55" required value="{{ old('temperature_c',$input['temperature_c']??'32') }}">
              <div class="hint">Typique : 26–42 °C</div>
            </div>
            <div class="fg">
              <label class="lbl">💦 Humidité relative (%)</label>
              <input type="number" name="humidity" class="inp" step="0.1" min="0" max="100" required value="{{ old('humidity',$input['humidity']??'35') }}">
              <div class="hint">Sèche ≈ 15–25% · pluies ≈ 55–75%</div>
            </div>
            <div class="fg">
              <label class="lbl">🌍 Humidité sol (m³/m³)</label>
              <input type="number" name="soil_moisture" class="inp" step="0.001" min="0" max="1" required value="{{ old('soil_moisture',$input['soil_moisture']??'0.08') }}">
              <div class="hint">Sec ≈ 0.04 · normal ≈ 0.12–0.20</div>
            </div>
            <div class="fg">
              <label class="lbl">🌿 NDVI (végétation)</label>
              <input type="number" name="ndvi" class="inp" step="0.001" min="0" max="1" required value="{{ old('ndvi',$input['ndvi']??'0.10') }}">
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

  {{-- RÉSULTAT --}}
  <div>
    @if(isset($result) && $result)
    @php
      $rc=$result['risk_class']??0;
      $cls=\App\Services\DroughtAiService::riskClasses()[$rc]??['icon'=>'✅','fr'=>'Aucun','color'=>'#22c55e'];
      $conf=round(($result['confidence']??0)*100);
      $cc=$conf>=75?'#16a34a':($conf>=50?'#d97706':'#dc2626');
      $probas=$result['probabilities']??[];
      $rcols=['#22c55e','#eab308','#f97316','#ef4444','#7c3aed'];
    @endphp
    <div class="card" style="border-top:4px solid {{ $cls['color'] }}">
      <div class="ch">
        <div class="ci" style="background:{{ $cls['color'] }}22">🎯</div>
        <h3>Résultat de la prédiction</h3>
        <span class="badge" style="background:{{ $cls['color'] }}18;color:{{ $cls['color'] }}">{{ $result['model_used']??'GB' }} · {{ $result['processing_ms']??'?' }}ms</span>
      </div>
      <div class="cb">
        <div style="display:flex;align-items:center;gap:1.2rem;padding:1rem;background:{{ $cls['color'] }}0d;border-radius:12px;border:1.5px solid {{ $cls['color'] }}33;margin-bottom:1.2rem">
          <span style="font-size:2.8rem;line-height:1">{{ $cls['icon'] }}</span>
          <div style="flex:1">
            <div style="font-size:1.5rem;font-weight:800;color:{{ $cls['color'] }}">{{ $cls['fr'] }}</div>
            <div style="font-size:.77rem;color:var(--mu);margin-top:.1rem">
              {{ $result['input']['point']??'—' }} · {{ $result['input']['year']??'' }}/{{ sprintf('%02d',$result['input']['month']??0) }}
            </div>
          </div>
          <div style="text-align:center">
            <div style="font-family:var(--mo);font-size:1.8rem;font-weight:800;color:{{ $cc }}">{{ $conf }}%</div>
            <div style="font-size:.63rem;color:var(--mu)">confiance</div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.55rem;margin-bottom:1.1rem">
          @foreach([['Point',$result['input']['point']??'—'],['Classe',($rc).'/3'],['Modèle',ucwords(str_replace('_',' ',$result['model_used']??''))]] as [$l,$v])
          <div style="background:#f8fafc;border-radius:8px;padding:.55rem;text-align:center">
            <div style="font-size:.63rem;color:var(--mu);margin-bottom:.15rem;text-transform:uppercase">{{ $l }}</div>
            <div style="font-weight:700;font-size:.88rem">{{ $v }}</div>
          </div>
          @endforeach
        </div>

        @if($probas)
        <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--mu);margin-bottom:.55rem">Probabilités par classe</div>
        @foreach($probas as $lbl=>$p)
        @php $pct=round($p*100);$li=array_search($lbl,['Aucun','Faible','Modere','Severe','Extreme']);$col=$rcols[$li!==false?$li:0]; @endphp
        <div style="margin-bottom:.45rem">
          <div style="display:flex;justify-content:space-between;margin-bottom:.18rem;font-size:.77rem">
            <span>{{ $lbl }}</span><span style="font-family:var(--mo);font-weight:600">{{ $pct }}%</span>
          </div>
          <div class="pb"><div class="pf" style="width:{{ $pct }}%;background:{{ $col }}"></div></div>
        </div>
        @endforeach
        @endif

        <div style="margin-top:1.1rem">
          <a href="{{ route('analysis') }}" class="btn btn-o btn-w">📷 Analyser une photo de cette zone →</a>
        </div>
      </div>
    </div>
    @else
    <div class="card" style="display:flex;align-items:center;justify-content:center;min-height:400px">
      <div style="text-align:center;padding:2rem">
        <div style="font-size:4rem;margin-bottom:1rem">🌾</div>
        <div style="font-size:1.05rem;font-weight:700;margin-bottom:.4rem">Prêt à analyser</div>
        <div style="font-size:.83rem;color:var(--mu);max-width:230px;margin:0 auto;line-height:1.6">Remplissez le formulaire et cliquez sur <strong>Lancer la prédiction</strong></div>
        <div style="margin-top:1.4rem;display:inline-flex;flex-direction:column;gap:.4rem;text-align:left">
          @foreach([['#22c55e','✅','Aucun — Conditions normales'],['#eab308','⚠️','Faible — Surveillance conseillée'],['#f97316','🔶','Modéré — Irrigation requise'],['#ef4444','🚨','Sévère — Action urgente']] as [$c,$ic,$d])
          <div style="display:flex;align-items:center;gap:7px;font-size:.78rem">
            <span>{{ $ic }}</span><span style="color:{{ $c }};font-weight:600">{{ $d }}</span>
          </div>
          @endforeach
        </div>
      </div>
    </div>
    @endif
  </div>

</div>
@endsection
@push('scripts')
<script>
document.getElementById('pform').addEventListener('submit',function(){
  const b=document.getElementById('sbtn');b.innerHTML='⏳ Analyse en cours...';b.disabled=true;
});
</script>
@endpush
