@extends('layouts.app')
@section('title','Résultat Analyse')
@section('content')
@php
  $ti=$types[$type]??['label'=>'Analyse','icon'=>'🔍'];
  $urgence=$result['urgence']??$result['urgence_globale']??'Moyenne';
  $uc=['Faible'=>'#15803d','Moyenne'=>'#d97706','Élevée'=>'#ea580c','Critique'=>'#dc2626'][$urgence]??'#64748b';
  $demo=$result['demo']??false;
  $isFull=$type==='full';
  $rcols=['#22c55e','#eab308','#f97316','#ef4444','#7c3aed'];
@endphp

<div style="display:flex;align-items:center;flex-wrap:wrap;gap:.75rem;margin-bottom:1.6rem">
  <div>
    <h1 style="font-size:1.65rem;font-weight:800;letter-spacing:-.5px">{{ $ti['icon'] }} {{ $ti['label'] }}</h1>
    <p style="font-size:.875rem;color:var(--mu);margin-top:3px">Analyse IA · {{ now()->format('d/m/Y à H:i') }}</p>
  </div>
  <div style="margin-left:auto;display:flex;gap:.55rem;align-items:center;flex-wrap:wrap">
    @if($demo)
    <span class="badge" style="background:#fffbeb;color:#92400e;border:1px solid #fde68a">🎭 Démonstration</span>
    @else
    <span class="badge" style="background:#dcfce7;color:#14532d;border:1px solid #bbf7d0">✅ Analyse réelle</span>
    @endif
    <span class="badge" style="background:{{ $uc }}18;color:{{ $uc }};border:1px solid {{ $uc }}33">Urgence : {{ $urgence }}</span>
    <a href="{{ route('analysis') }}" class="btn btn-o" style="padding:.42rem .9rem;font-size:.8rem">← Nouvelle analyse</a>
  </div>
</div>

@if($demo)
<div class="alert a-demo" style="margin-bottom:1.2rem">🎭 <div><strong>Résultat de démonstration.</strong> {{ $result['note']??'Ajoutez CLAUDE_API_KEY dans .env pour analyser vos vraies photos.' }}</div></div>
@endif

@if(!$result['success'])
  <div class="alert a-err">⚠️ {{ $result['error']??'Erreur lors de l\'analyse.' }}</div>
  <a href="{{ route('analysis') }}" class="btn btn-g">← Réessayer</a>
@else

<div class="g2" style="margin-bottom:1.2rem">

  {{-- GAUCHE : image + résumé --}}
  <div style="display:flex;flex-direction:column;gap:1.2rem">

    @if($isImage && $url)
    <div class="card">
      <div class="ch"><div class="ci" style="background:#eff6ff">🖼️</div><h3>Image analysée</h3></div>
      <img src="{{ $url }}" alt="Image analysée" style="width:100%;max-height:300px;object-fit:cover;display:block">
    </div>
    @elseif(!$isImage && $url)
    <div class="card">
      <div class="ch"><div class="ci" style="background:#eff6ff">🎥</div><h3>Vidéo analysée</h3></div>
      <video src="{{ $url }}" controls style="width:100%;max-height:250px;display:block"></video>
    </div>
    @endif

    <div class="card">
      <div class="ch"><div class="ci" style="background:{{ $uc }}18">📋</div><h3>Diagnostic principal</h3></div>
      <div class="cb">
        @php $resume=$result['resume_global']??$result['resume']??'Analyse terminée.' @endphp
        <div style="font-size:.92rem;line-height:1.65;padding:.9rem;background:#f8fafc;border-radius:10px;border-left:4px solid {{ $uc }};margin-bottom:1rem">
          {{ $resume }}
        </div>
        @if($isFull && isset($result['score_sante']))
        @php $s=$result['score_sante'];$sc=$s>=70?'#16a34a':($s>=45?'#d97706':'#dc2626');$sl=$s>=70?'Bon':($s>=45?'Moyen':'Mauvais') @endphp
        <div style="display:flex;align-items:center;gap:.9rem;margin-bottom:.9rem">
          <div class="sring" style="border-color:{{ $sc }};background:{{ $sc }}10;color:{{ $sc }}">
            <span class="snum">{{ $s }}</span><span class="smax">/100</span>
          </div>
          <div>
            <div style="font-weight:700">Santé parcelle : {{ $sl }}</div>
            <div style="font-size:.77rem;color:var(--mu)">Score global de santé</div>
          </div>
        </div>
        @endif
        @if(isset($result['alerte']))
        <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:.65rem;font-size:.81rem;color:#9a3412">
          ⚡ <strong>Alerte :</strong> {{ $result['alerte'] }}
        </div>
        @endif
      </div>
    </div>
  </div>

  {{-- DROITE : indicateurs + actions --}}
  <div style="display:flex;flex-direction:column;gap:1.2rem">

    @if($isFull)
    <div class="card">
      <div class="ch"><div class="ci" style="background:#f0fdf4">📊</div><h3>Les 4 indicateurs</h3></div>
      <div class="cb">
        @php
          $inds=[
            ['key'=>'gaspillage_eau',   'ico'=>'💧','lbl'=>"Gaspillage d'eau",    'vk'=>'niveau','dk'=>'detecte'],
            ['key'=>'stress_hydrique',  'ico'=>'🌿','lbl'=>'Stress hydrique',      'vk'=>'niveau','dk'=>'detecte'],
            ['key'=>'risque_secheresse','ico'=>'☀️','lbl'=>'Risque sécheresse',    'vk'=>'label', 'dk'=>null],
            ['key'=>'anomalies_plantes','ico'=>'🔬','lbl'=>'Anomalies / carences', 'vk'=>'type',  'dk'=>'detectee'],
          ];
          $lc=['Aucun'=>'#22c55e','Léger'=>'#22c55e','Faible'=>'#22c55e','Modéré'=>'#f97316','Sévère'=>'#dc2626','Critique'=>'#dc2626','Élevé'=>'#dc2626','Extrême'=>'#dc2626'];
        @endphp
        @foreach($inds as $ind)
        @php
          $d=$result[$ind['key']]??[];$score=$d['score']??0;
          $lbl=$d[$ind['vk']]??'—';
          $det=$ind['dk']?($d[$ind['dk']]??false):true;
          $lcolor=$det?($lc[$lbl]??'#f97316'):'#22c55e';
        @endphp
        <div style="display:flex;gap:9px;align-items:flex-start;margin-bottom:.85rem;padding:.75rem;background:#f8fafc;border-radius:10px">
          <span style="font-size:1.3rem;flex-shrink:0;line-height:1;margin-top:.1rem">{{ $ind['ico'] }}</span>
          <div style="flex:1;min-width:0">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.22rem">
              <span style="font-size:.84rem;font-weight:700">{{ $ind['lbl'] }}</span>
              <span style="font-size:.74rem;font-family:var(--mo);font-weight:700;color:{{ $lcolor }}">{{ $lbl }}</span>
            </div>
            <div class="pb"><div class="pf" style="width:{{ min(100,$score) }}%;background:{{ $lcolor }}"></div></div>
            @if(!empty($d['details']))<div style="font-size:.7rem;color:var(--mu);margin-top:.22rem">{{ $d['details'] }}</div>@endif
          </div>
        </div>
        @endforeach
      </div>
    </div>
    @else
    <div class="card">
      <div class="ch"><div class="ci" style="background:{{ $uc }}18">{{ $ti['icon'] }}</div><h3>Détails</h3></div>
      <div class="cb">
        @php $score=$result['score']??$result['score_risque']??$result['score_stress']??$result['score_anomalie']??0;$sc=$score>=70?'#dc2626':($score>=40?'#f97316':'#22c55e') @endphp
        <div style="display:flex;align-items:center;gap:.9rem;margin-bottom:1rem">
          <div class="sring" style="border-color:{{ $sc }};background:{{ $sc }}10;color:{{ $sc }}">
            <span class="snum">{{ $score }}</span><span class="smax">/100</span>
          </div>
          <div>
            @php
              $mainLabel = null;
              foreach(['niveau','label','type_anomalie','classe_risque'] as $kk) {
                if(isset($result[$kk])) { $mainLabel = $result[$kk]; break; }
              }
            @endphp
            @if($mainLabel)
            <div style="font-size:1.05rem;font-weight:800">{{ $mainLabel }}</div>
            @endif
            <div style="font-size:.77rem;color:var(--mu)">Urgence : <strong style="color:{{ $uc }}">{{ $urgence }}</strong></div>
          </div>
        </div>
        @foreach(['zones','symptomes','carences_suspectees','indicateurs_negatifs','indicateurs_positifs'] as $lk)
        @if(!empty($result[$lk]))
        <div style="margin-bottom:.75rem">
          <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--mu);margin-bottom:.35rem;letter-spacing:.5px">{{ ucfirst(str_replace('_',' ',$lk)) }}</div>
          <ul class="acts">@foreach($result[$lk] as $item)<li>{{ $item }}</li>@endforeach</ul>
        </div>
        @endif
        @endforeach
      </div>
    </div>
    @endif

    @php
      $imm=$result['actions_immediates']??$result['recommandations']??$result['actions']??$result['traitements']??[];
      $prv=$result['actions_preventives']??[];
    @endphp
    @if(count($imm)||count($prv))
    <div class="card">
      <div class="ch"><div class="ci" style="background:#fee2e2">⚡</div><h3>Actions recommandées</h3></div>
      <div class="cb">
        @if(count($imm))
        <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--r);margin-bottom:.4rem;letter-spacing:.5px">Immédiates</div>
        <ul class="acts" style="margin-bottom:.9rem">@foreach($imm as $a)<li>{{ $a }}</li>@endforeach</ul>
        @endif
        @if(count($prv))
        <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;color:var(--g);margin-bottom:.4rem;letter-spacing:.5px">Préventives</div>
        <ul class="acts">@foreach($prv as $a)<li>{{ $a }}</li>@endforeach</ul>
        @endif
      </div>
    </div>
    @endif

  </div>
</div>

<div style="display:flex;gap:.7rem;flex-wrap:wrap">
  <a href="{{ route('analysis') }}"  class="btn btn-g">📷 Nouvelle analyse</a>
  <a href="{{ route('predict') }}"   class="btn btn-o">🎯 Prédiction climatique</a>
  <a href="{{ route('dashboard') }}" class="btn btn-o">📊 Tableau de bord</a>
</div>

@endif
@endsection
