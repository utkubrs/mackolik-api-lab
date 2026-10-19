<?php
declare(strict_types=1);
/** Maçkolik APK statik analizinden alınan yollarla GET/JSON bağlantı teşhisi; PHP 8+ */
function mackolikUrl(string $mode, array $parts=[]): string {
    $base='https://api.mackolikfeeds.com';
    $common=['language'=>'tr','country'=>'tr'];
    $id=static function(int $index)use($parts):string{
        $v=$parts[$index]??'';
        if(!is_string($v)||!preg_match('/^[a-z0-9-]{1,64}$/iD',$v)) throw new InvalidArgumentException('Gecerli ID gerekli.');
        return $v;
    };
    switch($mode) {
        case 'matches':
            $path='/api/matches/';
            $tz=new DateTimeZone('Europe/Istanbul');
            $q=$common+['date'=>(new DateTimeImmutable('now',$tz))->format('Y-m-d'),'tz'=>'Europe/Istanbul'];
            break;
        case 'search':
            if(!isset($parts[0])||strlen($parts[0])<2||strlen($parts[0])>160) throw new InvalidArgumentException('Arama ifadesi gecersiz.');
            $path='/soccer/api/search/';$q=$common+['search'=>$parts[0]];break;
        case 'player':
            $path='/api/player/';$q=$common+['player_id'=>$id(0)];break;
        case 'player_matches':
            $path='/api/player/matches';$q=$common+['player_id'=>$id(0)];break;
        case 'match':
            $path='/api/match/';$q=$common+['match_id'=>$id(0)];break;
        case 'team':
            $path='/api/team/';$q=$common+['team_id'=>$id(0)];break;
        case 'player_stats':
            $path='/statistics-service/match/'.$id(0).'/player/'.$id(1).'/stats';
            $q=['language'=>'tr'];break;
        default: throw new InvalidArgumentException('Gecersiz test modu.');
    }
    return $base.$path.'?'.http_build_query($q,'','&',PHP_QUERY_RFC3986);
}
function mackolikRequest(string $mode, array $parts=[]): array {
    $url=mackolikUrl($mode,$parts);
    if(!extension_loaded('curl')) throw new RuntimeException('PHP curl uzantisi eksik.');
    $curl=curl_init($url);
    if($curl===false) throw new RuntimeException('curl_init basarisiz.');
    curl_setopt_array($curl,[
        CURLOPT_RETURNTRANSFER=>true,CURLOPT_FOLLOWLOCATION=>false,
        CURLOPT_CONNECTTIMEOUT=>7,CURLOPT_TIMEOUT=>15,
        CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,
        CURLOPT_HTTPHEADER=>['Accept: application/json'],
        CURLOPT_USERAGENT=>'MackolikApiLab/0.1 diagnostics'
    ]);
    $started=microtime(true);
    $body=curl_exec($curl);
    $code=(int)curl_getinfo($curl,CURLINFO_HTTP_CODE);
    $type=(string)curl_getinfo($curl,CURLINFO_CONTENT_TYPE);
    $error=curl_error($curl)?:null;
    curl_close($curl);
    $json=is_string($body)?json_decode($body,true):null;
    $valid=json_last_error()===JSON_ERROR_NONE && $json!==null;
    return [
        'url'=>$url,'http_status'=>$code,'content_type'=>$type,
        'duration_ms'=>round((microtime(true)-$started)*1000),
        'bytes'=>is_string($body)?strlen($body):0,
        'error'=>$error,'is_json'=>$valid,
        'json'=>$valid?$json:null
    ];
}
if(realpath($_SERVER['SCRIPT_FILENAME']??'')===__FILE__) {
    if(PHP_SAPI!=='cli') {http_response_code(403);exit('CLI only');}
    try {
        $result=mackolikRequest($argv[1]??'matches',array_slice($argv,2));
        unset($result['json']);
        echo json_encode($result,JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE)."\n";
    } catch(Throwable $e) {fwrite(STDERR,$e->getMessage()."\n");exit(1);}
}
