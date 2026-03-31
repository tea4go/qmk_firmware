#!/bin/bash
# Wrapper for qmk to fix HOME directory issue
export HOME=/c/Users/tony
export USERPROFILE=C:\\Users\\tony
export HOMEDRIVE=C:
export HOMEPATH=\\Users\\tony

# Call the real qmk with all arguments
exec /c/DevDisk/DevSoft/QMK_MSYS/mingw64/bin/qmk.exe "$@"
