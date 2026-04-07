@echo off
cd /d C:\Users\krato\claudgemgptcolab
del do_cleanup.bat
del 6.0.0
git rm --cached .claude/worktrees/admiring-tharp 2>nul
git rm --cached .claude/worktrees/intelligent-gagarin 2>nul
git add -A
git commit -m "chore: remove stray files from cleanup commit"
git push origin
