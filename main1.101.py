import os
import sys
import time
import random
import subprocess
import ctypes
import ctypes.wintypes
import msvcrt
import json
import re
import shutil
import uuid
import winsound
import wave
import tempfile
import threading
import struct

# ============================================================
# THE LAST SHELTER
# Версия 1.101
# Автономная консольная версия игры
# ============================================================

# ============================================================
# НАСТРОЙКИ
# ============================================================

GAME_TITLE = "THE LAST SHELTER"

MAP_WIDTH = 30
MAP_HEIGHT = 15

SCREEN_WIDTH = 60
SCREEN_HEIGHT = 30

MOVEMENT_INTERVAL = 0.12
HUD_HEIGHT = 10
INVENTORY_SLOTS = 40
SAVE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "saves"
)

# Отдельный файл пользовательских настроек.
# Здесь сохраняются только параметры интерфейса, которые должны
# переживать перезапуск игры.
SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "settings.json"
)

SOUNDS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "sounds"
)

SAVE_SLOTS = 6

WT_PROFILE_NAME = "THE_LAST_SHELTER_INTERNAL"
WT_FRAGMENT_APP_NAME = "TheLastShelter"
WT_FRAGMENT_FILE_NAME = "the_last_shelter.json"


PLAYER_SYMBOL = "@"
ENEMY_SYMBOL = "E"
OBJECT_SYMBOL = "O"
WALL_SYMBOL = "#"
GROUND_SYMBOL = "."

ANSI_YELLOW = "\033[93m"
ANSI_RESET = "\033[0m"
ANSI_ESCAPE_RE = re.compile(r"\033\[[0-9;?]*[A-Za-z]")


# ============================================================
# ЛОКАЛИЗАЦИЯ
# ============================================================
# Язык хранится как стабильное значение настройки. Все графические
# элементы интерфейса (рамки, символы карты, цифры и клавиши)
# остаются неизменными. Переводится только текст интерфейса.
UI_TRANSLATIONS = {
    "English": {
        "НОВАЯ ИГРА": "NEW GAME",
        "Введите имя персонажа:": "Enter character name:",
        "Назад [ESC]": "Back [ESC]",
        "Новая игра": "New Game",
        "Загрузить игру": "Load Game",
        "Сохранить игру": "Save Game",
        "Настройки": "Settings",
        "НАСТРОЙКИ": "SETTINGS",
        "Выход": "Exit",
        "До свидания!": "Goodbye!",
        "СОХРАНЕНИЕ ИГРЫ": "SAVE GAME",
        "ЗАГРУЗКА ИГРЫ": "LOAD GAME",
        "Удалить [X]": "Delete [X]",
        "Пустой слот": "Empty slot",
        "Слот пуст.": "Slot is empty.",
        "УДАЛЕНИЕ СОХРАНЕНИЯ": "DELETE SAVE",
        "Удалить сохранение": "Delete Save",
        "Отмена": "Cancel",
        "Не удалось удалить сохранение.": "Failed to delete save.",
        "Не удалось загрузить сохранение.": "Failed to load save.",
        "ПЕРЕЗАПИСЬ СЛОТА": "OVERWRITE SLOT",
        "Перезаписать слот": "Overwrite Slot",
        "Не удалось сохранить игру.": "Failed to save game.",
        "E / ESC — продолжить": "E / ESC — continue",
        "Слот ": "Slot ",
        " удалён.": " deleted.",
        " сохранён.": " saved.",
        "ЗВУК": "SOUND",
        "Звук": "Sound",
        "Общая громкость": "Master Volume",
        "Громкость музыки": "Music Volume",
        "Громкость интерфейса": "Interface Volume",
        "Звуки": "Sounds",
        "включены": "enabled",
        "выключены": "disabled",
        "ЭКРАН": "SCREEN",
        "Экран": "Screen",
        "Полный экран": "Fullscreen",
        "Включено": "Enabled",
        "Выключено": "Disabled",
        "Шрифт": "Font",
        "Обычный": "Normal",
        "Жирный": "Bold",
        "ЯЗЫК": "LANGUAGE",
        "Язык": "Language",
        "УПРАВЛЕНИЕ": "CONTROLS",
        "Управление": "Controls",
        "Руководство": "Guide",
        "Схема управления": "Control Scheme",
        "Клавиатура": "Keyboard",
        "Клавиатура+Мышь": "Keyboard+Mouse",
        "Движение: W/A/S/D": "Movement: W/A/S/D",
        "Взаимодействие: E": "Interaction: E",
        "Разместить объект: F": "Place object: F",
        "Инвентарь: TAB": "Inventory: TAB",
        "Карта: M": "Map: M",
        "W/A — вверх   S/D — вниз   E — выбор": "W/A — up   S/D — down   E — select",
        "ESC — назад": "ESC — back",
        "Игрок:": "Player:",
        "HP:": "HP:",
        "Энергия:": "Energy:",
        "Голод:": "Hunger:",
        "Жажда:": "Thirst:",
        "Усталость:": "Fatigue:",
        "Температура тела:": "Body Temperature:",
        "Вес:": "Weight:",
        "БИОМ: Лес": "BIOME: Forest",
        "Температура воздуха:": "Air Temperature:",
        "Погода: Ясно": "Weather: Clear",
        "Ветер:": "Wind:",
        "Время: День": "Time: Day",
        "Позиция:": "Position:",
        "ИНВЕНТАРЬ": "INVENTORY",
        "Атаковать": "Attack",
        "Уйти": "Leave",
        "Противник:": "Enemy:",
        "Осмотреть": "Inspect",
        "Взаимодействие:": "Interaction:",
        "Ваш персонаж погиб.": "Your character has died.",
        "ПОБЕДА!": "VICTORY!",
        "Вы победили всех противников.": "You defeated all enemies.",
        "ПАУЗА": "PAUSE",
        "Продолжить игру": "Continue Game",
        "Выйти в главное меню": "Return to Main Menu",
        "ОШИБКА ИГРЫ": "GAME ERROR",
        "Нажмите любую клавишу для выхода...": "Press any key to exit..."
    }
}


def visible_len(text):
    return len(ANSI_ESCAPE_RE.sub("", str(text)))


# ============================================================
# СУЩНОСТИ
# ============================================================

class Player:

    def __init__(
        self,
        x,
        y,
        name,
        hp=100,
        max_hp=100,
        attack=20
    ):

        self.x = x
        self.y = y

        self.name = name

        self.hp = hp
        self.max_hp = max_hp

        self.attack = attack

        # Базовые параметры выживания. Пока механики их изменения не
        # реализованы, значения используются как состояние интерфейса.
        self.energy = 100
        self.max_energy = 100
        self.hunger = 100
        self.thirst = 100
        self.fatigue = 0
        self.temperature = 36.6
        self.weight = 0.0
        self.max_weight = 20.0


class Enemy:

    def __init__(
        self,
        x,
        y,
        name,
        hp,
        max_hp,
        attack
    ):

        self.x = x
        self.y = y

        self.name = name

        self.hp = hp
        self.max_hp = max_hp

        self.attack = attack


class GameObject:

    def __init__(
        self,
        x,
        y,
        name,
        description
    ):

        self.x = x
        self.y = y

        self.name = name
        self.description = description

        self.used = False


# ============================================================
# ИГРА
# ============================================================

class SoundManager:
    """Проигрывание коротких звуков интерфейса с раздельной громкостью."""

    def __init__(self, game):
        self.game = game
        self.sounds = {
            "move": os.path.join(SOUNDS_DIR, "menu_move.wav"),
            "select": os.path.join(SOUNDS_DIR, "menu_select.wav"),
            "back": os.path.join(SOUNDS_DIR, "menu_back.wav")
        }
        self._scaled_cache = {}
        self._temp_dir = os.path.join(tempfile.gettempdir(), "the_last_shelter_sounds")
        try:
            os.makedirs(self._temp_dir, exist_ok=True)
        except Exception:
            pass

    def _effective_volume(self, channel="interface"):
        """Возвращает итоговую громкость с учётом общей и канальной громкости."""
        if not self.game.settings.get("sounds_enabled", True):
            return 0

        master = max(0, min(100, int(self.game.settings.get("master_volume", 100))))
        if channel == "music":
            specific = max(0, min(100, int(self.game.settings.get("music_volume", 80))))
        else:
            specific = max(0, min(100, int(self.game.settings.get("interface_volume", 100))))

        return round(master * specific / 100)

    def _scaled_wav_path(self, path, volume):
        """Создаёт и кэширует WAV с изменённой громкостью."""
        if volume >= 100:
            return path

        cache_key = (path, volume)
        cached = self._scaled_cache.get(cache_key)
        if cached and os.path.isfile(cached):
            return cached

        try:
            with wave.open(path, "rb") as source:
                params = source.getparams()
                frames = source.readframes(source.getnframes())

            # Поддерживаем обычный PCM WAV. Для неизвестного формата
            # безопасно используем исходный файл.
            if params.comptype != "NONE":
                return path

            sample_width = params.sampwidth
            data = bytearray(frames)
            ratio = volume / 100.0

            if sample_width == 1:
                for i, value in enumerate(data):
                    centered = value - 128
                    data[i] = max(0, min(255, int(round(128 + centered * ratio))))
            elif sample_width == 2:
                for i in range(0, len(data) - 1, 2):
                    sample = struct.unpack_from("<h", data, i)[0]
                    sample = max(-32768, min(32767, int(round(sample * ratio))))
                    struct.pack_into("<h", data, i, sample)
            elif sample_width == 3:
                for i in range(0, len(data) - 2, 3):
                    raw = data[i] | (data[i + 1] << 8) | (data[i + 2] << 16)
                    if raw & 0x800000:
                        raw -= 0x1000000
                    raw = max(-8388608, min(8388607, int(round(raw * ratio))))
                    if raw < 0:
                        raw += 0x1000000
                    data[i] = raw & 0xFF
                    data[i + 1] = (raw >> 8) & 0xFF
                    data[i + 2] = (raw >> 16) & 0xFF
            elif sample_width == 4:
                for i in range(0, len(data) - 3, 4):
                    sample = struct.unpack_from("<i", data, i)[0]
                    sample = max(-2147483648, min(2147483647, int(round(sample * ratio))))
                    struct.pack_into("<i", data, i, sample)
            else:
                return path

            base = os.path.splitext(os.path.basename(path))[0]
            out_path = os.path.join(self._temp_dir, f"{base}_{volume}.wav")
            with wave.open(out_path, "wb") as target:
                target.setparams(params)
                target.writeframes(data)

            self._scaled_cache[cache_key] = out_path
            return out_path
        except Exception:
            return path

    def play(self, sound_name, channel="interface", force=False):
        """Воспроизводит WAV с учётом громкости; force игнорирует отключение звуков."""
        volume = self._effective_volume(channel) if not force else max(0, min(100, int(self.game.settings.get("master_volume", 100))))
        if volume <= 0:
            return

        path = self.sounds.get(sound_name)
        if not path or not os.path.isfile(path):
            return

        play_path = self._scaled_wav_path(path, volume)

        try:
            winsound.PlaySound(
                play_path,
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            )
        except Exception:
            pass

    def move(self):
        self.play("move", "interface")

    def select(self, force=False):
        self.play("select", "interface", force=force)

    def back(self):
        self.play("back", "interface")


class Game:

    def __init__(self):

        self.player = None

        self.enemies = []

        self.objects = []

        self.map = []

        self.last_frame = ""

        # Режим инвентаря. В обычном режиме WASD управляют персонажем;
        # в режиме инвентаря те же клавиши перемещают выделение по слотам.
        self.inventory_mode = False
        self.inventory_selected = 0

        # Быстрое перелистывание слотов при удержании WASD.
        self.inventory_key_repeat = {
            "key": None,
            "started_at": 0.0,
            "last_move": 0.0
        }

        self.previous_movement = {
            "w": False,
            "a": False,
            "s": False,
            "d": False
        }

        self.previous_actions = {
            "e": False
        }

        self.axis_lock = {
            "vertical": None,
            "horizontal": None
        }

        # Настройки интерфейса.
        self.settings = {
            "master_volume": 100,
            "music_volume": 80,
            "interface_volume": 100,
            "sounds_enabled": True,
            "fullscreen": True,
            "interface_size": "Обычный",
            "animation": True,
            "font": "Обычный",
            "language": "Русский",
            "control_scheme": "Клавиатура"
        }

        # Язык и шрифт восстанавливаются из отдельного файла настроек.
        # Остальные параметры пока остаются с текущими значениями по умолчанию.
        self.load_user_settings()

        self.sound = SoundManager(self)

        # Состояние колёсика мыши. Используем глобальный low-level hook.
        # Это работает независимо от того, запущена игра в Windows Terminal
        # или в классической консоли, и не конфликтует с msvcrt.getwch().
        self._mouse_wheel_delta = 0
        self._mouse_hook = None
        self._mouse_hook_proc = None
        self._mouse_hook_thread = None
        self._mouse_hook_thread_id = None
        self._mouse_hook_ready = False
        self._start_mouse_wheel_hook()

    # ========================================================
    # КОЛЁСИКО МЫШИ
    # ========================================================

    def _start_mouse_wheel_hook(self):
        """Запускает отдельный поток с WH_MOUSE_LL и message loop."""
        if not sys.platform.startswith("win"):
            return

        def worker():
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            WH_MOUSE_LL = 14
            WM_MOUSEWHEEL = 0x020A
            WM_MOUSEHWHEEL = 0x020E

            class MSLLHOOKSTRUCT(ctypes.Structure):
                _fields_ = [
                    ("pt_x", ctypes.c_long),
                    ("pt_y", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong),
                    ("flags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ctypes.c_void_p),
                ]

            HOOKPROC = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_int,
                ctypes.c_uint,
                ctypes.c_void_p,
            )

            # Очень важно хранить callback в self: иначе Python может
            # удалить объект callback, пока Windows ещё держит его адрес.
            @HOOKPROC
            def hook_proc(n_code, w_param, l_param):
                if n_code >= 0 and w_param in (WM_MOUSEWHEEL, WM_MOUSEHWHEEL):
                    try:
                        event = ctypes.cast(
                            l_param,
                            ctypes.POINTER(MSLLHOOKSTRUCT)
                        ).contents

                        # Верхние 16 бит mouseData содержат WHEEL_DELTA.
                        delta = ctypes.c_short(
                            (event.mouseData >> 16) & 0xFFFF
                        ).value

                        if delta:
                            self._mouse_wheel_delta += delta
                    except Exception:
                        pass

                return user32.CallNextHookEx(
                    self._mouse_hook or 0,
                    n_code,
                    w_param,
                    l_param
                )

            self._mouse_hook_proc = hook_proc
            self._mouse_hook_thread_id = kernel32.GetCurrentThreadId()

            # Явно задаём типы функций ctypes. Это исключает неправильную
            # передачу HHOOK/HINSTANCE на 64-битной Windows.
            user32.SetWindowsHookExW.argtypes = [
                ctypes.c_int,
                HOOKPROC,
                ctypes.c_void_p,
                ctypes.c_uint32,
            ]
            user32.SetWindowsHookExW.restype = ctypes.c_void_p

            user32.CallNextHookEx.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_uint,
                ctypes.c_void_p,
            ]
            user32.CallNextHookEx.restype = ctypes.c_long

            user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
            user32.UnhookWindowsHookEx.restype = ctypes.c_bool

            user32.GetMessageW.argtypes = [
                ctypes.POINTER(ctypes.wintypes.MSG),
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_uint,
            ]
            user32.GetMessageW.restype = ctypes.c_int

            # Для глобального WH_MOUSE_LL callback находится в текущем
            # процессе Python. В этом случае hMod должен быть NULL.
            # Передача hModule.exe здесь может приводить к тому, что hook
            # вообще не устанавливается.
            hook = user32.SetWindowsHookExW(
                WH_MOUSE_LL,
                self._mouse_hook_proc,
                None,
                0
            )
            self._mouse_hook = hook
            self._mouse_hook_ready = bool(hook)

            # Сообщаем потоку о необходимости message queue.
            msg = ctypes.wintypes.MSG()

            if hook:
                while True:
                    result = user32.GetMessageW(
                        ctypes.byref(msg),
                        None,
                        0,
                        0
                    )
                    if result <= 0:
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))

                user32.UnhookWindowsHookEx(hook)

            self._mouse_hook = None
            self._mouse_hook_ready = False
            self._mouse_hook_thread_id = None
            self._mouse_hook_proc = None

        self._mouse_hook_thread = threading.Thread(
            target=worker,
            name="TheLastShelterMouseWheel",
            daemon=True
        )
        self._mouse_hook_thread.start()

    def _stop_mouse_wheel_hook(self):
        """Корректно останавливает поток mouse hook."""
        try:
            thread_id = self._mouse_hook_thread_id
            if thread_id:
                ctypes.windll.user32.PostThreadMessageW(
                    thread_id,
                    0x0012,  # WM_QUIT
                    0,
                    0
                )

            thread = self._mouse_hook_thread
            if thread and thread.is_alive():
                thread.join(timeout=1.0)
        except Exception:
            pass
        finally:
            self._mouse_hook_thread = None
            self._mouse_hook_thread_id = None
            self._mouse_hook = None
            self._mouse_hook_proc = None
            self._mouse_hook_ready = False

    def _consume_mouse_wheel(self):
        """Атомарно забирает накопленный delta колёсика."""
        delta = self._mouse_wheel_delta
        self._mouse_wheel_delta = 0
        return delta

    # ========================================================
    # ПОЛЬЗОВАТЕЛЬСКИЕ НАСТРОЙКИ
    # ========================================================

    def load_user_settings(self):
        """Загружает пользовательские настройки из settings.json.

        Файл намеренно используется как единое постоянное хранилище настроек
        между версиями игры. Отсутствующие ключи не считаются ошибкой: для них
        остаются безопасные значения из self.settings. Это сохраняет
        совместимость со старыми settings.json, где ещё не было настроек звука.
        """
        try:
            if not os.path.exists(SETTINGS_FILE):
                return

            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return

            language = data.get("language")
            font = data.get("font")
            control_scheme = data.get("control_scheme")

            if language in UI_TRANSLATIONS or language == "Русский":
                self.settings["language"] = language

            if font in ("Обычный", "Жирный"):
                self.settings["font"] = font

            if control_scheme in ("Клавиатура", "Клавиатура+Мышь"):
                self.settings["control_scheme"] = control_scheme

            # ----------------------------------------------------
            # ЗВУК
            # ----------------------------------------------------
            # Настройки звука появились позже. Старый settings.json может
            # не содержать этих ключей, поэтому читаем их только при наличии.
            for key, default in (
                ("master_volume", 100),
                ("music_volume", 80),
                ("interface_volume", 100)
            ):
                value = data.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    self.settings[key] = max(0, min(100, int(value)))

            sounds_enabled = data.get("sounds_enabled")
            if isinstance(sounds_enabled, bool):
                self.settings["sounds_enabled"] = sounds_enabled

            # Полный экран также можно сохранить, если ключ уже существует.
            fullscreen = data.get("fullscreen")
            if isinstance(fullscreen, bool):
                self.settings["fullscreen"] = fullscreen

        except (OSError, json.JSONDecodeError, TypeError, AttributeError):
            pass

    def save_user_settings(self):
        """Сохраняет все пользовательские настройки в settings.json."""
        data = {
            "language": self.settings.get("language", "Русский"),
            "font": self.settings.get("font", "Обычный"),
            "control_scheme": self.settings.get("control_scheme", "Клавиатура"),
            "master_volume": max(0, min(100, int(self.settings.get("master_volume", 100)))),
            "music_volume": max(0, min(100, int(self.settings.get("music_volume", 80)))),
            "interface_volume": max(0, min(100, int(self.settings.get("interface_volume", 100)))),
            "sounds_enabled": bool(self.settings.get("sounds_enabled", True)),
            "fullscreen": bool(self.settings.get("fullscreen", True))
        }

        temporary_file = SETTINGS_FILE + ".tmp"

        try:
            with open(temporary_file, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

            # Атомарная замена уменьшает вероятность получить
            # повреждённый settings.json при закрытии программы.
            os.replace(temporary_file, SETTINGS_FILE)
            return True

        except (OSError, PermissionError):
            try:
                if os.path.exists(temporary_file):
                    os.remove(temporary_file)
            except OSError:
                pass
            return False

    # ========================================================
    # НАСТРОЙКА КОНСОЛИ
    # ========================================================

    def update_terminal_size(self):
        """Получает текущий размер окна консоли Windows."""
        global SCREEN_WIDTH, SCREEN_HEIGHT

        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)

            class COORD(ctypes.Structure):
                _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

            class SMALL_RECT(ctypes.Structure):
                _fields_ = [
                    ("Left", ctypes.c_short), ("Top", ctypes.c_short),
                    ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)
                ]

            class CSBI(ctypes.Structure):
                _fields_ = [
                    ("dwSize", COORD),
                    ("dwCursorPosition", COORD),
                    ("wAttributes", ctypes.c_ushort),
                    ("srWindow", SMALL_RECT),
                    ("dwMaximumWindowSize", COORD)
                ]

            info = CSBI()
            if kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
                # Берём именно видимую область терминала. Нельзя принудительно
                # оставлять 60x24: в оконном режиме это приводит к выводу за
                # пределы viewport и к пустым/смещённым областям.
                SCREEN_WIDTH = max(1, info.srWindow.Right - info.srWindow.Left + 1)
                SCREEN_HEIGHT = max(1, info.srWindow.Bottom - info.srWindow.Top + 1)
                return
        except Exception:
            pass

        try:
            size = os.get_terminal_size()
            SCREEN_WIDTH = max(1, size.columns)
            SCREEN_HEIGHT = max(1, size.lines)
        except OSError:
            SCREEN_WIDTH = 60
            SCREEN_HEIGHT = 30

    def maximize_console(self):
        """
        Резервный режим для классической консоли Windows.

        Основной запуск игры выполняется через Windows Terminal
        с параметром --fullscreen.
        """
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

        self.update_terminal_size()

    @staticmethod
    def toggle_terminal_fullscreen():
        """
        Переключает полноэкранный режим Windows Terminal
        так же, как штатная клавиша F11.
        """
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()

            if not hwnd:
                return False

            user32.SetForegroundWindow(hwnd)
            time.sleep(0.05)

            VK_F11 = 0x7A
            KEYEVENTF_KEYUP = 0x0002

            user32.keybd_event(VK_F11, 0, 0, 0)
            user32.keybd_event(
                VK_F11,
                0,
                KEYEVENTF_KEYUP,
                0
            )

            time.sleep(0.20)
            return True

        except Exception:
            return False

    @staticmethod
    def _background_cell(x, y, width, height):
        """Одна ячейка декоративного фона без внешней рамки."""
        # Базовая точечная фактура. Внешняя рамка добавляется централизованно
        # в render(), поэтому она всегда имеет ровно один ряд сверху/снизу
        # и один столбец слева/справа независимо от размера окна.
        blocks = (
            (4, 4, min(27, width - 1), min(9, height - 1)),
            (max(1, width - 30), 3, max(1, width - 5), min(8, height - 1)),
            (8, max(1, height - 11), min(32, width - 1), max(1, height - 3)),
            (max(1, width - 35), max(1, height - 11), max(1, width - 6), max(1, height - 4)),
        )

        for left, top, right, bottom in blocks:
            if left <= x <= right and top <= y <= bottom:
                if x in (left, right) or y in (top, bottom):
                    return "#"
                if (x + y) % 11 == 0:
                    return "#"

        if (x * 37 + y * 17) % 29 != 0:
            return "."

        if (x * 11 + y * 7) % 97 == 0:
            return "O"

        return "."

    def build_menu_background(self):
        """Фон только внутренней области; рамка строится render()."""
        self.update_terminal_size()
        width = max(1, SCREEN_WIDTH - 2)
        height = max(1, SCREEN_HEIGHT - 2)
        return [
            "".join(
                self._background_cell(x, y, width, height)
                for x in range(width)
            )
            for y in range(height)
        ]

    def render_menu_screen(self, menu_lines):
        """Центрирует окно меню во внутренней области полного экрана."""
        self.update_terminal_size()
        background = self.build_menu_background()

        inner_width = max(1, SCREEN_WIDTH - 2)
        inner_height = max(1, SCREEN_HEIGHT - 2)

        menu_width = min(
            inner_width,
            max(visible_len(line) for line in menu_lines)
        )
        menu_height = min(inner_height, len(menu_lines))
        start_x = max(0, (inner_width - menu_width) // 2)
        start_y = max(0, (inner_height - menu_height) // 2)

        for index, raw_line in enumerate(menu_lines[:inner_height]):
            y = start_y + index
            if y >= inner_height:
                break
            line = self._fit_overlay_line(raw_line, menu_width)
            background[y] = (
                background[y][:start_x]
                + line
                + background[y][start_x + menu_width:]
            )

        self.render(background)

    def setup_console(self):

        os.system(
            f"title {GAME_TITLE}"
        )

        os.system(
            "chcp 65001 > nul"
        )

        # Переключаемся в альтернативный экран Windows Terminal.
        # Старый вывод консоли больше не будет виден во время игры.
        sys.stdout.write("\033[?1049h\033[2J\033[H")
        sys.stdout.flush()

        # Полноэкранный режим задаётся самим Windows Terminal
        # при запуске через wt.exe --fullscreen.
        self.update_terminal_size()

        self.disable_console_echo()

        self.hide_cursor()

    @staticmethod
    def disable_console_echo():

        kernel32 = ctypes.windll.kernel32

        handle = kernel32.GetStdHandle(-10)

        mode = ctypes.c_uint32()

        kernel32.GetConsoleMode(
            handle,
            ctypes.byref(mode)
        )

        mode.value &= ~0x0002  # ENABLE_LINE_INPUT
        mode.value &= ~0x0004  # ENABLE_ECHO_INPUT

        kernel32.SetConsoleMode(
            handle,
            mode
        )

    @staticmethod
    def hide_cursor():

        sys.stdout.write(
            "\033[?25l"
        )

        sys.stdout.flush()

    @staticmethod
    def show_cursor():

        sys.stdout.write(
            "\033[?25h"
        )

        sys.stdout.flush()

    # ========================================================
    # ОТРИСОВКА БЕЗ МЕРЦАНИЯ
    # ========================================================

    def render(self, lines, fill_char=" "):
        """Отрисовывает кадр во весь доступный viewport без остаточных данных."""
        self.update_terminal_size()

        width = max(1, SCREEN_WIDTH)
        height = max(1, SCREEN_HEIGHT)
        inner_width = max(1, width - 2)
        inner_height = max(1, height - 2)

        fill_char = str(fill_char or " ")[0]

        # Сначала формируем ПОЛНЫЙ внутренний экран. Никаких недописанных
        # строк и никакого обращения к старому содержимому терминала.
        canvas = [fill_char * inner_width for _ in range(inner_height)]

        for y, raw_line in enumerate(lines):
            if y >= inner_height:
                break

            raw_line = str(raw_line)
            visible = ANSI_ESCAPE_RE.sub("", raw_line)

            if len(visible) > inner_width:
                # Для ANSI-строк нельзя резать исходную строку по Python-индексу:
                # escape-коды занимают символы, но не занимают экранные ячейки.
                raw_line = visible[:inner_width]
                visible = raw_line

            padding = max(0, inner_width - len(visible))
            canvas[y] = raw_line + fill_char * padding

        # Внешняя рамка интерфейса — Unicode box-drawing.
        # Символы карты (#) при этом не затрагиваются.
        frame_lines = ["╔" + "═" * inner_width + "╗"]
        frame_lines.extend(
            "║" + line + "║"
            for line in canvas
        )
        frame_lines.append("╚" + "═" * inner_width + "╝")

        frame = "\n".join(frame_lines)

        if frame == self.last_frame:
            return

        # Полный кадр всегда записывается целиком. После него курсор
        # возвращается в начало, чтобы следующий кадр не мог оставить
        # хвост старого содержимого.
        output = "\033[0m\033[H"

        for index, line in enumerate(frame_lines):
            output += line + ANSI_RESET
            if index < len(frame_lines) - 1:
                output += "\n"

        output += "\033[H"

        sys.stdout.write(output)
        sys.stdout.flush()

        self.last_frame = frame

    # ========================================================
    # ОЧИСТКА СОСТОЯНИЯ ОТРИСОВКИ
    # ========================================================

    def reset_render(self):
        """
        Сбрасывает только кэш последнего кадра, не очищая терминал.

        Раньше здесь использовался ANSI-код 2J, который полностью очищал
        экран перед следующей отрисовкой. При переключении между меню это
        создавало короткий пустой кадр и визуальное мерцание.

        render() всегда формирует и записывает полный кадр, поэтому отдельная
        очистка экрана перед ним не требуется.
        """
        self.last_frame = ""

        # Сбрасываем только ANSI-состояние и возвращаем курсор в начало.
        # Экран при этом НЕ очищается. Следующий полный кадр render()
        # полностью заменит содержимое viewport.
        sys.stdout.write(
            "\033[0m\033[H"
        )
        sys.stdout.flush()

    @staticmethod
    def flush_console_input():
        # Меню обрабатываются через GetAsyncKeyState, а текстовый ввод —
        # через msvcrt. Очищаем очередь консоли перед переключением
        # между этими режимами, чтобы на следующий экран не попадали
        # клавиши из предыдущего меню.
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-10)
            kernel32.FlushConsoleInputBuffer(handle)
        except Exception:
            pass

    # ========================================================
    # РАЗМЕР ИГРОВОГО ПОЛЯ
    # ========================================================

    def set_map_size_for_screen(self):
        """
        Подгоняет игровое поле под верхнюю часть игрового интерфейса.

        Внизу постоянно резервируется HUD_HEIGHT строк под три панели:
        статистику игрока, активные предметы и информацию об окружении.
        """
        global MAP_WIDTH, MAP_HEIGHT

        self.update_terminal_size()

        content_width = max(1, SCREEN_WIDTH - 2)
        content_height = max(1, SCREEN_HEIGHT - 2)

        # Название игры не занимает отдельные строки во время игрового процесса:
        # верхняя часть экрана полностью отдана игровому полю.
        header_height = 0

        MAP_WIDTH = content_width
        MAP_HEIGHT = max(8, content_height - header_height - HUD_HEIGHT)

    # ========================================================
    # СОЗДАНИЕ КАРТЫ
    # ========================================================

    def create_map(self):

        self.map = []

        for y in range(MAP_HEIGHT):

            row = []

            for x in range(MAP_WIDTH):

                # Края игрового поля больше не являются стеной.
                # Граница определяется внешней рамкой интерфейса, поэтому
                # внутри неё всё поле состоит из обычных игровых клеток.
                row.append(GROUND_SYMBOL)

            self.map.append(row)

        # ----------------------------------------------------
        # ВНУТРЕННИЕ СТЕНЫ
        # ----------------------------------------------------

        walls = [

            (8, 3),
            (8, 4),
            (8, 5),
            (8, 6),

            (15, 8),
            (16, 8),
            (17, 8),
            (18, 8),

            (22, 3),
            (22, 4),
            (22, 5)

        ]

        for x, y in walls:

            if (
                0 <= x < MAP_WIDTH
                and
                0 <= y < MAP_HEIGHT
            ):

                self.map[y][x] = WALL_SYMBOL

    # ========================================================
    # СОЗДАНИЕ ВРАГОВ
    # ========================================================

    def create_enemies(self):

        self.enemies = [

            Enemy(
                x=12,
                y=4,
                name="Дикий зверь",
                hp=40,
                max_hp=40,
                attack=10
            ),

            Enemy(
                x=25,
                y=11,
                name="Мутант",
                hp=60,
                max_hp=60,
                attack=15
            )

        ]

    # ========================================================
    # СОЗДАНИЕ ОБЪЕКТОВ
    # ========================================================

    def create_objects(self):

        self.objects = [

            GameObject(
                x=5,
                y=5,
                name="Старый ящик",
                description=(
                    "Пыльный деревянный ящик. "
                    "Похоже, его давно никто не открывал."
                )
            ),

            GameObject(
                x=18,
                y=4,
                name="Старая машина",
                description=(
                    "Разбитый автомобиль. "
                    "Двигатель давно вышел из строя."
                )
            )

        ]

    # ========================================================
    # ПРОВЕРКА СТЕНЫ
    # ========================================================

    def is_wall(
        self,
        x,
        y
    ):

        if not (
            0 <= x < MAP_WIDTH
            and
            0 <= y < MAP_HEIGHT
        ):

            return True

        return (
            self.map[y][x]
            ==
            WALL_SYMBOL
        )

    # ========================================================
    # ПОИСК ВРАГА
    # ========================================================

    def get_enemy_at(
        self,
        x,
        y
    ):

        for enemy in self.enemies:

            if (
                enemy.x == x
                and
                enemy.y == y
            ):

                return enemy

        return None

    # ========================================================
    # ПОИСК ОБЪЕКТА
    # ========================================================

    def get_object_at(
        self,
        x,
        y
    ):

        for obj in self.objects:

            if (
                obj.x == x
                and
                obj.y == y
            ):

                return obj

        return None

    # ========================================================
    # ПОИСК СОСЕДНЕГО ОБЪЕКТА
    # ========================================================

    def get_adjacent_interactable(self):

        directions = [

            (0, -1),
            (1, 0),
            (0, 1),
            (-1, 0)

        ]

        # ----------------------------------------------------
        # СНАЧАЛА ВРАГИ
        # ----------------------------------------------------

        for dx, dy in directions:

            x = self.player.x + dx
            y = self.player.y + dy

            enemy = self.get_enemy_at(
                x,
                y
            )

            if enemy is not None:

                return (
                    "enemy",
                    enemy
                )

        # ----------------------------------------------------
        # ЗАТЕМ ОБЪЕКТЫ
        # ----------------------------------------------------

        for dx, dy in directions:

            x = self.player.x + dx
            y = self.player.y + dy

            obj = self.get_object_at(
                x,
                y
            )

            if obj is not None:

                return (
                    "object",
                    obj
                )

        return (
            None,
            None
        )

    # ========================================================
    # СОСТОЯНИЕ КЛАВИШИ
    # ========================================================

    @staticmethod
    def is_pressed(key):

        try:

            virtual_key = ord(
                key.upper()
            )

            return bool(
                ctypes.windll.user32.GetAsyncKeyState(
                    virtual_key
                )
                &
                0x8000
            )

        except Exception:

            return False

    # ========================================================
    # МЫШЬ
    # ========================================================

    @staticmethod
    def is_mouse_pressed(button="left"):
        try:
            vk = 0x01 if button == "left" else 0x02
            return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
        except Exception:
            return False

    @staticmethod
    def get_mouse_cell():
        """Возвращает координаты знакоместа терминала под системным курсором."""
        try:
            user32 = ctypes.windll.user32

            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            point = POINT()
            if not user32.GetCursorPos(ctypes.byref(point)):
                return None
            if not user32.ScreenToClient(hwnd, ctypes.byref(point)):
                return None

            rect = RECT()
            if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
                return None

            client_width = rect.right - rect.left
            client_height = rect.bottom - rect.top
            if client_width <= 0 or client_height <= 0:
                return None

            # Windows Terminal / ConPTY не даёт нам надёжный размер шрифта
            # через GetCurrentConsoleFontEx. Поэтому преобразуем координаты
            # пропорционально фактической области окна и текущей сетке терминала.
            x = max(0, min(SCREEN_WIDTH - 1, int(point.x * SCREEN_WIDTH / client_width)))
            y = max(0, min(SCREEN_HEIGHT - 1, int(point.y * SCREEN_HEIGHT / client_height)))
            return x, y
        except Exception:
            return None

    def mouse_enabled(self):
        return self.settings.get("control_scheme", "Клавиатура") == "Клавиатура+Мышь"

    def mouse_click(self):
        current = self.is_mouse_pressed("left")
        previous = getattr(self, "previous_mouse_left", False)
        self.previous_mouse_left = current
        return current and not previous

    def wait_for_mouse_release(self):
        while self.is_mouse_pressed("left") or self.is_mouse_pressed("right"):
            time.sleep(0.01)
        self.reset_mouse()

    def reset_mouse(self):
        self.previous_mouse_left = self.is_mouse_pressed("left")

    def handle_mouse_game_click(self):
        """Обрабатывает ЛКМ по игровой клетке в режиме «Клавиатура+Мышь»."""
        cell = self.get_mouse_cell()
        if cell is None:
            return False
        x, y = cell
        if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
            return False
        dx = x - self.player.x
        dy = y - self.player.y
        if dx == 0 and dy == 0:
            return False

        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        target_x = self.player.x + step_x
        target_y = self.player.y + step_y

        if abs(dx) <= 1 and abs(dy) <= 1:
            enemy = self.get_enemy_at(x, y)
            obj = self.get_object_at(x, y)
            if enemy is not None:
                self.enemy_interaction(enemy)
            elif obj is not None:
                self.object_interaction(obj)
            elif not self.is_wall(x, y):
                self.move_player(dx, dy)
            else:
                return False
        else:
            if self.is_wall(target_x, target_y):
                return False
            if self.get_enemy_at(target_x, target_y) is not None:
                return False
            if self.get_object_at(target_x, target_y) is not None:
                return False
            self.move_player(step_x, step_y)

        self.wait_for_all_keys_release()
        self.reset_input()
        self.reset_mouse()
        return True

    # ========================================================
    # ОЖИДАНИЕ ОТПУСКАНИЯ КЛАВИШ
    # ========================================================

    def wait_for_all_keys_release(self):

        while (

            self.is_pressed("w")
            or
            self.is_pressed("a")
            or
            self.is_pressed("s")
            or
            self.is_pressed("d")
            or
            self.is_pressed("e")
            or
            self.is_pressed("q")
            or
            self.is_pressed("x")
            or
            self.is_pressed("\x1b")
            or
            self.is_pressed("\t")

        ):

            time.sleep(0.01)

    # ========================================================
    # СБРОС СОСТОЯНИЯ КЛАВИШ
    # ========================================================

    def reset_input(self):

        self.previous_movement = {

            "w": False,
            "a": False,
            "s": False,
            "d": False

        }

        self.previous_actions = {

            "e": False,
            "q": False

        }

        self.axis_lock = {

            "vertical": None,
            "horizontal": None

        }

    # ========================================================
    # ПОЛУЧЕНИЕ ДВИЖЕНИЯ
    # ========================================================

    def get_movement(self):

        current = {

            "w": self.is_pressed("w"),
            "a": self.is_pressed("a"),
            "s": self.is_pressed("s"),
            "d": self.is_pressed("d")

        }

        # ----------------------------------------------------
        # НОВЫЕ НАЖАТИЯ
        # ----------------------------------------------------

        w_new = (
            current["w"]
            and
            not self.previous_movement["w"]
        )

        s_new = (
            current["s"]
            and
            not self.previous_movement["s"]
        )

        a_new = (
            current["a"]
            and
            not self.previous_movement["a"]
        )

        d_new = (
            current["d"]
            and
            not self.previous_movement["d"]
        )

        # ----------------------------------------------------
        # ВЕРТИКАЛЬНАЯ ОСЬ
        # ----------------------------------------------------

        if w_new and not s_new:

            self.axis_lock["vertical"] = "w"

        elif s_new and not w_new:

            self.axis_lock["vertical"] = "s"

        elif w_new and s_new:

            self.axis_lock["vertical"] = "w"

        # ----------------------------------------------------
        # ГОРИЗОНТАЛЬНАЯ ОСЬ
        # ----------------------------------------------------

        if a_new and not d_new:

            self.axis_lock["horizontal"] = "a"

        elif d_new and not a_new:

            self.axis_lock["horizontal"] = "d"

        elif a_new and d_new:

            self.axis_lock["horizontal"] = "a"

        # ----------------------------------------------------
        # W / S
        # ----------------------------------------------------

        if (
            not current["w"]
            and
            not current["s"]
        ):

            self.axis_lock["vertical"] = None

        elif (
            self.axis_lock["vertical"] == "w"
            and
            not current["w"]
            and
            current["s"]
        ):

            self.axis_lock["vertical"] = "s"

        elif (
            self.axis_lock["vertical"] == "s"
            and
            not current["s"]
            and
            current["w"]
        ):

            self.axis_lock["vertical"] = "w"

        # ----------------------------------------------------
        # A / D
        # ----------------------------------------------------

        if (
            not current["a"]
            and
            not current["d"]
        ):

            self.axis_lock["horizontal"] = None

        elif (
            self.axis_lock["horizontal"] == "a"
            and
            not current["a"]
            and
            current["d"]
        ):

            self.axis_lock["horizontal"] = "d"

        elif (
            self.axis_lock["horizontal"] == "d"
            and
            not current["d"]
            and
            current["a"]
        ):

            self.axis_lock["horizontal"] = "a"

        # ----------------------------------------------------
        # ФОРМИРОВАНИЕ ВЕКТОРА
        # ----------------------------------------------------

        dx = 0
        dy = 0

        if (
            self.axis_lock["vertical"]
            ==
            "w"
        ):

            dy = -1

        elif (
            self.axis_lock["vertical"]
            ==
            "s"
        ):

            dy = 1

        if (
            self.axis_lock["horizontal"]
            ==
            "a"
        ):

            dx = -1

        elif (
            self.axis_lock["horizontal"]
            ==
            "d"
        ):

            dx = 1

        self.previous_movement = current

        return (
            dx,
            dy
        )

    # ========================================================
    # ДЕЙСТВИЕ E
    # ========================================================

    def get_action(self):
        # Во время игры обрабатывается только E.
        # Q больше не является игровой клавишей, поэтому случайное
        # нажатие Q не может вывести игрока в главное меню.
        current_e = self.is_pressed("e")

        action = None

        if (
            current_e
            and
            not self.previous_actions["e"]
        ):
            action = "e"

        self.previous_actions = {
            "e": current_e
        }

        return action

    # ========================================================
    # ОЖИДАНИЕ КЛАВИШИ
    # ========================================================

    @staticmethod
    def get_key():

        while True:

            key = msvcrt.getwch()

            if key in (
                "\x00",
                "\xe0"
            ):

                msvcrt.getwch()

                continue

            return key.lower()

    # ========================================================
    # ОЖИДАНИЕ РАЗРЕШЁННОЙ КЛАВИШИ
    # ========================================================

    def get_allowed_key(
        self,
        allowed
    ):

        while True:

            key = self.get_key()

            if key in allowed:

                return key

    # ========================================================
    # ВВОД ИМЕНИ
    # ========================================================

    def get_player_name(self):

        name = ""

        # Ширина внутренней части общего меню.
        width = min(max(12, SCREEN_WIDTH - 8), 54)
        inner = max(4, width - 2)

        self.flush_console_input()
        self.reset_input()
        self.reset_mouse()
        self.reset_render()
        self.show_cursor()

        back_label = self._translate_text("Назад [ESC]")
        prompt = self._translate_text("Введите имя персонажа:")

        def build_name_lines(back_hovered=False):
            # При пустом имени кнопка «Назад [ESC]» всегда подсвечена.
            # После начала ввода имя снимает автоматическую подсветку,
            # но наведение курсора мыши снова зажигает кнопку жёлтым.
            if not name or back_hovered:
                back_line_text = ANSI_YELLOW + back_label + ANSI_RESET
            else:
                back_line_text = back_label

            input_text = prompt + " " + name
            input_text = input_text[:inner]

            return [
                "╔" + "═" * inner + "╗",
                "║" + f"{self._translate_text('НОВАЯ ИГРА'):^{inner}}" + "║",
                "╠" + "═" * inner + "╣",
                "║" + input_text.ljust(inner) + "║",
                "║" + back_line_text + " " * max(0, inner - len(back_label)) + "║",
                "╚" + "═" * inner + "╝"
            ]

        def draw_name_screen(back_hovered=False):
            lines = build_name_lines(back_hovered)
            self.render_menu_screen(lines)

            menu_width = max(visible_len(line) for line in lines)
            menu_height = len(lines)
            inner_width = max(1, SCREEN_WIDTH - 2)
            inner_height = max(1, SCREEN_HEIGHT - 2)
            start_x = 1 + max(0, (inner_width - menu_width) // 2)
            start_y = 1 + max(0, (inner_height - menu_height) // 2)

            cursor_row = start_y + 4
            cursor_col = start_x + 2 + len(prompt) + 1 + len(name)
            cursor_col = min(cursor_col, start_x + inner)

            sys.stdout.write(f"\033[{cursor_row};{cursor_col}H")
            sys.stdout.flush()

        def get_menu_geometry(back_hovered=False):
            lines = build_name_lines(back_hovered)
            menu_width = max(visible_len(line) for line in lines)
            menu_height = len(lines)
            inner_width = max(1, SCREEN_WIDTH - 2)
            inner_height = max(1, SCREEN_HEIGHT - 2)
            start_x = 1 + max(0, (inner_width - menu_width) // 2)
            start_y = 1 + max(0, (inner_height - menu_height) // 2)
            return menu_width, menu_height, start_x, start_y

        # Вместо msvcrt.kbhit() используем прямой опрос состояния клавиатуры
        # Windows. Это устраняет задержки и потерю символов в Windows Terminal
        # при одновременной проверке мыши.
        user32 = ctypes.windll.user32
        keyboard_state = (ctypes.c_ubyte * 256)()
        unicode_buffer = ctypes.create_unicode_buffer(8)
        previous_keys = set()

        # Клавиши-модификаторы сами по себе не должны порождать символы имени.
        modifier_vks = {
            0x10,  # SHIFT
            0x11,  # CTRL
            0x12,  # ALT
            0x5B,  # LWIN
            0x5C,  # RWIN
        }

        def read_keyboard_key():
            """Возвращает одну новую нажатую клавишу или None."""
            try:
                user32.GetKeyboardState(keyboard_state)
            except Exception:
                return None

            current_keys = set()

            for vk in range(1, 256):
                if vk in modifier_vks:
                    continue

                try:
                    pressed = bool(user32.GetAsyncKeyState(vk) & 0x8000)
                except Exception:
                    pressed = False

                if pressed:
                    current_keys.add(vk)

            new_keys = current_keys - previous_keys
            previous_keys.clear()
            previous_keys.update(current_keys)

            if not new_keys:
                return None

            # Сначала обрабатываем специальные клавиши, чтобы их значения
            # не зависели от раскладки клавиатуры.
            if 0x1B in new_keys:       # ESC
                return "\x1b"
            if 0x08 in new_keys:       # BACKSPACE
                return "\x08"
            if 0x0D in new_keys:       # ENTER
                return "\r"

            # Из новых клавиш выбираем клавишу с наименьшим VK-кодом.
            # Остальные остаются в состоянии pressed и будут проигнорированы
            # до их отпускания.
            for vk in sorted(new_keys):
                if vk in (0x1B, 0x08, 0x0D):
                    continue

                try:
                    scan_code = user32.MapVirtualKeyW(vk, 0)
                    unicode_buffer.value = ""
                    result = user32.ToUnicode(
                        vk,
                        scan_code,
                        keyboard_state,
                        unicode_buffer,
                        len(unicode_buffer),
                        0
                    )

                    if result > 0:
                        return unicode_buffer.value[:result]

                    # Dead-key: очищаем состояние ToUnicode вторым вызовом.
                    if result < 0:
                        unicode_buffer.value = ""
                        user32.ToUnicode(
                            vk,
                            scan_code,
                            keyboard_state,
                            unicode_buffer,
                            len(unicode_buffer),
                            0
                        )
                except Exception:
                    continue

            return None

        draw_name_screen(False)
        previous_back_hovered = False

        while True:
            # ----------------------------------------------------
            # НАВЕДЕНИЕ НА «НАЗАД [ESC]»
            # ----------------------------------------------------
            back_hovered = False
            if self.mouse_enabled() and name:
                mouse_cell = self.get_mouse_cell()
                if mouse_cell is not None:
                    mx, my = mouse_cell
                    _, _, start_x, start_y = get_menu_geometry(False)
                    local_x = mx - start_x
                    local_y = my - start_y
                    menu_width, _, _, _ = get_menu_geometry(False)
                    back_hovered = (
                        local_y == 4
                        and 0 <= local_x < menu_width
                    )

            if back_hovered != previous_back_hovered:
                draw_name_screen(back_hovered)
                if back_hovered:
                    self.sound.move()
                previous_back_hovered = back_hovered

            # ----------------------------------------------------
            # ЛКМ ПО «НАЗАД [ESC]»
            # ----------------------------------------------------
            if self.mouse_enabled() and self.mouse_click():
                mouse_cell = self.get_mouse_cell()
                if mouse_cell is not None:
                    mx, my = mouse_cell
                    menu_width, _, start_x, start_y = get_menu_geometry(False)
                    local_x = mx - start_x
                    local_y = my - start_y

                    if local_y == 4 and 0 <= local_x < menu_width:
                        self.sound.back()
                        self.hide_cursor()
                        self.wait_for_mouse_release()
                        self.reset_input()
                        self.reset_render()
                        return None

                self.reset_mouse()

            # ----------------------------------------------------
            # КЛАВИАТУРА
            # ----------------------------------------------------
            key = read_keyboard_key()

            if key is not None:
                # ESC всегда возвращает назад.
                if key == "\x1b":
                    self.sound.back()
                    self.hide_cursor()
                    self.wait_for_mouse_release()
                    self.reset_input()
                    self.reset_render()
                    return None

                # При пустом имени E действует как подтверждение кнопки Back.
                if not name and key.lower() == "e":
                    self.sound.back()
                    self.hide_cursor()
                    self.wait_for_mouse_release()
                    self.reset_input()
                    self.reset_render()
                    return None

                # ENTER подтверждает имя только при наличии текста.
                if key in ("\r", "\n"):
                    if name.strip():
                        self.hide_cursor()
                        self.wait_for_mouse_release()
                        self.reset_input()
                        self.reset_render()
                        return name.strip()

                # BACKSPACE удаляет последний символ.
                if key == "\x08":
                    if name:
                        name = name[:-1]
                        draw_name_screen(False)
                    continue

                # ToUnicode может вернуть несколько символов сразу.
                # Добавляем только печатные символы и ограничиваем имя 20
                # отображаемыми символами.
                if isinstance(key, str) and key:
                    printable = "".join(ch for ch in key if ch.isprintable())
                    if printable and len(name) < 20:
                        name += printable[:20 - len(name)]
                        draw_name_screen(False)

            time.sleep(0.005)

    # ========================================================
    # УНИВЕРСАЛЬНАЯ НАВИГАЦИЯ МЕНЮ
    # ========================================================

    @staticmethod
    def _wrap_text(text, max_width):
        """Переносит текст по целым словам, не разрывая слова."""
        clean = ANSI_ESCAPE_RE.sub("", str(text)).strip()

        if not clean:
            return [""]

        words = clean.split()
        result = []
        current = ""

        for word in words:
            if not current:
                current = word
            elif len(current) + 1 + len(word) <= max_width:
                current += " " + word
            else:
                result.append(current)
                current = word

        if current:
            result.append(current)

        return result

    def _translate_text(self, text):
        """Переводит только известные текстовые элементы интерфейса."""
        text = str(text)
        language = self.settings.get("language", "Русский")
        translations = UI_TRANSLATIONS.get(language, {})

        # Сначала заменяем длинные фразы, чтобы не затрагивать их частями.
        for source in sorted(translations, key=len, reverse=True):
            text = text.replace(source, translations[source])

        return text

    def _font_prefix(self):
        """Возвращает ANSI-режим визуального шрифта для текста интерфейса."""
        return {
            "Обычный": "\033[22m",
            "Жирный": "\033[1m"
        }.get(self.settings.get("font", "Обычный"), "\033[22m")

    def _ui_text(self, text):
        """Применяет перевод и выбранный стиль только к тексту интерфейса."""
        translated = self._translate_text(text)
        return self._font_prefix() + translated + "\033[22m"

    def _menu_box(self, title_lines, options, selected, footer=True):

        width = min(SCREEN_WIDTH - 8, 54)
        inner = max(1, width - 2)

        # Сначала переводим текст, затем рассчитываем его ширину и переносы.
        # Иначе английские строки могут стать длиннее русского оригинала и
        # выйти за границы окна, что ломает правую рамку.
        translated_titles = []
        if title_lines:
            for line in title_lines:
                clean = ANSI_ESCAPE_RE.sub("", str(line)).strip()
                if clean and not set(clean) <= {"="}:
                    translated = self._translate_text(clean)
                    translated_titles.extend(self._wrap_text(translated, inner))

        if not translated_titles:
            translated_titles = [GAME_TITLE]

        lines = []
        lines.append("╔" + "═" * inner + "╗")

        for title in translated_titles:
            left = max(0, (inner - len(title)) // 2)
            right = max(0, inner - len(title) - left)
            lines.append(
                "║" + (" " * left) + self._ui_text(title) + (" " * right) + "║"
            )

        lines.append("╠" + "═" * inner + "╣")

        for index, option in enumerate(options):
            # Перевод выполняется ДО переноса строки и расчёта ширины.
            translated_option = self._translate_text(option)
            wrapped = self._wrap_text(translated_option, max(1, inner - 2))

            for line_number, text in enumerate(wrapped):
                prefix = ("> " if line_number == 0 else "  ") if index == selected else "  "
                content = (prefix + text)[:inner]
                padding = " " * max(0, inner - len(content))

                if index == selected:
                    line = (
                        "║"
                        + ANSI_YELLOW
                        + self._ui_text(content)
                        + padding
                        + ANSI_RESET
                        + "║"
                    )
                else:
                    line = (
                        "║"
                        + self._ui_text(content)
                        + padding
                        + "║"
                    )

                lines.append(line)

        if footer:
            lines.append("╠" + "═" * inner + "╣")

            hint = self._translate_text("W/A — вверх   S/D — вниз   E — выбор")
            left = max(0, (inner - len(hint)) // 2)
            right = max(0, inner - len(hint) - left)
            lines.append(
                "║" + (" " * left) + self._ui_text(hint) + (" " * right) + "║"
            )

            hint2 = self._translate_text("ESC — назад")
            left = max(0, (inner - len(hint2)) // 2)
            right = max(0, inner - len(hint2) - left)
            lines.append(
                "║" + (" " * left) + self._ui_text(hint2) + (" " * right) + "║"
            )

        lines.append("╚" + "═" * inner + "╝")
        return lines

    def _mouse_menu_option(self, options, menu_lines, overlay=False):
        """Возвращает индекс пункта меню под курсором мыши, либо None."""
        cell = self.get_mouse_cell()
        if cell is None:
            return None
        mx, my = cell

        content_width = max(1, SCREEN_WIDTH - 2)
        if overlay:
            content_height = max(1, SCREEN_HEIGHT - 2)
            available_height = max(1, content_height - HUD_HEIGHT)
            menu_width = min(content_width, max(visible_len(line) for line in menu_lines))
            menu_height = min(available_height, len(menu_lines))
            start_x = max(0, (content_width - menu_width) // 2)
            start_y = max(0, (available_height - menu_height) // 2)
        else:
            inner_height = max(1, SCREEN_HEIGHT - 2)
            menu_width = min(content_width, max(visible_len(line) for line in menu_lines))
            menu_height = min(inner_height, len(menu_lines))
            start_x = max(0, (content_width - menu_width) // 2)
            start_y = max(0, (inner_height - menu_height) // 2)

        # Координаты терминала включают внешнюю рамку render().
        local_x = mx - (1 + start_x)
        local_y = my - (1 + start_y)
        if not (0 <= local_x < menu_width and 0 <= local_y < menu_height):
            return None

        title_lines = 0
        # _menu_box: верхняя рамка + заголовки + разделитель.
        # В title_lines число строк заголовка восстанавливаем по первой
        # разделительной рамке, чтобы корректно работать и с переносами.
        separator_index = None
        for i, line in enumerate(menu_lines):
            if ANSI_ESCAPE_RE.sub("", line).startswith("╠"):
                separator_index = i
                break
        if separator_index is None:
            return None
        option_start = separator_index + 1

        # Каждая опция может занимать несколько строк из-за переноса текста.
        inner = max(1, menu_width - 2)
        for index, option in enumerate(options):
            wrapped = self._wrap_text(
                self._translate_text(option),
                max(1, inner - 2)
            )
            count = max(1, len(wrapped))
            if option_start <= local_y < option_start + count:
                return index
            option_start += count

        return None

    def menu_select(self, options, title_lines=None, overlay=False, allow_escape=True, footer=True):
        """
        Универсальная навигация меню через состояние клавиш Windows.

        W / A  — вверх
        S / D  — вниз
        E      — выбрать
        ESC    — назад

        Используется GetAsyncKeyState, как и в игровом цикле.
        Это исключает конфликт между консольным вводом msvcrt
        и обработкой клавиш игры.
        """

        selected = 0

        # Ждём, пока клавиши, которыми могли войти в меню,
        # будут отпущены. Здесь нет перерисовки.
        while any(
            self.is_pressed(key)
            for key in ("w", "a", "s", "d", "e", "")
        ):
            time.sleep(0.01)

        self.wait_for_mouse_release()

        # Первичная отрисовка.
        lines = self._menu_box(
            title_lines or [GAME_TITLE],
            options,
            selected,
            footer=footer
        )

        if overlay:
            self.draw_game(overlay=lines)
        else:
            self.reset_render()
            self.render_menu_screen(lines)

        previous = {
            "w": False,
            "a": False,
            "s": False,
            "d": False,
            "e": False,
            "esc": False
        }

        while True:
            current = {
                "w": self.is_pressed("w"),
                "a": self.is_pressed("a"),
                "s": self.is_pressed("s"),
                "d": self.is_pressed("d"),
                "e": self.is_pressed("e"),
                "esc": self.is_pressed("")
            }

            # Наведение мыши переносит визуальное выделение на пункт.
            # Это работает в том числе в главном меню и в настройках,
            # которые используют общий menu_select().
            if self.mouse_enabled():
                hovered = self._mouse_menu_option(options, lines, overlay=overlay)
                if hovered is not None and hovered != selected:
                    selected = hovered
                    self.sound.move()
                    lines = self._menu_box(
                        title_lines or [GAME_TITLE],
                        options,
                        selected,
                        footer=footer
                    )
                    if overlay:
                        self.draw_game(overlay=lines)
                    else:
                        self.render_menu_screen(lines)

            # ЛКМ подтверждает пункт, на который наведён курсор.
            if self.mouse_enabled() and self.mouse_click():
                clicked = self._mouse_menu_option(options, lines, overlay=overlay)
                if clicked is not None:
                    selected = clicked
                    self.sound.select()
                    self.wait_for_mouse_release()
                    self.reset_input()
                    return selected

            # W / A — вверх
            if (
                (current["w"] and not previous["w"])
                or
                (current["a"] and not previous["a"])
            ):
                selected = (selected - 1) % len(options)
                self.sound.move()

                lines = self._menu_box(
                    title_lines or [GAME_TITLE],
                    options,
                    selected,
                    footer=footer
                )

                if overlay:
                    self.draw_game(overlay=lines)
                else:
                    self.render_menu_screen(lines)

            # S / D — вниз
            elif (
                (current["s"] and not previous["s"])
                or
                (current["d"] and not previous["d"])
            ):
                selected = (selected + 1) % len(options)
                self.sound.move()

                lines = self._menu_box(
                    title_lines or [GAME_TITLE],
                    options,
                    selected,
                    footer=footer
                )

                if overlay:
                    self.draw_game(overlay=lines)
                else:
                    self.render_menu_screen(lines)

            # E — выбрать
            elif current["e"] and not previous["e"]:
                while self.is_pressed("e"):
                    time.sleep(0.01)

                self.sound.select()
                self.reset_input()
                return selected

            # ESC — назад
            elif allow_escape and current["esc"] and not previous["esc"]:
                while self.is_pressed(""):
                    time.sleep(0.01)

                self.sound.back()
                self.reset_input()
                return None

            previous = current
            time.sleep(0.01)

    # ========================================================
    # ГЛАВНОЕ МЕНЮ
    # ========================================================

    def main_menu(self):

        self.reset_render()
        self.hide_cursor()

        while True:

            choice = self.menu_select(
                [
                    "Новая игра",
                    "Загрузить игру",
                    "Настройки",
                    "Выход"
                ],
                title_lines=[GAME_TITLE],
                allow_escape=False,
                footer=False
            )

            if choice == 0:
                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                started = self.new_game()
                if started:
                    self.run()
                self.reset_render()

            elif choice == 1:
                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                loaded = self.save_slots_menu("load")
                if loaded:
                    self.run()
                self.reset_render()

            elif choice == 2:
                self.settings_menu()
                self.reset_render()

            elif choice == 3:
                self.reset_render()
                self.render([
                    "До свидания!"
                ])
                time.sleep(0.7)
                return


    # ========================================================
    # НОВАЯ ИГРА
    # ========================================================

    def new_game(self):

        self.reset_render()
        self.show_cursor()

        name = self.get_player_name()

        if name is None:
            self.hide_cursor()
            self.wait_for_all_keys_release()
            self.reset_input()
            self.reset_render()
            return False

        self.player = Player(
            x=2,
            y=2,
            name=name,
            hp=100,
            max_hp=100,
            attack=20
        )

        # Новая карта создаётся точно под доступную область рамки.
        self.set_map_size_for_screen()

        self.create_map()
        self.create_enemies()
        self.create_objects()

        self.hide_cursor()
        self.wait_for_all_keys_release()
        self.reset_input()
        self.reset_render()

        return True


    # ========================================================
    # СОХРАНЕНИЯ
    # ========================================================

    @staticmethod
    def get_save_path(slot):

        return os.path.join(SAVE_DIR, f"slot_{slot}.json")

    def get_save_slots(self):

        os.makedirs(SAVE_DIR, exist_ok=True)
        slots = []

        for slot in range(1, SAVE_SLOTS + 1):
            path = self.get_save_path(slot)
            if not os.path.exists(path):
                slots.append(None)
                continue

            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                save_info = data.get("save_info")
                if save_info:
                    # Старые сохранения не содержали отдельного времени.
                    # Берём его из времени изменения файла, чтобы они
                    # отображались в новом формате без миграции сейва.
                    if not save_info.get("time"):
                        save_info["time"] = time.strftime(
                            "%H:%M:%S",
                            time.localtime(os.path.getmtime(path))
                        )
                slots.append(save_info)
            except Exception:
                slots.append(None)

        return slots

    def save_game(self, slot):

        if self.player is None:
            return False

        os.makedirs(SAVE_DIR, exist_ok=True)
        date = time.strftime("%d/%m/%Y", time.localtime())
        save_time = time.strftime("%H:%M:%S", time.localtime())

        data = {
            "save_info": {
                "name": self.player.name,
                "hp": self.player.hp,
                "date": date,
                "time": save_time
            },
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "name": self.player.name,
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "attack": self.player.attack,
                "energy": self.player.energy,
                "max_energy": self.player.max_energy,
                "hunger": self.player.hunger,
                "thirst": self.player.thirst,
                "fatigue": self.player.fatigue,
                "temperature": self.player.temperature,
                "weight": self.player.weight,
                "max_weight": self.player.max_weight
            },
            "enemies": [
                {
                    "x": enemy.x, "y": enemy.y,
                    "name": enemy.name, "hp": enemy.hp,
                    "max_hp": enemy.max_hp, "attack": enemy.attack
                }
                for enemy in self.enemies
            ],
            "objects": [
                {
                    "x": obj.x, "y": obj.y,
                    "name": obj.name,
                    "description": obj.description,
                    "used": obj.used
                }
                for obj in self.objects
            ],
            "map": self.map
        }

        path = self.get_save_path(slot)
        temporary_file = path + ".tmp"

        try:
            with open(temporary_file, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            os.replace(temporary_file, path)
            return True
        except Exception:
            try:
                if os.path.exists(temporary_file):
                    os.remove(temporary_file)
            except Exception:
                pass
            return False

    def delete_game(self, slot):
        """Удаляет сохранение из указанного слота."""

        path = self.get_save_path(slot)

        if not os.path.exists(path):
            return False

        try:
            os.remove(path)
            return True
        except Exception:
            return False

    def load_game(self, slot):

        path = self.get_save_path(slot)
        if not os.path.exists(path):
            return False

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            player_data = data["player"]
            self.player = Player(
                x=player_data["x"], y=player_data["y"],
                name=player_data["name"], hp=player_data["hp"],
                max_hp=player_data["max_hp"], attack=player_data["attack"]
            )

            # Дополнительные параметры совместимы со старыми сохранениями.
            self.player.energy = player_data.get("energy", 100)
            self.player.max_energy = player_data.get("max_energy", 100)
            self.player.hunger = player_data.get("hunger", 100)
            self.player.thirst = player_data.get("thirst", 100)
            self.player.fatigue = player_data.get("fatigue", 0)
            self.player.temperature = player_data.get("temperature", 36.6)
            self.player.weight = player_data.get("weight", 0.0)
            self.player.max_weight = player_data.get("max_weight", 20.0)

            self.enemies = [
                Enemy(
                    x=item["x"], y=item["y"], name=item["name"],
                    hp=item["hp"], max_hp=item["max_hp"], attack=item["attack"]
                )
                for item in data["enemies"]
            ]

            self.objects = []
            for item in data["objects"]:
                obj = GameObject(
                    x=item["x"], y=item["y"],
                    name=item["name"], description=item["description"]
                )
                obj.used = item.get("used", False)
                self.objects.append(obj)

            self.map = data["map"]

            # Загруженное сохранение использует собственный размер карты.
            # Это сохраняет совместимость со старыми сохранениями.
            global MAP_WIDTH, MAP_HEIGHT
            MAP_HEIGHT = len(self.map)
            MAP_WIDTH = len(self.map[0]) if self.map else 1

            # В старых сохранениях внешняя граница карты могла быть
            # выполнена символом #. Теперь граница интерфейса находится
            # снаружи карты, поэтому убираем только периметр карты.
            if self.map and len(self.map) >= 2 and len(self.map[0]) >= 2:
                for x in range(len(self.map[0])):
                    self.map[0][x] = GROUND_SYMBOL
                    self.map[-1][x] = GROUND_SYMBOL
                for y in range(len(self.map)):
                    self.map[y][0] = GROUND_SYMBOL
                    self.map[y][-1] = GROUND_SYMBOL

            self.hide_cursor()
            self.wait_for_all_keys_release()
            self.reset_input()
            self.reset_render()
            return True

        except Exception:
            return False

    def save_slots_menu(self, mode, overlay=False):
        """
        Меню слотов сохранений.

        W/S — выбор слота
        A/D — переключение между строкой сохранения и удалением
        E   — загрузить/сохранить выбранный слот
        X   — удалить выбранное сохранение
        ESC — назад

        Для каждого существующего сохранения справа всегда отображается
        «Удалить [X]». При выборе слота жёлтым подсвечивается либо сама
        строка сохранения, либо кнопка удаления — в зависимости от выбора A/D.
        """

        selected = 0
        action_selected = 0  # 0 — строка сохранения, 1 — удалить

        title = self._translate_text("СОХРАНЕНИЕ ИГРЫ" if mode == "save" else "ЗАГРУЗКА ИГРЫ")

        self.wait_for_all_keys_release()
        self.reset_input()
        self.flush_console_input()

        if not overlay:
            self.reset_render()

        previous = {
            "w": False,
            "a": False,
            "s": False,
            "d": False,
            "e": False,
            "x": False,
            "esc": False
        }

        while True:
            slots = self.get_save_slots()

            width = min(SCREEN_WIDTH - 8, 54)
            inner = width - 2
            delete_label = self._translate_text("Удалить [X]")
            delete_len = len(delete_label)

            # Левая часть строки сохранения имеет ФИКСИРОВАННУЮ структуру.
            # Имя всегда занимает одинаковое количество знакомест, поэтому
            # разделители "|" и дата/время больше не зависят от длины имени.
            name_width = 11  # длина "Пустой слот"
            left_margin = 1
            gap = 2
            right_margin = 1

            save_prefix_width = name_width + 3 + 10 + 3 + 8

            lines = ["╔" + "═" * inner + "╗"]

            title_left = max(0, (inner - len(title)) // 2)
            title_right = inner - len(title) - title_left
            lines.append(
                "║" + " " * title_left + title + " " * title_right + "║"
            )
            lines.append("╠" + "═" * inner + "╣")

            for index, info in enumerate(slots):
                if info:
                    save_date = info.get("date", "--/--/----")
                    save_time = info.get("time", "--:--:--")
                    name = str(info.get("name", "Неизвестно"))

                    # Фиксированная колонка имени. Если имя короче 11 символов,
                    # оно дополняется пробелами; если длиннее — аккуратно
                    # обрезается. Благодаря этому "|" всегда находится
                    # в одной и той же позиции независимо от имени персонажа.
                    fixed_name = name[:name_width].ljust(name_width)
                    save_text = (
                        fixed_name
                        + " | "
                        + str(save_date)[:10].ljust(10)
                        + " | "
                        + str(save_time)[:8].ljust(8)
                    )

                    if index == selected and action_selected == 0:
                        save_part = ANSI_YELLOW + self._ui_text(save_text) + ANSI_RESET
                        delete_part = self._ui_text(delete_label)
                    elif index == selected and action_selected == 1:
                        save_part = self._ui_text(save_text)
                        delete_part = ANSI_YELLOW + self._ui_text(delete_label) + ANSI_RESET
                    else:
                        save_part = self._ui_text(save_text)
                        delete_part = self._ui_text(delete_label)

                    # Левая часть и кнопка удаления являются двумя независимыми
                    # блоками. Кнопка фиксируется у правого края, а всё свободное
                    # место остаётся строго между ними.
                    middle_padding_len = max(
                        1,
                        inner
                        - left_margin
                        - len(save_text)
                        - gap
                        - delete_len
                        - right_margin
                    )
                    middle_padding = " " * middle_padding_len

                    text = (
                        " " * left_margin
                        + save_part
                        + " " * gap
                        + middle_padding
                        + delete_part
                        + " " * right_margin
                    )
                else:
                    empty_text = (
                        self._translate_text("Пустой слот").ljust(name_width)
                        + " | "
                        + "--/--/----"
                        + " | "
                        + "--:--:--"
                    )

                    if index == selected:
                        left_part = (
                            " " * left_margin
                            + ANSI_YELLOW
                            + empty_text
                            + ANSI_RESET
                        )
                    else:
                        left_part = " " * left_margin + empty_text

                    # У пустого слота кнопка удаления отсутствует.
                    # Остаток строки просто заполняется пробелами до рамки.
                    padding_len = max(
                        0,
                        inner - left_margin - len(empty_text) - right_margin
                    )

                    text = (
                        left_part
                        + " " * padding_len
                        + " " * right_margin
                    )

                lines.append("║" + text + "║")

            # Отдельная кнопка возврата находится после всех слотов.
            # На ней нет действий A/D — выбирать нечего.
            back_label = self._translate_text("Назад [ESC]")
            # Кнопка возврата выравнивается по левому краю,
            # как и элементы в остальных разделах интерфейса.
            back_left = left_margin
            back_right = max(0, inner - len(back_label) - back_left)
            if selected == SAVE_SLOTS:
                back_text = (
                    "║"
                    + " " * back_left
                    + ANSI_YELLOW
                    + back_label
                    + ANSI_RESET
                    + " " * back_right
                    + "║"
                )
            else:
                back_text = (
                    "║"
                    + " " * back_left
                    + back_label
                    + " " * back_right
                    + "║"
                )
            lines.append(back_text)
            lines.append("╚" + "═" * inner + "╝")

            if overlay and self.player is not None:
                self.draw_game(overlay=lines)
            else:
                self.render_menu_screen(lines)

            current = {
                "w": self.is_pressed("w"),
                "a": self.is_pressed("a"),
                "s": self.is_pressed("s"),
                "d": self.is_pressed("d"),
                "e": self.is_pressed("e"),
                "x": self.is_pressed("x"),
                "esc": self.is_pressed("\x1b")
            }

            if self.mouse_enabled():
                cell = self.get_mouse_cell()
                if cell is not None:
                    mx, my = cell
                    content_width = max(1, SCREEN_WIDTH - 2)
                    overlay_height = len(lines)
                    if overlay:
                        available_height = max(1, (SCREEN_HEIGHT - 2) - HUD_HEIGHT)
                        start_y = max(0, (available_height - overlay_height) // 2)
                    else:
                        start_y = max(0, ((SCREEN_HEIGHT - 2) - overlay_height) // 2)
                    local_y = my - (1 + start_y)
                    slot_row = local_y - 3
                    hover_changed = False
                    if 0 <= slot_row < SAVE_SLOTS:
                        if selected != slot_row:
                            selected = slot_row
                            hover_changed = True
                        if slots[slot_row] is not None:
                            save_date = slots[slot_row].get("date", "--/--/----")
                            save_time = slots[slot_row].get("time", "--:--:--")
                            name = str(slots[slot_row].get("name", "Неизвестно"))
                            fixed_name = name[:name_width].ljust(name_width)
                            save_text = fixed_name + " | " + str(save_date)[:10].ljust(10) + " | " + str(save_time)[:8].ljust(8)
                            middle_padding_len = max(1, inner - left_margin - len(save_text) - gap - delete_len - right_margin)
                            if overlay:
                                menu_width = min(content_width, max(visible_len(line) for line in lines))
                                start_x = max(0, (content_width - menu_width) // 2)
                            else:
                                menu_width = min(content_width, max(visible_len(line) for line in lines))
                                start_x = max(0, (content_width - menu_width) // 2)
                            delete_start = 1 + start_x + left_margin + len(save_text) + gap + middle_padding_len
                            new_action = 1 if mx >= delete_start else 0
                            if action_selected != new_action:
                                action_selected = new_action
                                hover_changed = True
                        else:
                            if action_selected != 0:
                                action_selected = 0
                                hover_changed = True
                    elif selected != SAVE_SLOTS:
                        # Наведение на кнопку "Назад [ESC]".
                        back_row = 3 + SAVE_SLOTS
                        if local_y == back_row:
                            selected = SAVE_SLOTS
                            action_selected = 0
                            hover_changed = True
                    if hover_changed:
                        self.sound.move()
                        continue

            if self.mouse_enabled() and self.mouse_click():
                cell = self.get_mouse_cell()
                if cell is not None:
                    _, my = cell
                    # В save_slots_menu строки начинаются после: верхней рамки,
                    # заголовка и разделителя. Они все однострочные.
                    content_width = max(1, SCREEN_WIDTH - 2)
                    overlay_height = len(lines)
                    if overlay:
                        available_height = max(1, (SCREEN_HEIGHT - 2) - HUD_HEIGHT)
                        start_y = max(0, (available_height - overlay_height) // 2)
                    else:
                        start_y = max(0, ((SCREEN_HEIGHT - 2) - overlay_height) // 2)
                    local_y = my - (1 + start_y)
                    slot_row = local_y - 3

                    if 0 <= slot_row < SAVE_SLOTS:
                        selected = slot_row
                        if slots[slot_row] is not None:
                            # Кнопка удаления начинается после правой части
                            # строки сохранения. Определяем её по фактической
                            # геометрии строки, а не по фиксированной координате.
                            save_date = slots[slot_row].get("date", "--/--/----")
                            save_time = slots[slot_row].get("time", "--:--:--")
                            name = str(slots[slot_row].get("name", "Неизвестно"))
                            fixed_name = name[:name_width].ljust(name_width)
                            save_text = fixed_name + " | " + str(save_date)[:10].ljust(10) + " | " + str(save_time)[:8].ljust(8)
                            middle_padding_len = max(1, inner - left_margin - len(save_text) - gap - delete_len - right_margin)
                            if overlay:
                                menu_width = min(content_width, max(visible_len(line) for line in lines))
                                start_x = max(0, (content_width - menu_width) // 2)
                            else:
                                menu_width = min(content_width, max(visible_len(line) for line in lines))
                                start_x = max(0, (content_width - menu_width) // 2)
                            delete_start = 1 + start_x + left_margin + len(save_text) + gap + middle_padding_len
                            if cell[0] >= delete_start:
                                action_selected = 1
                            else:
                                action_selected = 0
                        else:
                            action_selected = 0

                        self.sound.select()

                        # В меню загрузки ЛКМ по левой части существующего
                        # слота сразу загружает игру. Кнопка удаления
                        # остаётся отдельной зоной справа.
                        if (
                            mode == "load"
                            and slots[slot_row] is not None
                            and action_selected == 0
                        ):
                            slot = slot_row + 1
                            self.wait_for_mouse_release()
                            self.wait_for_all_keys_release()
                            self.reset_input()
                            self.flush_console_input()
                            if self.load_game(slot):
                                return True
                            self._slot_message(
                                "Не удалось загрузить сохранение.",
                                "ЗАГРУЗКА ИГРЫ",
                                overlay=overlay
                            )
                            previous = {k: False for k in previous}
                            continue

                        self.wait_for_mouse_release()
                        previous = {k: False for k in previous}
                        self.wait_for_all_keys_release()
                        self.reset_input()
                        continue

                    if slot_row == SAVE_SLOTS:
                        selected = SAVE_SLOTS
                        action_selected = 0
                        self.sound.back()
                        self.wait_for_all_keys_release()
                        self.reset_input()
                        self.flush_console_input()
                        self.reset_render()
                        return False

            # ------------------------------------------------
            # ВЫБОР СЛОТА
            # ------------------------------------------------

            if current["w"] and not previous["w"]:
                selected = (selected - 1) % (SAVE_SLOTS + 1)
                action_selected = 0
                self.sound.move()

            elif current["s"] and not previous["s"]:
                selected = (selected + 1) % (SAVE_SLOTS + 1)
                action_selected = 0
                self.sound.move()

            # ------------------------------------------------
            # ВЫБОР ДЕЙСТВИЯ
            # ------------------------------------------------

            elif current["a"] and not previous["a"]:
                # На пустом слоте и на «Назад [ESC]» переключать действие
                # нечего — menu_move не воспроизводится.
                if selected < SAVE_SLOTS and slots[selected] is not None and action_selected == 1:
                    action_selected = 0
                    self.sound.move()

            elif current["d"] and not previous["d"]:
                # На пустом слоте и на «Назад [ESC]» переключать действие
                # нечего — menu_move не воспроизводится.
                if selected < SAVE_SLOTS and slots[selected] is not None and action_selected == 0:
                    action_selected = 1
                    self.sound.move()

            # ------------------------------------------------
            # ESC — НАЗАД
            # ------------------------------------------------

            elif current["esc"] and not previous["esc"]:
                self.sound.back()
                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                self.reset_render()
                return False

            # ------------------------------------------------
            # X — УДАЛЕНИЕ
            # ------------------------------------------------

            elif current["x"] and not previous["x"] and action_selected == 1:
                slot = selected + 1
                info = slots[selected]

                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()

                if info is None:
                    self._slot_message(
                        "Слот пуст.",
                        "УДАЛЕНИЕ СОХРАНЕНИЯ",
                        overlay=overlay
                    )
                    previous = {k: False for k in previous}
                    continue

                confirmation = self.menu_select(
                    ["Удалить сохранение", "Отмена"],
                    title_lines=[
                        "УДАЛЕНИЕ СОХРАНЕНИЯ",
                        f"Слот {slot}",
                        f"{info.get('name', 'Неизвестно')}|"
                        f"{info.get('date', '--/--/----')}|"
                        f"{info.get('time', '--:--:--')}"
                    ],
                    overlay=overlay
                )

                if confirmation == 0:
                    if self.delete_game(slot):
                        self._slot_message(
                            f"Слот {slot} удалён.",
                            "УДАЛЕНИЕ СОХРАНЕНИЯ",
                            overlay=overlay
                        )
                    else:
                        self._slot_message(
                            "Не удалось удалить сохранение.",
                            "УДАЛЕНИЕ СОХРАНЕНИЯ",
                            overlay=overlay
                        )

                previous = {k: False for k in previous}
                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                continue

            # ------------------------------------------------
            # E — ВЫБОР «НАЗАД [ESC]»
            # ------------------------------------------------

            elif current["e"] and not previous["e"] and selected == SAVE_SLOTS:
                self.sound.select()
                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                self.reset_render()
                return False

            # ------------------------------------------------
            # E — ОСНОВНОЕ ДЕЙСТВИЕ
            # ------------------------------------------------

            elif current["e"] and not previous["e"] and action_selected == 0 and selected < SAVE_SLOTS:
                slot = selected + 1
                info = slots[selected]
                self.sound.select()

                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()

                if mode == "load":
                    if info is None:
                        self._slot_message(
                            "Слот пуст.",
                            "ЗАГРУЗКА ИГРЫ",
                            overlay=overlay
                        )
                        previous = {k: False for k in previous}
                        continue

                    if self.load_game(slot):
                        return True

                    self._slot_message(
                        "Не удалось загрузить сохранение.",
                        "ЗАГРУЗКА ИГРЫ",
                        overlay=overlay
                    )
                    previous = {k: False for k in previous}
                    continue

                # ------------------------------------------------
                # СОХРАНЕНИЕ
                # ------------------------------------------------

                if info is not None:
                    confirmation = self.menu_select(
                        ["Перезаписать слот", "Отмена"],
                        title_lines=[
                            "ПЕРЕЗАПИСЬ СЛОТА",
                            f"Слот {slot}",
                            f"{info.get('name', 'Неизвестно')}|"
                            f"{info.get('date', '--/--/----')}|"
                            f"{info.get('time', '--:--:--')}"
                        ],
                        overlay=overlay
                    )

                    if confirmation != 0:
                        previous = {k: False for k in previous}
                        self.flush_console_input()
                        continue

                if self.save_game(slot):
                    self._slot_message(
                        f"Слот {slot} сохранён.",
                        "СОХРАНЕНИЕ ИГРЫ",
                        overlay=overlay
                    )
                else:
                    self._slot_message(
                        "Не удалось сохранить игру.",
                        "СОХРАНЕНИЕ ИГРЫ",
                        overlay=overlay
                    )

                previous = {k: False for k in previous}
                self.flush_console_input()
                continue

            previous = current

    def _slot_message(self, message, title="СОХРАНЕНИЕ ИГРЫ", overlay=False):
        lines = self._menu_box(
            [title],
            [message],
            0,
            footer=False
        )
        inner = len(lines[0]) - 2
        hint = self._translate_text("E / ESC — продолжить")
        left = max(0, (inner - len(hint)) // 2)
        right = inner - len(hint) - left
        lines.insert(
            -1,
            "║" + " " * left + hint + " " * right + "║"
        )

        if overlay and self.player is not None:
            self.draw_game(overlay=lines)
        else:
            self.reset_render()
            self.render_menu_screen(lines)

        self.wait_for_all_keys_release()
        self.reset_input()
        self.flush_console_input()

        previous_e = False
        previous_esc = False

        while True:
            current_e = self.is_pressed("e")
            current_esc = self.is_pressed("\x1b")

            if (current_e and not previous_e) or (
                current_esc and not previous_esc
            ):
                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                self.reset_render()
                return

            previous_e = current_e
            previous_esc = current_esc
            time.sleep(0.01)

    # ========================================================
    # НАСТРОЙКИ
    # ========================================================

    def _settings_box(self, title, options, selected, hint=None, overlay=False):
        # В разделах настроек подсказки управления не отображаются.
        # Управление содержит отдельное подменю с руководством.
        box = self._menu_box([title], options, selected, footer=False)

        if overlay and self.player is not None:
            self.draw_game(overlay=box)
        else:
            self.render_menu_screen(box)

    def settings_menu(self, overlay=False):
        while True:
            choice = self.menu_select(
                [
                    "Звук",
                    "Управление",
                    "Экран",
                    "Язык",
                    "Назад [ESC]"
                ],
                title_lines=["НАСТРОЙКИ"],
                overlay=overlay,
                footer=False
            )

            if choice is None or choice == 4:
                self.sound.back()
                return
            if choice == 0:
                self.sound_settings(overlay)
            elif choice == 1:
                self.controls_menu(overlay)
            elif choice == 2:
                self.screen_settings(overlay)
            elif choice == 3:
                self.language_settings(overlay)

    def _settings_value_line(self, label, value, width=50):
        value_text = f"[{value}]"
        spaces = max(1, width - len(label) - len(value_text))
        return f"{label}{' ' * spaces}{value_text}"

    def _settings_loop(self, title, options_builder, selected, change_callback, overlay):
        previous = {k: False for k in ("w", "s", "a", "d", "e", "esc")}
        while True:
            options = options_builder()
            self._settings_box(title, options, selected, overlay=overlay)

            current = {
                "w": self.is_pressed("w"),
                "s": self.is_pressed("s"),
                "a": self.is_pressed("a"),
                "d": self.is_pressed("d"),
                "e": self.is_pressed("e"),
                "esc": self.is_pressed("\x1b")
            }

            if self.mouse_enabled():
                box = self._menu_box([title], options, selected, footer=False)
                hovered = self._mouse_menu_option(options, box, overlay=overlay)
                if hovered is not None and hovered != selected:
                    selected = hovered
                    self.sound.move()
                    self._settings_box(title, options, selected, overlay=overlay)

            # В разделе «Звук» колесо мыши изменяет громкость выбранной строки.
            if self.mouse_enabled() and title == "ЗВУК":
                wheel_delta = self._consume_mouse_wheel()
                if wheel_delta and selected in (0, 1, 2):
                    # Стандартный WHEEL_DELTA = 120. Обрабатываем каждый щелчок.
                    steps = max(1, abs(wheel_delta) // 120)
                    action = "right" if wheel_delta > 0 else "left"
                    for _ in range(steps):
                        change_callback(selected, action)
                    self._settings_box(
                        title,
                        options_builder(),
                        selected,
                        overlay=overlay
                    )

            if self.mouse_enabled() and self.mouse_click():
                box = self._menu_box([title], options, selected, footer=False)
                clicked = self._mouse_menu_option(options, box, overlay=overlay)
                if clicked is not None:
                    selected = clicked
                    result = change_callback(selected, "enter")
                    if result == "back":
                        self.sound.back()
                        self.wait_for_all_keys_release()
                        self.reset_input()
                        return
                    self.sound.select()
                    self.wait_for_mouse_release()
                    previous = {k: False for k in previous}
                    time.sleep(0.01)
                    continue

            if current["w"] and not previous["w"]:
                selected = (selected - 1) % len(options)
                self.sound.move()
            elif current["s"] and not previous["s"]:
                selected = (selected + 1) % len(options)
                self.sound.move()
            elif current["a"] and not previous["a"]:
                result = change_callback(selected, "left")
                if result == "back":
                    return
            elif current["d"] and not previous["d"]:
                result = change_callback(selected, "right")
                if result == "back":
                    return
            elif current["e"] and not previous["e"]:
                result = change_callback(selected, "enter")
                if result == "back":
                    self.sound.back()
                    self.wait_for_all_keys_release()
                    self.reset_input()
                    return
                self.sound.select()
            elif current["esc"] and not previous["esc"]:
                self.sound.back()
                self.wait_for_all_keys_release()
                self.reset_input()
                return

            previous = current
            time.sleep(0.01)

    def sound_settings(self, overlay=False):
        def options():
            return [
                self._settings_value_line("Общая громкость", f"{self.settings['master_volume']}%"),
                self._settings_value_line("Громкость музыки", f"{self.settings['music_volume']}%"),
                self._settings_value_line("Громкость интерфейса", f"{self.settings['interface_volume']}%"),
                self._settings_value_line("Звуки", "включены" if self.settings["sounds_enabled"] else "выключены"),
                "Назад [ESC]"
            ]

        def change(selected, action):
            if selected == 0 and action in ("left", "right"):
                self.settings["master_volume"] = max(0, min(100, self.settings["master_volume"] + (10 if action == "right" else -10)))
                self.save_user_settings()
                self.sound.move()
            elif selected == 1 and action in ("left", "right"):
                self.settings["music_volume"] = max(0, min(100, self.settings["music_volume"] + (10 if action == "right" else -10)))
                self.save_user_settings()
                self.sound.move()
            elif selected == 2 and action in ("left", "right"):
                self.settings["interface_volume"] = max(0, min(100, self.settings["interface_volume"] + (10 if action == "right" else -10)))
                self.save_user_settings()
                self.sound.move()
            elif selected == 3 and action in ("enter", "left", "right"):
                self.settings["sounds_enabled"] = not self.settings["sounds_enabled"]
                self.save_user_settings()
                self.sound.select(force=True)
            elif selected == 4 and action == "enter":
                return "back"

        self.wait_for_all_keys_release()
        self.reset_input()
        self._settings_loop("ЗВУК", options, 0, change, overlay)

    def screen_settings(self, overlay=False):
        font_options = ("Обычный", "Жирный")

        def options():
            return [
                self._settings_value_line(
                    "Полный экран",
                    "Включено" if self.settings["fullscreen"] else "Выключено"
                ),
                self._settings_value_line("Шрифт", self.settings.get("font", "Обычный")),
                "Назад [ESC]"
            ]

        def change(selected, action):
            if selected == 0 and action in ("enter", "left", "right"):
                self.settings["fullscreen"] = not self.settings["fullscreen"]
                self.save_user_settings()

                # Штатное переключение полноэкранного режима
                # Windows Terminal — то же действие, что F11.
                self.toggle_terminal_fullscreen()

                self.update_terminal_size()
                self.reset_render()
                return

            if selected == 1 and action in ("enter", "left", "right"):
                current = self.settings.get("font", "Обычный")
                index = font_options.index(current)

                if action == "left":
                    index = (index - 1) % len(font_options)
                else:
                    index = (index + 1) % len(font_options)

                self.settings["font"] = font_options[index]
                self.save_user_settings()
                return

            if selected == 2 and action == "enter":
                return "back"

        self.wait_for_all_keys_release()
        self.reset_input()
        self._settings_loop("ЭКРАН", options, 0, change, overlay)

    def control_scheme_settings(self, overlay=False):
        scheme_options = ("Клавиатура", "Клавиатура+Мышь")

        def options():
            return [
                self._settings_value_line(
                    "Схема управления",
                    self.settings.get("control_scheme", "Клавиатура")
                ),
                "Назад [ESC]"
            ]

        def change(selected, action):
            if selected == 0 and action in ("enter", "left", "right"):
                current = self.settings.get("control_scheme", "Клавиатура")
                index = scheme_options.index(current)

                if action == "left":
                    index = (index - 1) % len(scheme_options)
                else:
                    index = (index + 1) % len(scheme_options)

                self.settings["control_scheme"] = scheme_options[index]
                self.save_user_settings()
                return

            if selected == 1 and action == "enter":
                return "back"

        self.wait_for_all_keys_release()
        self.reset_input()
        self._settings_loop("СХЕМА УПРАВЛЕНИЯ", options, 0, change, overlay)

    def language_settings(self, overlay=False):
        def options():
            return [
                self._settings_value_line("Язык", self.settings["language"]),
                "Назад [ESC]"
            ]

        def change(selected, action):
            if selected == 0 and action in ("enter", "left", "right"):
                self.settings["language"] = "English" if self.settings["language"] == "Русский" else "Русский"
                self.save_user_settings()
            elif selected == 1 and action == "enter":
                return "back"

        self.wait_for_all_keys_release()
        self.reset_input()
        self._settings_loop("ЯЗЫК", options, 0, change, overlay)

    # ========================================================
    # УПРАВЛЕНИЕ
    # ========================================================

    def controls_menu(self, overlay=False):
        scheme_options = ("Клавиатура", "Клавиатура+Мышь")

        def options():
            return [
                "Руководство",
                self._settings_value_line("Схема управления", self.settings.get("control_scheme", "Клавиатура")),
                "Назад [ESC]"
            ]

        def change(selected, action):
            if selected == 0 and action == "enter":
                self.show_controls_guide(overlay)
                return

            if selected == 1 and action in ("enter", "left", "right"):
                current = self.settings.get("control_scheme", "Клавиатура")
                index = scheme_options.index(current)

                if action == "left":
                    index = (index - 1) % len(scheme_options)
                else:
                    index = (index + 1) % len(scheme_options)

                self.settings["control_scheme"] = scheme_options[index]
                return

            if selected == 2 and action == "enter":
                return "back"

        self.wait_for_all_keys_release()
        self.reset_input()
        self._settings_loop("УПРАВЛЕНИЕ", options, 0, change, overlay)

    def show_controls_guide(self, overlay=False):
        lines = [
            "Движение: W/A/S/D",
            "Взаимодействие: E",
            "Разместить объект: F",
            "Инвентарь: TAB",
            "Карта: M",
            "Назад [ESC]"
        ]

        # В руководстве нет перелистывания пунктов: это информационный экран.
        # Кнопка "Назад [ESC]" сразу является выбранной и подсвечивается жёлтым.
        selected = len(lines) - 1

        self.wait_for_all_keys_release()
        self.reset_input()
        previous_e = False
        previous_esc = False

        while True:
            box = self._menu_box(
                ["РУКОВОДСТВО"],
                lines,
                selected,
                footer=False
            )

            if overlay and self.player is not None:
                self.draw_game(overlay=box)
            else:
                self.render_menu_screen(box)

            current_e = self.is_pressed("e")
            current_esc = self.is_pressed("\x1b")

            if self.mouse_enabled() and self.mouse_click():
                clicked = self._mouse_menu_option(lines, box, overlay=overlay)
                if clicked == len(lines) - 1:
                    self.sound.back()
                    self.wait_for_all_keys_release()
                    self.reset_input()
                    return

            # E подтверждает уже выбранную кнопку "Назад [ESC]".
            if current_e and not previous_e:
                self.sound.back()
                self.wait_for_all_keys_release()
                self.reset_input()
                return

            elif current_esc and not previous_esc:
                self.sound.back()
                self.wait_for_all_keys_release()
                self.reset_input()
                return

            previous_e = current_e
            previous_esc = current_esc
            time.sleep(0.01)

    # Обратная совместимость с прежним именем метода.
    def show_controls(self, overlay=False):
        self.controls_menu(overlay)

    # ========================================================
    # НОРМАЛИЗАЦИЯ ОКНА ПОВЕРХ ИГРОВОГО ПОЛЯ
    # ========================================================

    @staticmethod
    def _fit_overlay_line(line, width):
        """
        Гарантирует строго заданную видимую ширину строки overlay.
        ANSI-коды цвета не учитываются в геометрии строки.

        Важно: если строка уже содержит ANSI-цвет, дополнительные пробелы
        должны добавляться ДО ANSI_RESET, иначе цветная строка и её правая
        рамка могут оказаться короче остальных строк overlay.
        """
        line = str(line)
        visible = ANSI_ESCAPE_RE.sub("", line)

        if len(visible) >= width:
            if len(visible) > width:
                # Для текущих меню этого не происходит, но безопасно
                # обрезаем строку, если она всё же оказалась шире окна.
                line = visible[:width]
            return line

        padding = " " * (width - len(visible))

        # Если строка заканчивается ANSI_RESET + рамкой, вставляем padding
        # перед сбросом цвета и перед правой рамкой.
        if line.endswith(ANSI_RESET + "║"):
            content = line[:-len(ANSI_RESET + "║")]
            return content + padding + ANSI_RESET + "║"

        return line + padding

    # ========================================================
    # ОТРИСОВКА ИГРОВОГО ПОЛЯ
    # ========================================================

    def draw_game(
        self,
        action_menu=None,
        overlay=None
    ):

        self.update_terminal_size()

        content_width = max(1, SCREEN_WIDTH - 2)
        content_height = max(1, SCREEN_HEIGHT - 2)
        header_height = 0
        hud_height = min(max(HUD_HEIGHT, 9), max(3, content_height - 8))
        available_map_height = max(1, content_height - header_height - hud_height)

        display_map = [row.copy() for row in self.map]

        # ----------------------------------------------------
        # ОБЪЕКТЫ
        # ----------------------------------------------------

        for obj in self.objects:
            if 0 <= obj.x < len(display_map[0]) and 0 <= obj.y < len(display_map):
                display_map[obj.y][obj.x] = OBJECT_SYMBOL

        # ----------------------------------------------------
        # ВРАГИ
        # ----------------------------------------------------

        for enemy in self.enemies:
            if 0 <= enemy.x < len(display_map[0]) and 0 <= enemy.y < len(display_map):
                display_map[enemy.y][enemy.x] = ENEMY_SYMBOL

        # ----------------------------------------------------
        # ИГРОК
        # ----------------------------------------------------

        if display_map and 0 <= self.player.y < len(display_map) and 0 <= self.player.x < len(display_map[0]):
            display_map[self.player.y][self.player.x] = PLAYER_SYMBOL

        # Во время игры верхняя часть экрана — продолжение игрового поля.
        lines = []

        # ----------------------------------------------------
        # КАРТА
        # ----------------------------------------------------

        # Одна игровая клетка = один символ терминала.
        # Никаких пробелов между клетками.
        map_lines = ["".join(row) for row in display_map]
        map_lines = [line[:content_width].ljust(content_width, GROUND_SYMBOL) for line in map_lines]

        # Если сохранение старого формата оказалось выше доступной области,
        # показываем только видимую часть, не ломая HUD.
        map_lines = map_lines[:available_map_height]
        while len(map_lines) < available_map_height:
            map_lines.append(GROUND_SYMBOL * content_width)

        # ----------------------------------------------------
        # ОКНО ПОВЕРХ ИГРОВОГО ПОЛЯ
        # ----------------------------------------------------

        if overlay and map_lines:
            overlay_width = min(
                content_width,
                max(visible_len(line) for line in overlay)
            )
            overlay_height = len(overlay)

            start_y = max(0, (available_map_height - overlay_height) // 2)
            start_x = max(0, (content_width - overlay_width) // 2)

            for index, raw_overlay_line in enumerate(overlay):
                y = start_y + index
                if not (0 <= y < len(map_lines)):
                    continue

                overlay_line = self._fit_overlay_line(raw_overlay_line, overlay_width)
                base_line = map_lines[y].ljust(content_width, GROUND_SYMBOL)

                map_lines[y] = (
                    base_line[:start_x]
                    + overlay_line
                    + base_line[start_x + overlay_width:]
                )

        lines.extend(map_lines)

        # ----------------------------------------------------
        # ДЕЙСТВИЯ
        # ----------------------------------------------------

        # В режиме взаимодействия действие временно выводится над HUD.
        if action_menu:
            action_lines = [str(line) for line in action_menu]
            if len(action_lines) <= max(1, available_map_height):
                # Старое поведение сохраняем: меню остаётся частью игрового
                # поля, а постоянный HUD не сдвигается.
                for index, line in enumerate(action_lines):
                    if index < len(map_lines):
                        map_lines[index] = self._fit_overlay_line(line, content_width)
                lines = lines[:header_height] + map_lines

        # ----------------------------------------------------
        # НИЖНИЙ HUD
        # ----------------------------------------------------
        # HUD состоит из трёх зон:
        #   слева  — характеристики игрока;
        #   центр  — инвентарь со слотами;
        #   справа — окружающая обстановка.
        #
        # Внутренняя рамка карты здесь отсутствует: карта напрямую
        # переходит в HUD, а единственная общая рамка принадлежит экрану.

        if hud_height >= 3:
            left_width = max(28, content_width // 4)
            right_width = max(28, content_width // 4)

            if left_width + right_width + 4 >= content_width:
                left_width = max(10, content_width // 3)
                right_width = max(10, content_width // 3)

            # Внутри общей рамки HUD находятся:
            # 1 символ — левая граница,
            # 2 символа — два разделителя секций,
            # 1 символ — правая граница.
            #
            # Поэтому три содержимые области должны занимать
            # content_width - 4 символа.
            center_width = max(
                1,
                content_width - left_width - right_width - 4
            )

            def fit(text, width, align="left"):
                text = str(text)
                visible = ANSI_ESCAPE_RE.sub("", text)

                if len(visible) > width:
                    # Для строк с ANSI-стилем режем только видимый текст,
                    # чтобы escape-коды не влияли на геометрию панели.
                    text = visible[:width]
                    visible = text

                padding = max(0, width - len(visible))

                if align == "center":
                    left = padding // 2
                    right = padding - left
                    # Пробелы добавляем снаружи стилизованного текста,
                    # чтобы рамки и разделители оставались вне ANSI-режима.
                    return (" " * left) + text + (" " * right)

                return text + (" " * padding)

            def panel_line(left, center, right):
                return (
                    "│"
                    + fit(left, left_width)
                    + "│"
                    + fit(center, center_width, "center")
                    + "│"
                    + fit(right, right_width)
                    + "│"
                )

            def inventory_panel_line(left, grid_line, right):
                # Здесь сетка сама содержит свои левую и правую границы.
                # Поэтому отдельные разделители центральной панели не
                # добавляются: сетка становится единым целым с HUD.
                return (
                    "│"
                    + fit(left, left_width)
                    + grid_line
                    + fit(right, right_width)
                    + "│"
                )

            left_stats = [
                self._ui_text(f"Игрок: {self.player.name}"),
                self._ui_text(f"HP: {self.player.hp}/{self.player.max_hp}"),
                self._ui_text(f"Энергия: {self.player.energy}/{self.player.max_energy}"),
                self._ui_text(f"Голод: {self.player.hunger}%"),
                self._ui_text(f"Жажда: {self.player.thirst}%"),
                self._ui_text(f"Усталость: {self.player.fatigue}%"),
                self._ui_text(f"Температура тела: {self.player.temperature:.1f}°C"),
                self._ui_text(f"Вес: {self.player.weight:.1f}/{self.player.max_weight:.1f} кг")
            ]

            right_stats = [
                self._ui_text("БИОМ: Лес"),
                self._ui_text("Температура воздуха: -5°C"),
                self._ui_text("Погода: Ясно"),
                self._ui_text("Ветер: 3 м/с"),
                self._ui_text("Время: День"),
                self._ui_text(f"Позиция: X={self.player.x} Y={self.player.y}")
            ]

            # ------------------------------------------------
            # ИНВЕНТАРЬ
            # ------------------------------------------------
            # 40 слотов: 20 колонок × 2 ряда.
            # Один слот = один квадрат.
            # При выборе подсвечивается только его собственная рамка:
            # верх, низ, левая и правая стороны.
            columns = 20
            rows = 2
            cell_width = 3
            grid_width = columns * cell_width + (columns - 1) + 2

            min_side_width = 28

            while center_width < grid_width and (left_width > 10 or right_width > 10):
                deficit = grid_width - center_width
                reduce_left = min(max(0, left_width - min_side_width), (deficit + 1) // 2)
                reduce_right = min(max(0, right_width - min_side_width), deficit - reduce_left)

                if reduce_left + reduce_right < deficit:
                    extra = deficit - reduce_left - reduce_right
                    extra_left = min(max(0, left_width - 10 - reduce_left), extra)
                    reduce_left += extra_left
                    extra -= extra_left
                    extra_right = min(max(0, right_width - 10 - reduce_right), extra)
                    reduce_right += extra_right

                if reduce_left + reduce_right == 0:
                    break

                left_width -= reduce_left
                right_width -= reduce_right
                center_width = max(1, content_width - left_width - right_width - 4)

            # Слот 0..19 находится в верхнем ряду, 20..39 — в нижнем.
            def slot_selected(slot_index):
                return self.inventory_mode and slot_index == self.inventory_selected

            def paint(text, selected):
                if selected:
                    return ANSI_YELLOW + text + ANSI_RESET
                return text

            def paint(text, selected):
                if selected:
                    return ANSI_YELLOW + text + ANSI_RESET
                return text

            def inventory_top():
                result = paint("┌", slot_selected(0))
                for col in range(columns):
                    result += paint("─" * cell_width, slot_selected(col))
                    if col == columns - 1:
                        result += paint("┐", slot_selected(col))
                    else:
                        result += paint("┬", slot_selected(col) or slot_selected(col + 1))
                return result

            def inventory_row(top=True):
                result = paint("│", slot_selected(0 if top else columns))
                for col in range(columns):
                    slot_index = col if top else columns + col
                    result += " " * cell_width
                    next_index = (col + 1) if col < columns - 1 else None
                    edge_selected = slot_selected(slot_index) or (next_index is not None and slot_selected(next_index if top else columns + next_index))
                    result += paint("│", edge_selected)
                return result

            def inventory_middle():
                result = paint("├", slot_selected(0) or slot_selected(columns))
                for col in range(columns):
                    top_slot = col
                    bottom_slot = columns + col
                    segment_selected = slot_selected(top_slot) or slot_selected(bottom_slot)
                    result += paint("─" * cell_width, segment_selected)
                    if col == columns - 1:
                        result += paint("┤", segment_selected)
                    else:
                        joint_selected = (
                            slot_selected(top_slot)
                            or slot_selected(bottom_slot)
                            or slot_selected(top_slot + 1)
                            or slot_selected(bottom_slot + 1)
                        )
                        result += paint("┼", joint_selected)
                return result

            def inventory_bottom():
                result = paint("└", slot_selected(columns))
                for col in range(columns):
                    slot_index = columns + col
                    result += paint("─" * cell_width, slot_selected(slot_index))
                    if col == columns - 1:
                        result += paint("┘", slot_selected(slot_index))
                    else:
                        result += paint("┴", slot_selected(slot_index) or slot_selected(columns + col + 1))
                return result

            # Сетка 20 × 2 даёт ровно 40 слотов.
            # Каждый слот выбирается отдельно, поэтому подсветка никогда
            # не распространяется на соседний слот по вертикали.
            grid_left = max(0, (center_width - grid_width) // 2)
            grid_right = max(0, center_width - grid_width - grid_left)

            def grid_line(content):
                return (" " * grid_left) + content + (" " * grid_right)

            def hud_row(left, center, right, center_kind="text"):
                left_text = fit(left, left_width)
                right_text = fit(right, right_width)

                if center_kind == "grid_top":
                    center_text = grid_line(inventory_top())
                elif center_kind == "grid_row_top":
                    center_text = grid_line(inventory_row(True))
                elif center_kind == "grid_mid":
                    center_text = grid_line(inventory_middle())
                elif center_kind == "grid_row_bottom":
                    center_text = grid_line(inventory_row(False))
                elif center_kind == "grid_bottom":
                    center_text = grid_line(inventory_bottom())
                else:
                    center_text = fit(center, center_width, "center")

                # ВАЖНО: здесь ровно два внутренних разделителя HUD:
                # левый | центр | правый. Правая граница формируется
                # самой общей строкой HUD, а не сеткой инвентаря.
                return (
                    "│"
                    + left_text
                    + "│"
                    + center_text
                    + "│"
                    + right_text
                    + "│"
                )

            hud = [
                "┌" + "─" * left_width + "┬" + "─" * center_width + "┬" + "─" * right_width + "┐",
                panel_line(left_stats[0], self._ui_text("ИНВЕНТАРЬ"), right_stats[0]),
                hud_row(left_stats[1], "", right_stats[1], "grid_top"),
                hud_row(left_stats[2], "", right_stats[2], "grid_row_top"),
                hud_row(left_stats[3], "", right_stats[3], "grid_mid"),
                hud_row(left_stats[4], "", right_stats[4], "grid_row_bottom"),
                hud_row(left_stats[5], "", right_stats[5], "grid_bottom"),
                panel_line(left_stats[6], "", ""),
                panel_line(left_stats[7], "", ""),
                "└" + "─" * left_width + "┴" + "─" * center_width + "┴" + "─" * right_width + "┘"
            ]

            lines.extend(hud)

        self.render(lines, fill_char=GROUND_SYMBOL)

    # ========================================================
    # ДВИЖЕНИЕ
    # ========================================================

    def move_player(
        self,
        dx,
        dy
    ):

        if dx == 0 and dy == 0:

            return

        new_x = self.player.x + dx
        new_y = self.player.y + dy

        # ----------------------------------------------------
        # СТЕНА
        # ----------------------------------------------------

        if self.is_wall(
            new_x,
            new_y
        ):

            return

        # ----------------------------------------------------
        # ВРАГ
        # ----------------------------------------------------

        enemy = self.get_enemy_at(
            new_x,
            new_y
        )

        if enemy is not None:

            return

        # ----------------------------------------------------
        # ОБЪЕКТ
        # ----------------------------------------------------

        obj = self.get_object_at(
            new_x,
            new_y
        )

        if obj is not None:

            return

        # ----------------------------------------------------
        # ДВИЖЕНИЕ
        # ----------------------------------------------------

        self.player.x = new_x
        self.player.y = new_y

    # ========================================================
    # ВЗАИМОДЕЙСТВИЕ
    # ========================================================

    def interact(self):

        target_type, target = (
            self.get_adjacent_interactable()
        )

        if target is None:

            return

        if target_type == "enemy":

            self.enemy_interaction(
                target
            )

        elif target_type == "object":

            self.object_interaction(
                target
            )

    # ========================================================
    # ВЗАИМОДЕЙСТВИЕ С ВРАГОМ
    # ========================================================

    def enemy_interaction(self, enemy):

        self.reset_input()
        self.wait_for_all_keys_release()

        while self.player.hp > 0 and enemy.hp > 0:

            choice = self.menu_select(
                ["Атаковать", "Уйти"],
                title_lines=[
                    f"Противник: {enemy.name}",
                    f"HP: {enemy.hp}/{enemy.max_hp}",
                    "",
                ],
                overlay=True
            )

            if choice is None or choice == 1:
                self.wait_for_all_keys_release()
                self.reset_input()
                return

            damage = random.randint(
                max(1, self.player.attack - 5),
                self.player.attack + 5
            )
            enemy.hp = max(0, enemy.hp - damage)

            if enemy.hp <= 0:
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
                self.wait_for_all_keys_release()
                self.reset_input()
                return

            enemy_damage = random.randint(
                max(1, enemy.attack - 3),
                enemy.attack + 3
            )
            self.player.hp = max(0, self.player.hp - enemy_damage)

            if self.player.hp <= 0:
                self.reset_render()
                self.game_over()
                return

            self.wait_for_all_keys_release()
            self.reset_input()

        self.wait_for_all_keys_release()
        self.reset_input()


    # ========================================================
    # ВЗАИМОДЕЙСТВИЕ С ОБЪЕКТОМ
    # ========================================================

    def object_interaction(self, obj):

        while True:
            choice = self.menu_select(
                ["Осмотреть", "Уйти"],
                title_lines=["Взаимодействие: " + obj.name, ""],
                overlay=True
            )

            if choice is None or choice == 1:
                break

            # Экран осмотра: E или ESC возвращают к объекту.
            description_box = self._menu_box(
                [obj.name],
                [obj.description],
                0,
                footer=False
            )

            inner = max(4, min(max(12, SCREEN_WIDTH - 8), 54) - 2)
            hint = self._translate_text("E / ESC — назад")
            left = max(0, (inner - len(hint)) // 2)
            right = inner - len(hint) - left

            self.draw_game(overlay=description_box[:-1] + [
                "╠" + "═" * inner + "╣",
                "║" + " " * left + hint + " " * right + "║",
                "╚" + "═" * inner + "╝"
            ])

            while True:
                key = self.get_key()
                if key in ("e", "\x1b"):
                    self.wait_for_all_keys_release()
                    self.reset_input()
                    break

        self.wait_for_all_keys_release()
        self.reset_input()


    # ========================================================
    # GAME OVER
    # ========================================================

    def game_over(self):

        self.reset_render()
        self.show_cursor()

        lines = self._menu_box(
            ["GAME OVER"],
            ["Ваш персонаж погиб."],
            0,
            footer=False
        )
        inner = len(lines[0]) - 2
        hint = self._translate_text("E / ESC — продолжить")
        left = max(0, (inner - len(hint)) // 2)
        right = inner - len(hint) - left
        lines.insert(-1, "║" + " " * left + hint + " " * right + "║")

        self.hide_cursor()
        self.render_menu_screen(lines)

        while True:
            key = self.get_key()
            if key in ("e", "\x1b"):
                self.wait_for_all_keys_release()
                self.reset_input()
                return

    # ========================================================
    # ПОБЕДА
    # ========================================================

    def victory(self):

        self.reset_render()
        self.show_cursor()

        lines = self._menu_box(
            ["ПОБЕДА!"],
            ["Вы победили всех противников."],
            0,
            footer=False
        )
        inner = len(lines[0]) - 2
        hint = self._translate_text("E / ESC — продолжить")
        left = max(0, (inner - len(hint)) // 2)
        right = inner - len(hint) - left
        lines.insert(-1, "║" + " " * left + hint + " " * right + "║")

        self.hide_cursor()
        self.render_menu_screen(lines)

        while True:
            key = self.get_key()
            if key in ("e", "\x1b"):
                self.wait_for_all_keys_release()
                self.reset_input()
                return

    # ========================================================
    # ПАУЗА
    # ========================================================

    def pause_menu(self):
        selected = 0
        options = [
            "Продолжить игру",
            "Сохранить игру",
            "Загрузить игру",
            "Настройки",
            "Выйти в главное меню"
        ]

        # ESC, открывший паузу, не должен одновременно считаться
        # нажатием внутри самой паузы.
        self.wait_for_all_keys_release()
        self.reset_input()
        self.flush_console_input()

        previous = {
            "w": False,
            "a": False,
            "s": False,
            "d": False,
            "e": False,
            "esc": False
        }

        while True:
            overlay = self._menu_box(
                ["ПАУЗА"],
                options,
                selected,
                footer=False
            )
            self.draw_game(overlay=overlay)

            current = {
                "w": self.is_pressed("w"),
                "a": self.is_pressed("a"),
                "s": self.is_pressed("s"),
                "d": self.is_pressed("d"),
                "e": self.is_pressed("e"),
                "esc": self.is_pressed("\x1b")
            }

            if self.mouse_enabled():
                hovered = self._mouse_menu_option(options, overlay, overlay=True)
                if hovered is not None and hovered != selected:
                    selected = hovered
                    self.sound.move()
                    overlay = self._menu_box(
                        ["ПАУЗА"],
                        options,
                        selected,
                        footer=False
                    )
                    self.draw_game(overlay=overlay)

            if self.mouse_enabled() and self.mouse_click():
                clicked = self._mouse_menu_option(options, overlay, overlay=True)
                if clicked is not None:
                    selected = clicked
                    self.sound.select()
                    self.wait_for_all_keys_release()
                    self.reset_input()
                    self.flush_console_input()

                    if selected == 0:
                        self.reset_render()
                        return "continue"
                    elif selected == 1:
                        self.save_slots_menu("save", overlay=True)
                    elif selected == 2:
                        loaded = self.save_slots_menu("load", overlay=True)
                        if loaded:
                            return "continue"
                    elif selected == 3:
                        self.settings_menu(overlay=True)
                    elif selected == 4:
                        self.reset_render()
                        return "menu"

                    self.wait_for_all_keys_release()
                    self.reset_input()
                    self.flush_console_input()
                    previous = {k: False for k in previous}
                    continue

            if (
                (current["w"] and not previous["w"])
                or
                (current["a"] and not previous["a"])
            ):
                selected = (selected - 1) % len(options)
                self.sound.move()

            elif (
                (current["s"] and not previous["s"])
                or
                (current["d"] and not previous["d"])
            ):
                selected = (selected + 1) % len(options)
                self.sound.move()

            elif current["esc"] and not previous["esc"]:
                self.sound.back()
                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                self.reset_render()
                return "continue"

            elif current["e"] and not previous["e"]:
                if selected in (0, 4):
                    self.sound.back()
                else:
                    self.sound.select()

                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()

                if selected == 0:
                    self.reset_render()
                    return "continue"

                elif selected == 1:
                    self.save_slots_menu("save", overlay=True)

                elif selected == 2:
                    loaded = self.save_slots_menu("load", overlay=True)
                    if loaded:
                        return "continue"

                elif selected == 3:
                    self.settings_menu(overlay=True)

                elif selected == 4:
                    self.reset_render()
                    return "menu"

                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                previous = {k: False for k in previous}
                continue

            previous = current
            time.sleep(0.01)

    # ========================================================
    # ОСНОВНОЙ ИГРОВОЙ ЦИКЛ
    # ========================================================

    def run(self):

        self.reset_input()
        self.inventory_mode = False
        self.inventory_selected = 0

        self.wait_for_all_keys_release()
        self.reset_mouse()

        last_movement = time.monotonic()
        previous_tab = False
        inventory_previous = {
            "w": False,
            "a": False,
            "s": False,
            "d": False,
            "esc": False
        }

        while True:

            # ------------------------------------------------
            # СМЕРТЬ
            # ------------------------------------------------

            if self.player.hp <= 0:
                self.game_over()
                return

            # ------------------------------------------------
            # ПОБЕДА
            # ------------------------------------------------

            if not self.enemies:
                self.victory()
                return

            # ------------------------------------------------
            # ОТРИСОВКА
            # ------------------------------------------------

            self.draw_game()

            current_time = time.monotonic()
            current_tab = self.is_pressed("\t")

            # ------------------------------------------------
            # TAB — ПЕРЕКЛЮЧЕНИЕ РЕЖИМА ИНВЕНТАРЯ
            # ------------------------------------------------

            if current_tab and not previous_tab:
                self.wait_for_all_keys_release()
                self.reset_input()
                self.flush_console_input()
                self._consume_mouse_wheel()

                self.inventory_mode = not self.inventory_mode
                self.inventory_key_repeat = {
                    "key": None,
                    "started_at": 0.0,
                    "last_move": 0.0
                }

                if self.inventory_mode:
                    self.inventory_selected = 0
                    inventory_previous = {k: False for k in inventory_previous}
                else:
                    inventory_previous = {k: False for k in inventory_previous}
                    last_movement = time.monotonic()

                previous_tab = False
                continue

            previous_tab = current_tab

            # ------------------------------------------------
            # РЕЖИМ ИНВЕНТАРЯ
            # ------------------------------------------------

            if self.inventory_mode:
                current_inventory = {
                    "w": self.is_pressed("w"),
                    "a": self.is_pressed("a"),
                    "s": self.is_pressed("s"),
                    "d": self.is_pressed("d"),
                    "esc": self.is_pressed("\x1b")
                }

                # ESC закрывает инвентарь.
                if current_inventory["esc"] and not inventory_previous["esc"]:
                    self.sound.back()
                    self.wait_for_all_keys_release()
                    self.reset_input()
                    self.inventory_mode = False
                    self.inventory_key_repeat = {
                        "key": None,
                        "started_at": 0.0,
                        "last_move": 0.0
                    }
                    self._consume_mouse_wheel()
                    inventory_previous = {k: False for k in inventory_previous}
                    last_movement = time.monotonic()
                    continue

                # В режиме «Клавиатура+Мышь» колесо мыши листает слоты
                # только по горизонтали. В обычной «Клавиатуре» колесо
                # полностью игнорируется.
                if self.mouse_enabled():
                    wheel_delta = self._consume_mouse_wheel()
                    if wheel_delta:
                        steps = max(1, abs(wheel_delta) // 120)
                        direction = -1 if wheel_delta > 0 else 1
                        for _ in range(steps):
                            row = self.inventory_selected // 20
                            col = self.inventory_selected % 20
                            old_col = col
                            col = max(0, col - 1) if direction < 0 else min(19, col + 1)
                            if col != old_col:
                                self.inventory_selected = row * 20 + col
                                self.sound.move()

                # WASD работают в обеих схемах управления.
                # При первом нажатии перемещение происходит сразу,
                # затем при удержании включается ускоренный автоповтор.
                pressed_keys = [
                    key for key in ("w", "a", "s", "d")
                    if current_inventory[key]
                ]

                active_key = None
                for key in ("w", "a", "s", "d"):
                    if current_inventory[key]:
                        active_key = key
                        break

                if active_key is None:
                    self.inventory_key_repeat = {
                        "key": None,
                        "started_at": 0.0,
                        "last_move": 0.0
                    }
                else:
                    is_new_press = not inventory_previous[active_key]

                    if is_new_press or self.inventory_key_repeat["key"] != active_key:
                        self.inventory_key_repeat = {
                            "key": active_key,
                            "started_at": current_time,
                            "last_move": current_time
                        }
                        should_move = True
                    else:
                        held_time = current_time - self.inventory_key_repeat["started_at"]
                        repeat_delay = 0.35
                        repeat_interval = 0.07 if held_time >= repeat_delay else 0.22
                        should_move = (
                            current_time - self.inventory_key_repeat["last_move"]
                            >= repeat_interval
                        )

                    if should_move:
                        row = self.inventory_selected // 20
                        col = self.inventory_selected % 20

                        old_col = col
                        if active_key == "a":
                            col = max(0, col - 1)
                        elif active_key == "d":
                            col = min(19, col + 1)
                        elif active_key == "w":
                            row = (row - 1) % 2
                        elif active_key == "s":
                            row = (row + 1) % 2

                        if col != old_col or active_key in ("w", "s"):
                            self.inventory_selected = row * 20 + col
                            self.sound.move()
                        self.inventory_key_repeat["last_move"] = current_time

                inventory_previous = current_inventory
                time.sleep(0.01)
                continue

            # ------------------------------------------------
            # ESC — ПАУЗА
            # ------------------------------------------------

            if self.is_pressed("\x1b"):
                self.sound.back()
                pause_result = self.pause_menu()

                if pause_result == "menu":
                    return

                last_movement = time.monotonic()
                continue

            # ------------------------------------------------
            # ДВИЖЕНИЕ
            # ------------------------------------------------

            if current_time - last_movement >= MOVEMENT_INTERVAL:
                dx, dy = self.get_movement()

                if dx != 0 or dy != 0:
                    self.move_player(dx, dy)
                    last_movement = current_time

            # ------------------------------------------------
            # E — ВЗАИМОДЕЙСТВИЕ
            # ------------------------------------------------

            action = self.get_action()

            if action == "e":
                self.interact()
                self.wait_for_all_keys_release()
                self.reset_input()
                last_movement = time.monotonic()

            time.sleep(0.01)


# ============================================================
# НАСТРОЙКА WINDOWS TERMINAL ДЛЯ ИГРЫ
# ============================================================

def get_windows_terminal_fragment_paths():
    """Возвращает возможные пользовательские каталоги JSON-фрагментов WT."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return []

    return [
        os.path.join(
            local_app_data,
            "Microsoft",
            "Windows Terminal",
            "Fragments",
            WT_FRAGMENT_APP_NAME,
            WT_FRAGMENT_FILE_NAME
        ),
        os.path.join(
            local_app_data,
            "Packages",
            "Microsoft.WindowsTerminal_8wekyb3d8bbwe",
            "LocalState",
            "Fragments",
            WT_FRAGMENT_APP_NAME,
            WT_FRAGMENT_FILE_NAME
        )
    ]


def install_windows_terminal_game_profile():
    """
    Создаёт временный профиль Windows Terminal только для игры.

    padding=0 убирает внутренние поля Terminal, а scrollbarState=hidden
    убирает полосу прокрутки. Это устраняет физические пустые области
    справа/снизу, которые невозможно заполнить символами Python.
    """
    paths = get_windows_terminal_fragment_paths()
    if not paths:
        return []

    namespace = uuid.UUID("f65ddb7e-706b-4499-8a50-40313caf510a")
    app_namespace = uuid.uuid5(
        namespace,
        WT_FRAGMENT_APP_NAME.encode("utf-16le").decode("ascii")
    )
    profile_guid = uuid.uuid5(
        app_namespace,
        WT_PROFILE_NAME.encode("utf-16le").decode("ascii")
    )

    fragment = {
        "$schema": "https://aka.ms/terminal-profiles-schema",
        "profiles": [
            {
                "name": WT_PROFILE_NAME,
                "guid": "{" + str(profile_guid) + "}",
                "commandline": "cmd.exe",
                "padding": 0,
                "scrollbarState": "hidden",
                "suppressApplicationTitle": True
            }
        ]
    }

    created = []

    # Используем только существующий вариант расположения WT. Если каталог
    # отсутствует, пробуем создать первый пользовательский вариант.
    for path in paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                json.dump(fragment, file, ensure_ascii=False, indent=2)
            created.append(path)
        except (OSError, PermissionError):
            continue

    return created


def remove_windows_terminal_game_profile(paths):
    """Удаляет временные фрагменты после завершения игры."""
    for path in paths or []:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


# ============================================================
# ЗАПУСК
# ============================================================

def run_game():

    game = Game()

    game.setup_console()

    try:
        game.main_menu()
    finally:
        # Настройки сохраняются при любом штатном завершении игрового цикла,
        # а также при возникновении исключения после создания объекта Game.
        game.save_user_settings()


# ============================================================
# ТОЧКА ВХОДА
# ============================================================

if __name__ == "__main__":

    if os.name == "nt" and os.environ.get("GAME_CONSOLE") != "1":

        env = os.environ.copy()
        env["GAME_CONSOLE"] = "1"

        game_path = os.path.abspath(__file__)

        # Windows Terminal имеет официальный режим --fullscreen,
        # который соответствует F11/fullscreen.
        wt_command = (
            shutil.which("wt.exe")
            or
            shutil.which("wt")
        )

        if wt_command:
            fragment_paths = install_windows_terminal_game_profile()

            try:
                subprocess.Popen(
                    [
                        wt_command,
                        "--window",
                        "new",
                        "--fullscreen",
                        "new-tab",
                        "--profile",
                        WT_PROFILE_NAME,
                        "--title",
                        GAME_TITLE,
                        "--suppressApplicationTitle",
                        sys.executable,
                        game_path
                    ],
                    env=env
                )
            except Exception:
                # Если запуск через специальный профиль не удался,
                # пробуем штатный Windows Terminal без него.
                remove_windows_terminal_game_profile(fragment_paths)
                subprocess.Popen(
                    [
                        wt_command,
                        "--fullscreen",
                        "new-tab",
                        "--title",
                        GAME_TITLE,
                        "--suppressApplicationTitle",
                        sys.executable,
                        game_path
                    ],
                    env=env
                )
        else:
            # Fallback для систем, где Windows Terminal недоступен.
            subprocess.Popen(
                [
                    sys.executable,
                    game_path
                ],
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

        sys.exit()

    try:

        run_game()

    except KeyboardInterrupt:

        pass

    except Exception as error:

        # Не даём консоли мгновенно закрыться,
        # чтобы при ошибке был виден traceback.

        Game.show_cursor()

        print()
        print("=" * 60)
        print("ОШИБКА ИГРЫ")
        print("=" * 60)
        print()
        print(
            f"{type(error).__name__}: {error}"
        )
        print()
        print(
            "Нажмите любую клавишу для выхода..."
        )

        try:

            msvcrt.getwch()

        except Exception:

            input()

    finally:

        Game.show_cursor()

        try:
            game._stop_mouse_wheel_hook()
        except Exception:
            pass

        # Удаляем временный профиль WT после завершения игры.
        # Профиль уже загружен активным окном и продолжает действовать
        # до его закрытия.
        try:
            remove_windows_terminal_game_profile(
                get_windows_terminal_fragment_paths()
            )
        except Exception:
            pass

        # Возвращаем обычный экран консоли после завершения игры.
        sys.stdout.write("\033[?1049l")
        sys.stdout.flush()