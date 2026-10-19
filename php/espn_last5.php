<?php
declare(strict_types=1);
/** Standalone PHP 8+ ESPN soccer last-five league appearances: no API key. */
date_default_timezone_set('Europe/Istanbul');
header('X-Content-Type-Options: nosniff');
function safeId(string $name, string $default): string {
    $x = (string)($_GET[$name] ?? $default);
    if (!preg_match('/^[0-9]{1,10}$/D', $x)) throw new InvalidArgumentException("Invalid {$name}");
    return $x;
}
function safeLeague(): string {
    $x=(string)($_GET['league'] ?? 'eng.1');
    if (!preg_match('/^[a-z]{3}\.[0-9]{1,2}$/D',$x)) throw new InvalidArgumentException('Invalid league');
    return $x;
}
function espnFetch(string $url): array {
    if (!str_starts_with($url,'https://site.api.espn.com/apis/site/v2/sports/soccer/'))
        throw new InvalidArgumentException('Unknown source host');
    $ch=curl_init($url);
    if ($ch===false) throw new RuntimeException('Cannot start cURL');
    curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true, CURLOPT_FOLLOWLOCATION=>false,
        CURLOPT_TIMEOUT=>16,CURLOPT_CONNECTTIMEOUT=>7,CURLOPT_SSL_VERIFYPEER=>true,
        CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_HTTPHEADER=>['Accept: application/json'],
        CURLOPT_USERAGENT=>'MackolikAPILab-ESPNFiveMatches/1.0']);
    $raw=curl_exec($ch);$status=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE);
    $error=curl_error($ch);curl_close($ch);
    if (!is_string($raw) || $status!==200) throw new RuntimeException('ESPN response HTTP '.$status.' '.$error);
    if(strlen($raw)>2000000)throw new RuntimeException('Unexpected response size');
    $data=json_decode($raw,true);
    if(!is_array($data))throw new RuntimeException('ESPN response was not JSON');
    return $data;
}
function playerStat(array $p,string $name):?int {
    foreach(($p['stats']??[]) as $s){
        if (!is_array($s)||($s['name']??null)!==$name)continue;
        $v=$s['value']??null;
        if ((is_int($v)||is_float($v))&&$v>=0&&floor((float)$v)==(float)$v)return (int)$v;
    }
    return null;
}
function playedMatch(array $data,string $playerId):array {
    foreach(($data['rosters']??[]) as $team){
        if(!is_array($team))continue;
        foreach(($team['roster']??[]) as $p){
            if(!is_array($p)||!isset($p['athlete']) || (string)($p['athlete']['id']??'')!==$playerId)continue;
            $appearances=playerStat($p,'appearances');
            if($appearances===null || $appearances===0)return ['played'=>false];
            return ['played'=>true,'player'=>$p['athlete']['displayName']??null,
                'team'=>$team['team']['displayName']??null,
                'starter'=>($p['starter']??false)===true,
                'total_shots'=>playerStat($p,'totalShots'),
                'shots_on_target'=>playerStat($p,'shotsOnTarget')];
        }
    }
    return ['played'=>false];
}
function fetchLastFive(string $league,string $teamId,string $playerId):array {
    $prefix='https://site.api.espn.com/apis/site/v2/sports/soccer/'.$league.'/';
    $schedule=espnFetch($prefix.'teams/'.$teamId.'/schedule');
    $events=[];$now=time();
    foreach(($schedule['events']??[]) as $ev){
        if(!is_array($ev)||!preg_match('/^[0-9]{5,12}$/D',(string)($ev['id']??'')))continue;
        $unix=strtotime((string)($ev['date']??''));
        if($unix===false||$unix>$now)continue;
        $done=($ev['status']['type']['completed']??false)===true ||
            ($ev['competitions'][0]['status']['type']['completed']??false)===true;
        if(!$done)continue;
        $events[]=['event_id'=>(string)$ev['id'],'date'=>(string)$ev['date'],'unix'=>$unix];
    }
    usort($events,static fn($a,$b)=>$b['unix']<=>$a['unix']);
    $matches=[];$checked=0;
    foreach(array_slice($events,0,16) as $ev){
        $checked++;
        $stats=playedMatch(espnFetch($prefix.'summary?event='.$ev['event_id']),$playerId);
        if(!$stats['played'])continue;
        $matches[]=['event_id'=>$ev['event_id'],'date'=>$ev['date'],
                    'played'=>true,'player'=>$stats['player'],'team'=>$stats['team'],
                    'starter'=>$stats['starter'],'total_shots'=>$stats['total_shots'],
                    'shots_on_target'=>$stats['shots_on_target']];
        if(count($matches)===5)break;
        usleep(400000);
    }
    return ['updated_at'=>date(DATE_ATOM),'source'=>'ESPN public soccer site data',
        'league'=>$league,'team_id'=>$teamId,'player_id'=>$playerId,
        'matches_checked'=>$checked,'last_five_appearances'=>$matches,
        'series'=>array_map(static fn($m)=>$m['total_shots'],$matches),
        'five_found'=>count($matches)===5,
        'five_verified'=>count($matches)===5 && !in_array(null,array_column($matches,'total_shots'),true),
        'note'=>'League matches only, newest first. Null means missing, not zero. Not a promise of API availability.'];
}
try {
    $league=safeLeague();$teamId=safeId('team_id','349');$playerId=safeId('player_id','357719');
    $cacheKey=hash('sha256',$league.'|'.$teamId.'|'.$playerId);
    $cacheDir=sys_get_temp_dir().'/mackolik_espn_cache';
    if(!is_dir($cacheDir))@mkdir($cacheDir,0700,true);
    $cacheFile=$cacheDir.'/'.$cacheKey.'.json';
    $cacheFresh=is_file($cacheFile)&&(time()-filemtime($cacheFile))<900;
    $data=$cacheFresh?json_decode((string)file_get_contents($cacheFile),true):null;
    if(!is_array($data)){
        $data=fetchLastFive($league,$teamId,$playerId);
        @file_put_contents($cacheFile,json_encode($data,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT),LOCK_EX);
    }
    $data['cache_hit']=$cacheFresh;
} catch(Throwable $e){
    http_response_code(502);
    $data=['error'=>$e->getMessage(),'source'=>'ESPN public soccer site data'];
}
if(($_GET['format']??'')==='json'){
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT|JSON_INVALID_UTF8_SUBSTITUTE);
    exit;
}
function esc(mixed $value):string {return htmlspecialchars((string)$value,ENT_QUOTES|ENT_SUBSTITUTE,'UTF-8');}
?><!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ESPN Son 5 Maç Şutları</title>
<style>:root{color-scheme:dark}body{background:#0e1726;color:#edf4ff;font:16px system-ui;margin:0;padding:18px}main{max-width:860px;margin:auto}.card{background:#1d2b40;border:1px solid #39516a;border-radius:18px;padding:18px;margin:16px 0}h1{font-size:26px}p,small{color:#c4d2e3}a{color:#98bffe}.green{color:#9cf2c2}.fail{color:#ffb8bc}.sequence{font-size:clamp(24px,5vw,42px);font-weight:800;letter-spacing:.06em;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse}th,td{padding:12px 7px;text-align:left;border-bottom:1px solid #445368}input{max-width:105px;border-radius:7px;background:#081423;color:#fff;border:1px solid #52708f;padding:8px;font:inherit}button{padding:9px 15px;border:0;border-radius:9px;background:#3b82f6;color:white;font:inherit}</style></head><body><main>
<h1>⚽ Son 5 Maç — Toplam Şut</h1><p>ESPN kaynaklı gerçek oyuncu istatistikleri. Toplam şut, isabetli şut değildir.</p>
<form class="card" method="get"><label>Lig <input name="league" value="<?=esc($league??'eng.1')?>" required></label> <label>Takım ID <input name="team_id" value="<?=esc($teamId??'349')?>" required></label> <label>Oyuncu ID <input name="player_id" value="<?=esc($playerId??'357719')?>" required></label> <button>Kontrol et</button></form>
<?php if(isset($data['error'])): ?><div class="card fail"><?=esc($data['error'])?></div><?php else: ?>
<div class="card"><h2><?=esc($data['last_five_appearances'][0]['player']??'Oyuncu')?></h2>
<div class="sequence"><?=esc(implode(' - ',array_map(static fn($v)=>$v===null?'?':(string)$v,$data['series'])))?></div>
<p class="<?=!empty($data['five_verified'])?'green':'fail'?>"><?=!empty($data['five_verified'])?'Son beş maç doğrulandı':'Eksik maç veya şut verisi var'?></p>
<table><thead><tr><th>Tarih</th><th>Toplam Şut</th><th>İsabetli</th><th>İlk 11</th></tr></thead><tbody>
<?php foreach($data['last_five_appearances'] as $row): ?><tr><td><?=esc(date('d.m.Y',strtotime($row['date'])))?></td><td><?=esc($row['total_shots']??'?')?></td><td><?=esc($row['shots_on_target']??'?')?></td><td><?=$row['starter']?'Evet':'Hayır'?></td></tr><?php endforeach; ?></tbody></table>
<p><small>Kaynak: ESPN · <?=esc($data['updated_at'])?> · Ön­bellek: <?=!empty($data['cache_hit'])?'Var':'Yenilendi'?> · Sadece seçilen lig maçları</small></p>
<a href="?league=<?=urlencode($league)?>&amp;team_id=<?=urlencode($teamId)?>&amp;player_id=<?=urlencode($playerId)?>&amp;format=json">JSON verisini aç</a></div><?php endif; ?>
</main></body></html>