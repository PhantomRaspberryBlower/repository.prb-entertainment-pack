#!/bin/python

import xbmc
import xbmcgui
import sys
import os
import re
import urllib2

try:
    # Python3
    import urllib.request
    import urllib.parse
except ImportError:
    # Python2
    import urllib

import jsunpack

'''
Written by: Phantom Raspberry Blower
Date: 21-08-2017
Description: Common Tasks for Addons
'''

INVALID_FILENAME_CHARS = u'\/:*?"<>|'
Juice = u"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="

def urlencode(values):
    try:
        resp = urllib.urlencode(values)
    except:
        resp = urllib.parse.urlencode(values)
    return resp


def quote_plus(text):
    try:
        resp = urllib.quote_plus(text)
    except:
        resp = urllib.parse.quote_plus(text)
    return resp


def unquote_plus(text):
    try:
        resp = urllib.unquote_plus(text)
    except:
        resp = urllib.parse.unquote_plus(text)
    return resp


def get_html(url, policy=None):
    header_dict = {}
    header_dict['Accept'] = 'application/json;pk=' + str(policy)
    header_dict['User-Agent'] = 'AppleWebKit/<WebKit Rev>'
    header_dict['Range'] = 'bytes=0-'
    req = urllib2.Request(url, headers=header_dict)
    try:
        response = urllib2.urlopen(req)
        html = response.read()
        response.close()
    except urllib2.HTTPError:
        response = False
        html = False
    return html


def get_url(url):
    try:
        resp = urllib.urlopen(url)
    except:
        try:
            resp = urllib.request.urlopen(url)
        except:
            resp = 0
    return resp.read()


def regex_from_to(text, from_string, to_string, excluding=True):
    if excluding:
        r = re.search(u'(?i)' + from_string +
                      u'([\S\s]+?)' +
                      to_string, text).group(1)
    else:
        r = re.search(u'(?i)(' +
                      from_string +
                      u'[\S\s]+?' +
                      to_string +
                      u')', text).group(1)
    return r


def xbmc_version():
    return float(xbmc.getInfoLabel("System.BuildVersion")[:4])


def notification(title, message, icon, duration):
    # Display notification to user
    dialog = xbmcgui.Dialog()
    dialog.notification(title,
                        message.encode('ascii', errors='ignore'),
                        icon,
                        duration)


def message(message, title):
    # Display message to user
    dialog = xbmcgui.Dialog()
    dialog.ok(title, message)


def remove_from_list(list, file):
    list = list.replace(u'<>Ungrouped', '').replace(u'All Songs', '')
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
        if u'song' not in file and u'album' not in file:
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


def validate_filename(filename):
    # Remove invalid characters from file name
    valid_filename = dict((ord(char), None) for char in INVALID_FILENAME_CHARS)
    file_name = filename.decode('ascii', errors='ignore')
    return file_name.translate(valid_filename)


def getLibrarySources(db_type):
    # Returns the paths of library sources both music and videos
    json_request = u'{ "jsonrpc" : "2.0", "method": "Files.GetSources", "id": 1, "params" : '+\
    '{"media":  "' + db_type + u'"}}'
    response = xbmc.executeJSONRPC(json_request)
    response = eval(response)
    return [source['file'] for source in response['result']['sources']]


def unjuice(e):
    try:
        e = re.findall(r'JuicyCodes.Run\(([^\)]+)', e, re.IGNORECASE)[0]
        e = re.sub(r'\"\s*\+\s*\"','', e)
        e = re.sub(r'[^A-Za-z0-9+\\/=]','', e)
    except:
        return None

    t = ""
    n=r=i=s=o=u=a=f=0

    while f < len(e):
        try:
            s = Juice.index(e[f]);f+=1; 
            o = Juice.index(e[f]);f+=1; 
            u = Juice.index(e[f]);f+=1; 
            a = Juice.index(e[f]);f+=1; 
            n = s << 2 | o >> 4; r = (15 & o) << 4 | u >> 2; i = (3 & u) << 6 | a
            t += chr(n)
            if 64 != u: t += chr(r)
            if 64 != a: t += chr(i)
        except:
            continue
        pass

    try:
        t = jsunpack.unpack(t)
        t = unicode(t, 'utf-8')
    except:
        t = None
    
    return t


def play(name, url, thumb):
    message(url, "url")
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': thumb})
    xbmc.Player().play(url, liz)
    sys.exit("Stop Video")
