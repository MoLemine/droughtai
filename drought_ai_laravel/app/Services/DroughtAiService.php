<?php
namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;

class DroughtAiService
{
    private string $baseUrl;
    private string $apiKey;
    private int    $timeout;

    public function __construct()
    {
        $this->baseUrl = config('droughtai.base_url', 'http://192.168.100.37:5000');
        $this->apiKey  = config('droughtai.api_key',  'droughtai-secret-2024');
        $this->timeout = (int) config('droughtai.timeout', 15);
    }

    private function headers(): array
    {
        return ['X-API-Key' => $this->apiKey, 'Content-Type' => 'application/json', 'Accept' => 'application/json'];
    }

    private function get(string $path, array $params = []): ?array
    {
        try {
            $r = Http::withHeaders($this->headers())->timeout($this->timeout)
                     ->get($this->baseUrl . $path, $params);
            return $r->successful() ? $r->json('data') : null;
        } catch (\Exception $e) {
            Log::warning("DroughtAI GET {$path}: " . $e->getMessage());
            return null;
        }
    }

    private function post(string $path, array $body): ?array
    {
        try {
            $r = Http::withHeaders($this->headers())->timeout($this->timeout)
                     ->post($this->baseUrl . $path, $body);
            return $r->successful() ? $r->json('data') : null;
        } catch (\Exception $e) {
            Log::warning("DroughtAI POST {$path}: " . $e->getMessage());
            return null;
        }
    }

    public function isOnline(): bool
    {
        try {
            $r = Http::timeout(4)->get($this->baseUrl . '/api/health');
            return $r->successful() && $r->json('data.status') === 'ok';
        } catch (\Exception $e) {
            return false;
        }
    }

    public function getHealth(): ?array
    {
        try {
            $r = Http::timeout(4)->get($this->baseUrl . '/api/health');
            return $r->successful() ? $r->json('data') : null;
        } catch (\Exception $e) {
            return null;
        }
    }

    public function predict(array $data): ?array       { return $this->post('/api/predict', $data); }

    public function getStats(?string $point = null, ?int $year = null): ?array
    {
        return Cache::remember("d_stats_{$point}_{$year}", 300, function () use ($point, $year) {
            return $this->get('/api/stats', array_filter(compact('point', 'year')));
        });
    }

    public function getMapData(int $year = 2023): ?array
    {
        return Cache::remember("d_map_{$year}", 300, fn() => $this->get('/api/map', ['year' => $year]));
    }

    public function getTimeseries(string $variable = 'predicted_risk', ?string $point = null): ?array
    {
        $params = array_filter(['variable' => $variable, 'point' => $point]);
        return Cache::remember("d_ts_{$variable}_{$point}", 300,
            fn() => $this->get('/api/timeseries', $params));
    }

    public function getHistory(array $filters = []): ?array
    {
        return $this->get('/api/history', array_filter($filters));
    }

    public function getPoints(): array
    {
        return Cache::remember('d_points', 3600, function () {
            $d = $this->get('/api/points');
            return $d['points'] ?? [];
        });
    }

    public static function riskClasses(): array
    {
        return [
            0 => ['label'=>'Aucun',   'fr'=>'Aucun Risque',   'color'=>'#22c55e','icon'=>'✅'],
            1 => ['label'=>'Faible',  'fr'=>'Risque Faible',  'color'=>'#eab308','icon'=>'⚠️'],
            2 => ['label'=>'Modere',  'fr'=>'Risque Modéré',  'color'=>'#f97316','icon'=>'🔶'],
            3 => ['label'=>'Severe',  'fr'=>'Risque Sévère',  'color'=>'#ef4444','icon'=>'🚨'],
            4 => ['label'=>'Extreme', 'fr'=>'Risque Extrême', 'color'=>'#7c3aed','icon'=>'💀'],
        ];
    }

    public static function points(): array
    {
        return ['Rosso','Boghe','Kaedi','Matam','NouakchottSud'];
    }
}
