@echo off
set /p tp= Test plan file:
echo Options:[--testlink, --autogenerate, --browser=[*chome, *safari] 
set /p options= Options:
python references\runner\runner.py %options% %tp% 