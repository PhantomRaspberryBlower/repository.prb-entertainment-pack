#!/usr/bin/python

import urllib
import urllib2
import xbmcplugin
import xbmcaddon
import xbmcgui
import os
import re
import sys
from HTMLParser import HTMLParser
from datetime import datetime, timedelta

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-12-2017
# Description: Addon for watching Quest TV on demand

# Get addon details
__addon_id__ = 'plugin.video.quest-tv'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
__baseurl__ = 'https://www.questod.co.uk'

# Get localized language text
__language__ = __addon__.getLocalizedString
_shows = __language__(30101)
_shows_title = __language__(30102)
_shows_desc = __language__(30103)
_genres = __language__(30104)
_genres_title = __language__(30105)
_genres_desc = __language__(30106)
_guide = __language__(30107)
_guide_title = __language__(30108)
_guide_desc = __language__(30109)
_live = __language__(30110)
_live_title = __language__(30111)
_live_desc = __language__(30112)
_no_streams_available = __language__(30113)
_something_wicked_happened = __language__(30114)
_unable_to_download_page = __language__(30115)
_error = __language__(30116)
_unable_to_download_stream = __language__(30117)


# Define local variables
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
                                __addon_id__ + '/resources/media/'))

hp = HTMLParser()

def message(message, title):
    # Display message to user
    dialog = xbmcgui.Dialog()
    dialog.ok(title, message)


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


def play_stream(name, url, thumbnail):
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': thumbnail})
    xbmc.Player().play(url, liz)
    sys.exit("Stop Video")


def menu():
    # Shows menu item
    addDir(_shows,
           __baseurl__ + '/shows',
           1,
           os.path.join(image_path, 'shows.png'),
           __fanart__,
           {'title': _shows_title,
            'plot': _shows_desc})
    # Genres menu item
    addDir(_genres,
           __baseurl__ + '/live/quest',
           2,
           os.path.join(image_path, 'genres.png'),
           __fanart__,
           {'title': _genres_title,
            'plot': _genres_desc})
    # Guide menu item
    addDir(_guide,
           __baseurl__ + '/live/quest',
           3,
           os.path.join(image_path, 'guide.png'),
           __fanart__,
           {'title': _guide_title,
            'plot': _guide_desc})
    # Live menu item
    addDir(_live,
           __baseurl__ + '/live/quest',
           4,
           os.path.join(image_path, 'live.png'),
           __fanart__,
           {'title': _live_title,
            'plot': _live_desc})


def shows_menu(url):
    response = get_html(url)
    match = re.compile('<a class="sub-filter-navigation__link(.+?) href="(.+?)">(.+?)</a></div>').findall(response)
    for junk, link, title in match:
        addDir(title.replace('&amp;', '&').replace('&#x27;', "'"), __baseurl__ + link, 11, os.path.join(image_path, 'shows.png'))


def shows(url):
    response = get_html(url)
    match = re.compile('<svg><use xlink:href="#placeholder">'
                       '</use></svg><img class="grid-item__image" src="(.+?)" alt="(.+?)"/></div>'
                       '<div class="grid-item__overlay"></div></div><div to="(.+?)" class="grid-item__link">'
                       '<h3 class="grid-item__title">(.+?)</h3><p class="grid-item__shortdesc">(.+?)</p></div>'
                       '</a></li>').findall(response)
    for img, alt, link, title, shortdesc in match:
        infoLabels = {"title": title.replace('&amp;', '&').replace('&#x27;', "'"),
                      "plot": shortdesc.replace('&amp;', '&').replace('&#x27;', "'")}
        icon = img
        fanart = img.replace('w=480', 'w=1250')
        addDir(title.replace('&amp;', '&').replace('&#x27;', "'"), __baseurl__ + link, 12, icon, fanart, infoLabels)


def parse_season_episode(name):
    try:
        name = name.replace('S', 'Season').replace('Season', 'Season:').replace('E', 'Episode:')
        season = int(regex_from_to(name, 'Season:', '.Episode'))
        episode = int(regex_from_to(name, 'Episode:', ': '))
        return season, episode
    except:
        return 0, 0


def show_episodes(url):
    response = get_html(url)
    match = re.compile('<svg><use xlink:href="#placeholder"></use></svg><img class="vertical-'
                       'list-item__image" src="(.+?)" alt="(.+?)"/></div><div class="video-'
                       'play-icon"><svg class="video-play-icon__svg"><use xlink:href="#play-'
                       'icon"></use></svg></div>(.+?)<div class="vertical-list-item__content">'
                       '<h3 class="vertical-list-item__title"><a href="(.+?)">(.+?)</a></h3>'
                       '<div class="vertical-list-item__description">(.+?)</div><div '
                       'class="vertical-list-item__details"><span>Duration</span>: '
                       '(.+?) Min</div>').findall(response)
    for img, alt, junk, link, title, shortdesc, dur in match:
        season, episode = parse_season_episode(title)
        duration = int(dur.replace('<!-- -->', ''))*60
        infoLabels = {'title': title.replace('&amp;', '&').replace('&#x27;', "'"),
                      'duration': duration,
                      'season': season,
                      'episode': episode,
                      'plot': shortdesc.replace('&amp;', '&').replace('&#x27;', "'"),
                      'mediatype': 'episode'}
        icon = img
        fanart = img.replace('w=480', 'w=1250')
        addDir(title.replace('&amp;', '&').replace('&#x27;', "'"), __baseurl__ + link, 13, icon, fanart, infoLabels)
    if len(match) < 1:
        addDir(_no_streams_available, __baseurl__ + '/shows', 1, __icon__)


def episode_streams(url, name, thumb):
    response = get_html(url)
    match = re.compile('streamUrlHls":"(.+?)","streamUrlDash"').findall(response)
    if len(match) > 0:
        play_stream(name, match[0], __icon__)


def shows_a_z():
    url = 'https://www.questod.co.uk/shows/a-z'
    response = get_html(url)
    match = re.compile('{"id":"(.+?)","title":"(.+?)","url":"(.+?)"},').findall(response)
    for ident, title, link in match:
        addDir(title.replace('&amp;', '&').replace('&#x27;', "'"), __baseurl__ + link, 12, __icon__)


def guide(url):
    response = get_html(url)
    match = re.compile('<div class="sub-filter-navigation__item">'
                       '<a class="sub-filter-navigation__link(.+?)" '
                       'href="(.+?)">(.+?)</a></div>').findall(response)
    for junk, link, title in match:
        if (title != "QUEST" and title != "QUEST RED"):
            if title == "Today":
                title = '[COLOR orange]' + title + '[/COLOR]'
                link = '/live/quest/' + datetime.now().strftime("%Y-%m-%d")
            addDir(title, __baseurl__ + link, 31, os.path.join(image_path, 'guide.png'))


def guide_menu(url):
    qdate = url.replace('https://www.questod.co.uk/live/quest/', '')
    response = get_html('https://www.questod.co.uk/api/schedule?timerange=%s&offset=-60&channelId=quest' % qdate)
    match = re.compile('{"id"(.+?)}').findall(response)
    for item in match:
        match2 = re.compile(':"(.+?)","title":"(.+?)","utcStart":"(.+?)","duration":(.+?)'
                           ',"description":"(.+?)","seasonNumbers":(.+?),"episodeNumbers":(.+?)'
                           ',"url":"(.+?)"(.+?)"videoName":"(.+?)","image":{"height":(.+?)'
                           ',"width":(.+?),"src":"(.+?)"').findall(item)
        for ident, title, start, duration, shortdesc, season, episode, url, vidurl, vidname, height, width, img in match2:
            if len(vidurl)> 1:
                vidurl = regex_from_to(vidurl, 'videoUrl":"', '",')
                utc_datetime = datetime.utcnow()
                ltc_datetime = datetime.now()
                stc_datetime = datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ')
                if utc_datetime < ltc_datetime:
                    dtc_datetime = (ltc_datetime - utc_datetime)
                    diffhours = dtc_datetime.seconds/60/60
                    rtc_datetime = stc_datetime + timedelta(hours=diffhours)
                else:
                    dtc_datetime = (utc_datetime - ltc_datetime)
                    diffhours = dtc_datetime.seconds/60/60
                    rtc_datetime = stc_datetime - timedelta(hours=diffhours)
                name = "[COLOR orange]%s[/COLOR] %s: Season %s Episode %s - %s" % (rtc_datetime.strftime("%H:%M"), title, season, episode, vidname)
                infoLabels = {'Title': title.replace('&amp;', '&').replace('&#x27;', "'"),
                              'duration': duration,
                              'season': season,
                              'episode': episode,
                              'plot': shortdesc.replace('&amp;', '&').replace('&#x27;', "'"),
                              'mediatype': 'episode'}
                icon = img
                fanart = img.replace('w=480', 'w=1250')
                addDir(name.replace('&amp;', '&').replace('&#x27;', "'"), __baseurl__ + vidurl, 13, icon, fanart, infoLabels)


def live(url):
#    url = 'https://dplaynordics-live-01.akamaized.net/questuk/14/1/dash/Quest/manifest.mpd?hdnts=st=1535747436~exp=1535833836~acl=/*~hmac=b36f0c3c7a2d0e78943be8b7b586b469ac9e8c4eea931ec2b324a1efb9d8045b&bw_start=800'
    live_url = 'https://www.questod.co.uk/channel/quest'
    response = get_html(live_url)
    match = re.compile('streamUrlHls":"(.+?)","streamUrlDash"').findall(response)
    if len(match) > 0:
        message(str(match[0]), "Match")
        play_stream(name, match[0], __icon__)


def live_menu(url):
    response = get_html(url)
    match = re.compile('<li class="epg__list__item"><a class="epg__list__item__linkwrapper" href(.+?)"><div class="epg__list__item__time"><span>(.+?)</span></div><div class="epg__list__item__image-column"><div class="epg__list__item__image-wrapper"><div class="item-thumbnail epg__list__item__image-container"><svg><use xlink:href="#placeholder"></use></svg><img class="epg__list__item__image" src="(.+?)" alt="(.+?)"></div><div class="epg__list__item__progress" style="width: 0%;"></div><div class="epg__list__item__overlay"></div><div class="epg__list__item__icon"><svg class="epg__list__item__icon__svg epg__list__item__icon__svg--play"><use xlink:href="#play2-icon"></use></svg></div></div></div><div to="(.+?)" class="epg__list__item__link"><h3 class="epg__list__item__title">(.+?)</h3><div class="epg__list__item__title-second-line"><span>(.+?)</span><span>(.+?)</span></div><p class="epg__list__item__shortdesc">(.+?)</p></div></a></li>').finall(response)
    for link, time, img, alt, to, title, se, title2, shortdesc in match:
        addDir(title.replace('&amp;', '&').replace('&#x27;', "'"), __baseurl__ + link, 31, icon, fanart, infoLabels)


def genres_menu(url):
    html = get_html(url)
    gens = regex_from_to(html, '<ul class="header__nav__dd__sublist header__nav__dd__sublist--one-column">', '</ul>')
    match = re.compile('<li><a href="(.+?)">(.+?)</a></li>').findall(gens)
    for link, title in sorted(match):
        addDir(title.replace('&amp;', '&').replace('&#x27;', "'"), __baseurl__ + link, 11, os.path.join(image_path, 'genres.png'))


def add_directory(name,url,mode,fanart,thumbnail,infoLabels):
    u=sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + "&thumb=" + urllib.quote_plus(thumbnail)
    ok=True
    liz=xbmcgui.ListItem(name)
    if not infoLabels:
        infoLabels = {'title': name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if not fanart:
        fanart=__fanart__
    liz.setArt({'fanart': fanart,
                'thumb': thumbnail})
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False, totalItems=10)
    return ok


def addDir(name, url, mode, iconimage, fanart=False, infoLabels=True, account=None, player=None, embedid=None):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + "&account=" + str(account) + "&player=" + str(player) + "&embedid=" + str(embedid) + "&thumb=" + str(iconimage)
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


def get_html(url, policy=None):
    header_dict = {}
    header_dict['Accept'] = 'application/json;pk=' + str(policy)
    header_dict['User-Agent'] = 'AppleWebKit/<WebKit Rev>'
    req = urllib2.Request(url, headers=header_dict)
    try:
        response = urllib2.urlopen(req)
        html = response.read()
        response.close()
    except urllib2.HTTPError:
        response = False
        html = False
    return html


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
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
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
    thumb = urllib.unquote(params["thumb"])
except:
    pass

# Message below used to test the addon
#message("Mode: %s\nURL: %s\nName: %s" % (mode, url, name), "Test")

if mode == None or url == None or len(url) < 1:
    menu()
elif mode == 1:
    shows_menu(url)
elif mode == 11:
    if name == "A-Z":
        shows_a_z()
    else:
        shows(url)
elif mode == 12:
    show_episodes(url)
elif mode == 13:
    episode_streams(url, name, thumb)
elif mode == 2:
    genres_menu(url)
elif mode == 3:
    guide(url)
elif mode ==31:
    guide_menu(url)
elif mode == 4:
    live(url)
elif mode == 41:
    live_menu(url)
elif mode == 8:
    if not thumb:
        thumb = __icon__
    play_stream(name, url, thumb)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
