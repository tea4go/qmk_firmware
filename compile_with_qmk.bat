@echo off
:: Batch script to compile in QMK MSYS environment
cd /d D:\MyWork\AiCode\qmk_firmware
set HOME=C:\Users\tony
set MSYSTEM=MINGW64
set MSYS2_PATH_TYPE=inherit
C:\DevDisk\DevSoft\QMK_MSYS\usr\bin\bash.exe --login -c "cd /d/MyWork/AiCode/qmk_firmware && qmk compile -kb keychron/v5_max/ansi_encoder -km default"
pause
