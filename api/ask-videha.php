<?php
header('Content-Type: application/json; charset=utf-8');
$origin=$_SERVER['HTTP_ORIGIN']??'';
if(in_array($origin,['https://videha-ejournal.github.io','https://www.videha.co.in','https://videha.co.in'],true)){header('Access-Control-Allow-Origin: '.$origin);header('Vary: Origin');}
header('Access-Control-Allow-Headers: Content-Type');
if($_SERVER['REQUEST_METHOD']==='OPTIONS'){http_response_code(204);exit;}
$in=json_decode(file_get_contents('php://input'),true) ?: [];$q=trim($in['query']??'');$ev=$in['evidence']??[];
if(!$q||!is_array($ev)){http_response_code(400);echo json_encode(['error'=>'query/evidence required'],JSON_UNESCAPED_UNICODE);exit;}
$configFile=__DIR__.'/videha-ai-config.php';$cfg=file_exists($configFile)?include $configFile:[];
if(!is_array($cfg)||empty($cfg['endpoint'])||empty($cfg['api_key'])||empty($cfg['model'])){echo json_encode(['configured'=>false,'mode'=>'archive-answer-only','answer'=>''],JSON_UNESCAPED_UNICODE);exit;}
if(!function_exists('curl_init')){echo json_encode(['configured'=>false,'mode'=>'curl-unavailable','answer'=>''],JSON_UNESCAPED_UNICODE);exit;}
$evidence='';foreach(array_slice($ev,0,8) as $i=>$e){$txt=strip_tags($e['text']??'');$txt=function_exists('mb_substr')?mb_substr($txt,0,1500,'UTF-8'):substr($txt,0,3500);$evidence.='['.($i+1).'] '.($e['title']??'').' | '.($e['url']??'')."\n".$txt."\n\n";}
$payload=['model'=>$cfg['model'],'messages'=>[['role'=>'system','content'=>'You are Ask Videha, the source-grounded assistant for Videha eJournal. Answer only from supplied VIDEHA evidence. If evidence is insufficient, say so. Reply in the language/script of the user where practical. Cite source numbers like [1], [2]. Do not invent facts.'],['role'=>'user','content'=>"Question: $q\n\nVIDEHA evidence:\n$evidence"]],'temperature'=>0.1];
$ch=curl_init($cfg['endpoint']);curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>30,CURLOPT_HTTPHEADER=>['Content-Type: application/json','Authorization: Bearer '.$cfg['api_key']],CURLOPT_POSTFIELDS=>json_encode($payload)]);$raw=curl_exec($ch);$code=curl_getinfo($ch,CURLINFO_HTTP_CODE);curl_close($ch);$x=json_decode($raw,true);$answer=$x['choices'][0]['message']['content']??'';
if($code<200||$code>=300||!$answer){http_response_code(502);echo json_encode(['configured'=>true,'mode'=>'ai-error','error'=>'Generative endpoint failed'],JSON_UNESCAPED_UNICODE);exit;}
echo json_encode(['configured'=>true,'mode'=>'source-grounded-generative','answer'=>$answer],JSON_UNESCAPED_UNICODE);
?>
