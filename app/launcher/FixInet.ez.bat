@echo off
title FixInet.ez (By Seb0g1)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0FixInet.ez.ps1"
