@echo off
title InetFix (By Seb0g1)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0InetFix.ps1"
