#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import subprocess
import platform
import time
from pynput import keyboard
from pynput.keyboard import Controller, Key
import pyperclip
import pyautogui

# --- DEBUG SETTING ---
DEBUG_MODE = True  # Установите True для отладки, False для обычной работы
# ---------------------

# Disable pyautogui fail-safe (optional)
pyautogui.FAILSAFE = False

kb_controller = Controller()

# --- Layout mappings ---
EN_LOWER = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
RU_LOWER = "йцукенгшщзхъфывапролджэячсмитьбю.ё"
EN_UPPER = "QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?~"
RU_UPPER = "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё"

if len(EN_LOWER) != len(RU_LOWER) or len(EN_UPPER) != len(RU_UPPER):
    print("FATAL ERROR: Keyboard mapping strings have unequal lengths.")
    sys.exit(1)

RU_TO_EN = str.maketrans(RU_LOWER + RU_UPPER, EN_LOWER + EN_UPPER)
EN_TO_RU = str.maketrans(EN_LOWER + EN_UPPER, RU_LOWER + RU_UPPER)


# -------------------------

class PlatformHandler:
    """Platform-specific operations"""

    @staticmethod
    def is_linux():
        return sys.platform.startswith('linux')

    @staticmethod
    def is_mac():
        return sys.platform == 'darwin'

    # ... (методы get_clipboard, set_clipboard, select_text_left, copy_selection, paste_text, switch_layout остаются без изменений) ...
    @staticmethod
    def get_clipboard():
        try:
            text = pyperclip.paste()
            if text: return text
            if PlatformHandler.is_linux():
                try:
                    result = subprocess.run(['wl-paste'], capture_output=True, text=True, timeout=0.5)
                    if result.stdout: return result.stdout
                    result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True,
                                            timeout=0.5)
                    if result.stdout: return result.stdout
                except:
                    pass
        except:
            pass
        return ""

    @staticmethod
    def set_clipboard(text):
        try:
            pyperclip.copy(text)
        except:
            try:
                if PlatformHandler.is_linux():
                    subprocess.run(['wl-copy'], input=text.encode('utf-8'), timeout=0.5)
                elif PlatformHandler.is_mac():
                    subprocess.run(['pbcopy'], input=text.encode('utf-8'), timeout=0.5)
            except:
                pass

    @staticmethod
    def select_text_left():
        if PlatformHandler.is_linux():
            try:
                subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+shift+Home'], timeout=0.5)
                return True
            except:
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
        if PlatformHandler.is_mac():
            with kb_controller.pressed(Key.cmd if hasattr(Key, 'cmd') else Key.ctrl):
                kb_controller.press('c')
                kb_controller.release('c')
        else:
            with kb_controller.pressed(Key.ctrl):
                kb_controller.press('c')
                kb_controller.release('c')
        time.sleep(0.05)

    @staticmethod
    def paste_text():
        if PlatformHandler.is_mac():
            with kb_controller.pressed(Key.cmd if hasattr(Key, 'cmd') else Key.ctrl):
                kb_controller.press('v')
                kb_controller.release('v')
        else:
            with kb_controller.pressed(Key.ctrl):
                kb_controller.press('v')
                kb_controller.release('v')
        time.sleep(0.05)

    @staticmethod
    def switch_layout():
        time.sleep(0.05)
        if PlatformHandler.is_linux():
            try:
                subprocess.run(['xdotool', 'key', 'alt+shift'], timeout=0.5)
            except:
                with kb_controller.pressed(Key.alt_l):
                    kb_controller.press(Key.shift)
                    kb_controller.release(Key.shift)
        elif PlatformHandler.is_mac():
            with kb_controller.pressed(Key.cmd if hasattr(Key, 'cmd') else Key.ctrl):
                kb_controller.press(Key.space)
                kb_controller.release(Key.space)


def is_cyrillic(char):
    return '\u0400' <= char <= '\u04FF'


def is_latin(char):
    char_lower = char.lower()
    return 'a' <= char_lower <= 'z'


def is_letter(char):
    return is_cyrillic(char) or is_latin(char)


def find_wrong_layout_boundary(text):
    if not text: return None
    last_letter = next((char for char in reversed(text) if is_letter(char)), None)
    if not last_letter: return None
    wrong_is_cyrillic = is_cyrillic(last_letter)
    boundary_pos = 0
    for i in range(len(text) - 1, -1, -1):
        char = text[i]
        if is_letter(char):
            if (wrong_is_cyrillic and is_latin(char)) or (not wrong_is_cyrillic and is_cyrillic(char)):
                boundary_pos = i + 1
                break
    wrong_text = text[boundary_pos:]
    return wrong_text if wrong_text else None


def convert_layout(text):
    if not text: return text
    first_letter = next((c for c in text if is_letter(c)), None)
    if not first_letter: return text
    if is_cyrillic(first_letter):
        return text.translate(RU_TO_EN)
    else:
        return text.translate(EN_TO_RU)


def fix_layout():
    """Main function to fix keyboard layout triggered by the hotkey"""
    if DEBUG_MODE:
        print("\n--- Hotkey pressed: Attempting layout fix ---")
    try:
        original_clipboard = PlatformHandler.get_clipboard()
        if DEBUG_MODE:
            print(f"Original clipboard: '{original_clipboard[:30]}...'")

        # Select text from cursor to start of line
        PlatformHandler.select_text_left()
        time.sleep(0.05)

        # Copy selected text
        PlatformHandler.copy_selection()
        time.sleep(0.1)

        all_text = PlatformHandler.get_clipboard()
        if DEBUG_MODE:
            print(f"Selected text ('all_text'): '{all_text[:30]}...'")

        if not all_text or all_text == original_clipboard:
            if DEBUG_MODE:
                print("No new text selected or clipboard is empty. Exiting fix_layout.")
            PlatformHandler.set_clipboard(original_clipboard)
            return

        wrong_text = find_wrong_layout_boundary(all_text)
        if wrong_text:
            if DEBUG_MODE:
                print(f"Wrong layout part identified: '{wrong_text}'")
            converted_text = convert_layout(wrong_text)
            full_corrected_text = all_text[:len(all_text) - len(wrong_text)] + converted_text

            if DEBUG_MODE:
                print(f"Converted text: '{converted_text}'")
                print(f"Full corrected text: '{full_corrected_text[:30]}...'")

            PlatformHandler.set_clipboard(full_corrected_text)

            # Paste the corrected text back into the application
            PlatformHandler.paste_text()

        PlatformHandler.set_clipboard(original_clipboard)  # Restore original clipboard content
        if DEBUG_MODE:
            print("--- Layout fix completed ---")

    except Exception as e:
        print(f"An error occurred during layout fixing: {e}")


# ... (весь остальной код скрипта остается прежним до функций on_press) ...

# --- KEYBOARD LISTENER LOGIC ---

def on_press(key):
    """Handles key press events."""
    if DEBUG_MODE:
        try:
            print(f"Key pressed: {key.char!r} (Special Key: {key})")
        except AttributeError:
            # Это сработает для специальных клавиш
            print(f"Key pressed: {key}")

    # *** ИЗМЕНЕНО: Убрали 'break_space'. Используем 'pause' или 'insert' или 'f12' ***
    # Используйте одну из этих клавиш в качестве горячей:
    if key == keyboard.Key.pause or key == keyboard.Key.insert or key == keyboard.Key.f12:
        fix_layout()

    # Если вы хотите использовать комбинацию (например, Ctrl + Insert),
    # логика pynput усложняется, но для одиночной клавиши так проще.


def on_release(key):
    pass


# Setup and start the listener
if __name__ == '__main__':
    # Также обновим сообщение при запуске
    print(
        f"Layout fixer script started. DEBUG_MODE is {DEBUG_MODE}. Waiting for hotkey (Pause, Insert, or F12) press...")
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()
