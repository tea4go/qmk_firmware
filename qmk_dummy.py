#!/usr/bin/env python3
# Dummy qmk script to work around HOME directory issue
import sys

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

    # For unknown commands, just exit successfully
    sys.exit(0)
