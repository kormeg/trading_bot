import os
import sys
import subprocess
import importlib.util
from importlib.metadata import version as get_version
from ctypes import windll

# Список необходимых библиотек
required_modules = {"pybit" : "5.7.0", 
                    "pandas" : "2.0.2", 
                    "numpy" : "1.24.3", 
                    "IPython" : "8.8.0", 
                    "matplotlib" : "3.6.3",  
                    "ta" : "0.10.2"}

# проверка наличия и установка библиотек
for module, version in required_modules.items():
    if importlib.util.find_spec(module) is not None:
        vers = get_version(module)
        if vers != version:
            print(f"Модуль {module} присутствует в системе")
            print("Установлена неподходящая версия")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "--upgrade", f"{module}=={version}"
                ])
                print(f"Необходимая версия {module} успешно установлена")
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при установке {module}: {e}")
                print(f"Критическая ошибка: не удалось установить {module}")
        else:
            print(f"Модуль {module} уже установлен")
    else:
        try:
            print(f"Модуль {module} не найден, устанавливается...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--upgrade", f"{module}=={version}"
            ])
            print(f"Необходимая версия {module} успешно установлена")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при установке {module}: {e}")
            print(f"Критическая ошибка: не удалось установить {module}")
            sys.exit(1)
print("Все пакеты готовы к использованию!")

try:
    # Метод 1: современный (Windows 10 1607+)
    windll.user32.SetProcessDpiAwarenessContext(0)  # DPI_AWARENESS_CONTEXT_UNAWARE
    print("SetProcessDpiAwarenessContext(0) succeeded")
except AttributeError:
    print("SetProcessDpiAwarenessContext not available")

try:
    # Метод 2: старый (Windows 8.1+)
    windll.shcore.SetProcessDpiAwareness(0)  # PROCESS_DPI_UNAWARE
    print("SetProcessDpiAwareness(0) succeeded")
except AttributeError:
    print("SetProcessDpiAwareness not available")

try:
    # Метод 3: самый старый (Windows Vista+)
    windll.user32.SetProcessDPIAware()
    print("SetProcessDPIAware succeeded")
except AttributeError:
    print("SetProcessDPIAware not available")

import bot

# # синхронизация времени
os.system('w32tm /resync')

if __name__ == "__main__":
    new_bot = bot.Bot()

