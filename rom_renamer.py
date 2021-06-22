#!/usr/bin/env python3

import hashlib
import os
import random
import shutil
import sys
import xml.etree.ElementTree as ET
import zlib


class GameFile:
    def __init__(self, rom_node):
        self.name = rom_node.attrib['name']
        self.size = rom_node.attrib['size']
        self.crc = rom_node.attrib['crc'].lower()
        self.md5 = rom_node.attrib['md5'].lower()
        self.sha1 = rom_node.attrib['sha1'].lower()

    def __eq__(self, other):
        if self.name != other.name:
            return False
        if self.size != other.size:
            return False
        if self.crc != other.crc:
            return False
        if self.md5 != other.md5:
            return False
        return self.sha1 == other.sha1

    def __hash__(self):
        return hash((self.name, self.size, self.crc, self.md5, self.sha1))

    def checksums(self):
        return (self.sha1, self.md5, self.crc, self.size)


class Game:
    def __init__(self, console, game_node):
        self.console = console
        self.name = game_node.attrib['name']
        file_list = []
        for child in game_node.findall('rom'):
            file_list.append(GameFile(child))
        self.files = tuple(file_list)

    def __eq__(self, other):
        if self.console != other.console:
            return False
        if self.name != other.name:
            return False
        return self.files == other.files

    def __hash__(self):
        return hash((self.console, self.name, self.files))


class GameList:
    def __init__(self):
        self.games = []

    def append_dat(self, dat):
        root = dat.getroot()
        console = root.find('header').find('name').text

        for child in root.findall('game'):
            self.games.append(Game(console, child))
            print

    def lookup_file(self, file):
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        crc = 0
        size = 0

        with open(file, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                md5.update(data)
                sha1.update(data)
                crc = zlib.crc32(data, crc)
                size += len(data)

        hashes = (
            sha1.hexdigest(), md5.hexdigest(), '{:08x}'.format(crc), str(size))

        # Necessary because different multi-file games can share some files,
        # e.g., Rayman (Europe) and Rayman (USA) for PSX.
        matches = []
        for game in self.games:
            for file in game.files:
                if hashes == file.checksums():
                    matches.append((file, game))

        return matches


class GameCollection:
    def __init__(self):
        self.__collection = {}
        self.unrecognised_files = set()

    def add_game_file(self, db, file):
        matches = db.lookup_file(file)
        if not matches:
            self.unrecognised_files.add(file)
        for game_file, game in matches:
            if game not in self.__collection:
                self.__collection[game] = {}
            if game_file not in self.__collection[game]:
                self.__collection[game][game_file] = []
            self.__collection[game][game_file].append(file)

    def __complete_games(self):
        complete_games = set()
        for game, files in self.__collection.items():
            if len(files) == len(game.files):
                complete_games.add(game)
        return complete_games

    def __used_files(self):
        used_files = set()
        full_games = self.__complete_games()
        for game, files in self.__collection.items():
            if game in full_games:
                used_files.update(f.checksums() for f in files)
        return used_files

    def files_in_games(self):
        game_files = set()
        for files in self.__collection.values():
            for dat_entry, file_paths in files.items():
                game_files.update((f, dat_entry.sha1) for f in file_paths)
        return game_files

    def __file_path(self, game, file_hash):
        path = game.console
        if len(game.files) > 1:
            path = os.path.join(path, game.name)
        for file in game.files:
            if file.sha1 == file_hash:
                return os.path.join(path, file.name)
        raise RuntimeError("File not in game")

    def renames(self):
        used_files = self.__used_files()
        full_games = self.__complete_games()
        file_dsts = {}
        for game, files in self.__collection.items():
            if game in full_games:
                for f in files:
                    if f.sha1 not in file_dsts:
                        file_dsts[f.sha1] = []
                    file_dsts[f.sha1].append(self.__file_path(game, f.sha1))
            else:
                for f in files:
                    if f.checksums() not in used_files:
                        if f.sha1 not in file_dsts:
                            file_dsts[f.sha1] = []
                        path = self.__file_path(game, f.sha1)
                        path = os.path.join('Incomplete games', path)
                        file_dsts[f.sha1].append(path)
        return file_dsts


def move_with_dirs(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)


def copy_with_dirs(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def move_unrecognised_files(rom_dir, collection):
    unrecognised = os.path.join(rom_dir, 'Unrecognised files')
    for file in collection.unrecognised_files:
        dst = os.path.relpath(file, rom_dir)
        if os.path.realpath(file).startswith(os.path.realpath(unrecognised)):
            continue
        dst = os.path.join(unrecognised, dst)
        move_with_dirs(file, dst)


def create_temp_dir(rom_dir):
    while True:
        try:
            temp_dir = f'temp_{random.randrange(0xFFFFFFFF)}'
            temp_dir = os.path.join(rom_dir, temp_dir)
            os.mkdir(temp_dir)
            return temp_dir
        except FileExistsError:
            pass


def move_into_temp(collection, temp_dir):
    files_to_move = collection.files_in_games()
    for path, hash in files_to_move:
        move_with_dirs(path, os.path.join(temp_dir, hash))


def move_from_temp(rom_dir, collection, temp_dir):
    renames = collection.renames()
    for file_hash, dsts in renames.items():
        src = os.path.join(temp_dir, file_hash)
        for dst in dsts[1:]:
            copy_with_dirs(src, os.path.join(rom_dir, dst))
        move_with_dirs(src, os.path.join(rom_dir, dsts[0]))


def clean_empty_folders(rom_dir):
    while True:
        empty_dirs = []
        for root, subdirs, files in os.walk(rom_dir):
            if not subdirs and not files:
                empty_dirs.append(root)
        for dir in empty_dirs:
            os.rmdir(dir)
        if not empty_dirs:
            return


def main(rom_dir, dat_dir):
    dats = []
    with os.scandir(dat_dir) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_file():
                dats.append(entry.path)

    game_list = GameList()
    for file in dats:
        dat = ET.parse(file)
        game_list.append_dat(dat)

    roms = []
    for root, _, files in os.walk(rom_dir):
        roms.extend(os.path.join(root, f) for f in files)

    collection = GameCollection()
    for rom in roms:
        collection.add_game_file(game_list, rom)

    move_unrecognised_files(rom_dir, collection)
    temp_dir = create_temp_dir(rom_dir)
    move_into_temp(collection, temp_dir)
    move_from_temp(rom_dir, collection, temp_dir)
    clean_empty_folders(rom_dir)


if __name__ == '__main__':
    main(sys.argv[1], 'DATs')
