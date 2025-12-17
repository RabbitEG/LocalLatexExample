@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem -----------------------------------------------------------------------------
rem docs\build.bat
rem
rem Windows-friendly wrapper for building docs without GNU Make.
rem Output directory is always: docs\build\
rem
rem Commands:
rem   build.bat            -> release build (silent)
rem   build.bat all        -> release build (silent)
rem   build.bat draft      -> draft build (silent, images as placeholders; wrapper generated in build\)
rem   build.bat debug      -> debug build (verbose, errorstopmode)
rem   build.bat draftdebug -> draft debug build (verbose)
rem   build.bat clean      -> remove intermediates (keep PDF)
rem   build.bat distclean  -> remove build\ entirely (including PDF)
rem   build.bat view       -> open build\TritonSurvey.pdf
rem
rem Options (environment variables):
rem   set ENGINE=xelatex        (default) or lualatex
rem   set SHELL_ESCAPE=1        enable -shell-escape (needed for minted)
rem -----------------------------------------------------------------------------

pushd "%~dp0"

set TEX_MAIN=TritonSurvey.tex
set OUTDIR=build

if "%ENGINE%"=="" set ENGINE=xelatex
if "%SHELL_ESCAPE%"=="" set SHELL_ESCAPE=0

set CMD=%1
if "%CMD%"=="" set CMD=all

set EXITCODE=0

rem Pick latexmk engine switch.
set ENGINE_FLAG=
if /I "%ENGINE%"=="xelatex" set ENGINE_FLAG=-xelatex
if /I "%ENGINE%"=="lualatex" set ENGINE_FLAG=-lualatex
if "%ENGINE_FLAG%"=="" (
  echo Unsupported ENGINE="%ENGINE%". Use ENGINE=xelatex or ENGINE=lualatex.
  set EXITCODE=2
  goto end
)

rem latexmk does not have a dedicated -shell-escape flag; pass it via -latexoption.
set SHELL_ESCAPE_FLAG=
if "%SHELL_ESCAPE%"=="1" set SHELL_ESCAPE_FLAG=-latexoption=-shell-escape

if /I "%CMD%"=="all" goto build_release
if /I "%CMD%"=="draft" goto build_draft_release
if /I "%CMD%"=="debug" goto build_debug
if /I "%CMD%"=="draftdebug" goto build_draft_debug
if /I "%CMD%"=="clean" goto do_clean
if /I "%CMD%"=="distclean" goto do_distclean
if /I "%CMD%"=="view" goto do_view

echo Unknown command: %CMD%
echo Valid: all ^| draft ^| debug ^| draftdebug ^| clean ^| distclean ^| view
set EXITCODE=2
goto end

:build_release
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
call :run_release "%TEX_MAIN%" "%OUTDIR%\\TritonSurvey.pdf" || goto end
goto end

:build_debug
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
echo [debug] Building "%TEX_MAIN%" with ENGINE=%ENGINE% (verbose)...
latexmk %ENGINE_FLAG% -outdir=%OUTDIR% -synctex=1 -file-line-error -interaction=errorstopmode -halt-on-error %SHELL_ESCAPE_FLAG% %TEX_MAIN%
set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" echo [debug] FAILED (exit %EXITCODE%)
if "%EXITCODE%"=="0" echo [debug] OK: %OUTDIR%\TritonSurvey.pdf
goto end

:build_draft_release
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
call :detect_single_main_tex || (set EXITCODE=%ERRORLEVEL% & goto end)
call :write_draft_wrapper || (set EXITCODE=%ERRORLEVEL% & goto end)
call :run_release "%WRAPPER_TEX%" "%OUTDIR%\\%MAIN_BASE%-draft.pdf" || goto end
goto end

:build_draft_debug
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
call :detect_single_main_tex || (set EXITCODE=%ERRORLEVEL% & goto end)
call :write_draft_wrapper || (set EXITCODE=%ERRORLEVEL% & goto end)
echo [debug] Draft building "%MAIN_TEX%" -> "%OUTDIR%\\%MAIN_BASE%-draft.pdf" (verbose)...
latexmk %ENGINE_FLAG% -outdir=%OUTDIR% -synctex=1 -file-line-error -interaction=errorstopmode -halt-on-error %SHELL_ESCAPE_FLAG% "%WRAPPER_TEX%"
set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" echo [debug] FAILED (exit %EXITCODE%)
if "%EXITCODE%"=="0" echo [debug] OK: %OUTDIR%\%MAIN_BASE%-draft.pdf
goto end

:do_clean
echo [clean] Removing intermediates (keeping PDF)...
latexmk -c -outdir=%OUTDIR% %TEX_MAIN% >nul 2>&1
if exist %OUTDIR%\\*-draft.tex (
  for %%F in (%OUTDIR%\\*-draft.tex) do latexmk -c -outdir=%OUTDIR% "%%~fF" >nul 2>&1
)
if exist "%OUTDIR%\\_minted-*" rd /s /q "%OUTDIR%\\_minted-*" 2>nul
if exist "_minted-*" rd /s /q "_minted-*" 2>nul
set EXITCODE=0
goto end

:do_distclean
echo [distclean] Removing build\ (including PDF)...
latexmk -C -outdir=%OUTDIR% %TEX_MAIN% >nul 2>&1
if exist "%OUTDIR%" rd /s /q "%OUTDIR%"
set EXITCODE=0
goto end

:detect_single_main_tex
set MAIN_TEX=
set MAIN_COUNT=0
for %%F in (*.tex) do (
  set /a MAIN_COUNT+=1
  set MAIN_TEX=%%F
)
if not "%MAIN_COUNT%"=="1" (
  echo Draft mode requires exactly one main .tex file in docs\; found %MAIN_COUNT%.
  echo Please keep only one top-level .tex file in docs\.
  exit /b 2
)
set MAIN_BASE=%MAIN_TEX:~0,-4%
exit /b 0

:write_draft_wrapper
rem Write wrapper into build\ and call it with forward slashes (TeX filename parsing).
set WRAPPER_WIN=%OUTDIR%\\%MAIN_BASE%-draft.tex
set WRAPPER_TEX=%OUTDIR%/%MAIN_BASE%-draft.tex
> "%WRAPPER_WIN%" echo \def\TRITONDRAFT{1}
>> "%WRAPPER_WIN%" echo \input{../%MAIN_TEX%}
exit /b 0

:run_release
rem Args:
rem   %1 = input tex path (can be build/... for wrapper)
rem   %2 = expected output PDF path (windows path, relative to docs\)
set "RUN_TEX=%~1"
set "RUN_PDF=%~2"
set "RUNLOG=%OUTDIR%\\latexmk-%RANDOM%.log"

for /f "delims=" %%I in ('powershell -NoProfile -Command "[long]([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"') do set START_MS=%%I
echo [build] %RUN_TEX%  (ENGINE=%ENGINE%, shell-escape=%SHELL_ESCAPE%)

latexmk %ENGINE_FLAG% -outdir=%OUTDIR% -synctex=1 -file-line-error -interaction=nonstopmode -halt-on-error -silent %SHELL_ESCAPE_FLAG% "%RUN_TEX%" > "%RUNLOG%" 2>&1
set EXITCODE=%ERRORLEVEL%

for /f "delims=" %%I in ('powershell -NoProfile -Command "[long]([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"') do set END_MS=%%I
for /f "delims=" %%I in ('powershell -NoProfile -Command "[math]::Ceiling((%END_MS% - %START_MS%)/1000.0)"') do set ELAPSED_SEC=%%I

for /f "delims=" %%C in ('findstr /R /C:"Latexmk: Run number [0-9][0-9]* of rule" "%RUNLOG%" ^| find /c /v ""') do set RUNS=%%C
if "%RUNS%"=="" set RUNS=?

if "%EXITCODE%"=="0" (
  echo [ok] %RUN_PDF%  (!RUNS! runs, !ELAPSED_SEC!s^)
  del /q "%RUNLOG%" 2>nul
  exit /b 0
)

echo [fail] Exit %EXITCODE%  (!ELAPSED_SEC!s)
echo [fail] See: %RUNLOG%
if exist "%OUTDIR%\\TritonSurvey-draft.log" echo [fail] Also check: %OUTDIR%\TritonSurvey-draft.log
if exist "%OUTDIR%\\TritonSurvey.log" echo [fail] Also check: %OUTDIR%\TritonSurvey.log
exit /b %EXITCODE%

:do_view
if not exist "%OUTDIR%\\TritonSurvey.pdf" (
  echo PDF not found: %OUTDIR%\\TritonSurvey.pdf
  set EXITCODE=1
  goto end
)
start "" "%OUTDIR%\\TritonSurvey.pdf"
set EXITCODE=0
goto end

:end
popd
endlocal & exit /b %EXITCODE%
popd
endlocal
