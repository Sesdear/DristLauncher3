import json
import os
import shutil
import zipfile
import requests

import manifest_reader
import server_connector

def createZeroClientFilesManifest(client_path):
    with open(client_path, 'w') as f:
        json.dump({"version": 0, "files": {}}, f, indent=4)
    print(f"Created {client_path}")
def getFileVersion(c_list: dict, file: str):
    if file in c_list:
        return c_list[file]
    return 0
def compareManifests(client_path, server_path) -> dict:
    c_manifest = manifest_reader.readMinecraftManifest(client_path)
    s_manifest = manifest_reader.readMinecraftManifest(server_path)
    if c_manifest == None:
        createZeroClientFilesManifest(client_path)
        c_manifest = manifest_reader.readMinecraftManifest(client_path)
    c_vers: int = c_manifest["version"]
    s_vers: int = s_manifest["version"]
    c_list: dict = c_manifest["files"]
    s_list: dict = s_manifest["files"]
    delete_list = []
    download_list = []
    if c_vers < s_vers:
        for i in s_list:
            if s_list[i] == -1:
                delete_list.append(i)
                print(f"Adding {i} to delete list")
            else:
                if getFileVersion(c_list, i) < s_list[i]:
                    download_list.append(i)
                    print(f"Adding {i} to update list")
    elif c_vers == s_vers:
        print("Manifest versions are equal, skipping checks")
    else:
        print("F#cking how?")

    return {"delete": delete_list, "download": download_list}

def updateFiles(upd_dict: dict, progress_callback=None):
    print("start update files")
    files_dir = "./minecraft/"
    total_tasks = len(upd_dict["delete"]) + len(upd_dict["download"])
    current_task = 0
    # Удаление файлов и директорий
    for d in upd_dict["delete"]:
        print(d)
        full_path = os.path.join(files_dir, d)
        print(f"file delete - {full_path}")
        if os.path.exists(full_path):
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    print(f"Deleted directory: {full_path}")
                else:
                    os.remove(full_path)
                    print(f"Deleted file: {full_path}")
            except Exception as e:
                print(f"Error deleting {full_path}: {e}")
        else:
            print(f"File or directory not found: {full_path}")
        # Обновляем прогресс
        current_task += 1
        if progress_callback:
            progress_callback(current_task, total_tasks)
    # Загрузка файлов
    succ_updated_list = []
    print("UFDownload")
    print(succ_updated_list)
    for i in upd_dict["download"]:
        print(i)
        url = server_connector.constructServerAdress(server_connector.getServerIp(), server_connector.getServerPort())
        if '.' not in i:
            i = i + ".zip"
        filepath = os.path.join(files_dir, i)
        try:
            try:
                response = requests.get(f"{url}/files/{i}", stream=True)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при скачивании {i}: {e}")
                continue
            if os.path.exists(filepath):
                if i.endswith(".zip"):
                    g = i[:-4]
                    print(g)
                full_path = os.path.join(".", g)
                if os.path.exists(full_path):
                    try:
                        if os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                            print(f"Deleted directory: {full_path}")
                        else:
                            os.remove(full_path)
                            print(f"Deleted file: {full_path}")
                    except Exception as e:
                        print(f"Error deleting {full_path}: {e}")
                else:
                    print(f"File or directory not found: {full_path}, nothing to delete")
            with open(filepath, 'wb') as f:
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback:
                            progress_callback(current_task + 1, total_tasks, downloaded_size, total_size)
            print(f"Downloaded: {i} to {filepath}")
            if i.endswith(".zip"):
                # Определяем путь для извлечения
                if i == "config.zip":
                    extract_dir = os.path.join(".", i[:-4])  # Извлекаем в ./config/
                else:
                    extract_dir = os.path.join("./minecraft/", i[:-4])  # Стандартный путь

                os.makedirs(extract_dir, exist_ok=True)

                try:
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        # Извлекаем все файлы
                        zip_ref.extractall(extract_dir)
                        print(f"Unzipped '{i}' to '{extract_dir}'")

                        # Определяем целевой путь для kubejs и fancymenu
                        target_dir = 'minecraft' if i != "config.zip" else '.'  # Для config.zip — в текущую директорию

                        # Извлекаем только kubejs и fancymenu
                        for file in zip_ref.namelist():
                            folder_name = file.split('/')[0]
                            if folder_name in ['kubejs', 'fancymenu']:
                                zip_ref.extract(file, target_dir)
                                print(f"Extracted '{file}' to '{target_dir}'")

                except Exception as e:
                    print(f"Error: Could not unzip file: {e}")
                finally:
                    os.remove(filepath)  # Удаляем zip файл после извлечения
            if i.endswith(".zip"):
                i = i[:-4]
            succ_updated_list.append(i)
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {i}: {e}")
        # Обновляем прогресс
        current_task += 1
        if progress_callback:
            progress_callback(current_task, total_tasks)
    equalizeClientManifest("configs/manifests/old_files_manifest.json", "configs/manifests/files_manifest.json")

def equalizeClientManifest(client_path, server_path):
    with open(server_path, 'r') as f_in:
        data = json.load(f_in)
    with open(client_path, 'w') as f_out:
        json.dump(data, f_out, indent=4)
def exists(filename:str):
    if filename.endswith(".zip"):
        filename = filename[:-4]
    return os.path.exists(filename)

def automaticUpdateFiles(progress_callback=None):
    server_connector.getFilesManifest(
        server_connector.constructServerAdress(server_connector.getServerIp(), server_connector.getServerPort()))
    server_connector.getMinecraftManifest(server_connector.constructServerAdress(server_connector.getServerIp(), server_connector.getServerPort()))
    updateFiles(compareManifests("configs/manifests/old_files_manifest.json", "configs/manifests/files_manifest.json"), progress_callback)