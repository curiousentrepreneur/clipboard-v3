@echo off
cd /d %~dp0
python -m pip install cryptography pyperclip Pillow
python main.py --klasik
pause
