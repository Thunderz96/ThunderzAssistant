@echo off
echo ========================================
echo Fixing config.py Git Tracking Issue
echo ========================================
echo.
echo This will remove config.py from git tracking
echo while keeping it on your local computer.
echo.
pause

echo Step 1: Unstaging config.py...
git reset HEAD config.py

echo.
echo Step 2: Removing from git index...
git rm --cached config.py

echo.
echo Step 3: Verifying .gitignore...
findstr "config.py" .gitignore
if %errorlevel% == 0 (
    echo ✓ config.py is in .gitignore
) else (
    echo ❌ config.py NOT in .gitignore - adding it now
    echo config.py >> .gitignore
)

echo.
echo Step 4: Check status...
git status

echo.
echo ========================================
echo ✓ Fixed! config.py is now ignored.
echo ========================================
echo.
echo Now you can run commit_v1.4.1.bat again
echo.
pause
