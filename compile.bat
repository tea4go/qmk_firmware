@echo off
cd /d D:\MyWork\AiCode\qmk_firmware
set MSYSTEM=MINGW64
set MSYS2_PATH_TYPE=inherit
set PATH=C:\DevDisk\DevSoft\QMK_MSYS\mingw64\bin;C:\DevDisk\DevSoft\QMK_MSYS\usr\bin;%PATH%
C:\DevDisk\DevSoft\QMK_MSYS\usr\bin\bash.exe -c "export QMK_BIN=/d/MyWork/AiCode/qmk_firmware/qmk && export SKIP_GIT=yes && make keychron/v5_max/ansi_encoder:default"
