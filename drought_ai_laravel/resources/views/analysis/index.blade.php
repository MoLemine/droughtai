@extends('layouts.app')
@section('title','Analyse Photo & Vidéo')
@section('content')

<div class="ph">
  <h1>📷 Analyse Photo & Vidéo</h1>
  <p>Uploadez une image ou vidéo de terrain pour une analyse IA instantanée sur 4 indicateurs</p>
</div>

<div class="g2">

  {{-- UPLOAD --}}
  <div>
    <div class="card">
      <div class="ch"><div class="ci" style="background:#eff6ff">📤</div><h3>Uploader un fichier</h3></div>
      <div class="cb">

        @if($errors->any())
        <div class="alert a-err">⚠️<div>@foreach($errors->all() as $e)<div>{{ $e }}</div>@endforeach</div></div>
        @endif

        <form method="POST" action="{{ route('analysis.post') }}" enctype="multipart/form-data" id="aform">
          @csrf

          {{-- TYPE PICKER --}}
          <div class="fg">
            <div class="lbl" style="margin-bottom:.55rem">🔍 Que voulez-vous détecter ?</div>
            <div class="tpicker">
              @foreach($types as $key=>$t)
              <label class="tp {{ $key==='full'?'picked':'' }}" onclick="pickType(this)">
                <input type="radio" name="type" value="{{ $key }}" {{ $key==='full'?'checked':'' }}>
                <span class="tp-i">{{ $t['icon'] }}</span>
                <span class="tp-l">{{ $t['label'] }}</span>
              </label>
              @endforeach
            </div>
          </div>

          {{-- DROP ZONE --}}
          <div class="dz" id="dz">
            <input type="file" name="file" id="finp" accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/quicktime,video/webm" required>
            <span class="dz-icon" id="dz-ico">📁</span>
            <div class="dz-title" id="dz-ttl">Glissez-déposez ou cliquez ici</div>
            <div class="dz-sub">📸 JPG, PNG, WebP &nbsp;·&nbsp; 🎥 MP4, MOV &nbsp;·&nbsp; Max 50 MB</div>
            <div class="dz-prev" id="dz-prev">
              <img id="prev-img" src="" alt="" style="display:none">
              <video id="prev-vid" controls style="display:none;max-height:170px;width:100%;border-radius:10px"></video>
              <div class="dz-fname" id="prev-name"></div>
            </div>
          </div>

          <div class="alert a-demo" style="margin-top:.65rem">
            💡 Sans <strong>CLAUDE_API_KEY</strong> dans .env → résultat de <strong>démonstration</strong>. Avec la clé → analyse IA réelle de vos photos.
          </div>

          <button type="submit" class="btn btn-g btn-w btn-lg" id="abtn" style="margin-top:.8rem" disabled>
            🔍 Analyser avec l'IA
          </button>
        </form>
      </div>
    </div>
  </div>

  {{-- INFO --}}
  <div style="display:flex;flex-direction:column;gap:1.2rem">
    <div class="card">
      <div class="ch"><div class="ci" style="background:#f0fdf4">🔬</div><h3>Ce que l'IA détecte</h3></div>
      <div class="cb">
        @foreach([
          ['💧',"Gaspillage d'eau","Débordements, fuites, irrigation excessive, évaporation inutile."],
          ['🌿','Stress hydrique','Flétrissement, enroulement foliaire, jaunissement des plantes.'],
          ['☀️','Risque de sécheresse','Sol craquelé, végétation clairsemée, couverture végétale insuffisante.'],
          ['🔬','Pesticides & carences','Taches, chloroses, nécroses, carences N/Fe/Mg, ravageurs.'],
        ] as [$ico,$ttl,$desc])
        <div style="display:flex;gap:10px;margin-bottom:.9rem">
          <span style="font-size:1.35rem;flex-shrink:0;line-height:1;margin-top:.1rem">{{ $ico }}</span>
          <div>
            <div style="font-weight:700;font-size:.87rem;margin-bottom:.15rem">{{ $ttl }}</div>
            <div style="font-size:.77rem;color:var(--mu);line-height:1.5">{{ $desc }}</div>
          </div>
        </div>
        @endforeach
      </div>
    </div>
    <div class="card">
      <div class="ch"><div class="ci" style="background:#fef9c3">📖</div><h3>Comment ça marche</h3></div>
      <div class="cb">
        @foreach([
          ['1','Choisissez le type',"Sélectionnez ce que vous voulez détecter, ou 'Analyse complète'."],
          ['2','Uploadez votre fichier','Photo ou vidéo de votre champ. Max 50 MB.'],
          ['3','Résultat IA en quelques secondes','Diagnostic avec niveau de risque, zones et causes.'],
          ['4','Suivez les recommandations','Actions immédiates et préventives adaptées.'],
        ] as [$n,$t,$d])
        <div style="display:flex;gap:9px;margin-bottom:.85rem">
          <div style="width:24px;height:24px;border-radius:50%;background:var(--g);color:#fff;font-weight:800;font-size:.78rem;display:flex;align-items:center;justify-content:center;flex-shrink:0">{{ $n }}</div>
          <div>
            <div style="font-weight:700;font-size:.85rem;margin-bottom:.12rem">{{ $t }}</div>
            <div style="font-size:.76rem;color:var(--mu);line-height:1.5">{{ $d }}</div>
          </div>
        </div>
        @endforeach
        <div style="background:var(--gl);border:1px solid var(--gxl);border-radius:8px;padding:.65rem;font-size:.74rem;color:var(--gd);margin-top:.3rem">
          📸 <strong>Conseil :</strong> Photo de jour, bonne lumière, focus sur plantes ou sol.
        </div>
      </div>
    </div>
  </div>

</div>
@endsection
@push('scripts')
<script>
function pickType(el){
  document.querySelectorAll('.tp').forEach(t=>t.classList.remove('picked'));
  el.classList.add('picked');el.querySelector('input').checked=true;
}
const inp=document.getElementById('finp'),btn=document.getElementById('abtn');
const dz=document.getElementById('dz'),ico=document.getElementById('dz-ico');
const ttl=document.getElementById('dz-ttl'),prev=document.getElementById('dz-prev');
const pimg=document.getElementById('prev-img'),pvid=document.getElementById('prev-vid');
const pname=document.getElementById('prev-name');

inp.addEventListener('change',function(){
  const f=this.files[0];if(!f){btn.disabled=true;return;}
  btn.disabled=false;prev.style.display='block';
  const url=URL.createObjectURL(f),isVid=f.type.startsWith('video/');
  pname.textContent=f.name+' ('+Math.round(f.size/1048576*10)/10+' MB)';
  if(isVid){pimg.style.display='none';pvid.style.display='block';pvid.src=url;ico.textContent='🎥';}
  else{pvid.style.display='none';pimg.style.display='block';pimg.src=url;ico.textContent='🖼️';}
  ttl.textContent='Fichier prêt pour analyse';
});
['dragenter','dragover'].forEach(e=>dz.addEventListener(e,ev=>{ev.preventDefault();dz.classList.add('over');}));
['dragleave','drop'].forEach(e=>dz.addEventListener(e,ev=>{ev.preventDefault();dz.classList.remove('over');}));
dz.addEventListener('drop',e=>{if(e.dataTransfer.files.length){inp.files=e.dataTransfer.files;inp.dispatchEvent(new Event('change'));}});
document.getElementById('aform').addEventListener('submit',function(){btn.innerHTML='⏳ Analyse IA en cours...';btn.disabled=true;});
</script>
@endpush
