<?php
declare(strict_types=1);
/** Mobile-friendly temporary connectivity diagnostics. Delete after testing. */
header('Content-Type: text/html; charset=utf-8');
date_default_timezone_set('Europe/Istanbul');
function redact(mixed $v, int $depth=0): mixed {
    if ($depth>8) return '[DEPTH LIMIT]';
    if (is_array($v)) {
        $o=[]; $i=0;
        foreach($v as $k=>$x) {
            if (++$i>30) { $o['_truncated']=true; break; }
            $key=(string)$k;
            $o[$k]=preg_match('/token|secret|key|auth|cookie|session|password|email|phone/i',$key)
                ? '[REDACTED]' : redact($x,$depth+1);
        }
        return $o;
    }
    return is_string($v) ? substr($v,0,700) : $v;
}
function probe(string $name, string $path, array $q): array {
    $url='https://api.mackolikfeeds.com'.$path.'?'.http_build_query($q,'','&',PHP_QUERY_RFC3986);
    $start=microtime(true);
    $result=['test'=>$name,'url'=>$url,'http_code'=>0,'elapsed_ms'=>0,'content_type'=>'','error'=>null,'bytes'=>0,'is_json'=>false,'sample'=>null];
    $ch=curl_init($url);
    if(!$ch) { $result['error']='curl_init failed'; return $result; }
    curl_setopt_array($ch,[
        CURLOPT_RETURNTRANSFER=>true,
        CURLOPT_CONNECTTIMEOUT=>7,
        CURLOPT_TIMEOUT=>15,
        CURLOPT_FOLLOWLOCATION=>false,
        CURLOPT_SSL_VERIFYPEER=>true,
        CURLOPT_SSL_VERIFYHOST=>2,
        CURLOPT_HTTPHEADER=>['Accept: application/json'],
        CURLOPT_USERAGENT=>'MackolikApiLab/0.1 diagnostics',
    ]);
    $body=curl_exec($ch);
    $result['http_code']=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);
    $result['content_type']=(string)curl_getinfo($ch,CURLINFO_CONTENT_TYPE);
    $result['error']=curl_error($ch)?:null;
    $result['elapsed_ms']=(int)round((microtime(true)-$start)*1000);
    $result['bytes']=is_string($body)?strlen($body):0;
    curl_close($ch);
    if(is_string($body)) {
        $json=json_decode($body,true);
        if(json_last_error()===JSON_ERROR_NONE && $json!==null) {
            $result['is_json']=true;
            $result['sample']=redact($json);
        } else {
            $result['non_json_prefix']=substr(trim(strip_tags($body)),0,150);
        }
    }
    return $result;
}
$results=[]; $error=null;
if(isset($_GET['run'])) {
    if(!function_exists('curl_init')) {
        $error='Sunucuda PHP cURL etkin değil';
    } else {
        $common=['language'=>'tr','country'=>'tr'];
        $results[]=probe('matches','/api/matches/',array_merge($common,['date'=>date('Y-m-d'),'tz'=>'Europe/Istanbul']));
        $results[]=probe('search','/soccer/api/search/',array_merge($common,['search'=>'Harry Winks']));
    }
}
?><!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maçkolik API - Canlı Test</title>
<style>body{font:16px system-ui;background:#101827;color:#edf2ff;max-width:900px;margin:auto;padding:22px}h1{font-size:23px}button{background:#3b82f6;color:white;padding:14px 24px;border:0;border-radius:12px;font-size:16px;cursor:pointer}article{background:#1d2a3d;padding:15px;margin:18px 0;border-radius:14px;overflow-wrap:anywhere}pre{white-space:pre-wrap;word-break:break-word;font-size:12px;background:#0c1220;padding:12px;border-radius:9px;max-height:500px;overflow:auto}small{color:#a8bad0}</style>
</head><body><h1>⚽ Maçkolik 8.5.4 — Canlı API Testi</h1>
<p><small>İki GET isteği: günlük maçlar + Harry Winks araması. Gerçek test sonuçları sayfa yenilendiğinde güncellenir.</small></p>
<form method="get"><button name="run" value="1">İki API isteğini test et</button></form>
<?php if($error): ?><article><?=htmlspecialchars($error,ENT_QUOTES,'UTF-8')?></article><?php endif;?>
<?php foreach($results as $r): ?><article><h2><?=htmlspecialchars($r['test'])?> — HTTP <?= (int)$r['http_code']?></h2>
<p>Süre: <?= (int)$r['elapsed_ms']?> ms · Veri: <?= (int)$r['bytes']?> bayt · JSON: <?= $r['is_json']?'Evet':'Hayır' ?></p>
<pre><?=htmlspecialchars(json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE),ENT_QUOTES,'UTF-8')?></pre>
</article><?php endforeach;?></body></html>
