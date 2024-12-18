import json
import os
from pathlib import Path

import requests
import manifest_reader
import server_connector


def createClientModsManifest():
    print("createClientModsManifest")
    version = 0
    modlist = []
    for filename in os.listdir("minecraft/mods"):
        if filename.endswith(".disabled"):
            filename = filename[:-9]
        if not filename.startswith("IGNORE."):
            if filename.endswith(".jar"):
                modlist.append(filename)

    print(modlist)

    with open("configs/manifests/client_mods_manifest.json", 'w') as f:
        json.dump({"version": version, "mods": modlist}, f, indent=4)
        print(f"Client manifest created!")


def compareManifests(client_path, server_path) -> dict:
    print("compareManifests")
    c_manifest = manifest_reader.readMinecraftManifest(client_path)
    s_manifest = manifest_reader.readMinecraftManifest(server_path)

    c_list: list = c_manifest["mods"]
    s_list: list = s_manifest["mods"]

    delete_list = []
    download_list = []

    for m in s_list:
        if m not in c_list:
            download_list.append(m)
        else:
            c_list.pop(c_list.index(m))

    for n in c_list:
        if n not in s_list:  # на всякий случай
            delete_list.append(n)

    return {"delete": delete_list, "download": download_list}


def updateMods(upd_dict: dict, progress_callback=None):
    print("Updatemods")
    mods_dir = "minecraft/mods"
    total_files = len(upd_dict["delete"]) + len(upd_dict["download"])
    current_task = 0

    # Удаление модов
    for d in upd_dict["delete"]:
        filepath = os.path.join(mods_dir, d)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted: {filepath}")
        elif os.path.exists(filepath + ".disabled"):
            os.remove(filepath + ".disabled")
            print(f"Deleted: {filepath}.disabled")
        else:
            print(f"File not found: {filepath}")

        current_task += 1
        if progress_callback:
            progress_callback(current_task, total_files, 0, 0)

    # Загрузка модов
    for index, i in enumerate(upd_dict["download"]):
        filepath = os.path.join(mods_dir, i)
        url = server_connector.constructServerAdress(
            server_connector.getServerIp(),
            server_connector.getServerPort()
        )
        full_url = f"{url}/mods/{i}"
        print(f"Downloading from: {full_url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            response = requests.get(full_url, headers=headers, stream=True)
            response.raise_for_status()  # Проверка на ошибки

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        if progress_callback:
                            progress_callback(index + 1, len(upd_dict["download"]), downloaded_size, total_size)

            print(f"Downloaded: {i} to {filepath}")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {i} from {full_url}: {e}")

        current_task += 1
        if progress_callback:
            progress_callback(current_task, total_files, 0, 0)


# Пример использования функции updateMods с обратным вызовом прогресса
def progress_callback(file_index, total_files, downloaded_size, total_size):
    percent_complete = (downloaded_size / total_size) * 100 if total_size > 0 else 0
    print(f"File {file_index}/{total_files}: {percent_complete:.2f}% complete ({downloaded_size}/{total_size} bytes)")


# Вызов функции с progress_callback
def automaticUpdateMods(progress_callback=None):
    server_connector.getModsManifest(
        server_connector.constructServerAdress(server_connector.getServerIp(), server_connector.getServerPort()))
    createClientModsManifest()
    updateMods(compareManifests("configs/manifests/client_mods_manifest.json", "configs/manifests/mods_manifest.json"),
               progress_callback)

