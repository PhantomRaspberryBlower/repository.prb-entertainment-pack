#!/bin/python

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
import os
import re
import threading
import random

from resources.lib.artistinfo import ArtistInfo
from resources.lib import commontasks

# Written by:	Phantom Raspberry Blower
# Date:		21-02-2019
# Description:	Addon for listening to PRB Radio live broadcasts

# Get addon details
__addon_id__ = u'plugin.audio.prb-radio'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = u'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

# Get localized language words
__language__ = __addon__.getLocalizedString
_prb_radio = __language__(30101)
_artist_info = __language__(30102)
_unable_to_download_artist_info = __language__(30103)
_no_artist_name_present = __language__(30104)
_no_audio_stream = __language__(30105)
_settings = __language__(30106)
_prb_desc = __language__(30107)
_artist_info_desc = __language__(30108)
_settings_desc = __language__(30109)
_prb_radio_not_broadcasting = __language__(30110)
_on_air = __language__(30111)
_prb_radio_off_air = __language__(30112)
_fav_songs = __language__(30113)
_fav_songs_desc = __language__(30114)
_clear_fav_list = __language__(30115)
_are_you_sure = __language__(30116)
_clear_list = __language__(30117)
_add_current_song_to_list = __language__(30118)

# Get addon user settings
_hide_fav_songs = __addon__.getSetting('hide_fav_songs')
_hide_artist_info = __addon__.getSetting('hide_artist_info')
_hide_artist_artwork = __addon__.getSetting('hide_artist_artwork')
_prevent_screensaver = __addon__.getSetting('prevent_screensaver')
_previous_url = __addon__.getSetting('previous_url')

# Define local variables
playable_url = ''
base_url = u'http://dir.xiph.org/search?search=PRB+Leicester'

__resources__ = xbmc.translatePath(os.path.join('special://home/addons/'
                                            'plugin.audio.prb-radio',
                                            'resources'))

# List of favourite songs
__fav_songs_list__ = os.path.join(__resources__, 'fav_songs.list')

# Define Images
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
                                __addon_id__ + '/resources/media/'))
g_default_icon = os.path.join(image_path, 'prb_radio.png')
g_default_fanart = os.path.join(image_path, 'prb_radio_fanart.jpg')
g_artist_info_icon = os.path.join(image_path, 'artist_info.png')
g_artist_info_fanart = os.path.join(image_path, 'artist_info_fanart.jpg')
g_fav_songs_icon = os.path.join(image_path, 'fav_songs.png')
g_fav_songs_fanart = os.path.join(image_path, 'fav_songs_fanart.jpg')
g_settings_icon = os.path.join(image_path, 'settings.png')
g_settings_fanart = os.path.join(image_path, 'settings_fanart.jpg')
g_blues_fanart = os.path.join(image_path, 'blues_fanart.jpg')
g_funk_fanart = os.path.join(image_path, 'funk_fanart.jpg')
g_gospel_fanart = os.path.join(image_path, 'gospel_fanart.jpg')
g_rnb_fanart = os.path.join(image_path, 'r&b_fanart.jpg')
g_hip_hop_fanart = os.path.join(image_path, 'hip-hop_fanart.jpg')
g_jazz_fanart = os.path.join(image_path, 'jazz_fanart.jpg')
g_neo_soul_fanart = os.path.join(image_path, 'neo_soul_fanart.jpg')
g_reggae_fanart = os.path.join(image_path, 'reggae_fanart.jpg')
g_soul_fanart = os.path.join(image_path, 'soul_fanart.jpg')

links_info = {_prb_radio:
              {'thumbs': g_default_icon,
               'fanart': g_default_fanart,
               'desc': _prb_desc
               },
              _artist_info:
              {'thumbs': g_artist_info_icon,
               'fanart': g_artist_info_fanart,
               'desc': _artist_info_desc
               },
              _fav_songs:
              {'thumbs': g_fav_songs_icon,
               'fanart': g_fav_songs_fanart,
               'desc': _fav_songs_desc
               },
              _settings:
              {'thumbs': g_settings_icon,
               'fanart': g_settings_fanart,
               'desc': _settings_desc
               }
              }


def get_stream_link():
    """
    Return list of live links.
    """
    if _previous_url is not None or _previous_url != "":
        domain_name = _previous_url.replace('http://', '').replace(':8000', '').replace('/rapi.mp3', '')
        if platform.system().lower() == 'windows':
            response = os.system('ping %s -n 1' % domain_name)
        else:
            # Below works on Linux
            response = os.system('ping -c 1 ' + domain_name)
        if response  == 0:
            return _previous_url
    link = ''
    title = ''
    content = commontasks.get_url(base_url)
    content = content.replace('\n', '').replace('\t', '')
    name = re.compile('class="card-title">(.+?)</h5> ').findall(content)[0]
    try:
        if name == 'PRB Radio':
            stream = re.compile('class="card-title">(.+?)</h5>(.+?)class' \
                                 '="d-inline-block float-right">(.+?)<a href' \
                                 '="(.+?)" class="btn btn-sm btn-primary">Play</a>').findall(content)[0]
            title = str(name)
            link = str(stream[3])
    except:
        pass
    if title == 'PRB Radio':
        __addon__.setSetting('previous_url', link)
        return link
    return 0


def addDir(name, url, mode, icon, fanart, desc, isFolder=False):
    """
    Display a list of links
    """
    u = (sys.argv[0] + '?url=' + commontasks.quote_plus(url) + '&mode=' + str(mode))
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
                            'genre': 'Blues, Gospel, Jazz, Soul, Reggae, Funk, Hip-Hop',
                            'year': 2019,
                            'mediatype': 'album'})

    ok = xbmcplugin.addDirectoryItem(handle=__handle__,
                                     url=u,
                                     listitem=liz,
                                     isFolder=isFolder)
    return ok


def main_menu():
    """
    Displays main menu.
    """
    playable_url = get_stream_link()
    if playable_url == 0:
        commontasks.message(_prb_radio_not_broadcasting, _prb_radio_off_air)
        return 0
    # Live stream link
    addDir(_prb_radio,
           playable_url,
           1,
           links_info[_prb_radio]['thumbs'],
           links_info[_prb_radio]['fanart'],
           links_info[_prb_radio]['desc'])
    if _hide_artist_info != 'true':
        # Artist information link
        addDir(_artist_info,
               playable_url,
               2,
               links_info[_artist_info]['thumbs'],
               links_info[_artist_info]['fanart'],
               links_info[_artist_info]['desc'])
    if _hide_fav_songs != 'true':
        # Favorite Songs link
        addDir(_fav_songs,
               playable_url,
               3,
               links_info[_fav_songs]['thumbs'],
               links_info[_fav_songs]['fanart'],
               links_info[_fav_songs]['desc'],
               isFolder=True)
    # Settings link
    addDir(_settings,
           playable_url,
           4,
           links_info[_settings]['thumbs'],
           links_info[_settings]['fanart'],
           links_info[_settings]['desc'])
    xbmcplugin.endOfDirectory(__handle__)


def play_audio(url):
    """
    Start playing the audio stream.
    """
    if xbmc.Player().isPlayingAudio:
        xbmc.Player().stop()
    liz = xbmcgui.ListItem('PRB Radio',
                           iconImage='Icon.png',
                           thumbnailImage=__icon__)
    # Set a fanart image for the list item.
    liz.setProperty('fanart_image', __fanart__)
    xbmc.Player().play(url, liz, False)
    while not xbmc.Player().isPlayingAudio():
        xbmc.sleep(1)
    # Start thread to display current artist image
    thread = threading.Thread(target=show_artist_image, args=())
    thread.start()


def get_artist_name(artist=None):
    """
    Parse artist name or current stream title
    """
    if artist == None:
        # Check audio atream is playing 
        if xbmc.Player().isPlayingAudio():
            # Get title of audio stream
            title = xbmc.Player().getMusicInfoTag().getTitle()
            if len(title) > 0:
                # Split artist name from stream title
                items = title.split(' - ')
                artist_name = items[0]
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
    count = 0
    fanart_images = [g_default_fanart,
                     g_blues_fanart,
                     g_soul_fanart,
                     g_rnb_fanart,
                     g_reggae_fanart,
                     g_hip_hop_fanart,
                     g_neo_soul_fanart]
    # While steaming audio check for changes in title every 2 seconds
    while (not xbmc.Monitor().abortRequested() and
           xbmc.Player().isPlayingAudio()):

        my_title = xbmc.Player().getMusicInfoTag().getTitle()
        # Poll for changes in title 
        if my_title != previous_title:
            # Get current artist image
            artist_image = get_current_artist_image()
            # Set artist image property within xml dialog
            window.setProperty('ArtistFanart',
                               artist_image)
            previous_title = my_title

        # Prevent activation of screensaver
        if xbmc.Monitor().onScreensaverActivated and _prevent_screensaver == 'true':
            # Wake up screen (stop screen diming)
            xbmc.executebuiltin('CECActivateSource')

        # Show randon default image
        if artist_image == g_default_fanart and _hide_artist_artwork != 'true':
            # Change image every 30 seconds
            if count == 15:
                # Show random fanart image
                img_count = random.randint(0,len(fanart_images)-1)
                window.setProperty('ArtistFanart',
                                   fanart_images[img_count])
                count = 0
            count += 1

        # Sleep for 2 seconds
        xbmc.sleep(2000)
    
    window.close()
    del window


def get_current_artist_image():
    """
    Discover artist name, download image and return the image path
    if no image can be found return the default image instead
    """
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
    return g_default_fanart


def clear_fav_songs():
    dialog = xbmcgui.Dialog()
    resp = dialog.yesno(_clear_fav_list, _are_you_sure)
    if resp:
        os.remove(__fav_songs_list__)
        xbmc.executebuiltin('Container.Refresh')


def show_fav_songs():
    menuitems = [(_clear_list,
                  'ClearFavSongs',
                  5,
                  os.path.join(image_path, 'fav_songs.png'),
                  os.path.join(image_path, 'fav_songs_fanart.jpg')),
                 (_add_current_song_to_list,
                  'AddFavSong',
                  6,
                  os.path.join(image_path, 'fav_songs.png'),
                  os.path.join(image_path, 'fav_songs_fanart.jpg'))]
    for title, url, mode, iconimage, fanartimage in menuitems:
        addDir(title, url, mode, iconimage, fanartimage, '')
    if not os.path.isfile(__fav_songs_list__):
        commontasks.create_file(__resources__, 'fav_songs.list')
    s = commontasks.read_from_file(__fav_songs_list__)
    search_list = s.split('\n')
    for list in search_list:
        if list != '':
            addDir(list,
                   list,
                   7,
                   os.path.join(image_path, 'fav_songs.png'),
                   os.path.join(image_path, 'fav_songs_fanart.jpg'),
                   '')
    xbmcplugin.endOfDirectory(__handle__)


def add_fav_song():
    if xbmc.Player().isPlayingAudio():
        title = xbmc.Player().getMusicInfoTag().getTitle()
        if len(title) > 0:
            commontasks.write_to_file(__fav_songs_list__, title + '\n', True)
        xbmc.executebuiltin('Container.Refresh')
    else:
        commontasks.message(_no_audio_stream, _fav_songs)


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
mode = None

# Parse the url & mode parameters
try:
    url = commontasks.unquote_plus(params['url'])
except:
    pass
try:
    mode = int(params['mode'])
except:
    pass

# Route the request based upon the mode number
if mode is None or url is None or len(url) < 1: # Show main menu
    main_menu()
elif mode == 1: # Start audio stream
    play_audio(url)
elif mode == 2: # Show current artist description
    artist_name = get_artist_name()
    if artist_name is not False and artist_name is not None:
        show_artist_details(artist_name)
elif mode == 3: # Show favorite songs list
    show_fav_songs()
elif mode == 4: # Show settings
    __addon__.openSettings()
    xbmc.executebuiltin("Container.Refresh")
elif mode == 5: # Clear favorite songs list
    clear_fav_songs()
elif mode == 6: # Add current song to favorite song list
    add_fav_song()
elif mode == 7: # Display artist information from favorite song list
    show_artist_details(get_artist_name(url))
