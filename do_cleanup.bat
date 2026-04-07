@echo off
cd /d C:\Users\krato\claudgemgptcolab
del launch.bat
del run.bat
del launch.sh
del run.sh
git add -A
git commit -m "chore: remove old launchers replaced by portable scripts"
git push origin
