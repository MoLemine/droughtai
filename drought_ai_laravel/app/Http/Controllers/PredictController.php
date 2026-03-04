<?php
namespace App\Http\Controllers;

use App\Services\DroughtAiService;
use Illuminate\Http\Request;

class PredictController extends Controller
{
    public function __construct(private DroughtAiService $drought) {}

    public function index()
    {
        $online  = $this->drought->isOnline();
        $points  = DroughtAiService::points();
        $classes = DroughtAiService::riskClasses();
        return view('predict.index', compact('online','points','classes'));
    }

    public function predict(Request $request)
    {
        $request->validate([
            'point'         => 'required|string|in:Rosso,Boghe,Kaedi,Matam,NouakchottSud',
            'year'          => 'required|integer|min:2018|max:2030',
            'month'         => 'required|integer|min:1|max:12',
            'soil_moisture' => 'required|numeric|min:0|max:1',
            'temperature_c' => 'required|numeric|min:10|max:55',
            'precipitation' => 'required|numeric|min:0|max:500',
            'humidity'      => 'required|numeric|min:0|max:100',
            'ndvi'          => 'required|numeric|min:0|max:1',
        ], [
            'point.in'      => 'Localité invalide.',
            'required'      => 'Le champ :attribute est obligatoire.',
            'numeric'       => 'Le champ :attribute doit être un nombre.',
            'min'           => 'Le champ :attribute est trop petit.',
            'max'           => 'Le champ :attribute est trop grand.',
        ]);

        $result  = $this->drought->predict($request->only([
            'point','year','month','soil_moisture','temperature_c','precipitation','humidity','ndvi'
        ]));

        $online  = $this->drought->isOnline();
        $points  = DroughtAiService::points();
        $classes = DroughtAiService::riskClasses();

        return view('predict.index', compact('online','result','points','classes'))
               ->with('input', $request->all());
    }
}
