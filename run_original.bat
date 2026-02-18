@echo off
@REM прочитать обязательно 123.md
setlocal
cd /d "%~dp0"
set "SITE_URL=http://127.0.0.1:8000"
set "SQLITE_NAME=site\db.sqlite3"
set "MEDIA_ROOT=%cd%\media"
if errorlevel 1 exit /b 1
python manage.py migrate
if errorlevel 1 exit /b 1
python manage.py runserver 127.0.0.1:8000
