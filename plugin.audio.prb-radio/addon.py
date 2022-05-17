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
_mixes = __language__(30119)
_mixes_desc = __language__(30120)

# Get addon user settings
_hide_fav_songs = __addon__.getSetting('hide_fav_songs')
_hide_artist_info = __addon__.getSetting('hide_artist_info')
_hide_artist_artwork = __addon__.getSetting('hide_artist_artwork')
_hide_mixes = __addon__.getSetting('hide_mixes')
_prevent_screensaver = __addon__.getSetting('prevent_screensaver')
_previous_url = __addon__.getSetting('previous_url')

# Define local variables
playable_url = ''
base_url = u'http://dir.xiph.org/search?q=PRB+Radio'

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
g_mixes_icon = os.path.join(image_path, 'mixes.png')
g_mixes_fanart = os.path.join(image_path, 'mixes_fanart.jpg')
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
              _mixes:
              {'thumbs': g_mixes_icon,
               'fanart': g_mixes_fanart,
               'desc': _mixes_desc
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
    global _previous_url
    if _previous_url is not None or _previous_url != "":
        response = os.system("ping -c 1 " + _previous_url.replace('http://', '').replace('/rapi.mp3', ''))
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


def addDir(name, url, mode, icon, fanart, desc, category=None, genre=None, duration=None, isFolder=False):
    """
    Display a list of links
    """
    u = (sys.argv[0] + '?url=' + commontasks.quote_plus(url) + '&mode=' + str(mode) + '&icon=' + str(icon) + '&name=' + str(name) + '&category=' + str(category) + '&genre=' + str(genre))
    ok = True
    liz = xbmcgui.ListItem(name)
    # Set fanart and thumb images for the list item.
    if not fanart:
        # Set fanrt to default image
        fanart = __fanart__
    if not icon:
        # Set icon to default image
        icon = __icon__

    if genre is None:
        genre = 'Blues, Gospel, Jazz, Soul, Reggae, Funk, Hip-Hop'

    artist = 'Various Artists'
    year = '2019'

    liz.setArt({'fanart': fanart, 'thumb': icon})
    # Set additional info for the list item.
    liz.setInfo(type='music',
                infoLabels={'title': name,
                            'artist': name,
                            'comment': desc,
                            'genre': genre,
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
    addDir(name=_prb_radio,
           url=playable_url,
           mode=1,
           icon=links_info[_prb_radio]['thumbs'],
           fanart=links_info[_prb_radio]['fanart'],
           desc=links_info[_prb_radio]['desc'])
    if _hide_mixes != 'true':
        # Mixes link
        addDir(name=_mixes,
               url=playable_url,
               mode=8,
               icon=links_info[_mixes]['thumbs'],
               fanart=links_info[_mixes]['fanart'],
               desc=links_info[_mixes]['desc'],
               isFolder=True)
    if _hide_artist_info != 'true':
        # Artist information link
        addDir(name=_artist_info,
               url=playable_url,
               mode=2,
               icon=links_info[_artist_info]['thumbs'],
               fanart=links_info[_artist_info]['fanart'],
               desc=links_info[_artist_info]['desc'])
    if _hide_fav_songs != 'true':
        # Favorite Songs link
        addDir(name=_fav_songs,
               url=playable_url,
               mode=3,
               icon=links_info[_fav_songs]['thumbs'],
               fanart=links_info[_fav_songs]['fanart'],
               desc=links_info[_fav_songs]['desc'],
               isFolder=True)
    # Settings link
    addDir(name=_settings,
           url=playable_url,
           mode=4,
           icon=links_info[_settings]['thumbs'],
           fanart=links_info[_settings]['fanart'],
           desc=links_info[_settings]['desc'])
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
    liz.setArt({'fanart': __fanart__, 'thumb': icon})
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
            # Get artist name of audio stream
            artist_name = xbmc.Player().getMusicInfoTag().getArtist()
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


def get_categories():
    global base_url
    pu = commontasks.decode(_previous_url).decode('utf-8')
    base_url = pu.replace(':8000/rapi.mp3', '')
    url = base_url + '/?page_id=2359'
    raw_categories = []
    response = commontasks.get_url(url)
    matches = re.compile('<h2>(.+?)</h2>').findall(str(response))
    return matches


def get_category(category):
    global base_url
    mixes = []
    pu = commontasks.decode(_previous_url).decode('utf-8')
    base_url = pu.replace(':8000/rapi.mp3', '')
    url = base_url + '/?page_id=2359'
    raw_categories = []
    response = commontasks.get_url(url)
    cat_mixes = re.compile('<!-- Mix Category Start -->(.+?)<!-- Mix Category End -->').findall(str(response))
    for cats in cat_mixes:
        if str(cats).find(str(category)) > -1:
            cat = str(cats)
            mixes = re.compile('<!-- Mix Start -->(.+?)<!-- Mix End -->').findall(str(cat))
    return mixes


def show_mix_categories():
    categories = get_categories()
    for category in categories:
        addDir(name=category,
               url=url,
               mode=9,
               icon=g_mixes_icon,
               fanart=g_mixes_fanart,
               category=category,
               isFolder=True)
    xbmcplugin.endOfDirectory(__handle__)


def show_mix_genres(category):
    raw_genres = []
    mix_gens = ''
    mixes = get_category(category)
    for mix in mixes:
        regex = '<h6 style="padding-left: 40px;">Genre: (.+?)<br'
        if mix != None:
            mix_genres = re.compile(regex).findall(str(mix))
            mix_gens = mix_gens + mix_genres[0] + ', '


    for gen in mix_gens.split(', '):
        try:
            if str(gen) not in raw_genres and str(gen) != '':
                raw_genres.append(gen)
        except:
            pass
    raw_genres.sort()
    for raw_gen in raw_genres:
        addDir(name=raw_gen,
               url=url,
               mode=10,
               icon=g_mixes_icon,
               fanart=g_mixes_fanart,
               category=category,
               genre=raw_gen,
               isFolder=True)
    xbmcplugin.endOfDirectory(__handle__)


def duration_seconds(duration):
    try:
        if ' hour' in duration:
            hours = duration[:duration.index(' hour')]
            minutes = commontasks.regex_from_to(duration, 'hour', ' minutes').replace('s ', '')
        else:
            hours = 0
            minutes = duration[:duration.index(' minutes')]
        seconds = commontasks.regex_from_to(duration, 'minutes ', ' seconds')
        duration_seconds = (int(hours)*60*60) + (int(minutes)*60) + int(seconds)
    except:
        return None
    return duration_seconds


def show_mixes(category, genre):
    matches = get_category(category)
    for items in matches:
        regex = '<h3 style="padding-left: 40px;">(.+?)</h3>(.+?)src="(.+?)"(.+?)<a href="(.+?).mp3">(.+?)<h6 style="padding-left: 40px;">Genre: (.+?)<b(.+?)Duration: (.+?)</h6>'
        item_matches = re.compile(regex).findall(str(items))
        if len(item_matches) > 0:
            for title, junk1, img_src, junk2, link, junk3, gen, junk4, dur in item_matches:
                if genre in gen:
                    title = title.replace('&#8211;', '-')
                    link = commontasks.requote_uri(link)
                    new_link = base_url + link.replace('../', '/') + '.mp3'
                    try:
                        new_cue = commontasks.regex_from_to(junk3, '<a href="', '">cue file')
                        new_cue = commontasks.requote_uri(new_cue)
                        new_cue = base_url + new_cue.replace('../', '/')
                    except:
                        new_cue = None
                    regex = '<li>(.+?)</li>'
                    item_matches = re.compile(regex).findall(str(items))
                    tracks = ''
                    for track in item_matches:
                        trk = '%s; ' % (track.replace('\n', '')
                                             .replace('&#8211;', '-')
                                             .replace('</strong>', '')
                                             .replace('<strong>', '')
                                             .replace('&amp;', '&')
                                             .replace('/', '')
                                             .replace('<br >', '')
                                             .replace('&#8243;', '"')
                                             .replace('&#8216;', "'")
                                             .replace('&#8217;', "'"))
                        tracks += '[COLOR orange]%s[/COLOR]%s' % (trk[:trk.index('-')], trk[trk.index('-'):])
                    addDir(name=title,
                           url=new_link,
                           mode=11,
                           icon=img_src,
                           fanart=__fanart__,
                           desc=tracks,
                           category=category,
                           genre=gen,
                           duration=duration_seconds(dur))
        else:
            regex = '<p style="padding-left: 40px;"><a href="(.+?).mp3">(.+?)</a(.+?)">Genre: (.+?)<b(.+?)Duration: (.+?)</h6>'
            item_matches = re.compile(regex).findall(str(items))
            for link, title, junk1, gen, junk2, dur in item_matches:
                if genre in gen:
                    title = title.replace('&#8211;', '-')
                    link = commontasks.requote_uri(link)
                    new_link = base_url + link.replace('../', '/') + '.mp3'
                    try:
                        new_cue = commontasks.regex_from_to(junk1, '<a href="', '">cue file')
                        new_cue = commontasks.requote_uri(link)
                        new_cue = base_url + new_cue.replace('../', '/')
                    except:
                        new_cue = None
                    regex = '<li>(.+?)</li>'
                    item_matches = re.compile(regex).findall(str(items))
                    tracks = ''
                    for track in item_matches:
                        trk = '%s; ' % (track.replace('\n', '')
                                              .replace('&#8211;', '-')
                                              .replace('</strong>', '')
                                              .replace('<strong>', '')
                                              .replace('&amp;', '&')
                                              .replace('/', '')
                                              .replace('<br >', '')
                                              .replace('&#8243;', '"')
                                              .replace('&#8216;', "'")
                                              .replace('&#8217;', "'"))
                        tracks += '[COLOR orange]%s[/COLOR]%s' % (trk[:trk.index('-')], trk[trk.index('-'):])
                    addDir(name=title,
                           url=new_link,
                           mode=11,
                           icon=g_mixes_icon,
                           fanart=g_mixes_fanart,
                           desc=tracks,
                           category=category,
                           genre=gen,
                           duration=duration_seconds(dur))

    xbmcplugin.endOfDirectory(__handle__)


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
        addDir(name=title, url=url, mode=mode, icon=iconimage, fanart=fanartimage)
    if not os.path.isfile(__fav_songs_list__):
        commontasks.create_file(__resources__, 'fav_songs.list')
    s = commontasks.read_from_file(__fav_songs_list__)
    search_list = s.split('\n')
    for list in search_list:
        if list != '':
            addDir(name=list,
                   url=list,
                   mode=7,
                   icon=os.path.join(image_path, 'fav_songs.png'),
                   fanart=os.path.join(image_path, 'fav_songs_fanart.jpg'))
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
icon = None
name = None
category = None
genre = None

# Parse the url & mode parameters
try:
    url = commontasks.unquote_plus(params['url'])
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
    name = commontasks.unquote_plus(params['name'])
except:
    pass
try:
    category = commontasks.unquote_plus(params['category'])
except:
    pass
try:
    genre = commontasks.unquote_plus(params['genre'])
except:
    pass

# For testing purposes
#commontasks.message('Url: %s\nName: %s\nCategory: %s\nGenre: %s' % (str(url), str(name), str(category), str(genre)), 'Mode: %s' % str(mode))

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
elif mode == 8: # Display mix categories
    show_mix_categories()
elif mode == 9: # Display mix genres
    show_mix_genres(category)
elif mode == 10: # Display mixes
    show_mixes(category, genre)
elif mode == 11: # Play mix
    play_audio(url, icon, name)