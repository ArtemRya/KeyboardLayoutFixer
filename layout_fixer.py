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
DEBUG_MODE = False
# ---------------------

# --- КОНСТАНТЫ ЛИМИТОВ ---
MAX_CHARS_TO_FIX = 100
# -------------------------

pyautogui.FAILSAFE = False
kb_controller = Controller()

# --- Layout mappings (без изменений) ---
EN_LOWER = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
RU_LOWER = "йцукенгшщзхъфывапролджэячсмитьбю.ё"
EN_UPPER = "QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?~"
RU_UPPER = "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё"
if len(EN_LOWER) != len(RU_LOWER) or len(EN_UPPER) != len(RU_UPPER):
    print("FATAL ERROR: Keyboard mapping strings have unequal lengths.")
    sys.exit(1)
RU_TO_EN = str.maketrans(RU_LOWER + RU_UPPER, EN_LOWER + EN_UPPER)
EN_TO_RU = str.maketrans(EN_LOWER + EN_UPPER, RU_LOWER + RU_UPPER)


# ----------------------------------------------------------------------


class PlatformHandler:
    @staticmethod
    def is_linux():
        return sys.platform.startswith('linux')

    @staticmethod
    def is_mac():
        return sys.platform == 'darwin'

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
        # Linux использует Ctrl+Shift+Home
        modifier_key = Key.ctrl_l if PlatformHandler.is_linux() else Key.cmd
        with kb_controller.pressed(modifier_key):
            with kb_controller.pressed(Key.shift):
                kb_controller.press(Key.home)
                kb_controller.release(Key.home)
        return True

    @staticmethod
    def copy_selection():
        modifier_key = Key.ctrl if PlatformHandler.is_linux() else Key.cmd
        with kb_controller.pressed(modifier_key):
            kb_controller.press('c')
            kb_controller.release('c')
        time.sleep(0.05)

    @staticmethod
    def paste_text():
        modifier_key = Key.ctrl if PlatformHandler.is_linux() else Key.cmd
        with kb_controller.pressed(modifier_key):
            kb_controller.press('v')
            kb_controller.release('v')
        time.sleep(0.05)

    # *** ОБНОВЛЕНО: Используем Win+Space (Key.cmd+Key.space) для переключения раскладки ***
    @staticmethod
    def switch_layout():
        if DEBUG_MODE: print("Switching layout (Win+Space)...")
        time.sleep(0.05)
        # На Linux/Windows Key.cmd соответствует клавише Super (Win)
        with kb_controller.pressed(Key.cmd):
            kb_controller.press(Key.space)
            kb_controller.release(Key.space)
        time.sleep(0.05)


def is_cyrillic(char): return '\u0400' <= char <= '\u04FF'


def is_latin(char): char_lower = char.lower(); return 'a' <= char_lower <= 'z'


def is_letter(char): return is_cyrillic(char) or is_latin(char)


def find_wrong_layout_boundary(text):
    if not text: return None
    search_text = text[-MAX_CHARS_TO_FIX:]
    if ' ' in search_text:
        last_space_index = search_text.rfind(' ')
        search_text = search_text[last_space_index + 1:]
    if not search_text: return None
    last_letter = next((char for char in reversed(search_text) if is_letter(char)), None)
    if not last_letter: return None
    wrong_is_cyrillic = is_cyrillic(last_letter)
    boundary_pos = 0
    for i in range(len(search_text) - 1, -1, -1):
        char = search_text[i]
        if is_letter(char):
            if (wrong_is_cyrillic and is_latin(char)) or (not wrong_is_cyrillic and is_cyrillic(char)):
                boundary_pos = i + 1
                break
    wrong_text_relative = search_text[boundary_pos:]
    if not wrong_text_relative: return None
    original_boundary_pos = len(text) - len(search_text) + boundary_pos
    return text[original_boundary_pos:]


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
    if DEBUG_MODE: print("\n--- Hotkey pressed: Attempting layout fix ---")
    try:
        original_clipboard = PlatformHandler.get_clipboard()
        PlatformHandler.select_text_left()
        time.sleep(0.05)
        PlatformHandler.copy_selection()
        time.sleep(0.1)
        all_text = PlatformHandler.get_clipboard()

        if not all_text or all_text == original_clipboard:
            PlatformHandler.set_clipboard(original_clipboard)
            return

        wrong_text = find_wrong_layout_boundary(all_text)
        if wrong_text:
            converted_text = convert_layout(wrong_text)

            if not converted_text or converted_text == wrong_text:
                PlatformHandler.set_clipboard(original_clipboard)
                return

            full_corrected_text = all_text[:len(all_text) - len(wrong_text)] + converted_text

            PlatformHandler.set_clipboard(full_corrected_text)
            PlatformHandler.paste_text()

            # *** ИСПОЛЬЗУЕМ WIN+SPACE ***
            PlatformHandler.switch_layout()

        PlatformHandler.set_clipboard(original_clipboard)
        if DEBUG_MODE: print("--- Layout fix completed ---")

    except Exception as e:
        print(f"An error occurred during layout fixing: {e}")


# --- KEYBOARD LISTENER LOGIC ---

def on_press(key, injected=False):
    if injected: return
    if DEBUG_MODE:
        try:
            print(f"\nUser key pressed: {key.char!r} (Special Key: {key})")
        except AttributeError:
            print(f"\nUser key pressed: {key}")

    # Горячая клавиша: Insert, Pause или F12
    if key == keyboard.Key.insert or key == keyboard.Key.pause: # or key == keyboard.Key.f12:
        fix_layout()


def on_release(key):
    pass


if __name__ == '__main__':
    print(f"Layout fixer script started. Waiting for hotkey (Pause, Insert, or F12) press...")
    with keyboard.Listener(
            on_press=lambda key, injected=False: on_press(key, injected),
            on_release=on_release) as listener:
        listener.join()
