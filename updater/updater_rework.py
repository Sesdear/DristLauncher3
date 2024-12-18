import sys
import os
import shutil
import zipfile
import requests
import json
from PyQt6 import QtWidgets, QtCore
from updater_ui import Ui_MainWindow

class Downloader(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)

    def run(self):
        self.download_launcher()

    def download_launcher(self):
        launcher_dir = 'launcher'
        os.makedirs(launcher_dir, exist_ok=True)
        repo_url = 'https://codeload.github.com/Sesdear/Drist_Sources/zip/refs/heads/main'
        destination_zip = os.path.join(launcher_dir, 'main.zip')

        try:
            response = requests.get(repo_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(destination_zip, 'wb') as f:
                for data in response.iter_content(chunk_size=1024):
                    f.write(data)
                    downloaded_size += len(data)
                    if total_size > 0:
                        progress = int(downloaded_size / total_size * 100)
                        self.progress.emit(progress)

            with zipfile.ZipFile(destination_zip, 'r') as zip_ref:
                zip_ref.extractall(launcher_dir)

            source_folder = os.path.join(launcher_dir, 'Drist_Sources-main')
            if os.path.exists(source_folder):
                for filename in os.listdir(source_folder):
                    shutil.move(os.path.join(source_folder, filename), os.path.join(launcher_dir, filename))

            os.remove(destination_zip)
            shutil.rmtree(source_folder)

            launch_executable = os.path.join(launcher_dir, 'launch.exe')
            if os.path.exists(launch_executable):
                os.startfile(launch_executable)

            QtCore.QCoreApplication.instance().quit()  # Close updater

        except Exception as e:
            print(f"Error during download: {e}")



class App(QtWidgets.QMainWindow):  # Change QWidget to QMainWindow
    def __init__(self):
        super().__init__()  # Calls the constructor of QMainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.downloader = Downloader()
        self.downloader.progress.connect(self.update_progress)

    def update_progress(self, value):
        self.ui.progressBar.setValue(value)

    def start_download(self):
        self.downloader.start()

    def check_and_update_version(self):
        launcher_dir = 'launcher'

        if not os.path.exists("lv.json"):
            with open("lv.json", 'w') as f:
                json.dump({"version": None}, f)

        url = "https://raw.githubusercontent.com/Sesdear/Drist_Sources/manifests/launcher_version.json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            launcher_version = data.get("version")

            with open("lv.json", 'r') as f:
                local_version_data = json.load(f)

            if launcher_version != local_version_data["version"]:
                # Update lv.json with the new version
                local_version_data["version"] = launcher_version
                with open("lv.json", 'w') as f:
                    json.dump(local_version_data, f)

                # If versions differ, start the download process
                self.start_download()
            else:
                # If versions are the same, launch the executable
                launch_executable = os.path.join(launcher_dir, 'launch.exe')
                if os.path.exists(launch_executable):
                    os.startfile(launch_executable)
                self.close()  # Close the updater window here

    def closeEvent(self, event):
        self.downloader.quit()
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()

    # Check version before starting download
    window.check_and_update_version()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
