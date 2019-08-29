#!/usr/bin/python

import xbmcplugin
import xbmcaddon
import xbmcgui
import sys
import os

import sportsreplay

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 11-06-2019
# Description: Replay Football Matches

# Get addon details
__addon_id__ = u'plugin.video.full-match-replay'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = u'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
__baseurl__ = 'http://fullmatchsports.com/'

# Define local variables
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
                                __addon_id__ + '/resources/media/'))
thumbs = {'Premier League': image_path + 'Premier_League.png',
          'Serie A Italy': image_path + 'Serie_A.png',
          'La Liga Spain': image_path + 'La_Liga.png',
          'Bundesliga Germany': image_path + 'Bundesliga.png',
          'Ligue 1 France': image_path + 'Ligue_1.png',
          'Champions League': image_path + 'Champions_League.png',
          'Europa League': image_path + 'Europa_League.png',
          'EURO 2020': image_path + 'Euro_2020.png',
          'UEFA Nations League': image_path + 'Nations_League.png',
          'World Cup 2018': image_path + 'World_Cup_2018.png',
          'World Cup 2014': image_path + 'World_Cup_2014.png',
          'Friendly Match': image_path + 'Friendly_Match.png',
          'EURO 2016': image_path + 'Euro_2016.png',
          'Copa America': image_path + 'Copa_America.png',
          'Africa Cup 2015': image_path + 'Africa_Cup_2015.png'}


def main_menu():
    # Shows menu items
    for url, name, mode in sportsreplay.main_menu_and_no_submenus('Full Match Replay'):
        try:
            addDir(name,
                   url,
                   mode,
                   thumbs[name],
                   __fanart__,
                   {'title': name,
                    'plot': name})
        except:
            pass
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def seasons(league, thumb):
    # Shows seasons
    for name, url, mode in sportsreplay.seasons(league):
      addDir(name,
             url,
             mode,
             thumb,
             __fanart__,
             {'title': name,
              'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def submenu(url, thumb):
    format_text = {'EPL ': '',
                   'EFL': '',
                   'Replay': '',
                   '2018': '',
                   '2017': '',
                   '2016-17': '',
                   '2015-16': '',
                   '  ': ' ',
                   ' NA': ' ([COLOR red]No longer available![/COLOR])'}
    for href, title, img, mode in sportsreplay.submenu(url, thumb):
        for item in format_text:
          title = title.replace(item, format_text[item])
        if mode == None:
          new_mode = 3
        else:
          new_mode = mode
        addDir(title.strip(),
            href,
            new_mode,
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
               4,
               thumb,
               __fanart__,
               {'title': label,
                'plot': label})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_streams(name, url, thumb):
    name = name.replace(' HD 720p', '').replace(' HD 1080p', '')
    for href, label in sportsreplay.get_streams(url):
        addDir('%s %s' % (name, label.strip()),
               href,
               5,
               thumb,
               __fanart__,
               {'title': name,
                'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def addDir(name, url, mode, iconimage, fanart=False, infoLabels=True):
    u = sys.argv[0] + "?url=" + sportsreplay.quote_plus(url) + "&mode=" + str(mode) + "&name=" + sportsreplay.quote_plus(name) + "&thumb=" + str(iconimage)
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
mode = None
url = None
name = None
thumb = None

try:
    mode = int(params["mode"])
except:
    pass
try:
    url = sportsreplay.unquote_plus(params["url"])
except:
    pass
try:
    name = sportsreplay.unquote_plus(params["name"])
except:
    pass
try:
    thumb = sportsreplay.unquote(params["thumb"])
except:
    pass

# Message below used to test the addon
#sportsreplay.commontasks.message("Mode: %s\nURL: %s\nName: %s" % (mode, url, name), "Test")

if mode == None or url == None or len(url) < 1:
    main_menu()
elif mode == 1:
    seasons(name, thumb)
elif mode == 2:
    submenu(url, thumb)
elif mode == 3:
    # Display Links
    get_links(name, url, thumb)
#    match(name, url, thumb)
elif mode == 4:
    get_streams(name, url, thumb)
elif mode == 5:
    # Play Stream
    sportsreplay.play_stream(name, url, thumb)
