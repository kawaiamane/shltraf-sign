@echo off
cd /d "%~dp0"
py -3 -m pip install pyinstaller
py -3 -m PyInstaller --noconfirm --onefile --name ProjectVault --add-data "frontend;frontend" --hidden-import tkinter --hidden-import tkinter.filedialog run.py
echo See dist\ProjectVault.exe
pause
