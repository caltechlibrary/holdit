@echo off
REM ===========================================================================
REM @file    create_binary.bat
REM @brief   Build a .exe using PyInstaller
REM @author  Michael Hucka <mhucka@caltech.edu>
REM @license Please see the file named LICENSE in the project directory
REM @website https://github.com/caltechlibrary/holdit
REM
REM Usage:
REM   1. cd into this directory
REM   2. run "create_binary.bat"
REM ===========================================================================

REM remember where we started from
SET ORIG_DIR=%~dp0

cd /d ../../..
pyinstaller --clean pyinstaller-win32.spec
cd  /d %ORIG_DIR%

echo "The .exe will be in the '../../../dist' subdirectory"
