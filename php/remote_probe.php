<?php
/**
 * Dedicated fixed-target read-only API probe, served only from a separate test directory.
 * Never accepts external host/path input. No private credentials needed.
 */
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
date_default_timezone_set('Europe/Istanbul');

function testApi(string $label, string $route, array $params): array {
    $url = 'https://api.mackolikfeeds.com'.$route.'?'.http_build_query($params, '', '&', PHP_QUERY_RFC3986);
    $out = [
        'test'=>$label,'route'=>$route,'http_status'=>0,
        'duration_ms'=>0,'bytes'=>0,'content_type'=>'','is_json'=>false,
        'json_top_keys'=>[],'error'=>null,'error_text_excerpt'=>null
    ];
    $started=microtime(true);
    $ch=curl_init($url);
    if ($ch===false) { $out['error']='curl_init failed'; return $out; }
    curl_setopt_array($ch,[
        CURLOPT_RETURNTRANSFER=>true,
        CURLOPT_CONNECTTIMEOUT=>6,
        CURLOPT_TIMEOUT=>12,
        CURLOPT_FOLLOWLOCATION=>false,
        CURLOPT_HTTPHEADER=>['Accept: application/json'],
        CURLOPT_USERAGENT=>'MackolikApiLab/0.2 public diagnostics',
        CURLOPT_SSL_VERIFYHOST=>2,
        CURLOPT_SSL_VERIFYPEER=>true,
    ]);
    $body=curl_exec($ch);
    $out['http_status']=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);
    $out['content_type']=(string)curl_getinfo($ch,CURLINFO_CONTENT_TYPE);
    $out['error']=curl_error($ch)?:null;
    $out['duration_ms']=(int)round((microtime(true)-$started)*1000);
    $out['bytes']=is_string($body)?strlen($body):0;
    curl_close($ch);
    if (is_string($body)) {
        $decoded=json_decode($body,true);
        $out['is_json']=(json_last_error()===JSON_ERROR_NONE && $decoded!==null);
        if ($out['is_json'] && is_array($decoded)) {
            $out['json_top_keys']=array_slice(array_keys($decoded),0,35);
        } elseif(stripos($out['content_type'],'text/')!==false) {
            $excerpt=trim(preg_replace('/\\s+/', ' ',strip_tags(substr($body,0,1024))));
            $out['error_text_excerpt']=substr($excerpt,0,160);
        }
    }
    return $out;
}

try {
    if(!extension_loaded('curl')) throw new RuntimeException('PHP cURL not enabled');
    $date=(new DateTimeImmutable('now',new DateTimeZone('Europe/Istanbul')))->format('Y-m-d');
    $common=['language'=>'tr','country'=>'tr'];
    $tests=[
        testApi('matches','/api/matches/',array_merge($common,['date'=>$date,'tz'=>'Europe/Istanbul'])),
        testApi('search','/soccer/api/search/',array_merge($common,['search'=>'Harry Winks']))
    ];
    echo json_encode([
        'source'=>'duvar-host-php',
        'checked_at'=>gmdate('c'),
        'results'=>$tests
    ],JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
} catch(Throwable $e) {
    http_response_code(500);
    echo json_encode(['source'=>'duvar-host-php','error'=>$e->getMessage()],JSON_UNESCAPED_UNICODE);
}
