@echo off
title InetFix Setup (By Seb0g1)
echo.
echo  InetFix Setup 1.0.0
echo  ===================
echo.
set "INSTALL_DIR=%LOCALAPPDATA%\InetFix"
set "SRC=%~dp0"

if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%"

if exist "%SRC%InetFix-Portable-1.0.0.zip" (
    powershell -NoProfile -Command "Expand-Archive -Path '%SRC%InetFix-Portable-1.0.0.zip' -DestinationPath '%INSTALL_DIR%' -Force"
) else if exist "%SRC%..\app\dist" (
    xcopy /E /I /Y "%SRC%..\app\dist" "%INSTALL_DIR%\InetFix\dist"
    xcopy /E /I /Y "%SRC%..\app\launcher" "%INSTALL_DIR%\InetFix"
    if exist "%SRC%..\app\src-tauri\binaries\sing-box.exe" (
        mkdir "%INSTALL_DIR%\InetFix\bin" 2>nul
        copy /Y "%SRC%..\app\src-tauri\binaries\sing-box.exe" "%INSTALL_DIR%\InetFix\bin\"
    )
) else (
    echo Error: InetFix-Portable-1.0.0.zip not found.
    pause
    exit /b 1
)

powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\InetFix.lnk'); $s.TargetPath='%INSTALL_DIR%\InetFix\InetFix.bat'; $s.WorkingDirectory='%INSTALL_DIR%\InetFix'; $s.Save()"

echo.
echo  Installed to: %INSTALL_DIR%\InetFix
echo  Shortcut created on Desktop.
echo.
pause
