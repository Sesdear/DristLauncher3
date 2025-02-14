import os.path
import shutil
import subprocess
import uuid
import json
import zipfile

import minecraft_launcher_lib as mll
import requests


def generate_cracked_uid():
    # Read data from the JSON file
    file_path = 'configs/client_config.json'
    with open(file_path) as f:
        data1 = json.load(f)

    # Check if UUID is None or a placeholder
    if data1["User-info"][0]["UUID"] is None:
        # Generate a new UUID
        uid = uuid.uuid4().hex
        data1["User-info"][0]["UUID"] = str(uid)
        # Write the updated data back to the JSON file
        with open(file_path, 'w') as js_set:
            json.dump(data1, js_set, indent=4)

        print(f"Generated new UUID: {uid}")
    else:
        uid = data1["User-info"][0]["UUID"]
        print(f"Using existing UUID: {uid}")

    return uid


def download_server_dat():
    repo_url = 'https://codeload.github.com/Sesdear/Drist_Sources/zip/refs/heads/server_dat'
    destination_folder_parent = '.'
    source_folder = 'Drist_Sources-server_dat'
    destination_folder = 'minecraft'  # Папка, куда будет перемещен server.dat

    destination = os.path.join(destination_folder_parent, 'server_dat.zip')
    response = requests.get(repo_url, stream=True)
    with open(destination, 'wb') as f:
        f.write(response.content)

    extracted_folder_path = os.path.join(destination_folder_parent, '.')
    with zipfile.ZipFile(destination, 'r') as zip_ref:
        # Вывод содержимого архива для проверки
        print("Содержимое архива:")
        zip_ref.printdir()
        zip_ref.extractall(extracted_folder_path)

    # Проверка и перемещение файла server.dat
    server_dat_file = 'servers.dat'
    found = False
    for root, dirs, files in os.walk(source_folder):
        if server_dat_file in files:
            source_file_path = os.path.join(root, server_dat_file)
            destination_file_path = os.path.join(destination_folder, server_dat_file)
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            shutil.move(source_file_path, destination_file_path)
            print(f"{server_dat_file} перемещен в {destination_folder}")
            found = True
            break

    if not found:
        print(f"{server_dat_file} не найден в {source_folder}")

    try:
        print("Delete Temp Folder status: in progress")
        file_path = destination
        os.remove(file_path)
        shutil.rmtree(source_folder)
        print("Delete Temp Folder status: Done")
    except Exception as e:
        print(f"Error while deleting temp Folder: {e}")




def start_minecraft():
    try:
        download_server_dat()
    except Exception as e:
        print(e)

    with open('configs/manifests/minecraft_manifest.json', 'r') as f:
        config_manifest = json.load(f)
    with open('configs/client_config.json', 'r') as f:
        config_client = json.load(f)

    minecraft_directory = "minecraft"
    xmx = config_client["Xmx"]
    xms = config_client["Xms"]
    minecraft_version = config_manifest["minecraft-version"]
    modloader = config_manifest["modloader"]
    modloader_version = config_manifest["modloader-version"]

    print(minecraft_directory)
    print(xmx)
    print(xms)
    print(minecraft_version)
    print(modloader)
    print(modloader_version)

    # Ensure UUID is generated or retrieved
    uuid_ = generate_cracked_uid()
    username = config_client["User-info"][0]["username"]

    if uuid_ is None or username is None:
        raise ValueError("UUID or username is missing")

    options = {
        "username": username,
        "uuid": uuid_,
        "token": "",
        "jvmArguments": [f"-Xmx{xmx}m", f"-Xms{xms}m"],
        "executablePath": config_client["java_path"],
        "gameDirectory": minecraft_directory
    }

    print(options)



    minecraft_command = mll.command.get_minecraft_command(
        f"{minecraft_version}-{modloader}-{modloader_version}",
        minecraft_directory,
        options
    )

    try:
        subprocess.Popen(minecraft_command)
    except Exception as e:
        print(e)


