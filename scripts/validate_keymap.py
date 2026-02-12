#!/usr/bin/env python3
"""
Validate ZMK keymap keycodes against known valid codes.
This catches common typos like C_VOL_MUTE (should be C_MUTE).
"""

import re
import sys
from pathlib import Path

# Common valid ZMK keycodes (not exhaustive but covers most usage)
VALID_KEYCODES = {
    # Letters
    *[chr(c) for c in range(ord('A'), ord('Z') + 1)],
    # Numbers
    *[f'N{i}' for i in range(10)], *[f'NUMBER_{i}' for i in range(10)],
    # Function keys
    *[f'F{i}' for i in range(1, 25)],
    # Modifiers
    'LSHFT', 'RSHFT', 'LSHIFT', 'RSHIFT', 'LCTRL', 'RCTRL', 'LALT', 'RALT',
    'LGUI', 'RGUI', 'LMETA', 'RMETA', 'LWIN', 'RWIN', 'LCMD', 'RCMD',
    # Navigation
    'UP', 'DOWN', 'LEFT', 'RIGHT', 'HOME', 'END', 'PG_UP', 'PG_DN',
    'PAGE_UP', 'PAGE_DOWN', 'INS', 'INSERT', 'DEL', 'DELETE',
    # Common keys
    'SPACE', 'RET', 'RETURN', 'ENTER', 'TAB', 'ESC', 'ESCAPE',
    'BSPC', 'BACKSPACE', 'CAPS', 'CAPSLOCK', 'CAPS_LOCK',
    'PSCRN', 'PRINTSCREEN', 'PRINT_SCREEN', 'SLCK', 'SCROLLLOCK', 'SCROLL_LOCK',
    'PAUSE_BREAK', 'PAUSE',
    # Punctuation
    'MINUS', 'EQUAL', 'LBKT', 'RBKT', 'LBRC', 'RBRC',
    'LEFT_BRACKET', 'RIGHT_BRACKET', 'LEFT_BRACE', 'RIGHT_BRACE',
    'BSLH', 'BACKSLASH', 'SEMI', 'SEMICOLON', 'SQT', 'APOS', 'APOSTROPHE',
    'GRAVE', 'COMMA', 'DOT', 'PERIOD', 'SLASH', 'FSLH',
    'TILDE', 'EXCL', 'EXCLAMATION', 'AT', 'AT_SIGN', 'HASH', 'POUND',
    'DLLR', 'DOLLAR', 'PRCNT', 'PERCENT', 'CARET', 'AMPS', 'AMPERSAND',
    'ASTRK', 'ASTERISK', 'STAR', 'LPAR', 'RPAR',
    'LEFT_PARENTHESIS', 'RIGHT_PARENTHESIS', 'UNDER', 'UNDERSCORE',
    'PLUS', 'PIPE', 'COLON', 'DQT', 'DOUBLE_QUOTES', 'LT', 'GT',
    'QMARK', 'QUESTION',
    # Numpad
    *[f'KP_N{i}' for i in range(10)], 'KP_PLUS', 'KP_MINUS', 'KP_MULTIPLY',
    'KP_DIVIDE', 'KP_DOT', 'KP_ENTER', 'KP_EQUAL', 'KP_NUMLOCK', 'NUMLOCK',
    # Consumer/Media controls
    'C_MUTE', 'C_VOL_UP', 'C_VOL_DN', 'C_VOLUME_UP', 'C_VOLUME_DOWN',
    'C_PP', 'C_PLAY_PAUSE', 'C_PLAY', 'C_PAUSE', 'C_STOP',
    'C_NEXT', 'C_PREV', 'C_PREVIOUS', 'C_FF', 'C_RW', 'C_FAST_FORWARD', 'C_REWIND',
    'C_BRI_UP', 'C_BRI_DN', 'C_BRIGHTNESS_INC', 'C_BRIGHTNESS_DEC',
    'C_AL_CALC', 'C_AL_WWW', 'C_AL_MAIL', 'C_AL_FILES',
    'C_AC_SEARCH', 'C_AC_HOME', 'C_AC_BACK', 'C_AC_FORWARD', 'C_AC_REFRESH',
    # Mouse scroll
    'SCRL_UP', 'SCRL_DOWN', 'SCRL_LEFT', 'SCRL_RIGHT',
    # Mouse move
    'MOVE_UP', 'MOVE_DOWN', 'MOVE_LEFT', 'MOVE_RIGHT',
    # Mouse buttons
    'LCLK', 'RCLK', 'MCLK', 'MB1', 'MB2', 'MB3', 'MB4', 'MB5',
    # Bluetooth
    'BT_CLR', 'BT_CLR_ALL', 'BT_NXT', 'BT_PRV',
    *[f'BT_SEL {i}' for i in range(5)],
    # Output selection
    'OUT_USB', 'OUT_BLE', 'OUT_TOG',
    # Power
    'C_PWR', 'C_POWER', 'C_SLEEP', 'C_AL_LOCK',
    # Reset
    'RESET', 'BOOTLOADER',
}

# Behaviors that don't need keycode validation
VALID_BEHAVIORS = {
    'trans', 'none', 'kp', 'mo', 'lt', 'mt', 'sk', 'sl', 'tog', 'to',
    'bt', 'mkp', 'msc', 'mmv', 'mms', 'out', 'rgb_ug', 'ext_power',
    'caps_word', 'key_repeat', 'reset', 'bootloader', 'sys_reset',
}

def extract_bindings(content: str) -> list[tuple[int, str, str]]:
    """Extract all binding references from keymap content."""
    bindings = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('//') or line.strip().startswith('/*'):
            continue
        # Find all &behavior ARG patterns
        for match in re.finditer(r'&(\w+)\s+([A-Za-z0-9_]+)', line):
            behavior = match.group(1)
            arg = match.group(2)
            bindings.append((i, behavior, arg))
    return bindings

def validate_keymap(filepath: Path) -> list[str]:
    """Validate keymap and return list of errors."""
    content = filepath.read_text()
    bindings = extract_bindings(content)
    errors = []
    
    # Valid mouse button codes
    valid_mkp = {'LCLK', 'RCLK', 'MCLK', 'MB1', 'MB2', 'MB3', 'MB4', 'MB5'}
    # Valid scroll codes  
    valid_msc = {'SCRL_UP', 'SCRL_DOWN', 'SCRL_LEFT', 'SCRL_RIGHT'}
    # Valid mouse move codes
    valid_mmv = {'MOVE_UP', 'MOVE_DOWN', 'MOVE_LEFT', 'MOVE_RIGHT'}
    
    for line_num, behavior, arg in bindings:
        if behavior == 'kp':
            if arg not in VALID_KEYCODES:
                suggestions = []
                if 'VOL_MUTE' in arg:
                    suggestions.append('C_MUTE')
                if 'VOL_DOWN' in arg:
                    suggestions.append('C_VOL_DN')
                msg = f"Line {line_num}: Unknown keycode '{arg}'"
                if suggestions:
                    msg += f" (did you mean: {', '.join(suggestions)}?)"
                errors.append(msg)
        elif behavior == 'mkp':
            if arg not in valid_mkp:
                errors.append(f"Line {line_num}: Invalid mouse button '{arg}' (valid: {', '.join(sorted(valid_mkp))})")
        elif behavior == 'msc':
            if arg not in valid_msc:
                errors.append(f"Line {line_num}: Invalid scroll code '{arg}' (valid: {', '.join(sorted(valid_msc))})")
        elif behavior == 'mmv':
            if arg not in valid_mmv:
                errors.append(f"Line {line_num}: Invalid mouse move '{arg}' (valid: {', '.join(sorted(valid_mmv))})")
    
    return errors

def main():
    if len(sys.argv) < 2:
        print("Usage: validate_keymap.py <keymap_file>")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    errors = validate_keymap(filepath)
    
    if errors:
        print("✗ Keymap validation failed:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✓ Keymap keycodes are valid")
        sys.exit(0)

if __name__ == '__main__':
    main()
