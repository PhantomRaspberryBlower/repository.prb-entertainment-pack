#!/usr/bin/python

import xbmcplugin
import xbmcaddon
import xbmcgui
import os
import re
import sys

import urlresolver # Resolves media file from url

from resources.lib import unjuice # Returns url from JuicyCodes.run()
from resources.lib import commontasks

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-12-2017
# Description: Streams NBA games since 2017

# Get addon details
__addon_id__ = 'plugin.video.nba-replay'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
__baseurl__ = 'http://fullmatch.net/'

# Define local variables
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
                                __addon_id__ + '/resources/media/'))

def main_menu():
    # Shows menu items
    resp = commontasks.get_html(__baseurl__)
    content = commontasks.regex_from_to(resp, 'data-toggle="dropdown">NBA ', 'data-toggle=')
    menus_content = commontasks.regex_from_to(content, '<ul class="dropdown-menu menu-depth-1">',
                                              'parent dropdown-submenu">')
    submenus_content = commontasks.regex_from_to(content, '<ul class="dropdown-menu menu-depth-2">', '</ul>')
    menus = re.compile('<a target="_blank" href="(.+?)" class="menu-link  sub-menu-link">(.+?)</a>').findall(menus_content)
    submenus = re.compile('<a target="_blank" href="(.+?)" class="menu-link  sub-menu-link">(.+?)</a>').findall(submenus_content)
    for url, name in menus:
        addDir(name,
               url + 'page/1',
               2,
               __icon__,
               __fanart__,
               {'title': name,
                'plot': name})
    for url, name in submenus:
        addDir(name,
               url,
               4,
               __icon__,
               __fanart__,
               {'title': name,
                'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def main_menu_old():
    # Shows menu items
    resp = commontasks.get_html(__baseurl__)
    content = commontasks.regex_from_to(resp, 'data-toggle="dropdown">NBA ', 'data-toggle=')
    menus = re.compile('<a target="_blank" href="(.+?)" class="menu-link  sub-menu-link">(.+?)</a>').findall(content)
    for url, name in menus:
        addDir(name,
               url + 'page/1',
               2,
               __icon__,
               __fanart__,
               {'title': name,
                'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def submenu(url):
    items_per_page = 48
    item = 0
    if url.find('page/') > 0:
        pgnumf = url.find('page/') + 5
        pgnum = int(url[pgnumf:])
    else:
      pgnum = 1
    url = url.replace('page/%d' % pgnum, '')
    while item < items_per_page:
        resp = commontasks.get_html(url + 'page/%d' % pgnum)
        try:
            articles = re.compile('<article(.+?)</article>').findall(resp)
        except:
            articles = ''
        if len(articles) > 0:
            for article in articles:
                item += 1
                matches = re.compile('<div class="picture-content " data-post-id="(.+?)"> '
                                     '<a href="(.+?)" target="_self" title="(.+?)"> <img (.+?) '
                                     'data-src="(.+?)" data-srcset=').findall(article)
                for dpi, href, title, junk, img in matches:
                    title = title.replace('Replay', '').replace('NBA', '').replace('  ', ' ').strip()
                    addDir(title,
                           href,
                           3,
                           img,
                           __fanart__,
                           {'title': title,
                            'plot': title})
        else:
            break
        pgnum += 1
    url = url + 'page/%d' % (pgnum - 1)
    if url.find('page/') > 0:
        pgnumf = url.find('page/') + 5
        pgnum = int(url[pgnumf:]) + 1
        nxtpgurl = url[:pgnumf]
        nxtpgurl = "%s%s" % (nxtpgurl, pgnum)
        if item < 1 and pagenum <= 1:
            addDir('[COLOR red]No streams available! :([/COLOR]', url, 0, thumb, '', '')
        if item >= items_per_page:
            addDir('[COLOR green]>> Next page[/COLOR]', nxtpgurl, 2, thumb, '', '')
        else:
            addDir("[COLOR orange]That's all folks!!![/COLOR]", url, 0, thumb, '', '')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def submenu_old(url):
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
                matches = re.compile('<div class="picture-content " data-post-id="(.+?)"> '
                                     '<a href="(.+?)" target="_self" title="(.+?)"> <img (.+?) '
                                     'data-src="(.+?)" data-srcset=').findall(article)
                for dpi, href, title, junk, img in matches:
                    addDir(title.replace('Race Replay', '').strip(),
                           href,
                           3,
                           img,
                           __fanart__,
                           {'title': title,
                            'plot': title})
        page += 1
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def links_menu(name, url, thumb):
    format_text = {'1080p': '([COLOR orange]1080[/COLOR])',
                   '720p': '([COLOR orange]720[/COLOR])',
                   '480p': '([COLOR orange]480[/COLOR])',
                   '360p': '([COLOR orange]360[/COLOR])',
                   'Main Video': '',
                   'Server 2 -': '',
                   'Server 3 -': '',
                   ' -': '',
                   '  ': ' '}
    resp = commontasks.get_html(url)
    matches = re.compile('<a id="video-server-(.+?)" class="" href="(.+?)"><i class="fas fa-play"></i>(.+?)</a>').findall(resp)
    for junk, href, label in matches:
        menu_fanart = __fanart__
        for item in format_text:
            label = label.replace(item, format_text[item]).strip()
        addDir(name.replace('([COLOR orange]720[/COLOR])', '') + ' ' + label.replace('HD', '').replace(' 1080p', ''),
               href,
               4,
               thumb,
               menu_fanart,
               {'title': label,
                'plot': label})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_streams(name, url, thumb):
    format_text = {'1080P': '([COLOR orange]1080[/COLOR])',
                   '720P': '([COLOR orange]720[/COLOR])',
                   '480P': '([COLOR orange]480[/COLOR])',
                   '360P': '([COLOR orange]360[/COLOR])'}
    format_text = {'1080P': '([COLOR orange]1080[/COLOR])',
                   '720P': '([COLOR orange]720[/COLOR])',
                   '480P': '([COLOR orange]480[/COLOR])',
                   '360P': '([COLOR orange]360[/COLOR])',
                   'Server 1 -': '',
                   '- Main Video': '',
                   '  ': ' '}
    resp = commontasks.get_html(url)
    resp = commontasks.regex_from_to(resp, '<div id="player-embed">', '</div>')
    matches = re.compile('<iframe (.+?) src="(.+?)"').findall(resp)
    resp = commontasks.get_html(matches[0][1])
    resp = commontasks.regex_from_to(resp, 'JuicyCodes.Run(', ');</script>')
    resp = 'JuicyCodes.Run%s)' % resp
    resp = unjuice.run(resp)
    resp = commontasks.regex_from_to(resp, 'sources:', ',tracks:')
    matches = re.compile('{"file":"(.+?)","label":"(.+?)","type":"(.+?)"}').findall(resp)
    name = name.replace(' HD 720p', '').replace(' HD 1080p', '').replace('([COLOR orange]720[/COLOR])', '').replace('Server 1 ', '').replace('Server 2 ', '').replace('Server 3 ', '').strip()
    menu_icon = thumb
    menu_fanart = __fanart__
    for url, label, stype in matches:
        for item in format_text:
            label = label.replace(item, format_text[item]).strip()
        addDir((name + ' ' + label).replace(' NA', ' ([COLOR red]No longer available![/COLOR])'),
               url,
               5,
               menu_icon,
               menu_fanart,
               {'title': name,
                'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_stream(name, url, thumb):
    sources = []
    label = name
    format_text = [' ([COLOR orange]',
                   '[/COLOR])',
                   '1080',
                   '720',
                   '480',
                   '360']

    hosted_media = urlresolver.HostedMediaFile(url=url,title=name)
    sources.append(hosted_media)
    source = urlresolver.choose_source(sources)
    for item in format_text:
        name = name.replace(item, '')
    if source:
        vidlink = source.resolve()
        play_stream(name, vidlink, thumb)
    else:
        play_stream(name, url, thumb)


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


def addDir(name, url, mode, iconimage, fanart=False, infoLabels=True, account=None, player=None, embedid=None):
    u = sys.argv[0] + "?url=" + commontasks.urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + commontasks.urllib.quote_plus(name) + "&account=" + str(account) + "&player=" + str(player) + "&embedid=" + str(embedid) + "&thumb=" + str(iconimage)
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
    account = int(params["account"])
except:
    pass
try:
    player = params["player"]
except:
    pass
try:
    embed_id = params["embedid"]
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
    if url is not None:
        play_stream(_stream_name, url, __icon__)
elif mode ==2:
    submenu(url)
elif mode ==3:
    links_menu(name, url, thumb)
elif mode == 4:
    get_streams(name, url, thumb)
elif mode == 5:
    get_stream(name, url, thumb)
