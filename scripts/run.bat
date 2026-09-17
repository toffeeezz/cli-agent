@echo off
if not exist "venv" (
    echo Setting up environment...
    python -m venv venv
    echo api_key=placeholder > .env
    call venv\Scripts\activate
    call pip install -e .
) else (
    call venv\Scripts\activate
)
call kagent
pause
