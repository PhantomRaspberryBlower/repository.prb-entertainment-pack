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
# Description: Streams Forumla 1 races since 2014

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
    content = commontasks.regex_from_to(resp, '<a title="Formula 1 Race" ', '</ul></li>')
    menus = re.compile('<a target="_blank" rel="noopener noreferrer" href="(.+?)" '
                       'itemprop="url"><span itemprop="name">(.+?)</span></a></li>').findall(content)
    for url, name in menus:
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
                    addDir(title.replace('Race Replay', '').strip(),
                           href,
                           2,
                           img,
                           __fanart__,
                           {'title': title,
                            'plot': title})
        page += 1
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def links_menu(name, url, thumb):
    resp = commontasks.get_html(url)
    resp = commontasks.regex_from_to(resp, '<div class="streaming"', '<div class="tab-content"')
    matches = re.compile('<div class="tab-title(.+?)"><a href="(.+?)">(.+?)</a></div>').findall(resp)
    for junk, href, title in matches:
        if not ('720p' in title or '/' in title or 'LINKS' in title):
            addDir(name + ' ' + title.replace('HD', '').replace(' 1080p', '').replace('BTSport', '').replace('&#8211;', ''),
                   url + href,
                   3,
                   thumb,
                   __fanart__,
                   {'title': title,
                    'plot': title})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_streams(name, url, thumb):
    format_text = {'1080P': '([COLOR orange]1080[/COLOR])',
                   '720P': '([COLOR orange]720[/COLOR])',
                   '480P': '([COLOR orange]480[/COLOR])',
                   '360P': '([COLOR orange]360[/COLOR])'}
    resp = commontasks.get_html(url)
    resp = commontasks.regex_from_to(resp, '<div class="tab-content">', '</div>')
    matches = re.compile('<iframe src="(.+?)"').findall(resp)
    resp = commontasks.get_html('https:' + str(matches[0]))
    resp = commontasks.regex_from_to(resp, 'JuicyCodes.Run(', ');</script>')
    resp = 'JuicyCodes.Run%s)' % resp
    resp = unjuice.run(resp)
    resp = commontasks.regex_from_to(resp, 'sources:', ',tracks:')
    matches = re.compile('{"file":"(.+?)","label":"(.+?)","type":"(.+?)"}').findall(resp)
    name = name.replace(' HD 720p', '').replace(' HD 1080p', '')
    menu_icon = thumb
    menu_fanart = __fanart__
    for url, label, stype in matches:
        for item in format_text:
            label = label.replace(item, format_text[item])
        addDir((name + ' ' + label).replace(' NA', ' ([COLOR red]No longer available![/COLOR])'),
               url,
               4,
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
    links_menu(name, url, thumb)
elif mode == 3:
    get_streams(name, url, thumb)
elif mode == 4:
    get_stream(name, url, thumb)
