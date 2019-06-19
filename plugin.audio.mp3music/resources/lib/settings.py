#!/bin/python

import xbmc
import xbmcaddon
import os
import commontasks

# Written by: Phantom Raspberry Blower
# Date: 21-08-2017
# Description: Fetch Settings for Addons

__addon__ = xbmcaddon.Addon(id='plugin.audio.mp3music')
DATA_PATH = os.path.join(xbmc.translatePath('special://profile/addon_data'
                                            '/plugin.audio.mp3music'), '')


def cookie_jar():
    return create_file(DATA_PATH, "cookiejar.lwp")


def addon():
    return __addon__


def artist_icons():
    return create_directory(DATA_PATH, "artist_icons")


def folder_structure():
    return __addon__.getSetting('folder_structure')


def favourites_file_artist():
    return create_file(DATA_PATH, "favourites_artist.list")


def favourites_file_album():
    return create_file(DATA_PATH, "favourites_album.list")


def id3tags_list():
    return create_file(DATA_PATH, "id3tags.list")


def download_list():
    return create_file(DATA_PATH, "downloads.list")


def favourites_file_songs():
    return create_file(DATA_PATH, "favourites_songs.list")


def custom_directory():
    if __addon__.getSetting('custom_directory') == "true":
        return True
    else:
        return False


def show_progress():
    if __addon__.getSetting('show_progress') == "true":
        return True
    else:
        return False


def keep_downloads():
    if __addon__.getSetting('keep_downloads') == "true":
        return True
    else:
        return False


def default_queue():
    if __addon__.getSetting('default_queue') == "true":
        return True
    else:
        return False


def hide_fanart():
    if __addon__.getSetting('hide_fanart') == "true":
        return True
    else:
        return False


def default_queue_album():
    if __addon__.getSetting('default_queue_album') == "true":
        return True
    else:
        return False


def queue_downloads():
    if __addon__.getSetting('queue_downloads') == "true":
        return True
    else:
        return False


def music_dir():
    if __addon__.getSetting('music_dir') == "set":
        return create_directory(DATA_PATH, "music")
    else:
        return __addon__.getSetting('music_dir')


def create_directory(dir_path, dir_name=None):
    return commontasks.create_directory(dir_path, dir_name)


def create_file(dir_path, file_name=None):
    return commontasks.create_file(dir_path, file_name)


commontasks.create_directory(DATA_PATH, "")
