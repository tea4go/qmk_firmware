#!/usr/bin/env python3
# Dummy qmk script to work around HOME directory issue
import sys
import json
import os

def generate_config_h(keyboard, output_file):
    """Generate config.h from info.json files"""
    # Find all info.json files for this keyboard
    info_data = {}

    # Walk up the keyboard path and merge info.json files
    path_parts = keyboard.split('/')
    for i in range(len(path_parts), 0, -1):
        current_path = os.path.join('keyboards', *path_parts[:i])
        info_file = os.path.join(current_path, 'info.json')
        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                current_info = json.load(f)
                # Merge info (earlier files override later ones)
                for key, value in current_info.items():
                    if key not in info_data:
                        info_data[key] = value

    # Generate config.h content
    config_lines = ['// Generated config header', '#pragma once', '']

    # Product name
    if 'keyboard_name' in info_data:
        config_lines.append(f'#define PRODUCT "{info_data["keyboard_name"]}"')

    # Manufacturer
    if 'manufacturer' in info_data:
        config_lines.append(f'#define MANUFACTURER "{info_data["manufacturer"]}"')

    # USB settings (for direct use in config.h)
    if 'usb' in info_data:
        usb = info_data['usb']
        if 'vid' in usb:
            config_lines.append(f'#define VENDOR_ID {usb["vid"]}')
        if 'pid' in usb:
            config_lines.append(f'#define PRODUCT_ID {usb["pid"]}')
        if 'device_version' in usb:
            # Convert version string like "1.0.0" to hex like 0x0100
            ver_str = str(usb["device_version"])
            if '.' in ver_str:
                parts = ver_str.split('.')
                # Major.minor format: e.g., "1.0.0" -> 0x0100
                major = int(parts[0]) if len(parts) > 0 else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                hex_ver = f'0x{major:02X}{minor:02X}'
                config_lines.append(f'#define DEVICE_VER {hex_ver}')
            else:
                config_lines.append(f'#define DEVICE_VER {usb["device_version"]}')

    # Matrix configuration
    if 'matrix_pins' in info_data:
        matrix_pins = info_data['matrix_pins']
        if 'rows' in matrix_pins:
            config_lines.append(f'#define MATRIX_ROWS {len(matrix_pins["rows"])}')
            row_pins = ', '.join(matrix_pins['rows'])
            config_lines.append(f'#define MATRIX_ROW_PINS {{ {row_pins} }}')
        if 'cols' in matrix_pins:
            config_lines.append(f'#define MATRIX_COLS {len(matrix_pins["cols"])}')
            col_pins = ', '.join(matrix_pins['cols'])
            config_lines.append(f'#define MATRIX_COL_PINS {{ {col_pins} }}')

    # Include original config.h files if they exist
    for i in range(len(path_parts), 0, -1):
        current_path = os.path.join('keyboards', *path_parts[:i])
        config_h = os.path.join(current_path, 'config.h')
        if os.path.exists(config_h):
            config_lines.append(f'#include "{config_h}"')

    # Encoder configuration
    if 'encoder' in info_data and 'rotary' in info_data['encoder']:
        rotary = info_data['encoder']['rotary']
        if rotary:
            pin_a_list = [enc['pin_a'] for enc in rotary]
            pin_b_list = [enc['pin_b'] for enc in rotary]
            config_lines.append(f'#ifndef ENCODERS_PAD_A')
            config_lines.append(f'#define ENCODERS_PAD_A {{ {", ".join(pin_a_list)} }}')
            config_lines.append(f'#endif')
            config_lines.append(f'#ifndef ENCODERS_PAD_B')
            config_lines.append(f'#define ENCODERS_PAD_B {{ {", ".join(pin_b_list)} }}')
            config_lines.append(f'#endif')

    return '\n'.join(config_lines) + '\n'

def generate_rules_mk(keyboard, output_file):
    """Generate rules.mk from info.json files"""
    # Find all info.json files for this keyboard
    keyboard_path = os.path.join('keyboards', keyboard.replace('/', os.sep))
    info_data = {}

    # Walk up the keyboard path and merge info.json files (from root to leaf)
    path_parts = keyboard.split('/')
    for i in range(1, len(path_parts) + 1):
        current_path = os.path.join('keyboards', *path_parts[:i])
        info_file = os.path.join(current_path, 'info.json')
        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                current_info = json.load(f)
                # Deep merge for nested dicts like 'features'
                for key, value in current_info.items():
                    if key == 'features' and key in info_data:
                        # Merge features dictionaries
                        info_data[key].update(value)
                    elif key == 'usb' and key in info_data:
                        # Merge USB settings
                        info_data[key].update(value)
                    else:
                        info_data[key] = value

    # Generate rules.mk content
    rules = []

    # Determine PLATFORM_KEY based on processor
    platform_key = None
    if 'processor' in info_data:
        processor = info_data["processor"].upper()
        if 'STM32' in processor or 'RP2040' in processor or 'GD32V' in processor or 'WB32' in processor:
            platform_key = 'chibios'
        elif any(avr in processor for avr in ['ATMEGA', 'AT90USB', 'ATXMEGA']):
            platform_key = 'avr'
        elif 'CORTEX' in processor:
            platform_key = 'chibios'

    # Set PLATFORM_KEY first
    if platform_key:
        rules.append(f'PLATFORM_KEY = {platform_key}')

    # MCU/Processor
    if 'processor' in info_data:
        rules.append(f'MCU = {info_data["processor"]}')

    # Bootloader
    if 'bootloader' in info_data:
        rules.append(f'BOOTLOADER = {info_data["bootloader"]}')

    # Features
    if 'features' in info_data:
        for feature, enabled in info_data['features'].items():
            feature_upper = feature.upper()
            value = 'yes' if enabled else 'no'
            rules.append(f'{feature_upper}_ENABLE = {value}')

    # RGB Matrix driver
    if 'rgb_matrix' in info_data and isinstance(info_data['rgb_matrix'], dict):
        if 'driver' in info_data['rgb_matrix']:
            rules.append(f'RGB_MATRIX_DRIVER = {info_data["rgb_matrix"]["driver"]}')

    # USB settings
    if 'usb' in info_data:
        usb = info_data['usb']
        if 'vid' in usb:
            rules.append(f'VENDOR_ID = {usb["vid"]}')
        if 'pid' in usb:
            rules.append(f'PRODUCT_ID = {usb["pid"]}')
        if 'device_version' in usb:
            rules.append(f'DEVICE_VER = {usb["device_version"]}')

    # Write output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('# This file was generated by qmk_dummy.py\n\n')
        f.write('\n'.join(rules))
        f.write('\n')

    print(output_file)

if __name__ == "__main__":
    # Handle different qmk commands
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "hello":
            # Just exit successfully
            sys.exit(0)
        elif cmd == "git-submodule":
            # Skip git submodule checks
            sys.exit(0)
        elif cmd == "list-keyboards":
            # This shouldn't be called since we're using SKIP_GIT
            print("keychron/v5_max/ansi_encoder", end='')
            sys.exit(0)
        elif cmd == "resolve-alias":
            # Return the keyboard name as-is
            if len(sys.argv) > 3 and sys.argv[2] == "--allow-unknown":
                print(sys.argv[3])
            sys.exit(0)
        elif cmd == "list-layouts":
            # Return empty for now
            sys.exit(0)
        elif cmd == "generate-rules-mk":
            # Parse arguments
            keyboard = None
            output_file = None
            i = 2
            while i < len(sys.argv):
                if sys.argv[i] in ['--keyboard', '-kb']:
                    keyboard = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] in ['--output', '-o']:
                    output_file = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1

            if keyboard and output_file:
                generate_rules_mk(keyboard, output_file)
                sys.exit(0)
            else:
                print("Error: Missing keyboard or output parameter", file=sys.stderr)
                sys.exit(1)
        elif cmd in ["generate-config-h", "generate-keyboard-c", "generate-keyboard-h",  "generate-version-h", "generate-make-dependencies"]:
            # Parse --output or -o parameter (ignore other parameters)
            output_file = None
            keyboard = None
            quiet = False
            i = 2
            while i < len(sys.argv):
                if sys.argv[i] in ['--output', '-o']:
                    output_file = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] in ['--keyboard', '-kb']:
                    keyboard = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] in ['-q', '--quiet']:
                    quiet = True
                    i += 1
                elif sys.argv[i].startswith('-'):
                    # Skip other flags and their potential arguments
                    i += 1
                    if i < len(sys.argv) and not sys.argv[i].startswith('-'):
                        i += 1
                else:
                    i += 1

            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                # Create placeholder files
                if cmd == "generate-config-h":
                    if keyboard:
                        # Generate actual config from info.json
                        content = generate_config_h(keyboard, output_file)
                        with open(output_file, 'w') as f:
                            f.write(content)
                    else:
                        # Fallback to empty config
                        with open(output_file, 'w') as f:
                            f.write('// Generated config header\n')
                            f.write('#pragma once\n\n')
                elif cmd == "generate-keyboard-c":
                    with open(output_file, 'w') as f:
                        f.write('// Generated keyboard.c\n')
                        f.write('#include QMK_KEYBOARD_H\n\n')
                elif cmd == "generate-keyboard-h":
                    # Generate keyboard.h with layout macros
                    if keyboard:
                        # Find info.json to get layouts
                        import json
                        import os
                        info_data = {}
                        path_parts = keyboard.split('/')
                        for i in range(1, len(path_parts) + 1):
                            current_path = os.path.join('keyboards', *path_parts[:i])
                            info_file = os.path.join(current_path, 'info.json')
                            if os.path.exists(info_file):
                                with open(info_file, 'r', encoding='utf-8') as f:
                                    current_info = json.load(f)
                                    for key, value in current_info.items():
                                        if key == 'layouts' and key in info_data:
                                            info_data[key].update(value)
                                        else:
                                            info_data[key] = value

                        with open(output_file, 'w') as f:
                            f.write('// Generated keyboard.h\n')
                            f.write('#pragma once\n')
                            f.write('#include "quantum.h"\n\n')

                            # Generate layout macros
                            if 'layouts' in info_data:
                                for layout_name, layout_data in info_data['layouts'].items():
                                    if 'layout' in layout_data:
                                        num_keys = len(layout_data['layout'])
                                        # Generate key parameter list
                                        keys = ', '.join([f'k{i:02d}' for i in range(num_keys)])

                                        # Build matrix mapping - create a 2D array
                                        # First, create empty matrix
                                        if 'matrix_pins' in info_data:
                                            rows = len(info_data['matrix_pins'].get('rows', []))
                                            cols = len(info_data['matrix_pins'].get('cols', []))
                                        else:
                                            rows = 6  # default
                                            cols = 19  # default

                                        # Build matrix from layout
                                        matrix = [['KC_NO' for _ in range(cols)] for _ in range(rows)]
                                        for i, key in enumerate(layout_data['layout']):
                                            row = key['matrix'][0]
                                            col = key['matrix'][1]
                                            matrix[row][col] = f'k{i:02d}'

                                        # Generate macro
                                        f.write(f'#define {layout_name}({keys}) {{ \\\n')
                                        for r, row_keys in enumerate(matrix):
                                            row_str = '{{ ' + ', '.join(row_keys) + ' }}'
                                            if r < len(matrix) - 1:
                                                f.write(f'    {row_str}, \\\n')
                                            else:
                                                f.write(f'    {row_str} \\\n')
                                        f.write('}\n\n')
                    else:
                        with open(output_file, 'w') as f:
                            f.write('// Generated keyboard.h\n')
                            f.write('#pragma once\n')
                            f.write('#include "quantum.h"\n\n')
                elif cmd == "generate-version-h":
                    with open(output_file, 'w') as f:
                        f.write('// Generated version.h\n')
                        f.write('#pragma once\n')
                        f.write('#define QMK_VERSION "0.14.29"\n')
                        f.write('#define QMK_BUILDDATE "2024-01-01-00:00:00"\n')
                elif cmd == "generate-make-dependencies":
                    with open(output_file, 'w') as f:
                        f.write('# Generated dependencies\n')

                # Only print output file path if not quiet
                if not quiet:
                    sys.stdout.write(output_file)
                    sys.stdout.flush()
                sys.exit(0)
            else:
                # Silent exit if no output file (some commands may be optional)
                sys.exit(0)

    # For unknown commands, just exit successfully
    sys.exit(0)
