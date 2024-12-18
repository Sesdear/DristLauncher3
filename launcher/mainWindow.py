import json
import os
import re
import subprocess
from os.path import split
from time import sleep
from urllib.parse import urlparse

import minecraft_launcher_lib
import psutil
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QFrame, QMessageBox, QProgressDialog
from PyQt6 import uic, QtCore

from settingsWindow import SettingsWindow
import files_updater
import mods_updater
import minecraft_launch


# Поток для обновления файлов
class FilesUpdateThread(QThread):
    progress_max = pyqtSignal(int)
    progress = pyqtSignal(int)
    text = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        try:
            self.text.emit("Начало обновления модов...")
            # Передаем update_progress как callback в mods_updater.automaticUpdateMods
            files_updater.automaticUpdateFiles(self.update_progress)
            self.text.emit("Обновление модов завершено.")
        except Exception as e:
            self.text.emit(f"Ошибка: {e}")

    def update_progress(self, current, total, downloaded_size=0, total_size=0):
        percent_complete = (downloaded_size / total_size) * 100 if total_size > 0 else 0
        self.progress.emit(int(percent_complete))
        self.progress_max.emit(total)
        self.text.emit(f"Файлы: {current}/{total} ({percent_complete:.2f}% выполнено)")


# Поток для обновления модов
class ModsUpdateThread(QThread):
    progress_max = pyqtSignal(int)
    progress = pyqtSignal(int)
    text = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        try:
            self.text.emit("Начало обновления модов...")
            # Передаем update_progress как callback в mods_updater.automaticUpdateMods
            mods_updater.automaticUpdateMods(self.update_progress)
            self.text.emit("Обновление модов завершено.")
        except Exception as e:
            self.text.emit(f"Ошибка: {e}")

    def update_progress(self, current, total, downloaded_size, total_size):
        percent_complete = (downloaded_size / total_size) * 100 if total_size > 0 else 0
        self.progress.emit(int(percent_complete))
        self.progress_max.emit(total)
        self.text.emit(f"Моды: {current}/{total} ({percent_complete:.2f}% выполнено)")


class MinecraftLaunchThread(QThread):
    progress_max = pyqtSignal(int)
    progress = pyqtSignal(int)
    text = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            self.text.emit(f"Запуск...")
            print(f"Запуск Minecraft")
            minecraft_launch.start_minecraft()
            self.text.emit("Minecraft запущен успешно.")
            print("Minecraft запущен успешно")
        except Exception as e:
            self.text.emit(f"Ошибка при запуске Minecraft: {e}")
            print(f"Ошибка при запуске Minecraft: {e}")

# Поток для установки Minecraft Forge
class InstallThread(QThread):
    progress_max = pyqtSignal(int)
    progress = pyqtSignal(int)
    text = pyqtSignal(str)

    def __init__(self) -> None:
        QThread.__init__(self)
        self._callback_dict = {
            "setStatus": lambda text: self.text.emit(text),
            "setMax": lambda max_progress: self.progress_max.emit(max_progress),
            "setProgress": lambda progress: self.progress.emit(progress),
        }

    def run(self) -> None:
        try:
            with open('configs/manifests/minecraft_manifest.json', 'r') as f:
                versions = json.load(f)
            minecraft_version = versions.get("minecraft-version")
            modloader_version = versions.get("modloader-version")

            if minecraft_version and modloader_version:
                self.text.emit("Начало установки Forge...")
                minecraft_launcher_lib.forge.install_forge_version(
                    f"{minecraft_version}-{modloader_version}", 'minecraft/', callback=self._callback_dict)
                self.text.emit("Установка завершена.")
                MainWindow.check_if_updates_finished()
            else:
                self.text.emit("Неверные версии в манифесте.")
        except Exception as e:
            self.text.emit(f"Ошибка: {e}")






class MainWindow(QFrame):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("DL3.ui", self)
        self.show()
        self.settingswin = None


        # Создаем потоки
        self._install_thread = InstallThread()
        self._files_update_thread = FilesUpdateThread()
        self._mods_update_thread = ModsUpdateThread()
        self._minecraft_launch_thread = MinecraftLaunchThread()

        # Подключаем прогресс-бар к потокам
        self.ui.progressBar.setTextVisible(True)

        self._install_thread.progress_max.connect(self.ui.progressBar.setMaximum)
        self._install_thread.progress.connect(self.ui.progressBar.setValue)
        self._install_thread.text.connect(self.ui.progressBar.setFormat)

        self._files_update_thread.progress_max.connect(self.ui.progressBar.setMaximum)
        self._files_update_thread.progress.connect(self.ui.progressBar.setValue)
        self._files_update_thread.text.connect(self.ui.progressBar.setFormat)

        self._mods_update_thread.progress_max.connect(self.ui.progressBar.setMaximum)
        self._mods_update_thread.progress.connect(self.ui.progressBar.setValue)
        self._mods_update_thread.text.connect(self.ui.progressBar.setFormat)

        self._minecraft_launch_thread.progress_max.connect(self.ui.progressBar.setMaximum)
        self._minecraft_launch_thread.progress.connect(self.ui.progressBar.setValue)
        self._minecraft_launch_thread.text.connect(self.ui.progressBar.setFormat)

        ################################
        ### Инициализация кнопок
        self.ui.settingsButton.clicked.connect(self.openSettings)  # Настройки
        self.ui.openFolderButton.clicked.connect(self.openFolder)  # Открытие папки текущей директории
        self.ui.startButton.clicked.connect(self.start_button)
        self.ui.stopButton.clicked.connect(self.stop_minecraft)
        with open('configs/client_config.json') as f:
            self.client_config = json.load(f)

        self.ui.nicknameLine.setText(self.client_config["User-info"][0]["username"])

        # Переменные для отслеживания завершения потоков
        self.mods_update_finished = False
        self.files_update_finished = False
        self.java_install = False
        self.set_java_default_path()

    def set_java_default_path(self):
        try:
            print(1)
            url = "https://raw.githubusercontent.com/Sesdear/Drist_Sources/manifests/java_info.json"
            response = requests.get(url)
            print(2)

            if response.status_code == 200:
                print("response 200")
                print(f"Response content: {response.text}")  # Print the raw response text

                try:
                    data = response.json()  # Attempt to parse JSON
                    print("Parsed data:", data)  # Print parsed JSON
                except json.JSONDecodeError as e:
                    raise Exception(f"JSON Decode Error: {e}\nResponse content was: {response.text}")

                java_path = f'C:\\Program Files\\Java\\jdk-{data.get("jdk_ver")}\\bin\\java.exe'
                self.client_config["java_path"] = java_path
                print(java_path)

                # Save the client config
                with open('configs/client_config.json', 'w') as f:
                    json.dump(self.client_config, f, indent=4)

            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить данные с GitHub.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Произошла ошибка: {e}")

    def set_start_button_enabled(self, enabled):
        self.ui.startButton.setEnabled(enabled)

    def stop_minecraft(self):
        for proc in psutil.process_iter():
            if proc.name() == 'java.exe':
                proc.terminate()

    def start_button(self):
        try:
            # Деактивируем кнопку
            self.set_start_button_enabled(False)
            # Проверка флажка обновления клиента
            if self.ui.updateClientCheckBox.isChecked():
                # Начинаем полную переустановку Minecraft
                print("Обновление клиента выбрано, начинаем полную переустановку Minecraft")

                self._install_thread.finished.connect(self.start_updates)
                self._install_thread.start()
            else:
                # Запускаем обновление файлов и модов
                print("Запускаем обновление файлов и модов")
                self.mods_update_finished = False
                self.files_update_finished = False

                self._mods_update_thread.finished.connect(self.on_mods_update_finished)
                self._files_update_thread.finished.connect(self.on_files_update_finished)

                self._mods_update_thread.start()
                self._files_update_thread.start()

        except Exception as e:
            print(e)
            # В случае ошибки активируем кнопку
            self.set_start_button_enabled(True)

    def start_updates(self):
        # Запускаем обновление файлов и модов
        print("Запускаем обновление файлов и модов")
        self.mods_update_finished = False
        self.files_update_finished = False

        self._mods_update_thread.finished.connect(self.on_mods_update_finished)
        self._files_update_thread.finished.connect(self.on_files_update_finished)

        self._mods_update_thread.start()
        self._files_update_thread.start()

    def on_mods_update_finished(self):
        print("Обновление модов завершено")
        self.mods_update_finished = True
        self.check_if_updates_finished()

    def download_java_installer(self):
        try:
            # URL к JSON-файлу с ссылкой на скачивание JDK
            url = "https://raw.githubusercontent.com/Sesdear/Drist_Sources/manifests/java_info.json"

            # Запрашиваем JSON с GitHub
            response = requests.get(url)
            if response.status_code == 200:
                # Разбираем JSON
                data = response.json()

                # Извлекаем ссылку на скачивание JDK
                jdk_url = data.get("jdk_url")
                if jdk_url:
                    # Определяем имя файла из URL
                    file_name = os.path.basename(jdk_url)
                    save_path = os.path.join(os.getcwd(), file_name)

                    # Скачиваем файл с прогрессом
                    self._download_file_with_progress(jdk_url, save_path)

                    # Запускаем загруженный файл
                    if os.path.exists(save_path):
                        os.startfile(save_path)
                    else:
                        QMessageBox.warning(self, "Ошибка", "Не удалось сохранить загруженный файл.")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось найти ссылку на скачивание JDK.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить данные с GitHub.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Произошла ошибка: {e}")

    def _download_file_with_progress(self, url: str, local_filename: str):
        try:
            # Запрашиваем файл с потоковой передачей данных
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            # Создаем окно прогресса
            progress = QProgressDialog("Скачивание файла...", "Отмена", 0, total_size, self)
            progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setAutoClose(True)
            progress.setValue(0)

            progress.setWindowTitle("Settings")

            # Скачивание файла с отображением прогресса
            with open(local_filename, 'wb') as f:
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.setLabelText(f"Загружено {downloaded_size // (1024 * 1024)} MB / {total_size // (1024 * 1024)} MB")
                        downloaded_size += len(chunk)
                        progress.setValue(downloaded_size)
                        if progress.wasCanceled():
                            QMessageBox.warning(self, "Отмена", "Загрузка была отменена.")
                            break

            if downloaded_size == total_size:
                progress.setValue(total_size)
                QMessageBox.information(self, "Скачивание завершено", "После установки запустите заново")
                self.java_install = True
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось скачать файл: {e}")

    def on_files_update_finished(self):
        print("Обновление файлов завершено")
        self.files_update_finished = True
        self.check_if_updates_finished()

    def check_if_updates_finished(self):
        print(self.mods_update_finished, self.files_update_finished)
        if self.mods_update_finished and self.files_update_finished:
            print("Все обновления завершены")

            # Когда оба потока завершены, проверяем установку Minecraft
            if minecraft_launcher_lib.utils.is_minecraft_installed('minecraft'):
                print("Minecraft установлен, запускаем его...")
                self.start_minecraft()
            else:
                self._install_thread.finished.connect(self.start_updates)
                self._install_thread.start()


    def start_minecraft(self):
        nickname = self.ui.nicknameLine.text()

        # Проверка никнейма
        if not self.check_username_valid(nickname):
            self.error_window("Ошибка", "Некоректное имя пользователя.")
            self.set_start_button_enabled(True)
            return

        if not os.path.exists(self.client_config["java_path"]):
            print("!!!java не скачана!!!")
            self.download_java_installer()

        print(f"Полученный никнейм: {nickname}")

        # Сохраняем никнейм в конфиг
        self.client_config["User-info"][0]["username"] = nickname
        with open('configs/client_config.json', 'w') as js_set:
            json.dump(self.client_config, js_set, indent=4)
        print("Никнейм сохранен")

        # Запускаем Minecraft только если никнейм корректен и моды/файлы обновлены
        self.set_start_button_enabled(True)
        self.mods_update_finished = False
        self.files_update_finished = False
        print("Проверка Java")
        if os.path.exists(self.client_config["java_path"]):
            print("Инициализируем поток MinecraftLaunchThread")
            self._minecraft_launch_thread.start()
            print("Поток Minecraft запущен")



    def error_window(self, window_name, error_text):
        QMessageBox.warning(self, window_name, error_text)
        self.set_start_button_enabled(True)
        return

    def check_username_valid(self, username: str) -> bool:
        # Проверка, что имя пользователя не пустое
        if not username:
            return False

        # Проверка длины имени пользователя (например, от 3 до 16 символов)
        if len(username) < 3 or len(username) > 16:
            return False

        # Проверка на допустимые символы (разрешены буквы и цифры)
        if not re.match("^[A-Za-z0-9_]+$", username):
            return False

        return True


    ####################################
    ### Второстепенные кнопки
    def openSettings(self):
        self.settingswin = None
        if self.settingswin is None:
            self.settingswin = SettingsWindow()
            self.settingswin.show()

    def openFolder(self):
        current_directory = os.getcwd()
        subprocess.Popen(r'explorer "{}"'.format(current_directory))
