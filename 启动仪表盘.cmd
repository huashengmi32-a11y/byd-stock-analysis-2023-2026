@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\index.html" (
  echo Building dashboard...
  call pnpm build
  if errorlevel 1 pause
)

start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:4174/"
call pnpm preview --port 4174 --strictPort

endlocal
