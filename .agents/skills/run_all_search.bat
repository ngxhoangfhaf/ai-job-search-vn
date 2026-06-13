@echo off
echo ==========================================
echo Vietnam Job Search - All Portals
echo ==========================================
echo.

echo [1/4] VietnamWorks...
python "%~dp0vietnamworks-search/cli/main.py" search --query "%~1" --jobage %~2 --limit %~3 --format json

echo.
echo [2/4] TopCV...
python "%~dp0topcv-search/cli/main.py" search --query "%~1" --jobage %~2 --limit %~3 --format json

echo.
echo [3/4] ITviec...
python "%~dp0itviec-search/cli/main.py" search --query "%~1" --jobage %~2 --limit %~3 --format json

echo.
echo [4/4] LinkedIn...
python "%~dp0linkedin-search/cli/main.py" search --query "%~1" --jobage %~2 --limit %~3 --format json

echo.
echo ==========================================
echo Done!
echo ==========================================
