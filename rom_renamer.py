#!/usr/bin/env python3

# RomRenamer - Script for renaming ROMs
# Copyright (C) 2021 Raymond Wright
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import hashlib
import os
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
                if hashes == (file.sha1, file.md5, file.crc, file.size):
                    matches.append((file, game))

        return matches


class GameCollection:
    def __init__(self):
        self.collection = {}
        self.unrecognised_files = set()

    def add_game_file(self, db, file):
        matches = db.lookup_file(file)
        if not matches:
            self.unrecognised_files.add(file)
        for game_file, game in matches:
            if game not in self.collection:
                self.collection[game] = {}
            if game_file not in self.collection[game]:
                self.collection[game][game_file] = []
            self.collection[game][game_file].append(file)

    def incomplete_games(self):
        for game, files in self.collection.items():
            if len(files) != len(game.files):
                yield game


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
        if not files:
            continue
        for f in files:
            roms.append(os.path.join(root, f))

    collection = GameCollection()
    for rom in roms:
        collection.add_game_file(game_list, rom)

    for file in sorted(collection.unrecognised_files):
        print(f'Unrecognised file: {file}')

    for game in collection.incomplete_games():
        print(f'Incomplete game: {game.name}')


if __name__ == '__main__':
    main(sys.argv[1], 'DATs')
