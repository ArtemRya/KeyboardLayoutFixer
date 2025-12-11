#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-Platform Keyboard Layout Fixer
Works on Ubuntu (X11/Wayland) and macOS (Intel/Apple Silicon)
Author: Created with Claude AI
License: MIT

Dependencies:
    pip install pynput pyperclip pyautogui

Ubuntu additional:
    sudo apt install wl-clipboard xdotool (for X11/Wayland)

macOS additional:
    No additional tools needed

AUTOSTART:
    Ubuntu: Save as ~/.config/autostart/layout-fixer.desktop
    macOS: Save as ~/Library/LaunchAgents/com.user.layoutfixer.plist
"""
import sys
import subprocess
import platform
import time
from pynput import keyboard
from pynput.keyboard import Controller, Key
import pyperclip
import pyautogui

# Disable pyautogui fail-safe (optional)
pyautogui.FAILSAFE = False

kb_controller = Controller()

# Layout mappings
RU_TO_EN = str.maketrans(
    "йцукенгшщзхъфывапролджэячсмитьбю.ёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё",
    "qwertyuiop[]asdfghjkl;'zxcvbnm,./`QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?~"
)

EN_TO_RU = str.maketrans(
    "qwertyuiop[]asdfghjkl;'zxcvbnm,./`QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?~",
    "йцукенгшщзхъфывапролджэячсмитьбю.ёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё"
)


class PlatformHandler:
    """Platform-specific operations"""

    @staticmethod
    def is_linux():
        return sys.platform.startswith('linux')

    @staticmethod
    def is_mac():
        return sys.platform == 'darwin'

    @staticmethod
    def get_clipboard():
        """Universal clipboard getter"""
        try:
            # Try pyperclip first
            text = pyperclip.paste()
            if text:
                return text

            # Fallback for Linux
            if PlatformHandler.is_linux():
                try:
                    # Try wl-clipboard (Wayland)
                    result = subprocess.run(['wl-paste'],
                                            capture_output=True, text=True, timeout=0.5)
                    if result.stdout:
                        return result.stdout

                    # Try xclip (X11)
                    result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'],
                                            capture_output=True, text=True, timeout=0.5)
                    if result.stdout:
                        return result.stdout
                except:
                    pass
        except:
            pass
        return ""

    @staticmethod
    def set_clipboard(text):
        """Universal clipboard setter"""
        try:
            pyperclip.copy(text)
        except:
            try:
                if PlatformHandler.is_linux():
                    # Try wl-copy (Wayland)
                    subprocess.run(['wl-copy'], input=text.encode('utf-8'), timeout=0.5)
                elif PlatformHandler.is_mac():
                    subprocess.run(['pbcopy'], input=text.encode('utf-8'), timeout=0.5)
            except:
                pass

    @staticmethod
    def select_text_left():
        """Select text from cursor to line start"""
        if PlatformHandler.is_linux():
            try:
                # Try X11 first
                subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+shift+Home'],
                               timeout=0.5)
                return True
            except:
                # Fallback to pyautogui for Wayland
                with kb_controller.pressed(Key.ctrl_l if hasattr(Key, 'ctrl_l') else Key.ctrl):
                    kb_controller.press(Key.shift)
                    kb_controller.press(Key.home)
                    kb_controller.release(Key.home)
                    kb_controller.release(Key.shift)
                return True
        elif PlatformHandler.is_mac():
            with kb_controller.pressed(Key.cmd if hasattr(Key, 'cmd') else Key.ctrl):
                kb_controller.press(Key.shift)
                kb_controller.press(Key.home)
                kb_controller.release(Key.home)
                kb_controller.release(Key.shift)
            return True
        return False

    @staticmethod
    def copy_selection():
        """Copy selected text"""
        if PlatformHandler.is_mac():
            # macOS uses Cmd+C
            with kb_controller.pressed(Key.cmd if hasattr(Key, 'cmd') else Key.ctrl):
                kb_controller.press('c')
                kb_controller.release('c')
        else:
            # Linux/Windows use Ctrl+C
            with kb_controller.pressed(Key.ctrl):
                kb_controller.press('c')
                kb_controller.release('c')
        time.sleep(0.05)

    @staticmethod
    def paste_text():
        """Paste text"""
        if PlatformHandler.is_mac():
            # macOS uses Cmd+V
            with kb_controller.pressed(Key.cmd if hasattr(Key, 'cmd') else Key.ctrl):
                kb_controller.press('v')
                kb_controller.release('v')
        else:
            # Linux/Windows use Ctrl+V
            with kb_controller.pressed(Key.ctrl):
                kb_controller.press('v')
                kb_controller.release('v')
        time.sleep(0.05)

    @staticmethod
    def switch_layout():
        """Switch keyboard layout (simulate Alt+Shift or Cmd+Space)"""
        time.sleep(0.05)
        if PlatformHandler.is_linux():
            # Linux layout switch
            try:
                subprocess.run(['xdotool', 'key', 'alt+shift'], timeout=0.5)
            except:
                # Simulate Alt+Shift
                with kb_controller.pressed(Key.alt_l):
                    kb_controller.press(Key.shift)
                    kb_controller.release(Key.shift)
        elif PlatformHandler.is_mac():
            # macOS layout switch (Cmd+Space)
            with kb_controller.pressed(Key.cmd if hasattr(Key, 'cmd') else Key.ctrl):
                kb_controller.press(Key.space)
                kb_controller.release(Key.space)


def is_cyrillic(char):
    """Check if character is Cyrillic"""
    return '\u0400' <= char <= '\u04FF'


def is_latin(char):
    """Check if character is Latin"""
    char_lower = char.lower()
    return 'a' <= char_lower <= 'z'


def is_letter(char):
    """Check if character is a letter"""
    return is_cyrillic(char) or is_latin(char)


def find_wrong_layout_boundary(text):
    """Find boundary where layout changes"""
    if not text:
        return None

    # Find the rightmost letter
    last_letter = None
    for char in reversed(text):
        if is_letter(char):
            last_letter = char
            break

    if not last_letter:
        return None

    # Determine what layout is "wrong" (last letter's layout)
    wrong_is_cyrillic = is_cyrillic(last_letter)

    # Find where the layout changes
    boundary_pos = 0
    for i in range(len(text) - 1, -1, -1):
        char = text[i]
        if is_letter(char):
            if wrong_is_cyrillic and is_latin(char):
                boundary_pos = i + 1
                break
            if not wrong_is_cyrillic and is_cyrillic(char):
                boundary_pos = i + 1
                break

    wrong_text = text[boundary_pos:]
    return wrong_text if wrong_text else None


def convert_layout(text):
    """Convert text between RU and EN layouts"""
    if not text:
        return text

    # Find first letter to determine layout
    first_letter = next((c for c in text if is_letter(c)), None)
    if not first_letter:
        return text

    if is_cyrillic(first_letter):
        return text.translate(RU_TO_EN)
    else:
        return text.translate(EN_TO_RU)


def fix_layout():
    """Main function to fix keyboard layout"""
    try:
        # Save original clipboard
        original_clipboard = PlatformHandler.get_clipboard()

        # Select text from cursor to start of line
        PlatformHandler.select_text_left()
        time.sleep(0.05)

        # Copy selected text
        PlatformHandler.copy_selection()
        time.sleep(0.1)

        # Get the text
        all_text = PlatformHandler.get_clipboard()

        if not all_text or all_text == original_clipboard:
            PlatformHandler.set_clipboard(original_clipboard)
            return

        # Find wrong layout part
        wrong_text = find_wrong_layout_boundary(all_text)
        if not wrong_text:
            PlatformHandler.set_clipboard(original_clipboard)
            return

        # Convert wrong part
        fixed_text = convert_layout(wrong_text)
        boundary_pos = len(all_text) - len(wrong_text)
        correct_part = all_text[:boundary_pos]
        result_text = correct_part + fixed_text

        # Put result to clipboard and paste
        PlatformHandler.set_clipboard(result_text)
        PlatformHandler.paste_text()

        # Restore original clipboard
        time.sleep(0.05)
        PlatformHandler.set_clipboard(original_clipboard)

        # Switch layout to correct one
        PlatformHandler.switch_layout()

    except Exception as e:
        print(f"Error in fix_layout: {e}")


def on_activate():
    """Hotkey activation handler"""
    try:
        fix_layout()
    except Exception as e:
        print(f"Error: {e}")


def check_dependencies():
    """Check and install dependencies"""
    system = platform.system()

    print(f"System: {system} {platform.machine()}")

    if system == "Linux":
        # Check for Wayland or X11
        session_type = subprocess.run(
            ['echo', '$XDG_SESSION_TYPE'],
            capture_output=True, text=True, shell=True
        ).stdout.strip()

        print(f"Session type: {session_type}")

        # Check for wl-clipboard (Wayland)
        if 'wayland' in session_type.lower():
            try:
                subprocess.run(['which', 'wl-copy'], check=True)
                subprocess.run(['which', 'wl-paste'], check=True)
            except:
                print("For Wayland support, install wl-clipboard:")
                print("sudo apt install wl-clipboard")
                return False

        # Check for xclip/xdotool (X11 fallback)
        try:
            subprocess.run(['which', 'xdotool'], check=True)
        except:
            print("Install xdotool for X11 support:")
            print("sudo apt install xdotool")
            # Continue anyway, we have fallbacks

    return True


def main():
    """Main function"""
    print("Cross-Platform Keyboard Layout Fixer")
    print("Press Pause/Break or Scroll Lock to fix layout")
    print("Press Ctrl+C to exit\n")

    if not check_dependencies():
        print("Some dependencies missing, but will try to continue...")

    # Define hotkeys based on platform
    if PlatformHandler.is_mac():
        # macOS doesn't have Pause/ScrollLock, use F13-F15
        hotkey_map = {
            '<f13>': on_activate,  # Often unused function key
            '<f14>': on_activate,
        }
    else:
        # Linux/Windows use standard keys
        hotkey_map = {
            '<pause>': on_activate,
            '<scroll_lock>': on_activate,
        }

    # Add Ctrl+Alt+L as universal hotkey
    hotkey_map['<ctrl>+<alt>+l'] = on_activate

    # Start hotkey listener
    with keyboard.GlobalHotKeys(hotkey_map) as hotkey:
        try:
            hotkey.join()
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()