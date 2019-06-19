#!/bin/python

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import urllib
import urllib2
import cookielib
import re
import sys
import os

from resources.lib.artistinfo import ArtistInfo

import thread

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-02-2017
# Description: Addon for listening to Absolute Radio live broadcasts

# Get addon details
__addon_id__ = 'plugin.audio.absolute-radio'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'
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
_unable_to_download_artist = __language__(30114)
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
_download_artist_info_desc = __language__(30125)
_settings_desc = __language__(30126)

# Get addon user settings
_compression_format = __addon__.getSetting('compression_format')
_hide_artist_info = __addon__.getSetting('hide_artist_info')
_hide_artist_artwork = __addon__.getSetting('hide_artist_artwork')

# Define local variables
g_default_image = None
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
	                            __addon_id__ + '/resources/media/'))
link_info = {'Absolute Radio':
             {'thumbs': os.path.join(image_path, 
                                     'absolute_radio.png'),
              'fanart': os.path.join(image_path,
                                     'absolute_radio_fanart.jpg'),
              'desc': _ar_desc
              },
             'Absolute Classic Rock':
             {'thumbs': os.path.join(image_path,
                                     'absolute_radio_classic_rock.png'),
              'fanart': os.path.join(image_path,
                                     'absolute_radio_classic_rock'
                                     '_fanart.jpg'),
              'desc': _ar_cr_desc
              },
             'Absolute 80s':
             {'thumbs': os.path.join(image_path,
                                     'absolute_radio_80s.png'),
              'fanart': os.path.join(image_path,
                                     'absolute_radio_80s_fanart.jpg'),
              'desc': _ar_80s_desc
              },
             'Absolute Radio 60s':
             {'thumbs': os.path.join(image_path,
                                     'absolute_radio_60s.png'),
              'fanart': os.path.join(image_path,
                                     'absolute_radio_60s_fanart.jpg'),
              'desc': _ar_60s_desc
              },
             'Absolute Radio 70s':
             {'thumbs': os.path.join(image_path,
                                     'absolute_radio_70s.png'),
              'fanart': os.path.join(image_path,
                                     'absolute_radio_70s_fanart.jpg'),
              'desc': _ar_70s_desc
              },
             'Absolute Radio 90s':
             {'thumbs': os.path.join(image_path,
                                     'absolute_radio_90s.png'),
              'fanart': os.path.join(image_path,
                                     'absolute_radio_90s_fanart.jpg'),
              'desc': _ar_90s_desc
              },
             'Absolute Radio 00s':
             {'thumbs': os.path.join(image_path,
                                     'absolute_radio_00s.png'),
              'fanart': os.path.join(image_path,
                                     'absolute_radio_00s_fanart.jpg'),
              'desc': _ar_00s_desc
              },
             _artist_info:
             {'thumbs': os.path.join(image_path,
                                     'artist_info.png'),
              'fanart': os.path.join(image_path,
                                     'artist_info_fanart.jpg'),
              'desc': _download_artist_info_desc
              },
             _settings:
             {'thumbs': os.path.join(image_path,
                                     'settings.png'),
              'fanart': os.path.join(image_path,
                                     'settings_fanart.jpg'),
              'desc': _settings_desc
              }
             }


def _login_absolute_radio(username, password):
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
        data = urllib.urlencode(values)
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
            notification(_login_success_title,
                             _login_success_msg, __icon__, 5000)
            return True
        else:
            notification(_login_failed_title,
                             _login_failed_msg, __icon__, 5000)
            return False


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


def categories():
    """
    Download categories from absolute radio
    and display a list of the stations
    """
    response = _get_url(__baseurl__)
    response = response.replace('\n', '').replace('\t', '').replace('  ', '')
    headings = re.compile('<h3>(.+?)</h3>').findall(response)
    if len(__addon__.getSetting('username')) > 1:
        _login_absolute_radio(__addon__.getSetting('username'),
                              __addon__.getSetting('password'))
    for item in headings:
        if 'Trial' not in item:
            list_item = item.replace(' stream URLs', '')
            addDir(list_item,
                   __baseurl__,
                   1,
                   link_info[list_item]['thumbs'],
                   link_info[list_item]['fanart'],
                   link_info[list_item]['desc'],
                   isFolder=False)
    if _hide_artist_info != 'true':
        addDir(_artist_info,
               'XBMC.RunPlugin({0}?url=artistinfo&mode=4)',
               4,
               link_info[_artist_info]['thumbs'],
               link_info[_artist_info]['fanart'],
               link_info[_artist_info]['desc'],
               isFolder=False)
    addDir(_settings,
           'XBMC.RunPlugin({0}?url=settings&mode=5)',
           5,
           link_info[_settings]['thumbs'],
           link_info[_settings]['fanart'],
           link_info[_settings]['desc'],
           isFolder=False)


def get_links(name, url, icon, fanart):
    """
    Fetch user's compression format and bitrate settings.
    Download links to the audio stream location.
    """
    response = _get_url(url).replace(' stream URLs', '')
    response = response.replace('\n', '').replace('\t', '').replace('  ', '')
    filter = re.compile('<h3>' +
                        name +
                        '</h3>(.+?)</p>').findall(response)
    regex = '<strong>(.+?)</strong> <span class="display-url">(.+?)</span>'
    data = re.compile(regex).findall(str(filter))
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
            get_audio(sound_quality, link, icon, fanart)


def get_audio(name, url, icon, fanart):
    """
    Parse the file location and title links from audio stream location.
    """
    response = _get_url(url)
    files = re.compile('File1=(.+?)\n').findall(response)
    titles = re.compile('Title1=(.+?)\n').findall(response)
    for file in files:
        for title in titles:
            play_audio(title, file, icon, fanart)
            while not xbmc.Player().isPlayingAudio():
                xbmc.sleep(3)
            thread.start_new_thread( _show_artist_image,())


def play_audio(name, url, icon, fanart):
    """
    Create a list item to the audio stream and
    start playing the audio stream.
    """
    if xbmc.Player().isPlayingAudio:
        xbmc.Player().stop()
    liz = xbmcgui.ListItem(str(name),
                           iconImage='Icon.png',
                           thumbnailImage=icon)
    # Set a fanart image for the list item.
    liz.setProperty('fanart_image', fanart)
    xbmc.Player().play(url, liz, False)
    xbmc.executebuiltin('Action(Fullscreen)')


def notification(message, title, icon, duration):
    # Show message notification
    dialog = xbmcgui.Dialog()
    dialog.notification(title, message, icon, duration)


def message(message, title):
    # Display message to user
    dialog = xbmcgui.Dialog()
    dialog.ok(title, message)


def show_artist_info():
    if xbmc.Player().isPlayingAudio():
        try:
            my_title = xbmc.Player().getMusicInfoTag().getTitle()
            if len(my_title) > 0:
                items = my_title.split(' - ')
                artist = items[0]
                song = items[1]
                previous = my_title
                if len(song) > 1:
                    show_artist_details(artist)
                else:
                    message(_unable_to_download_artist, _artist_info)
            else:
                message(_no_artist_name_present, _artist_info)
            _show_artist_image()
        except:
            message(_unable_to_download_artist, _artist_info)
    else:
        message(_no_audio_stream, _artist_info)


def show_artist_details(artistname):
    artist_info = ArtistInfo(artistname)
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
    window = xbmcgui.WindowXMLDialog('plugin-audio-absolute-radio.xml',
                                     __addon__.getAddonInfo('path'))
    win = xbmcgui.Window(10147)
    win.setProperty('HeadingLabel',
                    artistname)
    # Property can be accessed in the XML using:
    # <label fallback="416">$INFO[Window(10147).Property(HeadingLabel)]</label>
    win.setProperty('ArtistImage',
                    artist_info.fanart)
    win.setProperty('ArtistStyle',
                    artist_info.style)
    win.setProperty('ArtistGenre',
                    artist_info.genre)
    win.setProperty('ArtistName',
                    artist_info.artist_name)
    win.setProperty('ArtistFormed',
                    str(artist_info.year_formed).replace('None', ''))
    win.setProperty('ArtistBorn',
                    str(artist_info.year_born).replace('None', ''))
    win.setProperty('ArtistDied',
                    str(artist_info.year_died).replace('None', ''))
    win.setProperty('ArtistGender',
                    artist_info.gender)
    win.setProperty('ArtistCountry',
                    artist_info.country.replace('None', '') + ' ' +
                    artist_info.country_code.replace('None', ''))
    win.setProperty('ArtistWebsite',
                    artist_info.website)
    win.setProperty('Description',
                    artist_info.biography_en)
    window.doModal()
    del window


def get_current_artist_image():
    """
    Discover artist name, download image and return the image path
    if no image can be found return the default image instead
    """
    global g_default_image
    # Find the current artist name
    artist_name = ''
    if xbmc.Player().isPlayingAudio():
        try:
            my_title = xbmc.Player().getMusicInfoTag().getTitle()
            if len(my_title) > 0:
                items = my_title.split(' - ')
                artist = items[0]
                song = items[1]
                previous = my_title
                if len(song) > 1:
                    artist_name = artist
        except:
            notification(_no_artist_name_present,
                             _artist_info, __icon__, 5000)
    else:
        notification(_no_audio_stream, _artist_info, __icon__, 5000)
    # Find artist image
    if len(artist_name) > 1:
        # Find the artist information
        artist_info = ArtistInfo(artist_name)
        if artist_info != 0:
            try:
                if len(artist_info.fanart) > 1:
                    return artist_info.fanart
                else:
                    return g_default_image
            except:
                return g_default_image
        else:
            return g_default_image
    else:
        return g_default_image


def _show_artist_image():
    global g_default_image
    window = xbmcgui.WindowXMLDialog('plugin-music-visualisation.xml',
                                     __addon__.getAddonInfo('path'))
    win = xbmcgui.Window(12006)
    window.show()
    if xbmc.Player().isPlayingAudio():
        my_title = xbmc.Player().getMusicInfoTag().getTitle()
    previous_title = ''
    # main loop
    while (not xbmc.Monitor().abortRequested() and
           xbmc.Player().isPlayingAudio()):
        if _hide_artist_artwork != 'true':
            my_title = xbmc.Player().getMusicInfoTag().getTitle()
            if my_title != previous_title:
                # check if we are on the music visualization screen
                # do not try and set image for any background media
                if xbmc.getCondVisibility("Player.IsInternetStream"):
                    win.setProperty('ArtistFanart',
                                    get_current_artist_image())
                previous_title = my_title
        else:
            win.setProperty('ArtistFanart', g_default_image)
        xbmc.sleep(1000)
    del window


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


def addDir(name, url, mode, icon, fanart, desc, isFolder=False):
    """
    Display a list of links
    """
    u = (sys.argv[0] + '?url=' + urllib.quote_plus(url) +
         '&mode=' + str(mode) + '&name=' + urllib.quote_plus(name) +
         '&icon=' + str(icon) + '&fanart=' + str(fanart))
    ok = True
    liz = xbmcgui.ListItem(name)

    # Set fanart and thumb images for the list item.
    if not fanart:
        fanart = __fanart__
    if not icon:
        icon = __icon__
    liz.setArt({'fanart': fanart,
                'thumb': icon})

    # Set additional info for the list item.
    liz.setInfo(type='music',
                infoLabels={'title': name,
                            'artist': name,
                            'description': desc,
                            'genre': 'Internet Radio',
                            'year': 2015,
                            'mediatype': 'album'
                            }
                )
    ok = xbmcplugin.addDirectoryItem(handle=__handle__,
                                     url=u,
                                     listitem=liz,
                                     isFolder=isFolder)
    return ok


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
    categories()
elif mode == 1:
    g_default_image = fanart
    get_links(name, url, icon, fanart)
elif mode == 2:
    get_audio(name, url, icon, fanart)
elif mode == 3:
    play_audio(name, url, icon, fanart)
elif mode == 4:
    show_artist_info()
elif mode ==5:
    __addon__.openSettings()
    xbmc.executebuiltin("Container.Refresh")


xbmcplugin.endOfDirectory(__handle__)
