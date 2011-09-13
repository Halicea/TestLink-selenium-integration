@echo off

set /p browser= BrowserCode:

set /p startPage= StartPage:
set /p suitePath= Suite File:
set /p resultsFile= ResultsFile
java -jar selenium-server-standalone-2.3.0.jar -htmlSuite %browser% %StartPage%  %SuitePath% %ResultsFile%