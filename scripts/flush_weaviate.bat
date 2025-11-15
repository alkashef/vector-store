@echo off
REM Flush Weaviate by deleting the data folder contents
REM Reads WEAVIATE_DATA_PATH from config/.env

setlocal enabledelayedexpansion

REM Read WEAVIATE_DATA_PATH from config/.env
set "WEAVIATE_DATA_PATH="
for /f "usebackq tokens=1,* delims==" %%a in ("..\config\.env") do (
    set "line=%%a"
    if "!line:~0,18!"=="WEAVIATE_DATA_PATH" (
        set "WEAVIATE_DATA_PATH=%%b"
    )
)

REM Default to store/weaviate_data if not found
if "%WEAVIATE_DATA_PATH%"=="" (
    set "WEAVIATE_DATA_PATH=store\weaviate_data"
)

REM Convert to absolute path from repo root
set "REPO_ROOT=%~dp0.."
set "FULL_PATH=%REPO_ROOT%\%WEAVIATE_DATA_PATH%"

echo ========================================
echo Weaviate Flush Script
echo ========================================
echo Target folder: %FULL_PATH%
echo.

REM Check if folder exists
if not exist "%FULL_PATH%" (
    echo WARNING: Folder does not exist. Nothing to delete.
    exit /b 0
)

REM Delete all contents
echo Deleting folder contents...
rmdir /s /q "%FULL_PATH%" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to delete folder contents.
    exit /b 1
)

echo.
echo Recreating empty folder...
mkdir "%FULL_PATH%" 2>nul
echo All data flushed successfully (non-interactive).

