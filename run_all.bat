@echo off
REM ──────────────────────────────────────────────────────────────────────────
REM  Citation Reliability Paper — Automation Script
REM  Usage:  run_all [step]
REM  Steps:  prompts, summary, tables, sensitivity, viz, integrity, test, all
REM ──────────────────────────────────────────────────────────────────────────
setlocal enabledelayedexpansion
cd /d "%~dp0"

if "%1"=="" goto all
if /I "%1"=="prompts" goto prompts
if /I "%1"=="summary" goto summary
if /I "%1"=="tables" goto tables
if /I "%1"=="stats" goto tables
if /I "%1"=="sensitivity" goto sensitivity
if /I "%1"=="viz" goto viz
if /I "%1"=="integrity" goto integrity
if /I "%1"=="test" goto test
if /I "%1"=="all" goto all
echo Unknown step: %1
echo Usage: %0 [prompts^|summary^|tables^|sensitivity^|viz^|integrity^|test^|all]
exit /b 1

:prompts
echo === Building prompts ===
python code\build_prompts.py
if errorlevel 1 exit /b 1
if "%1"=="" goto :eof else shift & goto check

:summary
echo === Generating summary metrics ===
python analysis\summarize_results.py
if errorlevel 1 exit /b 1
if "%1"=="" goto :eof else shift & goto check

:tables
echo === Generating paper tables with significance tests ===
python analysis\statistical_analysis.py
if errorlevel 1 exit /b 1
if "%1"=="" goto :eof else shift & goto check

:sensitivity
echo === Running sensitivity analysis ===
python analysis\sensitivity_analysis.py
if errorlevel 1 exit /b 1
if "%1"=="" goto :eof else shift & goto check

:viz
echo === Generating visualizations ===
python analysis\visualizations.py
if errorlevel 1 exit /b 1
if "%1"=="" goto :eof else shift & goto check

:integrity
echo === Validating data integrity ===
python analysis\validate_integrity.py
if errorlevel 1 exit /b 1
if "%1"=="" goto :eof else shift & goto check

:test
echo === Running unit tests ===
python -m pytest tests\ -v
if errorlevel 1 exit /b 1
if "%1"=="" goto :eof else shift & goto check

:all
echo ============================================
echo  Citation Reliability Paper - Full Pipeline
echo ============================================
call :summary
call :tables
call :sensitivity
call :viz
call :integrity
echo.
echo All automated steps completed.
goto :eof

:check
if "%1"=="" goto :eof
goto %1
