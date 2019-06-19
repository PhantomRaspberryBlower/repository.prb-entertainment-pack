#!/usr/bin/python

import xbmcplugin
import xbmcaddon
import xbmcgui
import os
import re
import sys

from resources.lib import commontasks

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-12-2017
# Description: Testing playing URL's

# Get addon details
__addon_id__ = 'plugin.video.f1-replay'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
__baseurl__ = 'http://fullmatchsports.com/'

# Define local variables
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
                                __addon_id__ + '/resources/media/'))

def main_menu():
    # Shows menu items
    resp = commontasks.get_html(__baseurl__)
    #content = commontasks.regex_from_to(resp, '<a title="MotoGP Race" href="#" itemprop="url">', '</ul></li>')
    content = commontasks.regex_from_to(resp, '<a title="Formula 1 Race" ', '</ul></li>')
    menus = re.compile('<li id="(.+?)" class="(.+?)"><a target="_blank" rel="noopener noreferrer" href="(.+?)" itemprop="url"><span itemprop="name">(.+?)</span></a></li>').findall(content)
    for menu_item, clas, url, name in menus:
        addDir(name,
               url,
               1,
               __icon__,
               __fanart__,
               {'title': name,
                'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def submenu(url):
    page = 1
    loop = True
    while loop == True:
        resp = commontasks.get_html(url + 'page/%d' % page)
        try:
            articles = re.compile('<article(.+?)</article>').findall(resp)
        except:
            articles = ''
            loop = False
        if len(articles) > 0:
            for article in articles:
                matches = re.compile('<a href="(.+?)" itemprop="url" title="Permalink to: (.+?)" '
                                     'rel="bookmark"><img width="(.+?)" height="(.+?)" src="(.+?)" '
                                     'class="(.+?)" alt="(.+?)" itemprop="image" title="(.+?)" /></a>').findall(article)
                for href, title, imgwidth, imgheight, img, clss, alt, img_title in matches:
                    addDir(title.replace('Highlights Full Match', ''),
                           href,
                           2,
                           img,
                           __fanart__,
                           {'title': title,
                            'plot': title})
        page += 1
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def links_menu(name, url):
    resp = commontasks.get_html(url + '?tab=download')
    matches = re.compile('<a class="btn" href="(.+?)" target="_blank" rel="(.+?)">(.+?)</a>').findall(resp)
    for href, rel, title in matches:
        if 'videoz.me' in href:
            new_title = name + ' ' + title.replace('Videoz', '')
            menu_icon = __icon__
            menu_fanart = __fanart__
            addDir(new_title,
                   href,
                   3,
                   menu_icon,
                   menu_fanart,
                   {'title': new_title,
                    'plot': new_title})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_streams(name, url):
    resp = commontasks.get_html(url)
    content = re.compile('image(.+?)sources').findall(resp)
    string = ''
    parts = content[0].split('|')
    for part in parts:
        if len(part) > 1:
            string = part + "/" + string
    string = string.replace('/m3u8/', '.m3u8')
    play_stream(name, 'https://videoz.me/' + string, __icon__)


def play_stream(name, url, thumb):
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': thumb})
    xbmc.Player().play(url, liz)
    sys.exit("Stop Video")


def add_directory(name,url,mode,fanart,thumb,infoLabels):
    u=sys.argv[0] + "?url=" + commontasks.urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + commontasks.urllib.quote_plus(name) + "&thumb=" + commontasks.urllib.quote_plus(thumb)
    ok=True
    liz=xbmcgui.ListItem(name)
    if not infoLabels:
        infoLabels = {'title': name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if not fanart:
        fanart=__fanart__
    liz.setArt({'fanart': fanart,
                'thumb': thumb})
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False, totalItems=10)
    return ok


def addDir(name, url, mode, iconimage, fanart=False, infoLabels=True):
    u = sys.argv[0] + "?url=" + commontasks.urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + commontasks.urllib.quote_plus(name) + "&thumb=" + str(iconimage)
    ok = True
    liz = xbmcgui.ListItem(name)
    if not infoLabels:
        infoLabels =  {'title': name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    if not fanart:
        fanart = __fanart__
    liz.setArt({'fanart': fanart,
                'thumb': iconimage})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


''' Main '''
params = get_params()
url = None
name = None
mode = None
account = None
player = None
embed_id = None
thumb = None

try:
    url = commontasks.urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = commontasks.urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass
try:
    thumb = commontasks.urllib.unquote(params["thumb"])
except:
    pass

# Message below used to test the addon
#commontasks.message("Mode: %s\nURL: %s\nName: %s" % (mode, url, name), "Test")

if mode == None or url == None or len(url) < 1:
    main_menu()
elif mode == 1:
    submenu(url)
elif mode == 2:
    links_menu(name, url)
elif mode == 3:
    get_streams(name, url)
