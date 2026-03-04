<?php
namespace App\Http\Controllers;

use App\Services\DroughtAiService;

class DashboardController extends Controller
{
    public function __construct(private DroughtAiService $drought) {}

    public function index()
    {
        $online = $this->drought->isOnline();
        $stats  = $online ? $this->drought->getStats()       : null;
        $map    = $online ? $this->drought->getMapData(2023) : null;
        $ts     = $online ? $this->drought->getTimeseries()  : null;
        $points = $online ? $this->drought->getPoints()      : [];

        $distribution = [];
        if ($stats && isset($stats['global']['distribution'])) {
            foreach ($stats['global']['distribution'] as $label => $count) {
                $distribution[] = ['label' => $label, 'count' => $count];
            }
        }

        $timeseriesData = [];
        if ($ts && isset($ts['series_by_point'])) {
            foreach ($ts['series_by_point'] as $pt => $series) {
                $timeseriesData[$pt] = array_map(
                    fn($s) => ['date' => $s['date'], 'value' => round($s['value'] ?? 0, 2)],
                    $series
                );
            }
        }

        $globalStats = $stats['global']  ?? [];
        $byYear      = collect($stats['by_year']  ?? [])->sortBy('year')->values()->toArray();
        $byPoint     = collect($stats['by_point'] ?? [])->sortByDesc('mean_risk')->values()->toArray();

        return view('dashboard.index', compact(
            'online','map','points','globalStats',
            'distribution','timeseriesData','byYear','byPoint'
        ));
    }
}
