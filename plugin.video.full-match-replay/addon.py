#!/usr/bin/python

import xbmcplugin
import xbmcaddon
import xbmcgui
import os
import re
import sys

from resources.lib import commontasks

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-05-2019
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
    resp = commontasks.get_html(__baseurl__)
    content = commontasks.regex_from_to(resp, '<a title="Full Match Replay" ', '<li id="menu-item-54"')
    menus = re.compile('<li id="(.+?)" class="(.+?)"><a(.+?)href="#" itemprop="url">'
                       '<span itemprop="name">(.+?)</span></a>').findall(content)
    nosubmenus = re.compile('<a target="_blank" rel="noopener noreferrer" href="(.+?)" itemprop="url">'
                       '<span itemprop="name">(.+?)</span></a>').findall(content)
    for menu_item, clss, url, name in menus:
        addDir(name,
               url,
               1,
               thumbs[name],
               __fanart__,
               {'title': name,
                'plot': name})
    for url, name in nosubmenus:
        try:
            addDir(name,
                   url,
                   2,
                   thumbs[name],
                   __fanart__,
                   {'title': name,
                    'plot': name})
        except:
            pass
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def seasons(league, thumb):
    resp = commontasks.get_html(__baseurl__)
    content = commontasks.regex_from_to(resp, league + '</span>', '</ul></li>')
    menus = re.compile('<li id="(.+?)" class="(.+?)"><a target="_blank" rel="noopener '
                       'noreferrer" href="(.+?)" itemprop="url"><span itemprop="name">'
                       '(.+?)</span></a></li>').findall(content)
    for menu_item, clss, url, name in menus:
        if url == '#':
            new_url = __baseurl__
            new_mode = None
            new_name = ''
        else:
            new_url = url
            new_mode = 2
            new_name = name
        addDir(new_name,
               new_url,
               new_mode,
               thumb,
               __fanart__,
               {'title': new_name,
                'plot': new_name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def matches(url):
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
                matches = re.compile('<a href="(.+?)" itemprop="url" title="Permalink to: (.+?)" rel="bookmark">'
                                     '<img width="(.+?)" height="(.+?)" src="(.+?)" class="(.+?)" alt="(.+?)" '
                                     'itemprop="image" title="(.+?)" /></a>').findall(article)
                for href, title, imgwidth, imgheight, img, clss, alt, img_title in matches:
                    addDir(title.replace('Highlights Full Match', ''),
                           href,
                           3,
                           img,
                           __fanart__,
                           {'title': title,
                            'plot': title})
        page += 1
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def match(name, url, thumb):
    resp = commontasks.get_html(url + '?tab=download')
    matches = re.compile('</br> (.+?) <a class="btn" href="(.+?)" target="_blank" rel="(.+?)">(.+?)</a>').findall(resp)
    for mtitle, href, rel, title in matches:
        if 'videoz.me' in href:
            new_title = name + ' ' + mtitle.replace('&#8211;', '- ').replace(': ', '') + ' ' + title.replace('SD ', '(').replace('0p', '0)')
            addDir(new_title.replace(' : ', ' ').replace('-  SD', '').replace(' Videoz', ''),
                   href,
                   4,
                   thumb,
                   __fanart__,
                   {'title': new_title,
                    'plot': new_title})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_streams(name, url, thumb):
    resp = commontasks.get_html(url)
    content = re.compile('image(.+?)sources').findall(resp)
    string = ''
    parts = content[0].split('|')
    for part in parts:
        if len(part) > 1:
            string = part + "/" + string
    string = string.replace('/m3u8/', '.m3u8')
    play_stream(name, 'https://videoz.me/' + string, thumb)


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
    seasons(name, thumb)
elif mode == 2:
    matches(url)
elif mode == 3:
    match(name, url, thumb)
elif mode == 4:
    get_streams(name, url, thumb)
