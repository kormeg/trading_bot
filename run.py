import os
import sys
import subprocess
import importlib.util

# Список необходимых библиотек
required_modules = ["pybit", "pandas", "numpy", "IPython", "matplotlib", "pprint"]

# проверка наличия и установка библиотек
for module in required_modules:
    if importlib.util.find_spec(module) is not None:
        print(f"✓ Модуль {module} уже установлен")
    else:
        print(f"Модуль {module} не найден, устанавливается...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", module
            ])
            print(f"✓ Пакет {module} успешно установлен")
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка при установке {module}: {e}")
            print(f"Критическая ошибка: не удалось установить {module}")
            sys.exit(1)
print("Все пакеты готовы к использованию!")

import bot


# # синхронизация времени
os.system('w32tm /resync')

if __name__ == "__main__":
    new_bot = bot.Bot()

