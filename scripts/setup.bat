@echo off
REM [ame] fixed: cd to project root so pyproject.toml is findable
cd /d "%~dp0.."
if not exist "venv" (
    set /p api_key="Enter your api key: "
    
    setlocal enabledelatedexpansion
    echo api_key=!api_key!>.env
    endlocal

    echo Setting up environment...
    python -m venv venv
    echo api_key=placeholder > .env
    call .venv\Scripts\activate
    call pip install -e .
) else (
    call .venv\Scripts\activate
)
call kagent
pause
