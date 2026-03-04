<?php
namespace App\Services;

use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * ImageAnalysisService v5.0 — YOLO via Flask
 *
 * Flux :
 *   Photo → base64 → POST /api/analyze/image (Flask+YOLO)
 *            → Résultat détection YOLO DroughtAI
 *
 * Fallback si YOLO indisponible :
 *   Photo → PHP GD features → POST /api/predict (RF/GB)
 */
class ImageAnalysisService
{
    const TYPES = [
        'full'         => ['label' => 'Analyse complète',                'icon' => '🔍'],
        'water_waste'  => ['label' => "Gaspillage d'eau",                'icon' => '💧'],
        'water_stress' => ['label' => 'Stress hydrique',                 'icon' => '🌿'],
        'drought_risk' => ['label' => 'Risque de sécheresse',            'icon' => '☀️'],
        'pesticide'    => ['label' => 'Pesticides & carences nutritives', 'icon' => '🔬'],
    ];

    private string $baseUrl;
    private string $apiKey;
    private int    $timeout;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('droughtai.url', 'http://127.0.0.1:5000'), '/');
        $this->apiKey  = config('droughtai.key', 'droughtai-secret-2024');
        $this->timeout = (int) config('droughtai.timeout', 30);
    }

    // ── ENTRY POINT ───────────────────────────────────────────────────────

    public function analyze(UploadedFile $file, string $type = 'full'): array
    {
        $mime    = $file->getMimeType();
        $allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];

        if (!in_array($mime, $allowed)) {
            return ['success' => false, 'error' => 'Format non supporté. Utilisez JPG, PNG ou WebP.'];
        }

        // Essai 1 : YOLO via Flask
        $yolo = $this->analyzeWithYolo($file, $type);
        if ($yolo['success']) {
            return $yolo;
        }

        // Fallback : GD features → /api/predict
        return $this->analyzeWithGdFallback($file, $type);
    }

    public function analyzeVideo(UploadedFile $file, string $type = 'full'): array
    {
        return [
            'success' => false,
            'demo'    => false,
            'error'   => 'Analyse vidéo non supportée. Uploadez une image JPG/PNG.',
        ];
    }

    // ── MÉTHODE 1 : YOLO via Flask /api/analyze/image ────────────────────

    private function analyzeWithYolo(UploadedFile $file, string $type): array
    {
        try {
            // Encoder l'image en base64
            $imageData = base64_encode(file_get_contents($file->getRealPath()));

            $response = Http::withHeaders([
                'X-API-Key'    => $this->apiKey,
                'Content-Type' => 'application/json',
                'Accept'       => 'application/json',
            ])
            ->timeout($this->timeout)
            ->post("{$this->baseUrl}/api/analyze/image", [
                'image_base64' => $imageData,
                'type'         => $type,
                'conf'         => 0.25,
            ]);

            if (!$response->successful()) {
                $body = $response->json();
                // Si endpoint 404 → YOLO pas encore intégré
                if ($response->status() === 404 || $response->status() === 503) {
                    return ['success' => false, 'error' => 'yolo_not_ready'];
                }
                return ['success' => false, 'error' => $body['message'] ?? 'Erreur YOLO'];
            }

            $data = $response->json('data');
            if (!$data || !isset($data['risk_class'])) {
                return ['success' => false, 'error' => 'Réponse YOLO invalide'];
            }

            // Construire résultat Laravel depuis réponse YOLO
            return $this->formatYoloResult($data, $type);

        } catch (\Exception $e) {
            Log::warning('YOLO analyze failed: ' . $e->getMessage());
            return ['success' => false, 'error' => $e->getMessage()];
        }
    }

    private function formatYoloResult(array $data, string $type): array
    {
        $rc    = $data['risk_class']     ?? 0;
        $label = $data['risk_label']     ?? 'Aucun';
        $color = $data['risk_color']     ?? '#22c55e';
        $conf  = $data['confidence']     ?? 0;
        $score = $data['drought_score']  ?? 0;
        $health= $data['score_sante']    ?? max(5, 100 - $rc * 20);
        $urg   = $data['urgence']        ?? 'Faible';
        $resume= $data['resume_global']  ?? $data['resume'] ?? '';

        $base = [
            'success'    => true,
            'type'       => $type,
            'label'      => self::TYPES[$type]['label'] ?? $type,
            'demo'       => false,
            'source'     => 'yolo_droughtai',
            'model_used' => $data['model'] ?? 'drought_yolo_best.pt',
            'urgence'    => $urg,
            'resume'     => $resume,
            'confidence' => $conf,
            'risk_class' => $rc,
            'risk_label' => $label,
            'risk_color' => $color,
            'detections' => $data['detections']  ?? [],
            'n_detections'=> $data['n_detections'] ?? 0,
            'class_areas' => $data['class_areas']  ?? [],
        ];

        if ($type === 'full') {
            return array_merge($base, [
                'resume_global'      => $resume,
                'score_sante'        => $health,
                'alerte'             => $data['alerte'] ?? "Classe {$rc} — {$label}",
                'probabilities'      => [],
                'gaspillage_eau'     => $data['gaspillage_eau']    ?? $this->emptyIndicator(),
                'stress_hydrique'    => $data['stress_hydrique']   ?? $this->emptyIndicator(),
                'risque_secheresse'  => $data['risque_secheresse'] ?? ['classe'=>$rc,'label'=>$label,'score'=>$score,'details'=>''],
                'anomalies_plantes'  => $data['anomalies_plantes'] ?? $this->emptyIndicator(),
                'actions_immediates' => $data['actions_immediates']  ?? [],
                'actions_preventives'=> $data['actions_preventives'] ?? [],
                'visual_features'    => [
                    'score_secheresse' => $score,
                    'source'           => 'yolo_detection',
                    'classes_detectees'=> $data['class_counts'] ?? [],
                ],
            ]);
        }

        return array_merge($base, [
            'score'                => $score,
            'classe_risque'        => $rc,
            'indicateurs_negatifs' => $data['indicateurs_negatifs'] ?? [],
            'indicateurs_positifs' => $data['indicateurs_positifs'] ?? [],
            'actions'              => $data['actions_immediates']   ?? [],
            'gaspillage_detecte'   => ($data['gaspillage_eau']['detecte'] ?? false),
            'niveau'               => $label,
            'stress_detecte'       => $rc >= 1,
            'anomalie_detectee'    => ($data['anomalies_plantes']['detectee'] ?? false),
            'type_anomalie'        => $data['anomalies_plantes']['type'] ?? '',
            'symptomes'            => [],
            'recommandations'      => $data['actions_immediates'] ?? [],
        ]);
    }

    private function emptyIndicator(): array
    {
        return ['detecte' => false, 'niveau' => 'Faible', 'score' => 0, 'details' => ''];
    }

    // ── MÉTHODE 2 : GD Fallback → /api/predict ───────────────────────────

    private function analyzeWithGdFallback(UploadedFile $file, string $type): array
    {
        try {
            $features = extension_loaded('gd')
                ? ($this->extractGdFeatures($file->getRealPath(), $file->getMimeType()) ?? $this->defaultFeatures())
                : $this->defaultFeatures();

            $payload = [
                'point'           => $features['drought_score'] >= 70 ? 'Matam' : 'Kaedi',
                'year'            => (int) date('Y'),
                'month'           => $features['green_ratio'] > 0.25 ? 8 : 2,
                'ndvi'            => $features['ndvi'],
                'soil_moisture'   => $features['soil_moisture'],
                'temperature_c'   => $features['temperature_c'],
                'humidity'        => $features['humidity'],
                'precipitation'   => $features['precipitation'],
                'evaporation'     => round($features['temperature_c'] * 2.5, 1),
                'stress_hydrique' => round(max(0, min(1, 1 - ($features['soil_moisture'] / 0.25))), 2),
            ];

            $response = Http::withHeaders(['X-API-Key' => $this->apiKey])
                ->timeout($this->timeout)
                ->post("{$this->baseUrl}/api/predict", $payload);

            if (!$response->successful()) {
                return [
                    'success' => false,
                    'demo'    => false,
                    'error'   => "API Flask hors ligne. Lancez: python api\\app.py",
                ];
            }

            $flask = $response->json('data');
            return $this->buildGdResult($flask, $features, $type);

        } catch (\Exception $e) {
            return ['success' => false, 'demo' => false, 'error' => $e->getMessage()];
        }
    }

    private function extractGdFeatures(string $path, string $mime): ?array
    {
        try {
            $img = match($mime) {
                'image/jpeg' => @imagecreatefromjpeg($path),
                'image/png'  => @imagecreatefrompng($path),
                'image/webp' => @imagecreatefromwebp($path),
                default      => null,
            };
            if (!$img) return null;

            $w = imagesx($img); $h = imagesy($img);
            $n = min(1000, $w * $h);
            $tR = $tG = $tB = $gP = $bP = $gyP = $blP = 0;

            for ($i = 0; $i < $n; $i++) {
                $rgb = imagecolorat($img, rand(0,$w-1), rand(0,$h-1));
                $r = ($rgb>>16)&0xFF; $g = ($rgb>>8)&0xFF; $b = $rgb&0xFF;
                $tR += $r; $tG += $g; $tB += $b;
                if ($g > $r*1.1 && $g > $b*1.1 && $g > 50)             $gP++;
                elseif ($r > $g*1.1 && $r > $b && $r > 80)             $bP++;
                elseif (abs($r-$g)<30 && abs($g-$b)<30 && $r>60 && $r<180) $gyP++;
                elseif ($b > $r*1.15 && $b > $g && $b > 70)            $blP++;
            }
            imagedestroy($img);

            $gr = $gP/$n; $br = $bP/$n; $gy = $gyP/$n; $bl = $blP/$n;
            $aR = $tR/$n; $aG = $tG/$n;
            $ndviP = ($aG+$aR > 0) ? ($aG-$aR)/($aG+$aR+0.001) : 0;

            return [
                'ndvi'          => round(max(0.04, min(0.35, 0.04+(($ndviP+1)/2)*0.31)), 3),
                'temperature_c' => round(24+(($tR/$n+$tG/$n+$tB/$n)/3/255)*22, 1),
                'soil_moisture' => round(max(0.03, min(0.28, 0.03+$gr*0.25)), 3),
                'humidity'      => round(max(10, min(80, 10+$gr*70)), 1),
                'precipitation' => round($gr*60+$bl*40, 1),
                'green_ratio'   => round($gr, 3),
                'brown_ratio'   => round($br, 3),
                'gray_ratio'    => round($gy, 3),
                'blue_ratio'    => round($bl, 3),
                'drought_score' => min(100, max(0, (int)round($br*50+$gy*40+(1-$gr)*10))),
                'source'        => 'gd_fallback',
            ];
        } catch (\Exception $e) {
            return null;
        }
    }

    private function defaultFeatures(): array
    {
        return [
            'ndvi'=>0.07,'temperature_c'=>38.0,'soil_moisture'=>0.05,
            'humidity'=>18.0,'precipitation'=>3.0,'green_ratio'=>0.04,
            'brown_ratio'=>0.52,'gray_ratio'=>0.36,'blue_ratio'=>0.01,
            'drought_score'=>80,'source'=>'default',
        ];
    }

    private function buildGdResult(array $flask, array $f, string $type): array
    {
        $rc    = $flask['risk_class'] ?? 0;
        $label = $flask['risk_label'] ?? 'Aucun';
        $conf  = $flask['confidence'] ?? 0;
        $color = $flask['risk_color'] ?? '#22c55e';
        $ds    = $f['drought_score']  ?? 50;
        $gr    = $f['green_ratio']    ?? 0.05;
        $br    = $f['brown_ratio']    ?? 0.40;
        $gy    = $f['gray_ratio']     ?? 0.30;

        $urgence = ['Faible','Moyenne','Élevée','Critique','Critique'][$rc] ?? 'Faible';
        $resume  = "Classe {$rc} ({$label}) — modèle ML Flask (confiance ".round($conf*100)."%). "
                 . "NDVI {$f['ndvi']}, humidité sol {$f['soil_moisture']} m³/m³.";

        $actions = match(true) {
            $rc >= 3 => ['Irrigation urgente 24h','Alerter autorités agricoles','Protéger cultures avec paillage'],
            $rc >= 2 => ['Irriguer dans 48h','Appliquer paillage','Vérifier irrigation'],
            $rc >= 1 => ['Surveiller humidité sol','Préparer irrigation préventive'],
            default  => ['Maintenir irrigation habituelle','Surveillance normale'],
        };

        $base = [
            'success'    => true, 'type' => $type,
            'label'      => self::TYPES[$type]['label'] ?? $type,
            'demo'       => false, 'source' => 'ml_gd_fallback',
            'model_used' => $flask['model_used'] ?? 'gradient_boosting',
            'urgence'    => $urgence, 'resume' => $resume,
            'confidence' => $conf, 'risk_class' => $rc,
            'risk_label' => $label, 'risk_color' => $color,
        ];

        if ($type === 'full') {
            return array_merge($base, [
                'resume_global'      => $resume,
                'score_sante'        => max(5, 100 - $rc * 22),
                'alerte'             => "Classe {$rc} — {$label} · ML fallback",
                'probabilities'      => $flask['probabilities'] ?? [],
                'gaspillage_eau'     => ['detecte'=>$f['blue_ratio']>0.15,'niveau'=>$f['blue_ratio']>0.15?'Modéré':'Faible','score'=>(int)round($f['blue_ratio']*100),'details'=>'Eau visible: '.round($f['blue_ratio']*100).'%'],
                'stress_hydrique'    => ['detecte'=>$rc>=1,'niveau'=>$label,'score'=>min(100,$rc*25+(int)($ds/4)),'details'=>"NDVI {$f['ndvi']} · verdure ".round($gr*100)."%"],
                'risque_secheresse'  => ['classe'=>$rc,'label'=>$label,'score'=>$ds,'details'=>"Sol craquelé ".round($gy*100)."% · sol nu ".round($br*100)."%"],
                'anomalies_plantes'  => ['detectee'=>$gr<0.15,'type'=>$gr<0.05?'Absence végétation':'Végétation clairsemée','score'=>(int)round((1-$gr)*60),'details'=>"Couverture ".round($gr*100)."%"],
                'actions_immediates' => $actions,
                'actions_preventives'=> ['Installer stations météo','Rotation des cultures','Réserves eau de pluie'],
                'visual_features'    => ['ndvi'=>$f['ndvi'],'drought_score'=>$ds,'source'=>$f['source']],
            ]);
        }

        return array_merge($base, [
            'score'=>$ds,'classe_risque'=>$rc,'niveau'=>$label,
            'indicateurs_negatifs'=>[$gy>0.2?"Sol craquelé ".round($gy*100)."%":"Sol stable"],
            'indicateurs_positifs'=>[$gr>0.15?"Végétation ".round($gr*100)."%":"Surveillance requise"],
            'actions'=>$actions,'recommandations'=>$actions,
            'resume'=>$resume,
        ]);
    }
}
