import os
import sys
import subprocess
import importlib.util
# from importlib.metadata import version as get_version

# Список необходимых библиотек
required_modules = {"pybit" : "5.7.0", 
                    "pandas" : "2.0.2", 
                    "numpy" : "1.24.3", 
                    "IPython" : "8.8.0", 
                    "matplotlib" : "3.6.3",  
                    "ta" : "0.10.2"}

# проверка наличия и установка библиотек
for module, version in required_modules.items():
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", f"{module}=={version}"
        ])
    except subprocess.CalledProcessError as e:
        print(f"✗ Ошибка при установке {module}: {e}")
        print(f"Критическая ошибка: не удалось установить {module}")
        sys.exit(1)
        
import bot


# # синхронизация времени
os.system('w32tm /resync')

if __name__ == "__main__":
    new_bot = bot.Bot()

