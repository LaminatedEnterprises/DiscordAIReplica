import os
import json
import re
import codecs

from typing import *


class Manifest:
    def __init__(self, directory, manifest_path) -> None:
        self.directory = directory
        self.manifest_location = manifest_path
        self.manifest = self.load_manifest()
        self.index = self.load_index()
        self.username = self.manifest["username"]

    def load_manifest(self) -> dict[str, Any]:
        with open(self.manifest_location, "r") as f:
            return json.loads(f.read())


    def load_messages(self) -> Generator[str, None, None]:
        for id, channel_name in self.index.items():
            if self.can_use_channel(channel_name):
                print(f"Can use {channel_name}")
                yield from self.load_channel_messages(self.directory + "/c" + id)

    def can_use_channel(self, name):
        for channel in self.manifest["permitted_channels"]:
            if name == channel:
                return True
            
        for dm in self.manifest["permitted_dms"]:
            if re.match(".*" + dm, name):
                return True
            
        for server_name in self.manifest["permitted_servers"]:
            if re.match(".*" + server_name, name):
                return True
            

    def load_channel_messages(self, directory) -> Generator[str, None, None]:
        with codecs.open(directory + "/messages.json", "r", encoding="utf-8") as f:
            for message in json.loads(f.read()):
                yield message["Contents"]

    def load_index(self) -> dict[str, Any]:
        with open(self.directory + "/index.json", "r") as f:
            return json.loads(f.read())

def file_exists(path) -> bool:
    try:
        with open(path, "r") as f:
            return True
    except FileNotFoundError:
        return False

def load_manifests() -> dict[str, Manifest]:
    manifests = dict()
    for f in os.scandir("datasets/"):
        if not f.is_dir():
            continue
         
        manifest_path = f.path + "/manifest.json"
        if not file_exists(manifest_path):
            continue

        manifest = Manifest(f.path, manifest_path)
        manifests[manifest.username] = manifest

    return manifests

    
    