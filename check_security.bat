@echo off
cd /d "C:\Users\nickw\OneDrive\Documents\Programs\ThunderzAssistant"
echo Checking if config.py is tracked by Git...
echo.
git ls-files | findstr "config.py"
if errorlevel 1 (
    echo [GOOD] config.py is NOT in Git yet - you're safe!
) else (
    echo [WARNING] config.py is being tracked by Git - needs to be removed
)
echo.
echo Checking .gitignore...
findstr "config.py" .gitignore
echo.
pause
