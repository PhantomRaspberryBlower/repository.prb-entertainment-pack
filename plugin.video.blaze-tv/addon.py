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
from datetime import datetime

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-12-2017
# Description: Addon for watching Blaze TV on demand

# Get addon details
__addon_id__ = 'plugin.video.blaze-tv'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
__baseurl__ = 'http://www.blaze.tv'

# Get localized language text
__language__ = __addon__.getLocalizedString
_unable_to_download_page = __language__(30101)
_error = __language__(30102)
_something_wicked_happened = __language__(30103)
_unable_to_download_stream = __language__(30104)
_no_stream_available = __language__(30105)
_no_stream = __language__(30106)
_blaze_live_title = __language__(30107)
_blaze_live_desc = __language__(30108)
_blaze_catchup_title = __language__(30109)
_blaze_catchup_desc = __language__(30110)
_blaze_series_title = __language__(30111)
_blaze_series_desc = __language__(30112)
_blaze_guide_title = __language__(30113)
_blaze_guide_desc = __language__(30114)

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


def get_api_key(url, account):
    api_key = ''
    html = get_html(url).replace('\n', '').replace('\t', '').replace('  ', '')
    host = regex_from_to(html, '"cdn_host": "', '",')
    api_key = regex_from_to(html, '"apiKey": "', '"}')
    match = re.compile('"cdn_host": "(.+?)","apiKey": "(.+?)"}').findall(html)
    return api_key


def get_stream_desc(vidid):
    desc = ''
    url = 'http://www.blaze.tv/catchup/watch/' + vidid
    html = get_html(url)
    html = regex_from_to(html, '<div class="caption caption-big">', '</div>').replace('\n', '').replace('\t', '').replace('  ', '')
    match = re.compile('<h3>(.+?)</h3>(.+?)<p>(.+?)</p>(.+?)<p>(.+?)</p>').findall(html)
    for title, junk1, aired, junk2, plot in match:
        return plot


def get_video_resolution(bitrate):
    if bitrate == '968704':
        return '(512x288)'
    elif bitrate == '1327104':
        return '(640x360)'
    elif bitrate == '1974272':
        return '(1024x576)'
    elif bitrate == '3203072':
        return '(1280x720)'
    elif bitrate == '5251072':
        return '(1920x1080)'
    else:
        return '(%d kbps)' % (int(bitrate) / 1024)


def parse_season_episode(name):
    try:
        name = name.replace('Series', 'Season').replace('Season ', 'Season:').replace('Episode ', 'Episode:')
        try:
            season = int(regex_from_to(name, 'Season:', ' '))
        except:
            season = int(regex_from_to(name, 's', 'e'))
        try:
            episode = int(name[name.find('Episode:') + 8:])
        except:
            episode = int(name[name.find('e')+1])
        return season, episode
    except:
        return 0, 0


def live():
    url = 'http://www.blaze.tv/assets/blaze/js/live.js'
    html = get_html(url)
    link = 'd1ow4ie79fojl1'
    url = 'http://%s.cloudfront.net/blaze/live.m3u8' % link
    html = get_html(url)
    match = re.compile('#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=(.+?),(.+?)\n(.+?)\n').findall(html)
    info_labels = {'title': "live"}
    for bandwidth, crap, link in reversed(match):
        add_directory('%s %s' % (name, get_video_resolution(bandwidth)),
                      url.replace('live.m3u8', link),
                      8,
                      __icon__,
                      __fanart__,
                      infoLabels=info_labels,
                      isPlayable=False,
                      isFolder=False)


def stream_links(name, vidid):
    stream_url = ''
#    url = 'http://www.blaze.tv/assets/blaze/js/live.js'
    url = 'http://www.blaze.tv/catchup/watch/' + vidid
    html = get_html(url)
    fanart = regex_from_to(html, "background:url", " no-repeat")
    fanart = fanart.replace("('", "").replace("')", "")
    icon = fanart
    container = regex_from_to(html, '<div class="caption caption-big">', '</div>')
    title = regex_from_to(container, '<h3>', '</h3>')
    duration = regex_from_to(container, '<p>', '</p>')
    duration = duration.split(" | ")
    duration = regex_from_to(duration[2], "", " ")

    season = "1"
    episode = "1"
    plot = "Plot"
    stream_url = url
    icon = __icon__
    fanart = __fanart__
    link = 'd2q1b32gh59m9o'
#    link = regex_from_to(html, 'https://', '.cloudfront.net/')
    client = 'blaze'
    call_back = 'ssmp'
    vid_type = 'vod'
#    api_key = get_api_key('https://%s.cloudfront.net/configs/config.blaze.js' % link, client)
    api_key = '6Pr3Uj2Fo3Ix7Rb9Ze9Ro4Ez2Eq7Sy'
    link = 'd2q1b32gh59m9o'
    doc_format = 'jsonp'
    url = 'https://%s.cloudfront.net/player/config?callback=%s&client=%s&type=%s&apiKey=%s&videoId=%s&format=%s&callback=jQuery2030972595045945138_1535666366374&_=1535666366375' % (link, call_back, client, vid_type, api_key, vidid, doc_format)
    html = get_html(url)
    client_id  = regex_from_to(html, '"id":', ',')
    stream_url = regex_from_to(html, '"hls":"', '",').replace('\/', '/')
    fanart = regex_from_to(html, '"poster":"', '",').replace('\/', '/')
    icon = fanart
    context = regex_from_to(html, '"context":"', '",')
    title = regex_from_to(html, '"context":"vod","title":"', '"').replace('\/', '/')
    plot = get_stream_desc(vidid)
    duration = regex_from_to(html, '"duration":"', '",')
    season, episode = parse_season_episode(name)
    html = get_html(stream_url)

    match = re.compile('#EXT-X-STREAM-INF:BANDWIDTH=(.+?),(.+?)\n(.+?)\n').findall(html)
    info_labels = {'title': title,
                   'duration': duration,
                   'season': season,
                   'episode': episode,
                   'plot': plot,
                   'mediatype': 'episode'}
    for bandwidth, crap, link in reversed(match):
        add_directory('%s %s' % (name, get_video_resolution(bandwidth)),
                      stream_url.replace('playlist.m3u8', link),
                      8,
                      icon,
                      fanart,
                      infoLabels=info_labels,
                      isPlayable=False,
                      isFolder=False)


def catchup(url, index=0):
    if url.find('page=') > 0:
        pgnumf = url.find('page=') + 5
        pageno = int(url[pgnumf:])
        nxtpgurl = url[:pgnumf]
    html = get_html(url).replace('\n', '').replace('\t', '').replace('  ', '')
    html = regex_from_to(html, '<!-- Video on Demand -->', '<!-- /.container -->')
    match = re.compile('<div class="col-sm-6 col-md-4 wrapper-item"(.+?)<div class="item">(.+?)<a '
                       'href="(.+?)">(.+?)<img class="img-responsive" alt="(.+?)" src="(.+?)">(.+?)data'
                       '-uvid="(.+?)" data-episode="(.+?)" >(.+?)<span class="caption-title">(.+?)</'
                       'span>(.+?)<span class="caption-description">(.+?)</span>').findall(html)
    for junk1, junk2, link, junk3, alt, img, junk4, du, de, junk5, name, junk6, desc in match:
        now = datetime.now()
        plot = desc
        season, episode = parse_season_episode(de.replace(name, ""))
#        title = '%s Season:%d Episode:%d' % (de[:de.find(' Series')], season, episode)
        title = '%s Season:%d Episode:%d' % (name, season, episode)
        try:
            aired = datetime.strptime(desc + ' ' + str(now.year), '%H:%M %A, %d %B %Y').strftime('%Y-%m-%d %H:%M')
        except:
            aired = ''
        info_labels = {'title': name,
                       'season': season,
                       'episode': episode,
                       'aired': aired,
                       'plot': '%s. Broadcasted on Blaze - %s' % (title, plot),
                       'mediatype': 'episode'}
        add_directory(title, du, 3, img, infoLabels=info_labels, isPlayable=True, isFolder=True)
    if index < 8 and len(match) > 8:
        catchup(nxtpgurl + str(pageno + 1), index + 1)
    else:
        if url.find('page=') > 0 and len(match) > 8:
            pgnumf = url.find('page=') + 5
            pgnum = int(url[pgnumf:]) + pgnumf + 1
            nxtpgurl = url[:pgnumf]
            nxtpgurl = "%s%s" % (nxtpgurl, str(pageno + 1))
            add_directory('[COLOR orange]>> Next page[/COLOR]', nxtpgurl, 2, __icon__, isPlayable=True, isFolder=True)


def series(url, index=0):
    if url.find('page=') > 0:
        pgnumf = url.find('page=') + 5
        pageno = int(url[pgnumf:])
        nxtpgurl = url[:pgnumf]
    html = get_html(url).replace('\n', '').replace('\t', '').replace('  ', '')
    html = regex_from_to(html, '<!-- Video on Demand -->', '<!-- /.container -->')
    match = re.compile('<div class="col-sm-4 col-md-4 wrapper-item"(.+?)<div class="item">(.+?)<a '
                       'href="(.+?)">(.+?)<img class="img-responsive" alt="(.+?)" src="(.+?)">(.+?)<div class="series-folder text-center">(.+?)<'
                       'span>(.+?)</span>').findall(html)
    for junk1, junk2, link, junk3, alt, img, junk4, junk5, num in match:
        link = __baseurl__ + link
        if int(num) > 1:
            title = '%s ([COLOR orange]%s episodes[/COLOR])' % (alt, num)
            plot = '%s Episodes of %s' % (num, alt)
        else:
            title = '%s ([COLOR orange]%s episode[/COLOR])' % (alt, num)
            plot = '%s Episode of %s' % (num, alt)
        info_labels = {'title': title,
                       'plot': plot}
        add_directory(title, link, 5, img, infoLabels=info_labels, isPlayable=True, isFolder=True)
    if index < 8 and len(match) > 8:
    	try:
            series(nxtpgurl + str(pageno + 1), index + 1)
        except:
        	pass
    else:
        if url.find('page=') > 0 and len(match) > 8:
            pgnumf = url.find('page=') + 5
            pgnum = int(url[pgnumf:]) + pgnumf + 1
            nxtpgurl = url[:pgnumf]
            nxtpgurl = "%s%s" % (nxtpgurl, str(pageno + 1))
            add_directory('[COLOR orange]>> Next page[/COLOR]', nxtpgurl, 2, __icon__, isPlayable=True, isFolder=True)


def play_stream(name, url, thumbnail):
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': thumbnail})
    xbmc.Player().play(url, liz)
    sys.exit("Stop Video")


def episodes(url):
    html = get_html(url.replace(' ', '%20')).replace('\n', '').replace('\t', '').replace('  ', '')
    html = regex_from_to(html, '<div class="section-title seasons">', '</div>')
    match = re.compile(' href="(.+?)">(.+?)</a>').findall(html)
    for link, num in match:
        title = 'Season: %s' % num
        url = __baseurl__ + link
        img = ''
        html = get_html(url.replace(' ', '%20')).replace('\n', '').replace('\t', '').replace('  ', '')
        html = regex_from_to(html, '<div id="series-carousel" class="carousel slide" data-interval="false">', '<div class="section-title">')
        match = re.compile('<div class="item">(.+?)<a href="(.+?)">(.+?)<img class="img-responsive" alt="(.+?)" '
                           'src="(.+?)">(.+?)<span class="caption-title">(.+?)</span>(.+?)<span class="caption-'
                           'description">(.+?)</span>').findall(html)
        for junk1, href, junk2, alt, img, junk3, title, junk4, desc in match:
            image = img
            desc = desc.replace('Season ', 'Season:').replace('Episode ', 'Episode:').replace(' | ', ' ')
            url = __baseurl__ + href
            html = get_html(url.replace(' ', '%20')).replace('\n', '').replace('\t', '').replace('  ', '')
            vid_id = regex_from_to(html, 'data-uvid="', '"></i>')
            season, episode = parse_season_episode(desc)
            info_labels = {'title': title,
                           'season': season,
                           'episode': episode,
                           'mediatype': 'episode'}
            add_directory(title + ' ' + desc, vid_id, 3, image, infoLabels=info_labels, isPlayable=True, isFolder=True)


def guide(url):
    html = get_html(url).replace('\n', '').replace('\t', '').replace('  ', '')
    html = regex_from_to(html, '<ul class="dropdown-menu">', '</ul>')
    match = re.compile('<a href="(.+?)"(.+?)>(.+?)</a>').findall(html)
    for href, junk, title in match:
        if title == "Today":
            title = '[COLOR orange]%s[/COLOR]' % title
        add_directory(title, __baseurl__ + href, 7, __icon__, __fanart__, isPlayable=True, isFolder=True)


def guide_day(url):
    html = get_html(url).replace('\n', '').replace('\t', '').replace('  ', '')
    html = regex_from_to(html, '<div class="guide-container">', '</div><!-- page-wrap -->')
    match = re.compile('class="starting-time">(.+?)</div>(.+?)<div class="image-show">(.+?)alt="" src'
                       '="(.+?)">(.+?)<span class="title">(.+?)</span>(.+?)class="episode"><p>(.+?)</p>').findall(html)
    for time, junk1, info, src, junk3, title, junk4, episode in match:
        time = time.replace('<br/>', '')
        season, episode = parse_season_episode(episode)
        se = 'Season: %d Episode: %d' % (season, episode)
        try:
            href = regex_from_to(info, 'href="', '"')
        except:
            href = ''
        try:
            du = regex_from_to(info, 'data-uvid="', '"')
        except:
            du = ''
        if time == "Now":
            mode = 1
        else:
            mode = 3
        if href == '':
            url = du
        else:
            url = __baseurl__ + href
        info_labels = {'title': title,
                       'season': season,
                       'episode': episode,
                       'mediatype': 'episode'}
        title = '[COLOR orange]%s[/COLOR] - %s %s' % (time, title, se)
        add_directory(title, du, mode, src, src, infoLabels=info_labels, isPlayable=True, isFolder=True)


def menu():
    # Catchup menu item
    add_directory('Catchup',
                  __baseurl__ + '/catchup?page=0',
                  2,
                  os.path.join(image_path, 'catchup.png'),
                  os.path.join(image_path, 'catchup.jpg'),
                  {'title': _blaze_catchup_title,
                   'plot': _blaze_catchup_desc},
                  isPlayable=True,
                  isFolder=True)

    # Series menu item
    add_directory('Series',
                  __baseurl__ + '/series?page=0',
                  4,
                  os.path.join(image_path, 'series.png'),
                  os.path.join(image_path, 'series.jpg'),
                  {'title': _blaze_series_title,
                   'plot': _blaze_series_desc},
                  isPlayable=True,
                  isFolder=True)

    # Guide menu item
    add_directory('Guide',
                  __baseurl__ + '/guide/',
                  6,
                  os.path.join(image_path, 'guide.png'),
                  os.path.join(image_path, 'guide.jpg'),
                  {'title': _blaze_guide_title,
                   'plot': _blaze_guide_desc},
                  isPlayable=True,
                  isFolder=True)

    # Live menu item
    add_directory('[COLOR green]Live[/COLOR]',
                  __baseurl__ + '/live/',
                  1,
                  os.path.join(image_path, 'live.png'),
                  os.path.join(image_path, 'live.jpg'),
                  {'title': _blaze_live_title,
                   'plot': _blaze_live_desc},
                  isPlayable=True,
                  isFolder=True)


def add_directory(name, url, mode, thumbnail=False, fanart=False, infoLabels=False, isPlayable=False, isFolder=False):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + "&thumb=" + urllib.quote_plus(thumbnail)
    ok = True
    liz = xbmcgui.ListItem(name)
    if not infoLabels:
        infoLabels = {"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if isPlayable:
        liz.setProperty('IsPlayable', 'true')
    if not fanart:
        fanart = __fanart__
    if not thumbnail:
        thumbnail = __icon__
    liz.setArt({'fanart': fanart,
                'thumb': thumbnail})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder, totalItems=10)
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
    thumb = urllib.unquote(params["thumb"])
except:
    pass

#message("Mode: %s\nURL: %s\nName: %s" % (mode, url, name), "Test")

if url == None and mode != None:
    message(_no_stream_available, _no_stream)
elif mode == None or url == None or len(url) < 1:
    menu()
elif mode == 1:
    live()
elif mode == 2:
    catchup(url)
elif mode == 3:
    stream_links(name, url)
elif mode == 4:
    series(url)
elif mode == 5:
    episodes(url)
elif mode == 6:
    guide(url)
elif mode == 7:
    guide_day(url)
elif mode == 8:
    if not thumb:
        thumb = __icon__
    play_stream(name, url, thumb)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
