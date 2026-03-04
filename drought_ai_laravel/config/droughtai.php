<?php
// config/droughtai.php
return [
    'base_url'       => env('DROUGHTAI_URL',   'http://192.168.100.37:5000'),
    'api_key'        => env('DROUGHTAI_KEY',   'droughtai-secret-2024'),
    'timeout'        => env('DROUGHTAI_TIMEOUT', 15),
];
