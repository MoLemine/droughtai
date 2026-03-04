<?php
namespace App\Http\Controllers;

use App\Services\ImageAnalysisService;
use App\Services\DroughtAiService;
use Illuminate\Http\Request;

class AnalysisController extends Controller
{
    public function __construct(private ImageAnalysisService $ai) {}

    public function index()
    {
        $online = (new DroughtAiService())->isOnline();
        $types  = ImageAnalysisService::TYPES;
        return view('analysis.index', compact('online','types'));
    }

    public function analyze(Request $request)
    {
        $request->validate([
            'file' => 'required|file|mimes:jpg,jpeg,png,webp,gif,mp4,mov,avi,webm|max:51200',
            'type' => 'required|in:full,water_waste,water_stress,drought_risk,pesticide',
        ], [
            'file.required' => 'Veuillez sélectionner un fichier.',
            'file.mimes'    => 'Format non supporté. Formats acceptés : JPG, PNG, WebP, MP4, MOV.',
            'file.max'      => 'Fichier trop volumineux (maximum 50 MB).',
            'type.in'       => "Type d'analyse invalide.",
        ]);

        $file    = $request->file('file');
        $type    = $request->input('type', 'full');
        $isVideo = in_array(strtolower($file->getClientOriginalExtension()), ['mp4','mov','avi','webm']);

        // Stocker le fichier dans storage/app/public/analyses/
        $path = $file->store('analyses', 'public');
        $url  = asset('storage/' . $path);

        $result = $isVideo
            ? $this->ai->analyzeVideo($file, $type)
            : $this->ai->analyze($file, $type);

        $online  = (new DroughtAiService())->isOnline();
        $types   = ImageAnalysisService::TYPES;
        $isImage = !$isVideo;

        return view('analysis.result', compact('online','result','types','type','url','isImage'));
    }
}
