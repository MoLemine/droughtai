<?php

use App\Http\Controllers\DashboardController;
use App\Http\Controllers\PredictController;
use App\Http\Controllers\AnalysisController;
use Illuminate\Support\Facades\Route;

Route::get('/',          [DashboardController::class, 'index'])->name('dashboard');
Route::get('/predict',   [PredictController::class,   'index'])->name('predict');
Route::post('/predict',  [PredictController::class,   'predict'])->name('predict.post');
Route::get('/analysis',  [AnalysisController::class,  'index'])->name('analysis');
Route::post('/analysis', [AnalysisController::class,  'analyze'])->name('analysis.post');
