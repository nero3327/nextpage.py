<?php header("Content-Type: text/html;charset=utf-8");?>
<!DOCTYPE html>
<html>
<body>
<form action="get.php" method="POST">
URL:  <input type="text" name="url" value="url">
<br>
PAGE  <input type="text" name="pageNumber" value="15">
<br>
keywords <input type="text" name="keyWords" value="下一章">
<br>
enCode <input type="text" name="enCode" list="codeType" value="GBK">
<datalist id="codeType">
<option value="UTF-8">
<option value="GBK">
</datalist>
<br>
<input type="submit" value="Submit">
</form>
</body>
</html>
