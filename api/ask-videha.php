<?php
header('Content-Type: application/json; charset=utf-8');
$origin=$_SERVER['HTTP_ORIGIN']??'';
if($origin==='https://videha-ejournal.github.io'){header('Access-Control-Allow-Origin: '.$origin);header('Vary: Origin');}
header('Access-Control-Allow-Headers: Content-Type');
if ($_SERVER['REQUEST_METHOD']==='OPTIONS'){http_response_code(204);exit;}
$in=json_decode(file_get_contents('php://input'),true) ?: [];
$q=trim($in['query']??'');$ev=$in['evidence']??[];
if(!$q||!is_array($ev)){http_response_code(400);echo json_encode(['error'=>'query/evidence required']);exit;}
$configFile=__DIR__.'/videha-ai-config.php';$cfg=file_exists($configFile)?include $configFile:[];
if(!is_array($cfg)||empty($cfg['endpoint'])||empty($cfg['api_key'])||empty($cfg['model'])){
  $first=strip_tags($ev[0]['text']??'');
  $short=function_exists('mb_substr')?mb_substr($first,0,700,'UTF-8'):substr($first,0,1800);
  $ans='विदेह अभिलेखमे सम्बन्धित स्रोत भेटल। '.$short;
  echo json_encode(['mode'=>'search-only fallback','answer'=>$ans],JSON_UNESCAPED_UNICODE);exit;
}
$evidence='';foreach(array_slice($ev,0,8) as $i=>$e){$evidence.='['.($i+1).'] '.($e['title']??'').' | '.($e['url']??'')."\n".($e['text']??'')."\n\n";}
$payload=['model'=>$cfg['model'],'messages'=>[['role'=>'system','content'=>'Answer only from the supplied VIDEHA evidence. If evidence is insufficient, say so. Keep source numbers [1], [2] in the answer.'],['role'=>'user','content'=>"Question: $q\n\nVIDEHA evidence:\n$evidence"]],'temperature'=>0.1];
if(!function_exists('curl_init')){echo json_encode(['mode'=>'search-only fallback','answer'=>'Generative endpoint उपलब्ध नहि; स्रोत-सूची देखू।'],JSON_UNESCAPED_UNICODE);exit;}
$ch=curl_init($cfg['endpoint']);curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>30,CURLOPT_HTTPHEADER=>['Content-Type: application/json','Authorization: Bearer '.$cfg['api_key']],CURLOPT_POSTFIELDS=>json_encode($payload)]);$raw=curl_exec($ch);$code=curl_getinfo($ch,CURLINFO_HTTP_CODE);curl_close($ch);$j=json_decode($raw,true);$answer=$j['choices'][0]['message']['content']??'';
if($code<200||$code>=300||!$answer){$answer='Generative endpoint उपलब्ध नहि; स्रोत-सूची देखू।';$mode='search-only fallback';}else{$mode='source-grounded generative';}
echo json_encode(['mode'=>$mode,'answer'=>$answer],JSON_UNESCAPED_UNICODE);
?>
