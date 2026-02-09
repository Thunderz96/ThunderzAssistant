@echo off
echo ========================================
echo Thunderz Assistant v1.5.0
echo Git Commit Script - File Organizer
echo ========================================
echo.
echo This will commit:
echo - File Organizer module
echo - Safety system (30+ forbidden folders)
echo - Updated documentation
echo - Bug fixes
echo.
pause

echo.
echo Step 1: Checking git status...
echo ========================================
git status
echo.

echo Step 2: Verify config.py is NOT included...
echo ========================================
git status | findstr "config.py"
if %errorlevel% == 0 (
    echo.
    echo WARNING: config.py is staged!
    echo Run this first: git restore --staged config.py
    pause
    exit /b 1
) else (
    echo OK: config.py is properly ignored
)
echo.

echo Step 3: Adding all changes...
echo ========================================
git add .
echo Changes staged
echo.

echo Step 4: Committing...
echo ========================================
git commit -m "v1.5.0 - File Organizer module with safety system"
echo.

echo Step 5: Pushing to GitHub...
echo ========================================
git push origin main
echo.

if %errorlevel% == 0 (
    echo ========================================
    echo SUCCESS! v1.5.0 is now on GitHub!
    echo ========================================
    echo.
    echo Changes pushed:
    echo - File Organizer module (70+ file types)
    echo - Safety system (30+ forbidden folders)
    echo - Clean folder display UI
    echo - Complete documentation
    echo - Bug fixes and improvements
    echo.
) else (
    echo ========================================
    echo Push failed!
    echo ========================================
)

pause
