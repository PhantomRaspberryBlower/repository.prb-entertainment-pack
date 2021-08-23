#!/bin/python

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
import os
import re
import cookielib
import threading

import urllib2

from resources.lib.artistinfo import ArtistInfo
from resources.lib import commontasks

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-02-2017
# Description: Addon for listening to Absolute Radio live broadcasts

# Get addon details
__addon_id__ = u'plugin.audio.absolute-radio'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = u'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
__baseurl__ = 'https://absoluteradio.co.uk/listen/links/'
__fanarturl__ = 'http://www.theaudiodb.com/api/v1/json/1/search.php?s='
__cookie_file__ = xbmc.translatePath(os.path.join('special://profile/addon_data/'
                                                  'plugin.audio.absolute-radio',
                                                  'cookies-absolute-radio'))

# Get localized language text
__language__ = __addon__.getLocalizedString
_login_success_title = __language__(30109)
_login_success_msg = __language__(30110)
_login_failed_title = __language__(30111)
_login_failed_msg = __language__(30112)
_artist_info = __language__(30113)
_unable_to_download_artist_info = __language__(30114)
_no_artist_name_present = __language__(30115)
_no_audio_stream = __language__(30116)
_settings = __language__(30117)
_ar_desc = __language__(30118)
_ar_cr_desc = __language__(30119)
_ar_80s_desc = __language__(30120)
_ar_60s_desc = __language__(30121)
_ar_70s_desc = __language__(30122)
_ar_90s_desc = __language__(30123)
_ar_00s_desc = __language__(30124)
_artist_info_desc = __language__(30125)
_settings_desc = __language__(30126)

# Get addon user settings
_compression_format = __addon__.getSetting('compression_format')
_hide_artist_info = __addon__.getSetting('hide_artist_info')
_hide_artist_artwork = __addon__.getSetting('hide_artist_artwork')

# Define local variables
g_default_image = None
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
	                            __addon_id__ + '/resources/media/'))
_ar_icon = os.path.join(image_path, 'absolute_radio.png')
_ar_fanart = os.path.join(image_path, 'absolute_radio_fanart.jpg')
_ar_cr_icon = os.path.join(image_path, 'absolute_radio_classic_rock.png')
_ar_cr_fanart = os.path.join(image_path,'absolute_radio_classic_rock_fanart.jpg')
_ar_80s_icon = os.path.join(image_path, 'absolute_radio_80s.png')
_ar_80s_fanart = os.path.join(image_path, 'absolute_radio_80s_fanart.jpg')
_ar_60s_icon = os.path.join(image_path, 'absolute_radio_60s.png')
_ar_60s_fanart = os.path.join(image_path, 'absolute_radio_60s_fanart.jpg')
_ar_70s_icon = os.path.join(image_path, 'absolute_radio_70s.png')
_ar_70s_fanart = os.path.join(image_path, 'absolute_radio_70s_fanart.jpg')
_ar_90s_icon = os.path.join(image_path, 'absolute_radio_90s.png')
_ar_90s_fanart = os.path.join(image_path, 'absolute_radio_90s_fanart.jpg')
_ar_00s_icon = os.path.join(image_path, 'absolute_radio_00s.png')
_ar_00s_fanart = os.path.join(image_path, 'absolute_radio_00s_fanart.jpg')
_artist_info_icon = os.path.join(image_path, 'artist_info.png')
_artist_info_fanart = os.path.join(image_path, 'artist_info_fanart.jpg')
_settings_icon = os.path.join(image_path, 'settings.png')
_settings_fanart = os.path.join(image_path, 'settings_fanart.jpg')

link_infos = {u'Absolute Radio':
             {'thumbs': _ar_icon,
              'fanart': _ar_fanart,
              'desc': _ar_desc,
              'urls': {'mp3': 'http://ais.absoluteradio.co.uk/absoluteradio.mp3',
                       'aac': 'http://ais.absoluteradio.co.uk/absoluteradio.aac',
                       'ogg': 'http://ais.absoluteradio.co.uk/absoluteradio.ogg'
                       }
              },
             u'Absolute Classic Rock':
             {'thumbs': _ar_cr_icon,
              'fanart': _ar_cr_fanart,
              'desc': _ar_cr_desc,
              'urls': {'mp3': 'http://ais.absoluteradio.co.uk/absoluteclassicrock.mp3',
                       'aac': 'http://ais.absoluteradio.co.uk/absoluteclassicrock.aac',
                       'ogg': 'http://ais.absoluteradio.co.uk/absoluteclassicrock.ogg'
                       }
              },
             u'Absolute Radio 80s':
             {'thumbs': _ar_80s_icon,
              'fanart': _ar_80s_fanart,
              'desc': _ar_80s_desc,
              'urls': {'mp3': 'http://ais.absoluteradio.co.uk/absolute80s.mp3',
                       'aac': 'http://ais.absoluteradio.co.uk/absolute80s.aac',
                       'ogg': 'http://ais.absoluteradio.co.uk/absolute80s.ogg'
                       }
              },
             u'Absolute Radio 60s':
             {'thumbs': _ar_60s_icon,
              'fanart': _ar_60s_fanart,
              'desc': _ar_60s_desc,
              'urls': {'mp3': 'http://ais.absoluteradio.co.uk/absolute60s.mp3',
                       'aac': 'http://ais.absoluteradio.co.uk/absolute60s.aac',
                       'ogg': 'http://ais.absoluteradio.co.uk/absolute60s.ogg'
                       }
              },
             u'Absolute Radio 70s':
             {'thumbs': _ar_70s_icon,
              'fanart': _ar_70s_fanart,
              'desc': _ar_70s_desc,
              'urls': {'mp3': 'http://ais.absoluteradio.co.uk/absolute70s.mp3',
                       'aac': 'http://ais.absoluteradio.co.uk/absolute70s.aac',
                       'ogg': 'http://ais.absoluteradio.co.uk/absolute70s.ogg'
                       }
              },
             u'Absolute Radio 90s':
             {'thumbs': _ar_90s_icon,
              'fanart': _ar_90s_fanart,
              'desc': _ar_90s_desc,
              'urls': {'mp3': 'http://ais.absoluteradio.co.uk/absolute90s.mp3',
                       'aac': 'http://ais.absoluteradio.co.uk/absolute90s.aac',
                       'ogg': 'http://ais.absoluteradio.co.uk/absolute90s.ogg'
                       }
              },
             u'Absolute Radio 00s':
             {'thumbs': _ar_00s_icon,
              'fanart': _ar_00s_fanart,
              'desc': _ar_00s_desc,
              'urls': {'mp3': 'http://ais.absoluteradio.co.uk/absolute00s.mp3',
                       'aac': 'http://ais.absoluteradio.co.uk/absolute00s.aac',
                       'ogg': 'http://ais.absoluteradio.co.uk/absolute00s.ogg'
                       }
              },
             _artist_info:
             {'thumbs': _artist_info_icon,
              'fanart': _artist_info_fanart,
              'desc': _artist_info_desc
              },
             _settings:
             {'thumbs': _settings_icon,
              'fanart': _settings_fanart,
              'desc': _settings_desc
              }
             }


def login_absolute_radio(username, password):
    """
    Login into absolute radio and save the cookie to the cookie jar
    subsequent login's will re-use the cookie.
    """
    cookie_jar = cookielib.LWPCookieJar(__cookie_file__)
    try:
        cookie_jar.load()
    except:
        pass
    cookies = cookie_jar
    if len(cookies) > 1:
        return True
    else:
        url = 'https://absoluteradio.co.uk/_ajax/account-process.php'
        values = {'emailfield': username,
                  'passwordfield': password,
                  'signinbutton': 'signin'}
        data = commontasks.urlencode(values)
        opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(cookies))
        response = opener.open(url, data)
        the_page = response.read()
        http_headers = response.info()
        # The login cookies should be contained in the cookies variable
        if len(cookies) > 1:
            cookie_jar.save(ignore_discard=True)
            commontasks.notification(_login_success_title,
                                     _login_success_msg, __icon__, 5000)
            return True
        else:
            commontasks.notification(_login_failed_title,
                                     _login_failed_msg, __icon__, 5000)
            return False


def main_menu():
    """
    Download categories from absolute radio
    and display a list of the stations
    """
    for key in sorted(link_infos.keys()):
        if (key != _artist_info) and (key != _settings):
            addDir(key,
                   link_infos[key]['urls']['mp3'],
                   1,
                   link_infos[key]['thumbs'],
                   link_infos[key]['fanart'],
                   link_infos[key]['desc'])

    if _hide_artist_info != 'true':
        addDir(_artist_info,
               'RunPlugin({0}?url=artistinfo&mode=2)',
               2,
               link_infos[_artist_info]['thumbs'],
               link_infos[_artist_info]['fanart'],
               link_infos[_artist_info]['desc'])
    addDir(_settings,
           'RunPlugin({0}?url=settings&mode=3)',
           3,
           link_infos[_settings]['thumbs'],
           link_infos[_settings]['fanart'],
           link_infos[_settings]['desc'])
    xbmcplugin.endOfDirectory(__handle__)


def get_links(name, url):
    """
    Fetch user's compression format and bitrate settings.
    Download links to the audio stream location.
    """
    response = commontasks.get_url(url).replace(' stream URLs', '')
    response = response.replace('\n', '').replace('\t', '').replace('  ', '')
    filter = re.compile('<h3>' + name +
                        '</h3>(.+?)</p>').findall(response)
    regex = '<strong>(.+?)</strong> <span class="display-url">(.+?)</span>'
    data = re.compile(regex).findall(str(filter))
    compression_format = _compression_format
    compression_format = _compression_format
    bitrate = None
    if compression_format == 'AAC':
        bitrate = __addon__.getSetting('bitrate.aac')
        compression_format = 'AAC+'
    elif compression_format == 'MP3':
        bitrate = __addon__.getSetting('bitrate.mp3')
    elif compression_format == 'Ogg Vorbis':
        bitrate = __addon__.getSetting('bitrate.ogg')
    elif compression_format == 'Ogg FLAC - Lossless':
        bitrate = __addon__.getSetting('bitrate.ogg-flac')
    elif compression_format == 'Opus':
        bitrate = __addon__.getSetting('bitrate.opus')
    sound_quality = '%s (%s)' % (compression_format, bitrate)
    for quality, link in data:
        if (quality.replace(':', '').replace('~', '') ==
                sound_quality.replace('- Lossless (1024kbps)', '1Mb')
                .replace('(', '')
                .replace('bps)', '')):
            return sound_quality, link


def play_audio(name, url, icon, fanart):
    """
    Start playing the audio stream.
    """
#    sound_quality, link = get_links(name, url)
#    response = commontasks.get_url(link)
#    files = re.compile('File1=(.+?)\n').findall(response)
#    titles = re.compile('Title1=(.+?)\n').findall(response)
    if xbmc.Player().isPlayingAudio:
        xbmc.Player().stop()
    liz = xbmcgui.ListItem(name,
                           iconImage='Icon.png',
                           thumbnailImage=icon)
    # Set a fanart image for the list item.
    liz.setProperty('fanart_image', fanart)
    xbmc.Player().play(url, liz, False)
    while not xbmc.Player().isPlayingAudio():
        xbmc.sleep(1)
    # Start thread to display current artist image
    thread = threading.Thread(target=show_artist_image, args=())
    thread.start()
#    sys.exit("Stop Video")


def get_artist_name(artist=None):
    """
    Parse artist name or current stream title
    """
    if artist is None:
        # Check audio atream is playing 
        if xbmc.Player().isPlayingAudio():
            # Get title of audio stream
            title = xbmc.Player().getMusicInfoTag().getTitle()
            if len(title) > 0:
                # Split artist name from stream title
                items = title.split(' - ')
                artist_name = items[1]
                if len(artist_name) > 1:
                    return artist_name
            else:
                # No artist name present
                commontasks.notification(_no_artist_name_present,
                                         _artist_info,
                                         __icon__,
                                         5000)
        else:
            # No audio stream playing
            commontasks.message(_no_audio_stream, _artist_info)
    else:
        if len(artist) > 0:
            # Split artist name from artist
            items = artist.split(' - ')
            artist_name = items[0]
            if len(artist_name) > 1:
                return artist_name
    return None


def show_artist_details(artistname):
    """
    Shows artist information ie. image, genre, description etc.
    """
    artist_info = ArtistInfo(artistname)
    if artist_info.artist_id is not None:
        home = xbmc.translatePath('special://home')
        if xbmc.getInfoLabel('System.ProfileName') != 'Master user':
            you = xbmc.getInfoLabel('System.ProfileName')
        elif (xbmc.getCondVisibility('System.Platform.Windows') is True or
              xbmc.getCondVisibility('System.Platform.OSX') is True):
            if 'Users\\' in home:
                proyou = str(home).split('Users\\')
                preyou = str(proyou[1]).split('\\')
                you = preyou[0]
            else:
                you = 'You'
        else:
            you = 'You'
        # Open custom artist information dialog
        win = xbmcgui.WindowXMLDialog('artist-info.xml',
                                      __addon__.getAddonInfo('path'))
        # Set artist information properties within xml dialog for example
        # <label fallback="416">$INFO[Window.Property(HeadingLabel)]</label>
        win.setProperty('HeadingLabel', artistname)
        win.setProperty('ArtistImage', artist_info.fanart)
        win.setProperty('ArtistStyle', artist_info.style)
        win.setProperty('ArtistGenre', artist_info.genre)
        win.setProperty('ArtistName', artist_info.artist_name)
        win.setProperty('ArtistFormed',
                        str(artist_info.year_formed).replace('None', ''))
        win.setProperty('ArtistBorn',
                        str(artist_info.year_born).replace('None', ''))
        win.setProperty('ArtistDied',
                        str(artist_info.year_died).replace('None', ''))
        win.setProperty('ArtistGender', artist_info.gender)
        win.setProperty('ArtistCountry',
                        str(artist_info.country).replace('None', '') + ' ' +
                        str(artist_info.country_code).replace('None', ''))
        win.setProperty('ArtistWebsite', artist_info.website)
        win.setProperty('Description', artist_info.biography_en)
        win.doModal()
        del win
    else:
        # Unable to download artist information
        commontasks.notification(_artist_info,
                                 _unable_to_download_artist_info,
                                 xbmcgui.NOTIFICATION_INFO, 5000)
    if xbmc.Player().isPlayingAudio():
        thread = threading.Thread(target=show_artist_image, args=())
        thread.start()


def get_current_artist_image():
    """
    Discover artist name, download image and return the image path
    if no image can be found return the default image instead
    """
    global g_default_image
    # Check if user selected to hide artist image
    if _hide_artist_artwork != 'true':
        # Find the current artist name
        artist_name = get_artist_name()
        if artist_name is not None:
            if len(artist_name) > 1:
                # Fetch the artists information
                artist_info = ArtistInfo(artist_name)
                # Check for artist image
                if artist_info.fanart is not None:
                    if len(artist_info.fanart) > 1:
                        return artist_info.fanart
    return g_default_image


def show_artist_image():
    """
    Shows current artist as background image.
    """
    # Open custom music visualization dialog
    window = xbmcgui.WindowXMLDialog('music-visualization.xml',
                                     __addon__.getAddonInfo('path'))
    window.show()
    previous_title = ''
    artist_image = ''
    # While steaming audio check for changes in title every 2 seconds
    while (not xbmc.Monitor().abortRequested() and
           xbmc.Player().isPlayingAudio()):

        if _hide_artist_artwork != 'true':
            my_title = xbmc.Player().getMusicInfoTag().getTitle()

            # Poll for changes in title
            if my_title != previous_title:
                # Get current artist image
                artist_image = get_current_artist_image()
                # Set artist image property within xml dialog
                window.setProperty('ArtistFanart',
                                   artist_image)
                previous_title = my_title

        # Sleep for 2 seconds
        xbmc.sleep(2000)
    
    window.close()
    del window


def addDir(name, url, mode, icon, fanart, desc, isFolder=False):
    """
    Display a list of links
    """
    u = (sys.argv[0] + '?url=' + commontasks.quote_plus(url) +
         '&mode=' + str(mode) + '&name=' + commontasks.quote_plus(name) +
         '&icon=' + str(icon) + '&fanart=' + str(fanart))
    ok = True
    liz = xbmcgui.ListItem(name)
    # Set fanart and thumb images for the list item.
    if not fanart:
        # Set fanrt to default image
        fanart = __fanart__
    if not icon:
        # Set icon to default image
        icon = __icon__

    liz.setArt({'fanart': fanart, 'thumb': icon})
    # Set additional info for the list item.
    liz.setInfo(type='music',
                infoLabels={'title': name,
                            'artist': name,
                            'comment': desc,
                            'genre': 'Internet Radio',
                            'year': 2015,
                            'mediatype': 'album'})

    ok = xbmcplugin.addDirectoryItem(handle=__handle__,
                                     url=u,
                                     listitem=liz,
                                     isFolder=isFolder)
    return ok


def get_params():
    """
    Parse the paramters sent to the application
    """
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params)-1] == '/'):
            params = params[0:len(params)-2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


# Define local variables
params = get_params()
url = None
name = None
mode = None
icon = None
fanart = None

# Parse the url, name, mode, icon and fanart parameters
try:
    url = commontasks.unquote_plus(params['url'])
except:
    pass
try:
    name = commontasks.unquote_plus(params['name'])
except:
    pass
try:
    mode = int(params['mode'])
except:
    pass
try:
    icon = commontasks.unquote_plus(params['icon'])
except:
    pass
try:
    fanart = commontasks.unquote_plus(params['fanart'])
except:
    pass

# Route the request based upon the mode number
if mode is None or url is None or len(url) < 1: # Show main menu
    main_menu()
elif mode == 1: # Start audio stream
    g_default_image = fanart
    play_audio(name, url, icon, fanart)
elif mode == 2: # Show current artist description
    artist_name = get_artist_name()
    if artist_name is not False and artist_name is not None:
        show_artist_details(artist_name)
elif mode == 3: # Show settings
    __addon__.openSettings()
    xbmc.executebuiltin("Container.Refresh")
