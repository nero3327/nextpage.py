<?php header("Content-Type: text/html;charset=utf-8");?>
<!doctype html>
<html>
<body>
<?php
$UserAgent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, li                                                      ke Gecko) Chrome/78.0.3904.108 Safari/537.36';
$url = $_POST['url'];
$pageNumber = $_POST['pageNumber'];
$keyWords = $_POST['keyWords'];
$enCode = $_POST['enCode'];
$regAA="/<a .*?>.*?<\/a>/";
//$regUrl = '@(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\                                                      -]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()                                                      <>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))@';
$regUrl = '/href=".*?"/';
$aarray;
for ($iP=0;$iP<$pageNumber;$iP++){
        $curl = curl_init();
        curl_setopt($curl, CURLOPT_URL, $url);
        curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($curl, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($curl, CURLOPT_ENCODING, '');
        curl_setopt($curl, CURLOPT_USERAGENT, $UserAgent);
        curl_setopt($curl, CURLOPT_RETURNTRANSFER,1);
        echo $pageCon = mb_convert_encoding(curl_exec($curl),"UTF-8",$enCode);
//      $pageCon = curl_exec($curl);
        $aarayLen = preg_match_all($regAA,$pageCon,$aarray);
    for ($iA=0;$iA<$aarayLen;$iA++) {
        if(substr_count($aarray[0][$iA],$keyWords)){
                preg_match($regUrl,$aarray[0][$iA],$out);
        }
    }
    curl_close($curl);
                $outF = substr($out[0],6,-1);
                if(stripos($outF,'://') === false){
                        $sLenUrl = strlen($url);
                        $sLenOut = strlen($outF);
//                      if(stripos($outF,'../') === false){$sLenOut = $sLenOut-3                                                      ;}
                        $urlF =  substr($url, 0, -$sLenOut);
                        $url = $urlF.$outF;
                } else {
                        $url = $outF;
                }
                echo $url;

//      $url = $out[0];
//      echo $pageCon;
}
?>
</body>
</html>
