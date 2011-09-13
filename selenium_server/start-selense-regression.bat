@echo off

set browser= "*chrome"

set startPage= "http://devconnect5.dev.lwi.com:8083/Welcome.aspx"
set suitePath= "C:\testsuites\testSuite.html"
set resultsFile= "C:\testsuites\results.html"
java -jar selenium-server-standalone-2.3.0.jar -htmlSuite %browser% %StartPage%  %SuitePath% %ResultsFile%