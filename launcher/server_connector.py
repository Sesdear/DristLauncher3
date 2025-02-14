import json
import os

import requests

import manifest_reader


# server_ip: str = "localhost"
# server_port: int = 8000

def getIpManifest():
    """Downloads a JSON file from a given URL and saves it to a specified path."""

    with open('configs/server_config.json', 'r') as f:
        json_ip = json.load(f)

    try:
        response = requests.get(json_ip["ip_url"])
        print(response)
        response.raise_for_status()# Raise an exception for bad status codes

        os.makedirs(os.path.dirname("configs/manifests/launcher_ip.json"), exist_ok=True)  # Create directory if it doesn't exist

        with open("configs/manifests/launcher_ip.json", 'w') as f:
            f.write(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error: Could not download file: {e}")


def splitIp(ip_string):
    print("splitIp")
    parts = ip_string.split(':')
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return None, None
def getServerIp():
    print("getServerIp")
    getIpManifest()
    data = manifest_reader.readMinecraftManifest("configs/manifests/launcher_ip.json")
    mirror = manifest_reader.readMinecraftManifest("configs/mirror.json")["mirror"]
    ipstring = data[mirror]
    ip, port = splitIp(ipstring)

    return ip
def getServerPort():
    print("getServerPort")
    getIpManifest()
    data = manifest_reader.readMinecraftManifest("configs/manifests/launcher_ip.json")
    mirror = manifest_reader.readMinecraftManifest("configs/mirror.json")["mirror"]
    ipstring = data[mirror]
    ip, port = splitIp(ipstring)

    return port  # "localhost"

def constructServerAdress(ip: str, port) -> str:
    return f"http://{ip}:{port}"
def getMinecraftManifest(url: str):
    print("mine_mani")
    try:
        print("try response")
        response = requests.get(f"{url}/manifests/minecraft_manifest.json")
        print(response)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the JSON response
        manifest_data = response.json()
        print(manifest_data)
        with open("configs/manifests/minecraft_manifest.json", 'w') as f:
            json.dump(manifest_data, f, indent=4)
        return manifest_data

    except requests.exceptions.RequestException as e:
        print(f"Error retrieving manifest: {e}")
        return None

def getModsManifest(url: str):
    print("getModsManifest")
    try:
        response = requests.get(f"{url}/manifests/mods_manifest.json")
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the JSON response
        manifest_data = response.json()
        print(manifest_data)
        with open("configs/manifests/mods_manifest.json", 'w') as f:
            json.dump(manifest_data, f, indent=4)
        return manifest_data

    except requests.exceptions.RequestException as e:
        print(f"Error retrieving manifest: {e}")
        return None

def getFilesManifest(url: str):
    print("getFilesManifest")
    try:
        print("getFilesManifest 2")
        response = requests.get(f"{url}/manifests/files_manifest.json")
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the JSON response
        manifest_data = response.json()
        print(manifest_data)
        with open("configs/manifests/files_manifest.json", 'w') as f:
            json.dump(manifest_data, f, indent=4)
        return manifest_data

    except requests.exceptions.RequestException as e:
        print(f"Error retrieving manifest: {e}")
        return None


if __name__ == '__main__':
    print(getModsManifest(constructServerAdress(getServerIp(), getServerPort())))