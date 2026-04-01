#!/bin/bash
# =============================================================================
# QMK Firmware - Windows Auto Build Script
# =============================================================================
# Usage:
#   bash build_windows.sh <keyboard> [keymap]
#
# Examples:
#   # 编译 Keychron V5 Max (所有 keymap)
#   bash build_windows.sh keychron/v5_max/ansi_encoder
#
#   # 编译 Keychron V5 Max 仅 default keymap
#   bash build_windows.sh keychron/v5_max/ansi_encoder default
#
#   # 编译 Keychron V5 Max 仅 via keymap
#   bash build_windows.sh keychron/v5_max/ansi_encoder via
#
#   # 编译 Keychron Q1 Max
#   bash build_windows.sh keychron/q1_max/ansi_encoder
#
#   # 无参数则编译默认的 Keychron V5 Max
#   bash build_windows.sh
# =============================================================================

set -euo pipefail

# ---- Configuration ----
QMK_MSYS_PATH="/c/DevDisk/DevSoft/QMK_MSYS"
PROJECT_DIR="/d/MyWork/AiCode/qmk_firmware"
DEFAULT_KEYBOARD="keychron/v5_max/ansi_encoder"
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_CYAN='\033[0;36m'
COLOR_RESET='\033[0m'

# ---- Parse Arguments ----
show_usage() {
    echo -e "${COLOR_CYAN}Usage:${COLOR_RESET}"
    echo "  $0 <keyboard> [keymap]"
    echo ""
    echo -e "${COLOR_CYAN}Arguments:${COLOR_RESET}"
    echo "  keyboard    Keyboard path, e.g. keychron/v5_max/ansi_encoder"
    echo "  keymap      Keymap name: default | via | all (default: all)"
    echo ""
    echo -e "${COLOR_CYAN}Examples:${COLOR_RESET}"
    echo "  $0                                           # 默认编译 Keychron V5 Max 全部 keymap"
    echo "  $0 keychron/v5_max/ansi_encoder              # 编译 V5 Max 全部 keymap"
    echo "  $0 keychron/v5_max/ansi_encoder default      # 仅编译 default keymap"
    echo "  $0 keychron/v5_max/ansi_encoder via          # 仅编译 via keymap"
    echo "  $0 keychron/q1_max/ansi_encoder              # 编译 Q1 Max"
    echo ""
    echo -e "${COLOR_CYAN}Available keyboards (keychron):${COLOR_RESET}"
    find keyboards/keychron -mindepth 2 -maxdepth 2 -type d 2>/dev/null | sed 's|keyboards/||' | sort | head -20
    exit 1
}

# 第一个参数如果不是已知的 keymap 名，就当作 keyboard
KEYBOARD=""
BUILD_TARGET=""

if [[ $# -eq 0 ]]; then
    KEYBOARD="$DEFAULT_KEYBOARD"
    BUILD_TARGET="all"
elif [[ $# -eq 1 ]]; then
    if [[ "$1" == "default" || "$1" == "via" || "$1" == "all" ]]; then
        # 仅指定了 keymap，使用默认 keyboard
        KEYBOARD="$DEFAULT_KEYBOARD"
        BUILD_TARGET="$1"
    else
        KEYBOARD="$1"
        BUILD_TARGET="all"
    fi
elif [[ $# -ge 2 ]]; then
    KEYBOARD="$1"
    BUILD_TARGET="$2"
else
    show_usage
fi

# 自动发现该 keyboard 下所有可用的 keymap
discover_keymaps() {
    local kb_path="keyboards/$1/keymaps"
    if [[ -d "$kb_path" ]]; then
        find "$kb_path" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort
    fi
}

AVAILABLE_KEYMAPS=($(discover_keymaps "$KEYBOARD"))

if [[ ${#AVAILABLE_KEYMAPS[@]} -eq 0 ]]; then
    echo -e "${COLOR_RED}Error: No keymaps found for '$KEYBOARD'${COLOR_RESET}"
    echo "Check path: keyboards/$KEYBOARD/keymaps/"
    exit 1
fi

if [[ "$BUILD_TARGET" == "all" ]]; then
    KEYMAPS=("${AVAILABLE_KEYMAPS[@]}")
else
    # 验证指定的 keymap 存在
    found=0
    for km in "${AVAILABLE_KEYMAPS[@]}"; do
        if [[ "$km" == "$BUILD_TARGET" ]]; then
            found=1
            break
        fi
    done
    if [[ $found -eq 0 ]]; then
        echo -e "${COLOR_RED}Error: Keymap '$BUILD_TARGET' not found for $KEYBOARD${COLOR_RESET}"
        echo -e "Available keymaps: ${COLOR_GREEN}${AVAILABLE_KEYMAPS[*]}${COLOR_RESET}"
        exit 1
    fi
    KEYMAPS=("$BUILD_TARGET")
fi

# ---- Helper Functions ----
log_info()  { echo -e "${COLOR_CYAN}[INFO]${COLOR_RESET} $*"; }
log_ok()    { echo -e "${COLOR_GREEN}[OK]${COLOR_RESET} $*"; }
log_warn()  { echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $*"; }
log_error() { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $*"; }

# ---- Step 1: Environment Setup ----
log_info "Setting up build environment..."

# Fix HOME directory for QMK MSYS
export HOME=/c/Users/tony
export USERPROFILE='C:\Users\tony'
export HOMEDRIVE=C:
export HOMEPATH='\Users\tony'
export MSYSTEM=MINGW64
export MSYS2_PATH_TYPE=inherit

# Add QMK MSYS toolchain to PATH
export PATH="$QMK_MSYS_PATH/mingw64/bin:$QMK_MSYS_PATH/usr/bin:$QMK_MSYS_PATH/opt/qmk/bin:$PATH"

log_ok "Environment variables configured"

# ---- Step 2: Change to Project Directory ----
cd "$PROJECT_DIR"
log_ok "Working directory: $(pwd)"

# ---- Step 2.1: Create qmk wrapper ----
# MSYS2 sh strips USERPROFILE/HOMEDRIVE/HOMEPATH when spawning child processes,
# but Python's Path.home() on Windows requires these vars.
# A wrapper script re-exports them before calling the real qmk.exe.
QMK_WRAPPER_DIR="$PWD/.build"
mkdir -p "$QMK_WRAPPER_DIR"
QMK_WRAPPER="$QMK_WRAPPER_DIR/qmk"
cat > "$QMK_WRAPPER" <<WRAPPER_EOF
#!/bin/bash
export USERPROFILE='C:\\Users\\tony'
export HOMEDRIVE=C:
export HOMEPATH='\\Users\\tony'
export HOME=/c/Users/tony
export SHELL=/usr/bin/bash
exec "$QMK_MSYS_PATH/mingw64/bin/qmk.exe" "\$@"
WRAPPER_EOF
chmod +x "$QMK_WRAPPER"
export PATH="$QMK_WRAPPER_DIR:$PATH"

# ---- Step 3: Verify Prerequisites ----
log_info "Checking prerequisites..."

# Check ARM toolchain
if ! command -v arm-none-eabi-gcc &>/dev/null; then
    log_warn "ARM GCC toolchain not found. Installing..."
    pacman -Sy mingw-w64-x86_64-arm-none-eabi-toolchain --noconfirm
fi
log_ok "ARM GCC: $(arm-none-eabi-gcc --version | head -1)"

# Check qmk command (wrapper should be first in PATH)
if ! command -v qmk &>/dev/null; then
    log_error "'qmk' command not found. Ensure QMK MSYS is installed at: $QMK_MSYS_PATH"
    exit 1
fi
log_ok "QMK CLI available ($(which qmk))"

# ---- Step 4: Ensure printf.c placeholder exists ----
PRINTF_FILE="platforms/chibios/printf.c"
if [[ ! -f "$PRINTF_FILE" ]]; then
    log_warn "Creating $PRINTF_FILE placeholder..."
    cat > "$PRINTF_FILE" <<'PRINTFEOF'
/*
Copyright 2024 QMK

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.
*/

// ChibiOS uses standard library printf
// This file is included for compatibility with build system
PRINTFEOF
    log_ok "Created $PRINTF_FILE"
fi

# ---- Step 5: Initialize Git Submodules ----
log_info "Checking Git submodules..."

check_submodule() {
    local path="$1"
    if [[ ! -f "$path/.git" ]] && [[ ! -d "$path/.git" ]]; then
        return 1
    fi
    # Check if directory has content
    if [[ -z "$(ls -A "$path" 2>/dev/null)" ]]; then
        return 1
    fi
    return 0
}

NEED_INIT=0
for sub in lib/chibios lib/chibios-contrib lib/lufa; do
    if ! check_submodule "$sub"; then
        log_warn "Submodule $sub needs initialization"
        NEED_INIT=1
    fi
done

if [[ $NEED_INIT -eq 1 ]]; then
    log_info "Initializing Git submodules..."
    git submodule update --init --recursive lib/chibios lib/chibios-contrib
    git submodule update --init --recursive lib/lufa
    log_ok "Git submodules initialized"
else
    log_ok "Git submodules already initialized"
fi

# ---- Step 6: Build ----
build_keymap() {
    local keymap="$1"
    echo ""
    log_info "========================================"
    log_info "Building: $KEYBOARD / $keymap"
    log_info "========================================"
    echo ""

    local start_time=$(date +%s)

    if make "$KEYBOARD:$keymap"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        # Copy firmware to project root
        # QMK replaces '/' with '_' in firmware filename
        local kb_flat=$(echo "$KEYBOARD" | tr '/' '_')
        local firmware_name="${kb_flat}_${keymap}.bin"
        local src=".build/${firmware_name}"

        if [[ -f "$src" ]]; then
            cp "$src" "$firmware_name"
            local size=$(du -h "$firmware_name" | cut -f1)
            log_ok "Build succeeded: $firmware_name ($size) [${duration}s]"
        else
            log_warn "Build completed but firmware file not found at expected location"
            log_info "Searching in .build/ directory..."
            find .build/ -name "*.bin" -newer .build/ -type f 2>/dev/null | head -5
        fi
    else
        log_error "Build FAILED for keymap: $keymap"
        return 1
    fi
}

FAILED=0

if [[ "$BUILD_TARGET" == "all" ]]; then
    for km in "${KEYMAPS[@]}"; do
        if ! build_keymap "$km"; then
            FAILED=1
        fi
    done
else
    if ! build_keymap "$BUILD_TARGET"; then
        FAILED=1
    fi
fi

# ---- Step 7: Summary ----
echo ""
log_info "========================================"
log_info "Build Summary"
log_info "========================================"

kb_flat=$(echo "$KEYBOARD" | tr '/' '_')
for f in ${kb_flat}_*.bin; do
    if [[ -f "$f" ]]; then
        fsize=$(du -h "$f" | cut -f1)
        log_ok "$f ($fsize)"
    fi
done

if [[ $FAILED -eq 1 ]]; then
    log_error "Some builds failed! Check the output above for details."
    exit 1
else
    log_ok "All builds completed successfully!"
fi

echo ""
log_info "Firmware files are in: $PROJECT_DIR"
log_info "Use QMK Toolbox or dfu-util to flash the firmware."

# ---- Cleanup ----
rm -f "$QMK_WRAPPER"
