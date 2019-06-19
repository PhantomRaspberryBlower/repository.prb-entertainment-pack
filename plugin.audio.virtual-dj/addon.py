import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
import urllib
import urllib2
import datetime
import re

# Written by:	Phantom Raspberry Blower
# Date:		21-02-2017
# Description:	Addon for listening to Virtual DJ live broadcasts

# Get addon details
__addon_id__ = 'plugin.audio.virtual-dj'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = "Phantom Raspberry Blower"
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

# Get localized language words
__language__ = __addon__.getLocalizedString
_something_wicked_happened = __language__(30002)
_error = __language__(30003)
_failed_to_download = __language__(30004)
_internet_radio = __language__(30005)

image_path = 'special://home/addons/' + __addon_id__ + '/resources/media/'

category_list = ["DJ's"]

dj_list = ['DJ Bulis']

url = 'http://virtualdjradio.com:8000/'


def _get_url(url):
    """
    Download url and remove carriage return
    and tab spaces from page
    """
    req = urllib2.Request(url)
    req.add_header('User-Agent',
                   'Mozilla/5.0 (Windows; '
                   'U; Windows NT 5.1; en-GB; '
                   'rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def get_links(name, url, icon, fanart):
    """
    Fetch user's compression format and bitrate settings.
    Download links to the audio stream location.
    """
    response = _get_url(url).replace('(', '').replace(')','')
    temp = re.compile('<td class="tnl"><a href="(.+?)" title="MP3 @ '
    	              '128 kbps">(.+?)</a> <a href="(.+?)">Stream '
    	              'Login</a> <a href="(.+?)"><img border="0" '
    	              'title="Listen to Stream" alt="Listen to '
    	              'Stream" style="vertical-align:middle" '
    	              'src="images/listen.png"></a> <a href="(.+?)">'
    	              '<img border="0" title="Played History" '
    	              'alt="Played History" style="vertical'
    	              '-align:middle" src="images/history.png">'
    	              '</a></td></tr><tr><td><a target="_blank" '
    	              'href="(.+?)">(.+?)</a> MP3 @ 128 '
    	              'kbps<br></td></tr><tr><td valign="top">'
    	              'Current Song:&nbsp;<b><a href="(.+?)">'
    	              '(.+?)</a></b></td></tr>').findall(response)
    for index_url, stream_num, admin_url, listen_url, played_url, shoutcast_url, shoutcast_title, curr_song_url, curr_song in temp:
    	addDir(shoutcast_title, 'http://virtualdjradio.com:8000/' + listen_url, 2, __icon__, __fanart__, curr_song, False)


def addDir(name, url, mode, icon, fanart, desc, isFolder=False):
    """
    Display a list of links
    """
    u = (sys.argv[0] + '?url=' + urllib.quote_plus(url) +
         '&mode=' + str(mode) + '&name=' + urllib.quote_plus(name) +
         '&icon=' + str(icon) + '&fanart=' + str(fanart) + "&mode=" + str(mode))
    ok = True
    liz = xbmcgui.ListItem(name,
                           iconImage="DefaultFolder.png",
                           thumbnailImage=icon)
    # Set a fanart image for the list item.
    liz.setProperty('fanart_image', fanart)

    # Set additional info for the list item.
    liz.setInfo(type='music',
                infoLabels={'title': name,
                            'album': __addonname__,
                            'artist': name,
                            'genre': _internet_radio,
                            'year': 2015
                            }
                )
    liz.setInfo(type='video',
                infoLabels={'title': name,
                            'genre': _internet_radio,
                            'plot': desc,
                            'year': 2015,
                            'status': 'Live',
                            'mediatype': 'musicvideo'
                            }
                )
    ok = xbmcplugin.addDirectoryItem(handle=__handle__,
                                     url=u,
                                     listitem=liz,
                                     isFolder=isFolder)
    return ok


def play_audio(name, url, icon, fanart):
    """
    Create a list item to the audio stream and
    start playing the audio stream.
    """
    if xbmc.Player().isPlayingAudio:
        xbmc.Player().stop()
    response = _get_url(url)
    temp = re.compile('File1=(.+?)\nTitle1=').findall(response)
    for item_url in temp:
        liz = xbmcgui.ListItem(str(name),
                               iconImage='icon.png',
                               thumbnailImage=icon)
        # Set a fanart image for the list item.
        liz.setProperty('fanart_image', fanart)
        xbmc.Player().play(item_url, liz, False)


def get_params():
    """
    Get the current parameters
    :return: param[]
    """
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring[1:])>=1:
        params=paramstring[1:]
        pairsofparams=params.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param


def msg_notification(heading, message, icon, duration):
    # Show message notification
    dialog = xbmcgui.Dialog()
    dialog.notification(heading, message, icon, duration)


def message(message, title):
    # Display message to user
    dialog = xbmcgui.Dialog()
    dialog.ok(title, message)

# Define local variables
params = get_params()
url = None
name = None
mode = None
icon = None
fanart = None

# Parse the url, name, mode, icon and fanart parameters
try:
    url = urllib.unquote_plus(params['url'])
except:
    pass
try:
    name = urllib.unquote_plus(params['name'])
except:
    pass
try:
    mode = int(params['mode'])
except:
    pass
try:
    icon = urllib.unquote_plus(params['icon'])
except:
    pass
try:
    fanart = urllib.unquote_plus(params['fanart'])
except:
    pass

# Route the request based upon the mode number
if mode is None or url is None or len(url) < 1:
    get_links("Name", 'http://virtualdjradio.com:8000/index.html', '', '')
elif mode == 1:
    _default_image = fanart
    get_links(name, url, icon, fanart)
elif mode == 2:
    play_audio(name, url, icon, fanart)

xbmcplugin.endOfDirectory(__handle__)
