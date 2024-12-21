import json
import os
import sys

import requests

from PyQt6.QtWidgets import QApplication, QFrame, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QPushButton, \
    QComboBox, QProgressDialog
from PyQt6 import uic, QtCore


class JavaSelectionDialog(QDialog):
    def __init__(self, java_versions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор версии Java")
        self.setMinimumWidth(300)

        # Создаем выпадающий список
        self.combo_box = QComboBox(self)
        self.combo_box.addItems(java_versions)

        # Кнопка подтверждения выбора
        self.select_button = QPushButton("Выбрать", self)
        self.select_button.clicked.connect(self.select_java_version)

        # Устанавливаем макет
        layout = QVBoxLayout(self)
        layout.addWidget(self.combo_box)
        layout.addWidget(self.select_button)

        self.selected_version = None

    def select_java_version(self):
        # Сохраняем выбранную версию
        self.selected_version = self.combo_box.currentText()
        self.accept()  # Закрываем диалог с результатом


class SettingsWindow(QFrame):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("settings.ui", self)
        self.show()

        self.ui.saveSettingsButton.clicked.connect(self.save)
        self.ui.browseButton.clicked.connect(self.path_browse_button_clicked)
        self.ui.findJavaButton.clicked.connect(self.find_java)
        self.ui.downloadJavaButton.clicked.connect(self.download_java_installer)

        # Загрузка настроек из конфигурационного файла
        with open('configs/client_config.json', 'r') as f:
            self.settings_options = json.load(f)

        with open('.sl_password', 'r') as f:
            self.sl_password = f.read()
        with open('configs/mirror.json', 'r') as f:
            self.mirror_config = json.load(f)

        self.ui.javaPathLine.setText(self.settings_options["java_path"])
        ram_entry = int(self.settings_options["Xmx"] / 1024)
        self.ui.ramSpinBox.setValue(ram_entry)
        self.ui.slPasswordLine.setText(self.sl_password)
        self.populate_mirror_combobox()
        current_mirror = self.mirror_config.get("mirror", "default")  # Handle case where "mirror" is missing
        index = self.ui.mirrorComboBox.findText(current_mirror)
        if index != -1:
            self.ui.mirrorComboBox.setCurrentIndex(index)

    def find_java(self):
        # Возможные пути для поиска Java
        java_directories = [
            "C:\\Program Files\\Java",
            "C:\\Program Files (x86)\\Java"
        ]

        # Список найденных Java версий
        found_java_paths = []

        # Поиск исполняемых файлов java.exe в указанных директориях
        for directory in java_directories:
            if os.path.exists(directory):
                for folder in os.listdir(directory):
                    java_executable = os.path.join(directory, folder, 'bin', 'java.exe')
                    if os.path.exists(java_executable):
                        found_java_paths.append(os.path.join(directory, folder))

        # Если Java версии найдены, отображаем диалоговое окно выбора
        if found_java_paths:
            dialog = JavaSelectionDialog(found_java_paths, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_java = dialog.selected_version
                # Записываем выбранный путь в поле javaPathLine
                self.ui.javaPathLine.setText(os.path.join(selected_java, 'bin', 'java.exe'))
            else:
                QMessageBox.warning(self, "Ошибка", "Версия Java не была выбрана.")
        else:
            QMessageBox.warning(self, "Ошибка", "Java не найдена в стандартных директориях.")

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
                QMessageBox.information(self, "Скачивание завершено", "Java была успешно скачана.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось скачать файл: {e}")

    def save(self):
        ram = self.ui.ramSpinBox.value()
        sl_password = self.ui.slPasswordLine.text()
        java_path = self.ui.javaPathLine.text()
        mirror = self.ui.mirrorComboBox.currentText()

        # Сохраняем изменения в конфигурационный файл
        finally_ram = ram * 1024
        self.settings_options["Xmx"] = finally_ram
        self.settings_options["java_path"] = java_path
        self.mirror_config["mirror"] = mirror

        with open('configs/mirror.json', 'w') as f:
            json.dump(self.mirror_config, f, indent=4)

        with open('.sl_password', 'w') as f:
            f.write(sl_password)

        with open('configs/client_config.json', 'w') as f:
            json.dump(self.settings_options, f, indent=4)
        QMessageBox.information(self, "Setting Message", "Сохранение прошло успешно!", )

    def populate_mirror_combobox(self):
        try:
            response = requests.get("https://raw.githubusercontent.com/Sesdear/Drist_Sources/manifests/launcher_ip.json")
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            self.ui.mirrorComboBox.addItems(data.keys())  # Add keys as items to the combobox
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки данных с GitHub: {e}")
            print(f"Ошибка загрузки данных с GitHub: {e}")
        except json.JSONDecodeError as e:
            print(f"Ошибка разбора JSON: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка разбора JSON: {e}")

    def path_browse_button_clicked(self) -> None:
        fileName, _ = QFileDialog.getOpenFileName(self, 'Single File', QtCore.QDir.rootPath(), '*.exe')
        self.ui.javaPathLine.setText(fileName)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())
