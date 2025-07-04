@echo off
REM PyInstaller build script for Windjack game
REM Created: July 4, 2025

echo ========================================
echo Building Windjack Game with PyInstaller
echo ========================================

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo Failed to install PyInstaller. Please install it manually.
        pause
        exit /b 1
    )
)

REM Create build directory if it doesn't exist
if not exist "build" mkdir build
if not exist "dist" mkdir dist

echo.
echo Cleaning previous builds...
if exist "build\game" rmdir /s /q "build\game"
if exist "dist\windjack.exe" del /q "dist\windjack.exe"

echo.
echo Building executable...

REM PyInstaller command with options:
REM --onefile: Create a single executable file
REM --windowed: Hide console window (remove this if you want console visible)
REM --name: Set the name of the executable
REM --icon: Add an icon (uncomment and provide path if you have one)
REM --add-data: Include additional data files
REM --hidden-import: Include modules that might not be auto-detected
REM --exclude-module: Exclude unnecessary modules to reduce size

pyinstaller ^
    --onefile ^
    --console ^
    --name windjack ^
    --distpath dist ^
    --workpath build ^
    --specpath . ^
    --hidden-import=windows-curses ^
    --hidden-import=curses ^
    --add-data "src;src" ^
    --exclude-module=tkinter ^
    --exclude-module=matplotlib ^
    --exclude-module=PIL ^
    --exclude-module=numpy ^
    --exclude-module=scipy ^
    game.py

REM Check if build was successful
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Executable location: dist\windjack.exe
    echo File size:
    for %%A in ("dist\windjack.exe") do echo %%~zA bytes
    echo.
    echo You can now run the game with: dist\windjack.exe
    echo.
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
    echo Please check the error messages above.
    echo.
)

REM Optional: Clean up build files (uncomment if desired)
REM echo Cleaning up build files...
REM if exist "build" rmdir /s /q "build"
REM if exist "windjack.spec" del /q "windjack.spec"

echo Press any key to exit...
pause >nul
