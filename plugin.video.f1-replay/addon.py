#!/usr/bin/python

import xbmcplugin
import xbmcaddon
import xbmcgui
import sys
import os

import sportsreplay

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 11-06-2019
# Description: Streams Forumla 1 races since 2014

# Get addon details
__addon_id__ = u'plugin.video.f1-replay'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = u'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

# Define local variables
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
                                __addon_id__ + '/resources/media/'))

def main_menu():
    # Shows menu items
    menus = sportsreplay.main_menu('Formula 1 Race')
    for url, name, mode in menus:
        addDir(name.strip(),
               url,
               sportsreplay.Mode.SUB_MENU,
               __icon__,
               __fanart__,
               {'title': name,
                'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def submenu(url, thumb):
    for href, title, img, mode in sportsreplay.submenu(url, thumb, items_per_page=36, currmode=1):
        title = title.replace('Race', '').replace('Replay', '').replace('  ', ' ')
        addDir(title.strip(),
            href,
            sportsreplay.Mode.GET_LINKS,
            img,
            __fanart__,
            {'title': title,
             'plot': title})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_links(name, url, thumb):
    for href, title in sportsreplay.get_links(url):
        label = '%s %s' % (name, title.strip())
        addDir(label,
               url + href,
               sportsreplay.Mode.GET_STREAMS,
               __icon__,
               __fanart__,
               {'title': label,
                'plot': label})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_streams(name, url, thumb):
    name = name.replace(' HD 720p', '').replace(' HD 1080p', '')
    for href, label in sportsreplay.get_streams(url):
        addDir('%s %s'% (name, label.strip()),
               href,
               sportsreplay.Mode.PLAY_STREAM,
               thumb,
               __fanart__,
               {'title': name,
                'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def addDir(name, url, mode, thumb, fanart=False, infoLabels=True):
    u = sys.argv[0] + "?url=" + sportsreplay.quote_plus(url) + "&mode=" + str(mode) + "&name=" + sportsreplay.quote_plus(name) + "&thumb=" + str(thumb)
    ok = True
    liz = xbmcgui.ListItem(name)
    if not infoLabels:
        infoLabels =  {'title': name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    if not fanart:
        fanart = __fanart__
    liz.setArt({'fanart': fanart,
                'thumb': thumb})
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
mode = None
url = None
name = None
thumb = None

try:
    mode = int(params['mode'])
except:
    pass
try:
    url = sportsreplay.unquote_plus(params['url'])
except:
    pass
try:
    name = sportsreplay.unquote_plus(params['name'])
except:
    pass
try:
    thumb = sportsreplay.unquote(params['thumb'])
except:
    pass

# Message below used to test the addon
#sportsreplay.ct.message("Mode: %s\nURL: %s\nName: %s" % (mode, url, name), "Test")

if mode == None or mode == sportsreplay.Mode.MAIN_MENU or len(url) < 1:
    # Display Main Menu Items
    main_menu()
elif mode == sportsreplay.Mode.SUB_MENU:
    # Display Submenu Items
    submenu(url, thumb)
elif mode == sportsreplay.Mode.GET_LINKS:
    # Display Links
    get_links(name, url, thumb)
elif mode == sportsreplay.Mode.GET_STREAMS:
    # Display Link Streams
    get_streams(name, url, thumb)
elif mode == sportsreplay.Mode.PLAY_STREAM:
    # Play Stream
    sportsreplay.play_stream(name, url, thumb)
