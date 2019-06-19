#!/bin/python

import os
import re
import time
import xbmc
import xbmcgui
from PIL import Image

'''
Written by: Phantom Raspberry Blower
Date: 21-08-2017
Description: Common Tasks for Addons
'''

INVALID_FILENAME_CHARS = '\/:*?"<>|'


def regex_from_to(text, from_string, to_string, excluding=True):
    if excluding:
        r = re.search("(?i)" + from_string +
                      "([\S\s]+?)" +
                      to_string, text).group(1)
    else:
        r = re.search("(?i)(" +
                      from_string +
                      "[\S\s]+?" +
                      to_string +
                      ")", text).group(1)
    return r


def xbmc_version():
    return float(xbmc.getInfoLabel("System.BuildVersion")[:4])


def notification(title, message, ms, nart):
    xbmc.executebuiltin("XBMC.notification(" +
                        title + "," +
                        message.encode("ascii", errors="ignore") + "," +
                        ms + "," + nart + ")")


def message(message, title):
    # Display message to user
    dialog = xbmcgui.Dialog()
    dialog.ok(title, message)


def remove_from_list(list, file):
    list = list.replace('<>Ungrouped', '').replace('All Songs', '')
    index = find_list(list, file)
    if index >= 0:
        content = read_from_file(file)
        lines = content.split('\n')
        lines.pop(index)
        s = ''
        for line in lines:
            if len(line) > 0:
                s = s + line + '\n'
        write_to_file(file, s)
        if 'song' not in file and 'album' not in file:
            pass


def find_list(query, search_file):
    try:
        content = read_from_file(search_file)
        lines = content.split('\n')
        index = lines.index(query)
        return index
    except:
        return -1


def add_to_list(list, file, refresh):
    if find_list(list, file) >= 0:
        return
    if os.path.isfile(file):
        content = read_from_file(file)
    else:
        content = ""

    lines = content.split('\n')
    s = '%s\n' % list
    for line in lines:
        if len(line) > 0:
            s = s + line + '\n'
    write_to_file(file, s)

    if refresh:
        xbmc.executebuiltin("Container.Refresh")


def read_from_file(path):
    try:
        f = open(path, 'r')
        r = f.read()
        f.close()
        return str(r)
    except:
        return None


def write_to_file(path, content, append=False):
    try:
        if append:
            f = open(path, 'a')
        else:
            f = open(path, 'w')
        f.write(content)
        f.close()
        return True
    except:
        return False


def create_directory(dir_path, dir_name=None):
    if dir_name:
        dir_path = os.path.join(dir_path, dir_name)
    dir_path = dir_path.strip()
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def create_file(dir_path, file_name=None):
    if file_name:
        file_path = os.path.join(dir_path, file_name)
    file_path = file_path.strip()
    if not os.path.exists(file_path):
        f = open(file_path, 'w')
        f.write('')
        f.close()
    return file_path


def remove_old_temp_files(file_path, days=28):
    '''
    Remove temp files from directory that are older
    than the specified number of days
    '''
    SECONDS_PER_HOUR = 3600
    current_time = time.time()
    for f in os.listdir(file_path):
        creation_time = os.path.getctime(file_path + '/' + f)
        if ((current_time - creation_time) // (24 * SECONDS_PER_HOUR)) >= int(days):
            os.unlink(file_path + '/' + f)


def resize_image(image_file, width, height):
    # Resize images
    size = height, width
    img = Image.open(image_file)
    img.thumbnail(size, Image.ANTIALIAS)
    img.save(image_file)


def validate_filename(filename):
    # Remove invalid characters from file name
    valid_filename = dict((ord(char), None) for char in INVALID_FILENAME_CHARS)
    file_name = filename.decode("ascii", errors="ignore")
    return file_name.translate(valid_filename)


def getLibrarySources(db_type):
    # Returns the paths of library sources both music and videos
    json_request = '{ "jsonrpc" : "2.0", "method": "Files.GetSources", "id": 1, "params" : '+\
    '{"media":  "' + db_type + '"}}'
    response = xbmc.executeJSONRPC(json_request)
    response = eval(response)
    return [source['file'] for source in response['result']['sources']]
