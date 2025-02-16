import json
import os
import shutil
import sys
import zipfile
import mainWindow

import requests
from PyQt6.QtWidgets import QApplication, QMessageBox


def check_path_for_cyrillic(path):
    """
    Проверяет путь на наличие кириллических символов.
    Если найдены, показывает окно с ошибкой.

    :param path: Строка с путем для проверки
    :return: True если путь корректен, False если найдены кириллические символы
    """
    for char in path:
        if 'А' <= char <= 'я' or char in 'ёЁ':
            show_error_message()
            return False
    return True


def show_error_message():

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("Ошибка")
    msg_box.setText("Путь к программе содержит кириллические символы!")
    msg_box.setInformativeText("Переместите программу в папку с латинскими символами.")
    msg_box.exec()


def get_current_program_path():
    """
    Возвращает абсолютный путь к текущей программе.
    """
    return os.path.abspath(__file__)

def download_icons():
    repo_url = 'https://codeload.github.com/Sesdear/Drist_Sources/zip/refs/heads/Icons'
    destination_folder_parent = '.'
    source_folder = 'assets/Drist_Sources-Icons/'
    destination_folder = 'assets'

    destination = os.path.join(destination_folder_parent, 'icons.zip')
    response = requests.get(repo_url, stream=True)
    with open(destination, 'wb') as f:
        f.write(response.content)

    extracted_folder_path = os.path.join(destination_folder_parent, 'assets')
    with zipfile.ZipFile(destination, 'r') as zip_ref:
        zip_ref.extractall(extracted_folder_path)

    for filename in os.listdir(source_folder):
        source_file_path = os.path.join(source_folder, filename)
        destination_file_path = os.path.join(destination_folder, filename)
        shutil.move(source_file_path, destination_file_path)

    try:
        print("Delete Temp Icons files status: in progress")
        folder_path = 'assets/Drist_Sources-Icons'
        file_path = destination
        os.remove(file_path)
        shutil.rmtree(folder_path)
        print("Delete Temp files status: Done")
    except Exception as e:
        print(f"Error while deleting temp files: {e}")

def download_ui():
    repo_url = 'https://codeload.github.com/Sesdear/Drist_Sources/zip/refs/heads/Ui'
    destination_folder_parent = '.'
    source_folder = 'Drist_Sources-Ui'
    destination_folder = ''

    destination = os.path.join(destination_folder_parent, 'ui.zip')
    response = requests.get(repo_url, stream=True)
    with open(destination, 'wb') as f:
        f.write(response.content)

    extracted_folder_path = os.path.join(destination_folder_parent, '.')
    with zipfile.ZipFile(destination, 'r') as zip_ref:
        zip_ref.extractall(extracted_folder_path)

    for filename in os.listdir(source_folder):
        source_file_path = os.path.join(source_folder, filename)
        destination_file_path = os.path.join(destination_folder, filename)
        shutil.move(source_file_path, destination_file_path)

    try:
        print("Delete Temp Ui files status: in progress")
        folder_path = 'Drist_Sources-Ui'
        file_path = destination
        os.remove(file_path)
        shutil.rmtree(folder_path)
        print("Delete Temp Ui files status: Done")
    except Exception as e:
        print(f"Error while deleting temp Ui files: {e}")


def create_folders():
    create_minecraft_folder = "minecraft"

    if not os.path.exists(create_minecraft_folder):
        os.makedirs(create_minecraft_folder)
        print("Folder \"minecraft\" Create")

    create_minecraftmods_folder = "minecraft/mods"

    if not os.path.exists(create_minecraftmods_folder):
        os.makedirs(create_minecraftmods_folder)
        print("Folder \"mods\" Create")
    ###############################################
    create_assets_folder = "assets"

    if not os.path.exists(create_assets_folder):
        os.makedirs(create_assets_folder)
        print("Folder \"assets\" Create")
    ###############################################
    create_configs_folder = "configs"

    if not os.path.exists(create_configs_folder):
        os.makedirs(create_configs_folder)
        print("Folder \"configs\" Create")
    ###############################################
    folder_path_manifests_create = "configs/manifests"
    if not os.path.exists(folder_path_manifests_create):
        os.makedirs(folder_path_manifests_create)
        print("Folder \"manifests\" Create")

def create_jsons():
    config_path = 'configs/'
    json_file_path_minecraft_configs = os.path.join(config_path, 'client_config.json')
    if not os.path.exists(json_file_path_minecraft_configs):
        with open(json_file_path_minecraft_configs, 'w') as f:
            json.dump({
                "debug": False,
                "slPassword": None,
                "Xms": 2048,
                "Xmx": 4096,
                "java_path": None,
                "accessToken": None,
                "clientToken": None,
                "User-info": [{
                    "username": None,
                    "AUTH_TYPE": "Offline Login",
                    "UUID": None
                }]
            }, f, indent=4)
        print("Config file create: client_config.json")

    json_file_path_mirror = os.path.join(config_path, 'mirror.json')
    if not os.path.exists(json_file_path_mirror):
        with open(json_file_path_mirror, 'w') as f:
            json.dump({"mirror": "default"}, f, indent=4)
        print("Config file create: mirror.json")

    json_file_path_mirror = os.path.join(config_path, 'server_config.json')
    if not os.path.exists(json_file_path_mirror):
        with open(json_file_path_mirror, 'w') as f:
            json.dump({"ip_url": "https://raw.githubusercontent.com/Sesdear/Drist_Sources/manifests/launcher_ip.json"}, f, indent=4)
        print("Config file create: server_config.json")

def create_slPassword():
    sl_pass_path = os.path.join('.', '.sl_password')
    if not os.path.exists(sl_pass_path):
        with open(sl_pass_path, 'w') as f:
            f.write("")
        print("Config file create: .sl_password")




if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    current_path = get_current_program_path()

    if not check_path_for_cyrillic(current_path):
        sys.exit(1)

    create_folders()
    create_jsons()
    create_slPassword()
    download_ui()
    download_icons()

    window = mainWindow.MainWindow()
    window.show()

    sys.exit(app.exec())
