#!/bin/python

import urllib
import re
import xbmc
import xbmcplugin
import xbmcgui
import os
from threading import Thread

from resources.lib.artistinfo import ArtistInfo
from resources.lib import downloads
from resources.lib import commontasks
from resources.lib import playerMP3
from resources.lib import settings

'''
Written by: Phantom Raspberry Blower
Date: 21-08-2017
Description: Addon for streaming / downloading music
             and artwork. Derived from plugin.audio.mp3streams
'''
# Get addon details
__addon__ = settings.addon()

# Get addon user settings
__artist_art__ = settings.artist_icons()
__fav_artist__ = settings.favourites_file_artist()
__fav_album__ = settings.favourites_file_album()
__fav_song__ = settings.favourites_file_songs()
__music_dir__ = settings.music_dir()
__hide_fanart__ = settings.hide_fanart()
__queue_songs__ = settings.default_queue()
__queue_albums__ = settings.default_queue_album()
__download_list__ = settings.download_list()
__folder_structure__ = settings.folder_structure()
__queue_downloads__ = settings.queue_downloads()

# Get localized language text
__language__ = __addon__.getLocalizedString
_clear_downloads = __language__(20034)
_start_downloads = __language__(20035)
_downloads = __language__(20003)
_playlist = __language__(20007)
_cleared = __language__(20008)
_mp3_music = __language__(20011)
_browse_songs_or_play_album = __language__(20012)
_browse = __language__(20013)
_play_now = __language__(20014)
_creating_your_playlist = __language__(20015)
_select_group = __language__(20016)
_added_to_favourites = __language__(20017)
_removed_from_favourites = __language__(20018)
_remove = __language__(20036)
_artists = __language__(20019)
_top_albums =  __language__(20020)
_new_albums =  __language__(20021)
_compilations =  __language__(20022)
_search_lists = __language__(20037)
_search_artists = __language__(20023)
_search_albums = __language__(20024)
_search_songs = __language__(20025)
_favourite_lists = __language__(20038)
_favourite_artists = __language__(20026)
_favourite_albums = __language__(20027)
_favourite_songs = __language__(20028)
_instant_mix_favourite_albums = __language__(20029)
_instant_mix_favourite_songs = __language__(20030)
_clear_playlist = __language__(20031)
_settings = __language__(20032)
_instant = __language__(20063)
_clear = __language__(20064)
_top = __language__(20065)
__artists = __language__(20066)
_new = __language__(20067)
__albums = __language__(20068)
_best_compilations = __language__(20069)
_new_compilations = __language__(20070)
_major_hits = __language__(20071)
_nightclub_hits = __language__(20072)
_chillout_hits = __language__(20073)
_tributes_and_covers = __language__(20074)
_events = __language__(20075)
_err_downloading = __language__(20076)
_err_getting_webpage = __language__(20077)
_clear_download_list = __language__(20039)
_are_you_sure = __language__(20040)
_adding_to_your_playlist = __language__(20041)
_mp3_music_downloads_complete = __language__(20042)
_downloading = __language__(20043)
_n_of_n_tracks_downloaded = __language__(20044)
_all_songs = __language__(20045)
_all_albums = __language__(20046)
_add_new_group = __language__(20047)
_create_new_group = __language__(20048)
_artist_info = __language__(20049)
_unable_to_download_artist_info = __language__(20050)


_artist_info_heading = __language__(20051)
_clear_download_lock_heading = __language__(20052)
_added_to_favourite_artists_heading = __language__(20053)
_remove_from_favourite_artists_heading = __language__(20054)
_download_album_heading = __language__(20055)
_play_browse_album_heading = __language__(20056)
_queue_album_heading = __language__(20057)
_add_to_favourite_albums_heading = __language__(20058)
_remove_from_favourite_albums_heading =  __language__(20059)
_remove_heading = __language__(20060)
_download_song_heading = __language__(20061)
_queue_song_heading = __language__(20062)
_play_song_heading = __language__(20090)
_add_to_favourite_songs_heading = __language__(20091)
_remove_from_favourite_songs_heading = __language__(20092)


# Define local variables
resources = xbmc.translatePath(os.path.join('special://home/addons/'
	                                        'plugin.audio.mp3music',
	                                        'resources'))
fanart = xbmc.translatePath(os.path.join(resources, 'fanart.jpg'))
artfolder = xbmc.translatePath(os.path.join(resources, 'media/'))
artgenre = xbmc.translatePath(os.path.join(artfolder, 'genre/'))
iconart = xbmc.translatePath(os.path.join(resources, 'icon.png'))
download_lock = os.path.join(__music_dir__,  'downloading.txt')

MUSIC_DIR_URL = 'https://mp3music.ru'
MUSIC_LISTEN_URL = 'https://listen.musicmp3.ru/'

g_default_image = None


def CATEGORIES():
    global __queue_downloads__
    menuitems = [(_artists, MUSIC_DIR_URL + '/artists', 21, 'artists.jpg', ''),
                 (_top_albums, MUSIC_DIR_URL + '/top-albums', 12, 'topalbums.jpg', ''),
                 (_new_albums, MUSIC_DIR_URL + '/new-albums', 12, 'newalbums.jpg', ''),
                 (_compilations, 'url', 400, 'compilations.jpg', ''),
                 (_search_lists, 'url', 28, 'search.jpg', ''),
                 (_favourite_lists, 'url', 60, 'favourites.jpg', ''),
                 ('[COLOR lime]' + _downloads + '[/COLOR]', 'url', 70, 'downloads.jpg', ''),
                 ('[COLOR orange]' + _clear_playlist+ '[/COLOR]', 'url', 100, 'clearplaylist.jpg', 'clearplaylist'),
                 (_settings, 'url', 8, 'settings.jpg', 'settings')]
    for title, url, mode, iconimage, mtype in menuitems:
        if title.find(_downloads) >= 0:
            if __queue_downloads__:
                addDir(title, url, mode, artfolder + iconimage, '', '', '')
        else:
            addDir(title, url, mode, artfolder + iconimage, mtype, '', '')
        if title.find(_settings) >= 0:
            if not __queue_downloads__ == settings.queue_downloads():
                __queue_downloads__ = settings.queue_downloads()


def compilations_menu():
    url_path = 'https://www.goldenmp3.ru/albums_showcase.html?section=compilations%s&type=albums&page='
    menuitems = ([_best_compilations, '', 'topalbums.jpg'],
                 [_new_compilations, '&sort=new', 'newalbums.jpg'],
                 [_major_hits, '&gnr_id=806', 'newalbums.jpg'],
                 [_nightclub_hits, '&gnr_id=822', 'newalbums.jpg'],
                 [_chillout_hits, '&gnr_id=848', 'newalbums.jpg'],
                 [_tributes_and_covers, '&gnr_id=872', 'newalbums.jpg'],
                 [_events, '&gnr_id=875', 'newalbums.jpg'])
    for key, value, fanartimage in menuitems:
        addDir(key, url_path.replace('%s', value), 401, artfolder + fanartimage, '1', '', '')


def download_list():
    if os.path.isfile(__download_list__):
        s = commontasks.read_from_file(__download_list__)
        search_list = s.split('\n')
        if len(search_list) > 1 and not os.path.exists(download_lock):
            menuitems = [('[COLOR orange]' + _clear_downloads + '[/COLOR]', 'url', 610, 'clear_downloads.jpg'),
                         ('[COLOR lime]' + _start_downloads + '[/COLOR]', 'url', 600, 'start_downloads.jpg')]
            for title, url, mode, iconimage in menuitems:
                addDir(title, url, mode, artfolder + iconimage, 'downloadlist', '', '')
        for list in search_list:
            if list != '':
                splitlist = list.split('<>')
                url = splitlist[0]
                # Remove invalid characters from file name
                file_name = commontasks.validate_filename(str(splitlist[4]))
                filename = os.path.join(splitlist[1], file_name).strip()
                artist = splitlist[2]
                album = splitlist[3]
                trackname = splitlist[4].decode("utf-8").encode("ascii", errors="ignore")
                year = splitlist[5]
                genre =  str(splitlist[6]).strip()
                niconimage = splitlist[7]
                download_type = splitlist[8]
                if len(trackname) < 1:
                    title = ('%s - %s (%s)' % (artist, album, year)).replace('&amp;', 'and').decode("utf-8")
                    addDir(title, url, 5, niconimage, 'downloadlist', year, genre)
                else:
                    title = ('%s - %s (%s)' % (artist, trackname, year)).replace('&amp;', 'and').decode("utf-8")
                    addDirAudio(title,
                                url,
                                10,
                                niconimage,
                                trackname,
                                artist,
                                album,
                                '', 'downloadlist', year, genre)


def clear_download_list():
    global __download_list__
    dialog = xbmcgui.Dialog()
    resp = dialog.yesno(_clear_download_list, _are_you_sure)
    if resp:
        os.remove(__download_list__)
        __download_list__ = settings.download_list()
        xbmc.executebuiltin('Container.Refresh')


def artists_list(url):
    link = downloads.get_url(url)
    addDir('All Artists', MUSIC_DIR_URL + '/artists?page=1', 31,
           artfolder + 'allartists.jpg', '', '', '')
    sub_dir = re.compile('<li class="menu_sub__item"><a class='
                         '"menu_sub__link" href="(.+?)">(.+?)</a>'
                         '</li>').findall(link)
    for url1, title in sub_dir:
        iconimage = (MUSIC_DIR_URL + '/i' + url1.replace('.html',
                     '.jpg').replace('artists', 'genres').replace('tracks',
                     'track'))
        if title != 'Other':
            addDir(title.replace('&amp;', '&'), MUSIC_DIR_URL + url1, 41,
                   artgenre + title.replace(' ', '').replace('&amp;',
                   '_').lower() + '.jpg', '', '', '')


def all_artists(name, url):
    link = downloads.get_url(url)
    all_artists = re.compile('<li class="small_list__item"><a class='
                             '"small_list__link" href="(.+?)">(.+?)</a>'
                             '</li>').findall(link)
    for url1, title in all_artists:
        icon_path = os.path.join(__artist_art__, title.replace('&amp;', 'and') + '.jpg')
        if os.path.exists(icon_path):
            iconimage = icon_path
        else:
            iconimage = iconart
        fanart_path = os.path.join(__artist_art__, title.replace('&amp;', 'and') + '_fanart.jpg')
        if fanart_path.replace('.jpg', '_fanart.jpg'):
            fanartimage = fanart_path
        else:
            fanartimage = fanart
        addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url1, 22,
               iconimage, 'artists', '', '')
    pgnumf = url.find('page=') + 5
    pgnum = int(url[pgnumf:]) + 1
    nxtpgurl = url[:pgnumf]
    nxtpgurl = "%s%s" % (nxtpgurl, pgnum)
    addDir('>> Next page', nxtpgurl, 31,
           xbmc.translatePath(os.path.join('special://home/addons/'
                                           'plugin.audio.mp3music', 'media',
                                           'nextpage.jpg')), '', '', '')
    setView('movies', 'default')


def sub_dir(name, url, icon):
    link = downloads.get_url(url)
    addDir(_top + name + __artists, url + '?page=1', 31,
           artgenre + name.replace(' ', '').replace('&amp;', '_').lower() +
           '/' + 'top' + name.replace(' ', '').replace('&amp;', '_').lower() +
           '.jpg', '', '', '')
    sub_dir = re.compile('<li class="menu_sub__item"><a class='
                         '"menu_sub__link" href="(.+?)">(.+?)</a>'
                         '</li>').findall(link)
    for url, title in sub_dir:
        addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url + '?page=1',
               31, artgenre + name.replace(' ', '').replace('&amp;',
               '_').lower() + '/' + title.replace(' ', '').replace('&amp;',
               '_').lower() + '.jpg', '', '', '')


def genres(name, url):
    link = downloads.get_url(url)
    if name == _top_albums:
        addDir(_top_albums, MUSIC_DIR_URL + '/top-albums?page=1', 15,
               artfolder + 'alltopalbums.jpg', '', '', '')
    else:
        addDir(_new_albums, MUSIC_DIR_URL + '/new-albums?page=1', 15,
               artfolder + 'allnewalbums.jpg', '', '', '')
    sub_dir = re.compile('<li class="menu_sub__item"><a class='
                         '"menu_sub__link" href="(.+?)">(.+?)</a>'
                         '</li>').findall(link)
    for url1, title in sub_dir:
        iconimage = (MUSIC_DIR_URL + '/i' + url1.replace('.html',
                     '.jpg').replace('tracks', 'track'))
        addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url1, 14,
               artgenre + title.replace(' ', '').replace('&amp;',
               '_').lower() + '.jpg', '', '', '')


def all_genres(name, url):
    nxtpgnum = int(url.replace(MUSIC_DIR_URL + '/main_albums?gnr_id=2&sort='
                   'top&type=album&page=', '')) + 1
    nxtpgurl = "%s%s" % (MUSIC_DIR_URL + '/main_albums?gnr_id=2&sort='
                         'top&type=album&page=', str(nxtpgnum))
    link = downloads.get_url(url)
    all_genres = re.compile('<li class="small_list__item"><a class='
                            '"small_list__link" href="(.+?)">(.+?)</a>'
                            '</li>').findall(link)
    for url1, title in all_genres:
        addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url1, 22,
               'http://www.pearljamlive.com/images/pic_home.jpg', '')
    addDir('>> Next page', nxtpgurl, 13,
           xbmc.translatePath(os.path.join('special://home/addons/'
                                           'plugin.audio.mp3music',
                                           'media', 'nextpage.jpg')))


def genre_sub_dir(name, url, icon):
    link = downloads.get_url(url)
    if url[19:22] == 'top':
        addDir(_top + name + __artists, url + '?page=1', 15, artgenre +
               name.replace('and', '&').replace(' ', '').
               replace('&amp;', '_').lower() + '/top' + name.
               replace('and', '_').replace(' ', '').
               replace('&amp;', '_').lower() + '.jpg', '', '', '')
    else:
        addDir(_new + name + __albums, url + '?page=1', 15, artgenre +
               name.replace('and', '&').replace(' ', '').
               replace('&amp;', '_').lower() + '/top' + name.
               replace('and', '_').replace(' ', '').
               replace('&amp;', '_').lower() + '.jpg', '', '', '')
    sub_dir = re.compile('<li class="menu_sub__item"><a class='
                         '"menu_sub__link" href="(.+?)">(.+?)</a>'
                         '</li>').findall(link)
    for url, title in sub_dir:
        addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url + '?page=1',
               15, artgenre + name.replace('and', '&').replace(' ',
               '').replace('&amp;', '_').lower() + '/' + title.replace(' ',
               '').replace('&amp;', '_').lower() + '.jpg', '', '', '')


def genre_sub_dir2(name, url, icon):
    link = downloads.get_url(url)
    addDir('%s%s%s' % (_top, name, __albums), url, 15,
           os.path.join(genre, 'alltopalbums.jpg'), '')
    sub_dir = re.compile('<li class="menu_sub__item"><a class='
                         '"menu_sub__link" href="(.+?)">(.+?)</a>'
                         '</li>').findall(link)
    for url, title in sub_dir:
        addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url +
               '?page=1', 15, icon, '', '', '')


def compilations_list(name, url, iconimage, page):
    if page != 'n':
        nextpage = int(page) + 1
        nxtpgf = url.find('page=') + 5
        nxtpgurl = url[:nxtpgf]
        url = "%s%s" % (nxtpgurl, page)
    link = downloads.get_url(url)
    match = re.compile('<div><a href="(.+?)"><img alt="(.+?)" src="(.+?)"/>'
    	               '</a><a class="(.+?)" href="(.+?)">(.+?)</a><span '
    	               'class="(.+?)">(.+?)</span><span class="f_year">'
    	               '(.+?)</span><span class="ga_price">(.+?)'
    	               '</span></div>').findall(link)
    for url, d1, iconimage, cl, url2, title, cl, artist, year, prc in match:
        url = 'http://www.goldenmp3.ru' + url
        addDir(title.replace('&amp;', 'and'), url, 5, iconimage, 'albums', year, '')
    addDir('>> Next page', nxtpgurl, 401, xbmc.translatePath(os.path.join(
           'special://home/addons/plugin.audio.mp3music', 'media',
           'nextpage.jpg')), str(nextpage), '', '')
    setView('movies', 'album')


def search_lists():
    menuitems = [(_search_artists, 'url', 24, 'searchartists.jpg'),
                 (_search_albums, 'url', 24, 'searchalbums.jpg'),
                 (_search_songs, 'url', 24, 'searchsongs.jpg')]
    for title, url, mode, iconimage in menuitems:
        addDir(title, url, mode, artfolder + iconimage, '', '', '')


def search(name, url):
    keyboard = xbmc.Keyboard('', name, False)
    keyboard.doModal()
    if keyboard.isConfirmed():
        query = keyboard.getText()
        if len(query) > 0:
            if name == _search_artists:
                search_artists(query)
            elif name == _search_albums:
                search_albums(query)
            elif name == _search_songs:
                search_songs(query)


def search_artists(query):
    url = (MUSIC_DIR_URL + '/search.html?text=%s&all=artists' %
           urllib.quote_plus(query))
    link = downloads.get_url(url)
    all_artists = re.compile('<a class="artist_preview__title" href='
                             '"(.+?)">(.+?)</a>').findall(link)
    for url1, title in all_artists:
        icon_path = os.path.join(__artist_art__, title + '.jpg')
        if os.path.exists(icon_path):
            iconimage = icon_path
        else:
            iconimage = iconart
        addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url1, 22,
               iconimage, 'artists', '', '')


def search_albums(query):
    url = (MUSIC_DIR_URL + '/search.html?text=%s&all=albums' %
           urllib.quote_plus(query.replace(' - ', ' ').replace('-', ' ')))
    link = downloads.get_url(url)
    link = link.replace('<span class="album_report__artist">Various Artists'
                        '</span>', '<a class="album_report__artist" href='
                        '"/artist_various-artist">Various Artist</a>')
    all_albums = re.compile('<a class="album_report__link" href="(.+?)">'
    	                    '<img class="album_report__image" src="(.+?)"/>'
    	                    '<span class="album_report__name">(.+?)</span>'
    	                    '</a></h5><div class="album_report__second_line">'
    	                    '<a class="album_report__artist" href="(.+?)">'
    	                    '(.+?)</a>, <span class="album_report__date">'
    	                    '(.+?)</span></div>').findall(link)
    for url1, thumb, album, artisturl, artist, year in all_albums:
        title = "%s - %s (%s)" % (artist, album, year)
        thumb = thumb.replace('al', 'alm').replace('covers', 'mcovers')
        addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url1, 5,
               thumb, 'albums', year, '')
    setView('movies', 'album')


def search_songs(query):
    playlist = []
    url = (MUSIC_DIR_URL + '/search.html?text=%s&all=songs' %
           urllib.quote_plus(query.replace(' - ', ' ').
                             replace('-', ' ').replace(' FT ', ' ')))
    link = downloads.get_url(url)
    match = re.compile('<tr class="song"><td class="song__play_button"><a '
    	               'class="player__play_btn js_play_btn" href="#" '
    	               'rel="(.+?)" title="Play track"/></td><td '
    	               'class="song__name song__name--search"><a '
    	               'class="song__link" href="(.+?)">(.+?)</a>'
    	               '(.+?)song__link" href="(.+?)">(.+?)</a>'
    	               '(.+?)<a class="song__link" href="(.+?)">'
    	               '(.+?)</a>').findall(link)
    for id, songurl, song, d1, artisturl, artist, d2, albumurl, album in match:
        iconimage = ""
        url = MUSIC_LISTEN_URL + id
        title = "%s - %s - %s" % (artist.replace('&amp;', 'and'),
                                  song.replace('&amp;', '&'),
                                  album.replace('&amp;', '&'))
        addDirAudio(title, url, 10, iconimage, song, artist, album, '', '', '', '')
        liz = xbmcgui.ListItem(song,
                               iconImage=iconimage,
                               thumbnailImage=iconimage)
        liz.setInfo('music', {'Title': song, 'Artist': artist, 'Album': album})
        liz.setProperty('mimetype', 'audio/mpeg')
        liz.setThumbnailImage(iconimage)
        liz.setProperty('fanart_image', fetch_fanart(artist))
        playlist.append((url, liz))
    setView('music', 'song')


def list_albums(name, url):
    duplicate = []
    link = downloads.get_url(url)
    try:
        artist_url = commontasks.regex_from_to(link, 'class="art_wrap__img" src="', '"')
        get_artist_icon(name, artist_url)
    except:
        pass

    trial1 = re.compile('<a class="album_report__link" href="(.+?)">'
                            '<img alt="(.+?)" class="album_report__image" '
                            'src="(.+?)"/><span class="album_report__name">'
                            '(.+?)</span>(.+?)</ul>').findall(link)
    for url1, d1, thumb, album, raw_data in trial1:
        genre = ''
        artist = name
        trial2 = re.compile('(.+?)<span class="album_report__date">(.+?)</span>'
                            '</div>(.+?)</ul>').findall(raw_data + '</ul>')
        for artists, year, raw_genre in trial2:
            all_artists = re.compile('<a class="album_report__artist" href="(.+?)">(.+?)</a>').findall(artists)
            for artisturl, nartist in all_artists:
                artist = nartist
            all_genres = re.compile('<li class="tags__item">(.+?)</li>').findall(raw_genre)
            for genres in all_genres:
                genre += genres + ', '
            genre = genre[:-2]
        title = "%s - %s (%s)" % (artist, album, year)
        if title not in duplicate:
            duplicate.append(title)
            thumb = thumb.replace('al', 'alm').replace('covers', 'mcovers')
            addDir(title.replace('&amp;', 'and'), MUSIC_DIR_URL + url1, 5,
                   thumb, 'albums', year, genre)
    if url.find('page=') > 0:
        pgnumf = url.find('page=') + 5
        pgnum = int(url[pgnumf:]) + 1
        nxtpgurl = url[:pgnumf]
        nxtpgurl = "%s%s" % (nxtpgurl, pgnum)
        addDir('>> Next page', nxtpgurl, 15,
               xbmc.translatePath(os.path.join('special://home/addons/'
                                               'plugin.audio.mp3music',
                                               'media', 'nextpage.jpg')), '', '', '')
    setView('movies', 'album')


def play_album(name, url, iconimage, mix, clear, genre):
    if ' - ' in name:
        nartist = name.split(' - ')[0]
        nalbum = name.split(' - ')[1].split('(')[0]
    else:
        nartist = 'Various'
        nalbum = name
    nyear = name[name.find("(")+1:name.find(")")]
    url = url.replace('mp3music', 'www.goldenmp3').replace('ru/compilation/', 'ru/compilations/')
    link = downloads.get_url(url)
    filtered_url = commontasks.regex_from_to(link,'<tbody>','</tbody>')
    std = ('href="#" rel="(.+?)" title="Listen the song in low quality">(.+?)</a>'
           '</td><td><div class="title_td_wrap">(.+?)<span itemprop="name">(.+?)<'
           '/span>(.+?)<div ')
    match = re.compile(std).findall(filtered_url)
    browse = False
    playlist = []
    dialog = xbmcgui.Dialog()
    if mode != 6 and mix != 'mix' and mix != 'queue':
        if not dialog.yesno(_mp3_music, _browse_songs_or_play_album,
                        '', '', _browse, _play_now):
            browse = True
    if browse:
        for (song_id, crap1, track, songname, dur) in match:
            track = track.replace('.&ensp;', '')
            url = MUSIC_LISTEN_URL + song_id
            songname = songname.replace('&amp;', 'and')
            artist = nartist.replace('&amp;', 'and')
            album = nalbum.replace('&amp;', 'and')
            title = "%s. %s" % (track, songname)
            dur = dur.replace('.ensp;', '')
            addDirAudio(title, url, 10, iconimage, songname, artist,
                        album, dur, '', nyear, genre)
        return

    if mix != 'mix':
        dp = xbmcgui.DialogProgress()
        dp.create(_mp3_music, _creating_your_playlist)
        dp.update(0)

    nItem = 0
    for (song_id, crap1, track, songname, dur) in match:
        track = track.replace('.&ensp;', '')
        url = MUSIC_LISTEN_URL + song_id
        songname = songname.replace('&amp;', 'and')
        artist = nartist.replace('&amp;', 'and')
        album = nalbum.replace('&amp;', 'and')
        title = "%s. %s" % (track, songname)
        dur = dur.replace('.ensp;', '')
        addDirAudio(title,
                    url,
                    10,
                    iconimage,
                    songname,
                    artist,
                    album,
                    dur, '', nyear, genre)

        url, liz = playerMP3.getListItem(songname,
                                         artist,
                                         album,
                                         track,
                                         iconimage,
                                         dur,
                                         url,
                                         fanart,
                                         'true',
                                         True)

        if __folder_structure__ == "0":
            stored_path = os.path.join(__music_dir__,
                                       artist,
                                       album,
                                       songname + '.mp3')
        else:
            stored_path = os.path.join(__music_dir__,
                                       artist + ' - ' + album,
                                       songname + '.mp3')
        if os.path.exists(stored_path):
            url = stored_path

        playlist.append((url, liz))

        nItem += 1
        if mix != 'mix':
            progress = len(playlist) / float(nItem) * 100
            dp.update(int(progress), _adding_to_your_playlist, title)
            if dp.iscanceled():
                return

    pl = get_XBMCPlaylist(clear)
    for url, liz in playlist:
        pl.add(url, liz)
        # if pl.size() > 3:
        #    break

    dp.close()
    if clear or (not xbmc.Player().isPlayingAudio()):
        xbmc.Player().play(pl)


def play_song(url, name, songname, artist, album, iconimage, dur, clear):
    try:
        track = int(name[:name.find('.')])
    except:
        try:
            track = int(songname[:songname.find('.')])
        except:
            track = 0
    title = songname
    try:
      artist_fanart = get_current_artist_images(artist)[1]
    except:
      artist_fanart = fanart
    url, liz = playerMP3.getListItem(title,
                                     artist,
                                     album,
                                     track,
                                     iconimage,
                                     dur,
                                     url,
                                     artist_fanart,
                                     'true',
                                     True)

    if __folder_structure__ == "0":
        stored_path = os.path.join(__music_dir__,  artist,
                                   album,
                                   title + '.mp3')
    else:
        stored_path = os.path.join(__music_dir__,
                                   artist + ' - ' + album,
                                   title + '.mp3')

    if os.path.exists(stored_path):
        url = stored_path

    pl = get_XBMCPlaylist(clear)
    pl.add(url, liz)

    if clear or (not xbmc.Player().isPlayingAudio()):
        xbmc.Player().play(pl)


def get_artist_icon(name, url):
    data_path = os.path.join(__artist_art__, name + '.jpg')
    if not os.path.exists(data_path):
        dlThread = DownloadIconThread(name, url, data_path)
        dlThread.start()


def instant_mix():
    menu_texts = []
    menu_texts.append(_all_songs)
    dialog = xbmcgui.Dialog()
    if os.path.isfile(__fav_song__):
        s = commontasks.read_from_file(__fav_song__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                list1 = list.split('<>')
                try:
                    plname = list1[5]
                    if plname not in menu_texts:
                        menu_texts.append(plname)
                except:
                    if "Ungrouped" not in menu_texts:
                        menu_texts.append("Ungrouped")
    menu_id = dialog.select(_select_group, menu_texts)
    if(menu_id < 0):
        return (None, None)
        dialog.close()
    groupname = menu_texts[menu_id]

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    if os.path.isfile(__fav_song__):
        s = commontasks.read_from_file(__fav_song__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                splitdata = list.split('<>')
                artist = splitdata[0]
                album = splitdata[1]
                songname = splitdata[2]
                url1 = splitdata[3].replace('listen.musicmp3.ru',
                                            'files.mp3music.ru/lofi')
                iconimage = splitdata[4]
                try:
                    plname = splitdata[5]
                except:
                    plname = "Ungrouped"
                if (plname == groupname) or groupname == _all_songs:
                    play_song(url1,
                              songname,
                              songname,
                              artist,
                              album,
                              iconimage,
                              '',
                              False)
    playlist.shuffle()


def instant_mix_album():
    menu_texts = []
    menu_texts.append(_all_albums)
    dialog = xbmcgui.Dialog()
    if os.path.isfile(__fav_album__):
        s = commontasks.read_from_file(__fav_album__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                list1 = list.split('<>')
                try:
                    plname = list1[3]
                    if plname not in menu_texts:
                        menu_texts.append(plname)
                except:
                    if "Ungrouped" not in menu_texts:
                        menu_texts.append("Ungrouped")
    menu_id = dialog.select(_select_group, menu_texts)
    if(menu_id < 0):
        return (None, None)
        dialog.close()
    groupname = menu_texts[menu_id]
    shuffleThread = ShuffleAlbumThread(groupname)
    shuffleThread.start()


class ShuffleAlbumThread(Thread):
    def __init__(self, groupname):
        self.groupname = groupname
        Thread.__init__(self)

    def run(self):
        groupname = self.groupname
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        if os.path.isfile(__fav_album__):
            s = commontasks.read_from_file(__fav_album__)
            search_list = s.split('\n')
            for list in search_list:
                if list != '':
                    list1 = list.split('<>')
                    title = list1[0]
                    url = list1[1]
                    thumb = list1[2]
                    try:
                        plname = list1[3]
                    except:
                        plname = "Ungrouped"
                    if (plname == groupname) or groupname == _all_albums:
                        play_album(title, url, thumb, 'mix', False, '')
                        playlist.shuffle()
                    xbmc.sleep(15000)


class DownloadIconThread(Thread):
    def __init__(self, name, url, data_path):
        self.data = url
        self.path = data_path
        Thread.__init__(self)

    def run(self):
        path = str(self.path)
        data = self.data
        try:
            urllib.urlretrieve(data, path)
        except:
            pass


def favourite_lists():
    menuitems = [(_favourite_artists, 'url', 63, 'favouriteartists.jpg'),
                 (_favourite_albums, 'url', 66, 'favouritealbums.jpg'),
                 (_favourite_songs, 'url', 69, 'favouritesongs.jpg'),
                 (_instant_mix_favourite_albums, 'url', 89, 'mixfavouritealbums.jpg'),
                 (_instant_mix_favourite_songs, 'url', 99, 'mixfavouritesongs.jpg')]
    for title, url, mode, iconimage in menuitems:
        if title.find(_instant) >= 0:
            addDirAudio(title, url, mode, artfolder + iconimage, '', '', '', '', '', '', '')            
        else:
            addDir(title, url, mode, artfolder + iconimage, '', '', '')


def favourite_artists():
    if os.path.isfile(__fav_artist__):
        s = commontasks.read_from_file(__fav_artist__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                list1 = list.split('<>')
                title = list1[0]
                url = list1[1]
                icon_path = os.path.join(__artist_art__, title + '.jpg')
                if os.path.exists(icon_path):
                    iconimage = icon_path
                else:
                    iconimage = iconart
                addDir(title.replace('&amp;', '&'),
                       url,
                       22,
                       iconimage,
                       'artists', '', '')


def favourite_albums():
    menu_texts = []
    menu_texts.append("All Albums")
    dialog = xbmcgui.Dialog()
    if os.path.isfile(__fav_album__):
        s = commontasks.read_from_file(__fav_album__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                list1 = list.split('<>')
                try:
                    plname = list1[3]
                    if plname not in menu_texts:
                        menu_texts.append(plname)
                except:
                    if "Ungrouped" not in menu_texts:
                        menu_texts.append("Ungrouped")
    menu_id = dialog.select(_select_group, menu_texts)
    if(menu_id < 0):
        return (None, None)
        dialog.close()
    groupname = menu_texts[menu_id]
    if os.path.isfile(__fav_album__):
        s = commontasks.read_from_file(__fav_album__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                list1 = list.split('<>')
                title = list1[0]
                url = list1[1]
                thumb = list1[2]
                try:
                    plname = list1[3]
                except:
                    plname = "Ungrouped"
                if (plname == groupname) or groupname == _all_albums:
                    addDir(title.replace('&amp;', '&'),
                           url,
                           5,
                           thumb,
                           plname + 'qqalbums', '', '')


def favourite_songs():
    menu_texts = []
    menu_texts.append(_all_songs)
    dialog = xbmcgui.Dialog()
    if os.path.isfile(__fav_song__):
        s = commontasks.read_from_file(__fav_song__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                list1 = list.split('<>')
                try:
                    plname = list1[5]
                    if plname not in menu_texts:
                        menu_texts.append(plname)
                except:
                    if "Ungrouped" not in menu_texts:
                        menu_texts.append("Ungrouped")
    menu_id = dialog.select(_select_group, menu_texts)
    if(menu_id < 0):
        return (None, None)
        dialog.close()
    groupname = menu_texts[menu_id]

    if os.path.isfile(__fav_song__):
        s = commontasks.read_from_file(__fav_song__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                list1 = list.split('<>')
                artist = list1[0]
                album = list1[1]
                title = list1[2]
                url = list1[3].replace('listen.musicmp3.ru',
                                       'files.mp3music.ru/lofi')
                iconimage = list1[4]
                try:
                    plname = list1[5]
                except:
                    plname = "Ungrouped"
                text = "%s - %s - %s" % (title, artist, album)
                if (plname == groupname) or groupname == _all_songs:
                    addDirAudio(text,
                                url,
                                10,
                                iconimage,
                                title,
                                artist,
                                album,
                                'qq' + plname,
                                'favsong', '')


def add_favourite(name, url, dir, text):
    splitdata = url.split('<>')
    if 'artist' in dir:
        artist = splitdata[0]
        url1 = splitdata[1]
        commontasks.add_to_list(url, dir, True)
        commontasks.notification(name,
                     "[COLOR lime]" + text + "[/COLOR]",
                     '5000',
                     '')
        link = downloads.get_url(url1)
        try:
            artist_url = commontasks.regex_from_to(link,
                                                   'class="art_wrap__img" src="',
                                                   '"')
            get_artist_icon(artist, artist_url)
        except:
            pass
    else:
        menu_texts = []
        menu_texts.append(_add_new_group)
        dialog = xbmcgui.Dialog()
        if os.path.isfile(dir):
            s = commontasks.read_from_file(dir)
            search_list = s.split('\n')
            for list in search_list:
                if list != '':
                    list1 = list.split('<>')
                    try:
                        plname = list1[3]
                        if plname not in menu_texts:
                            menu_texts.append(plname)
                    except:
                        pass
        menu_id = dialog.select(_select_group, menu_texts)
        if(menu_id < 0):
            return (None, None)
            dialog.close()
        if (menu_id == 0):
            keyboard = xbmc.Keyboard('', _create_new_group, False)
            keyboard.doModal()
            if keyboard.isConfirmed():
                query = keyboard.getText()
                if len(query) > 0:
                    plname = query
        else:
            plname = menu_texts[menu_id]
        artist = splitdata[0]
        url1 = splitdata[1]
        thumb = splitdata[2]
        url = "%s<>%s" % (url, plname)
        if 'artist' in dir:
            commontasks.add_to_list(url, dir, True)
        else:
            commontasks.add_to_list(url, dir, False)
        commontasks.notification(name,
                     "[COLOR lime]" + text + "[/COLOR]",
                     '5000',
                     thumb)


def add_favourite_song(name, url, dir, text):
    menu_texts = []
    menu_texts.append(_add_new_group)
    dialog = xbmcgui.Dialog()
    if os.path.isfile(__fav_song__):
        s = commontasks.read_from_file(__fav_song__)
        search_list = s.split('\n')
        for list in search_list:
            if list != '':
                list1 = list.split('<>')
                try:
                    plname = list1[5]
                    if plname not in menu_texts:
                        menu_texts.append(plname)
                except:
                    pass
    menu_id = dialog.select(_select_group, menu_texts)
    if(menu_id < 0):
        return (None, None)
        dialog.close()
    if (menu_id == 0):
        keyboard = xbmc.Keyboard('', _create_new_group, False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
            if len(query) > 0:
                plname = query
    else:
        plname = menu_texts[menu_id]
    splitdata = url.split('<>')
    artist = splitdata[0]
    album = splitdata[1]
    songname = splitdata[2]
    url1 = splitdata[3]
    iconimage = splitdata[4]
    url = "%s<>%s" % (url, plname)
    commontasks.add_to_list(url, dir, False)
    commontasks.notification(songname,
                 "[COLOR lime]" + text + "[/COLOR]",
                 '5000',
                 iconimage)


def remove_from_favourites(name, url, dir, text):
    splitdata = url.split('<>')
    artist = splitdata[0]
    url1 = splitdata[1]
    try:
        thumb = splitdata[2]
    except:
        thumb = ''
    commontasks.remove_from_list(url, dir)
    commontasks.notification(name,
                 "[COLOR orange]" + text + "[/COLOR]",
                 '5000',
                 thumb)
    xbmc.executebuiltin("Container.Refresh")


def get_params():
        param = []
        paramstring = sys.argv[2]
        if len(paramstring) >= 2:
                params = sys.argv[2]
                cleanedparams = params.replace('?', '')
                if (params[len(params)-1] == '/'):
                        params = params[0:len(params) - 2]
                pairsofparams = cleanedparams.split('&')
                param = {}
                for i in range(len(pairsofparams)):
                        splitparams = {}
                        splitparams = pairsofparams[i].split('=')
                        if (len(splitparams)) == 2:
                                param[splitparams[0]] = splitparams[1]

        return param


def get_XBMCPlaylist(clear):
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    if clear:
        pl.clear()
    return pl


def clear_playlist():
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()
    commontasks.notification(_playlist, _cleared, '2000', iconart)


def setView(content, viewType):
    if content:
        xbmcplugin.setContent(int(sys.argv[1]), content)


def addDir(name, url, mode, iconimage, type, year, genre):
    type1 = type
    type = type.replace('qq', '')
    suffix = ''
    is_folder = True
    replace_items = False
    if type == "artists":
        list = "%s<>%s" % (str(name), url)
    else:
        if 'qq' in type1:
            spltype1 = type1.split('qq')
            list = "%s<>%s<>%s<>%s" % (str(name),
                                       url,
                                       str(iconimage),
                                       spltype1[0])
        else:
            list = "%s<>%s<>%s" % (name.encode("utf-8"),
                                   url, str(iconimage))
    list = list.replace(',', '')
    u = (sys.argv[0] +
         "?url=" + urllib.quote_plus(url) +
         "&mode=" + str(mode) +
         "&name=" + urllib.quote_plus(name) +
         "&iconimage=" + urllib.quote_plus(iconimage) +
         "&list=" + str(list) + "&type=" + str(type) + 
         "&genre=" + urllib.quote_plus(genre))
    ok = True
    contextMenuItems = []
    if type == "artists":
        if commontasks.find_list(list, __fav_artist__) < 0:
            suffix = ''
            contextMenuItems.append((_artist_info_heading,
                                      'XBMC.RunPlugin(%s?name=%s&url'
                                      '=%s&mode=4)' %
                                      (sys.argv[0],
                                       name,
                                       str(list))))
            if os.path.exists(download_lock):
                contextMenuItems.append((_clear_download_lock_heading,
                                         'XBMC.RunPlugin(%s?name=%s&url'
                                         '=%s&iconimage=%s&mode=333)' %
                                         (sys.argv[0],
                                          urllib.quote(name),
                                          url,
                                          iconimage)))
            contextMenuItems.append((_added_to_favourite_artists_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url'
                                     '=%s&mode=61)' %
                                     (sys.argv[0],
                                      name,
                                      str(list))))
        else:
            items = name.split(' - ')
            contextMenuItems.append((_artist_info_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url'
                                     '=%s&mode=4)' %
                                     (sys.argv[0],
                                      items[0],
                                      str(list))))
            suffix = ' [COLOR lime]+[/COLOR]'
            contextMenuItems.append((_remove_from_favourite_artists_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url='
                                     '%s&mode=62)' %
                                     (sys.argv[0],
                                      name,
                                      str(list))))
    if 'album' in type:
        items = name.split(' - ')
        contextMenuItems.append((_artist_info_heading,
                                  'XBMC.RunPlugin(%s?name=%s&url'
                                  '=%s&mode=4)' %
                                  (sys.argv[0],
                                   items[0],
                                   str(list))))
        if os.path.exists(download_lock):
            contextMenuItems.append((_clear_download_lock_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url'
                                     '=%s&iconimage=%s&mode=333)' %
                                     (sys.argv[0],
                                      urllib.quote(name),
                                      url,
                                      iconimage)))
        download_album = ('%s?name=%s&url=%s&iconimage=%s&year=%s&genre=%s&mode=202' %
                          (sys.argv[0],
                           urllib.quote(name),
                           url,
                           iconimage,
                           year,
                           urllib.quote(genre)))
        contextMenuItems.append((_download_album_heading,
                                 'XBMC.RunPlugin(%s)' % download_album))
        if __queue_albums__:
            play_music = ('%s?name=%s&url=%s&iconimage=%s&mode=7' %
                          (sys.argv[0],
                           urllib.quote(name),
                           url,
                           iconimage))
            contextMenuItems.append((_play_browse_album_heading,
                                     'XBMC.RunPlugin(%s)' % play_music))
        else:
            queue_music = ('%s?name=%s&url=%s&iconimage=%s&mode=6' %
                           (sys.argv[0],
                            urllib.quote(name),
                            url,
                            iconimage))
            contextMenuItems.append((_queue_album_heading,
                                     'XBMC.RunPlugin(%s)' % queue_music))
        if 'qq' not in type1:
            suffix = ""
            contextMenuItems.append((_add_to_favourite_albums_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url='
                                     '%s&mode=64)' %
                                     (sys.argv[0],
                                      name.replace(',', ''),
                                      str(list))))
        else:
            suffix = ' [COLOR lime]+[/COLOR]'
            contextMenuItems.append((_remove_from_favourite_albums_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url='
                                     '%s&mode=65)' %
                                     (sys.argv[0],
                                      name.replace(',', ''),
                                      str(list))))
    if type == 'downloadlist':
        if (not _clear_downloads in name) and (not _start_downloads in name):
            items = name.split(' - ')
            contextMenuItems.append((_artist_info_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url'
                                     '=%s&mode=4)' %
                                     (sys.argv[0],
                                      items[0],
                                      str(list))))
            contextMenuItems.append((_remove_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url='
                                     '%s&mode=800)' %
                                     (sys.argv[0],
                                      name.replace(',', ''),
                                      str(list))))
        else:
            is_folder = False
    elif type == 'settings' or type == 'clearplaylist':
        suffix = ''
        is_folder = False


    liz = xbmcgui.ListItem(name + suffix,
                           iconImage="DefaultAudio.png",
                           thumbnailImage=iconimage)
    liz.setInfo('music', {'Title': name,
                          'Genre': genre,
                          'Year': year})
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    liz.setProperty('fanart_image', fetch_fanart(name))
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                     url=u,
                                     listitem=liz,
                                     isFolder=is_folder)
    return ok


def addDirAudio(name, url, mode, iconimage, songname, artist, album, dur, type, year, genre):
    suffix = ""
    if 'qq' in dur:
        list = "%s<>%s<>%s<>%s<>%s<>%s" % (str(artist),
                                           str(album),
                                           str(songname).lower(),
                                           url,
                                           str(iconimage),
                                           str(dur).replace('qq',
                                           ''))
    else:
        list = "%s<>%s<>%s<>%s<>%s" % (str(artist),
                                       str(album),
                                       str(songname).lower(),
                                       url,
                                       str(iconimage))
    list = list.replace(', ', '')
    contextMenuItems = []
    u = sys.argv[0] + ("?url=" + urllib.quote_plus(url) +
                       "&mode=" + str(mode) +
                       "&name=" + urllib.quote_plus(name) +
                       "&iconimage=" + urllib.quote_plus(iconimage) +
                       "&songname=" + urllib.quote_plus(songname) +
                       "&artist=" + urllib.quote_plus(artist) +
                       "&album=" + urllib.quote_plus(album) +
                       "&dur=" + str(dur) +
                       "&type=" + str(type))
    ok = True
    if os.path.exists(download_lock):
        contextMenuItems.append((_clear_download_lock_heading,
                                'XBMC.RunPlugin(%s?name=%s&url='
                                '%s&iconimage=%s&songname=%s&artist='
                                '%s&album=%s&mode=333)' %
                                (sys.argv[0],
                                 songname,
                                 url,
                                 iconimage,
                                 name,
                                 artist,
                                 album)))
    if type == 'downloadlist':
        if (not _clear_downloads in name) and (not _start_downloads in name):
            items = name.split(' - ')
            contextMenuItems.append((_artist_info_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url'
                                     '=%s&mode=4)' %
                                     (sys.argv[0],
                                      items[0],
                                      str(list))))
            contextMenuItems.append((_remove_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url='
                                     '%s&mode=800)' %
                                     (sys.argv[0],
                                      name.replace(',', ''),
                                      str(list))))
        else:
            is_folder = False
    else:
        download_song = ('%s?name=%s&url=%s&iconimage=%s&songname=%s&artist='
                         '%s&album=%s&year=%s&genre=%s&mode=201' %
                         (sys.argv[0],
                          urllib.quote(songname),
                          url,
                          iconimage,
                          urllib.quote(name),
                          artist,
                          album,
                          year,
                          urllib.quote(genre)))
        contextMenuItems.append((_download_song_heading,
                                 'XBMC.RunPlugin(%s)' % download_song))
        if __queue_songs__:
            queue_song = ('%s?name=%s&url=%s&iconimage=%s&songname='
                          '%s&artist=%s&album=%s&dur=%s&mode=11' %
                          (sys.argv[0],
                           urllib.quote(songname),
                           url,
                           iconimage,
                           songname,
                           artist,
                           album,
                           dur))
            contextMenuItems.append((_queue_song_heading,
                                     'XBMC.RunPlugin(%s)' % queue_song))
        else:
            play_song = ('%s?name=%s&url=%s&iconimage=%s&songname=%s&artist='
                         '%s&album=%s&dur=%s&mode=18' %
                         (sys.argv[0],
                          urllib.quote(songname),
                          url,
                          iconimage,
                          urllib.quote(name),
                          artist,
                          album,
                          dur))
            contextMenuItems.append((_play_song_heading,
                                     'XBMC.RunPlugin(%s)' % play_song))
        if type != 'favsong':
            suffix = ""
            contextMenuItems.append((_add_to_favourite_songs_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url='
                                     '%s&mode=67)' %
                                     (sys.argv[0],
                                      name.replace(',', ''),
                                      str(list))))
        else:
            suffix = ' [COLOR lime]+[/COLOR]'
            contextMenuItems.append((_remove_from_favourite_songs_heading,
                                     'XBMC.RunPlugin(%s?name=%s&url='
                                     '%s&mode=68)' %
                                     (sys.argv[0],
                                      name.replace(',', ''),
                                      str(list))))
    liz = xbmcgui.ListItem(name + suffix,
                           thumbnailImage=iconimage)
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    liz.setInfo('mediatype', 'song')
    liz.setInfo('music', {'Title': name,
                          'Artist': artist,
                          'Album': album,
                          'Genre': genre,
                          'Year': year})
    if not __hide_fanart__:
        if len(str(artist)) > 0:
            liz.setProperty('fanart_image', get_current_artist_images(artist)[1])
        else:
            liz.setProperty('fanart_image', fetch_fanart(name))
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                     url=u, listitem=liz)
    return ok


def fetch_fanart(name):
    if name.find(' - ') > 0:
        fanartimage = os.path.join(__artist_art__, name.split(' - ')[0] + "_fanart.jpg")
    else:
        fanartimage = os.path.join(__artist_art__, name + "_fanart.jpg")
    if not os.path.exists(fanartimage):
        fanartimage = os.path.join(artfolder + 'genre',
                                   name.replace('&', '_').replace(' ', '').lower() + "_fanart.jpg")
    if not os.path.exists(fanartimage):
        return fanart
    else:
        return fanartimage


def get_current_artist_images(artistname=None, artistinfo=None):
    '''
    Discover artist name, download image and return the image path.
    If no image can be found return the default image instead
    '''
    fanartimage = ''
    thumb = ''
    days = 28
    if len(artistname) > 1:
        # Find the artist information
        if artistinfo == None:
            artist_info = ArtistInfo(artistname)
        else:
            artist_info = artistinfo
        try:
            # Remove temporary images older than 28 days
            commontasks.remove_old_temp_files(__artist_art__, days)
        except:
            pass
        try:
            # Download artist thumbnail image
            icon_path = os.path.join(__artist_art__, artistname + '.jpg')
            if (not os.path.exists(icon_path) and not artist_info.artist_thumb == None):
                urllib.urlretrieve(artist_info.artist_thumb, icon_path)
                commontasks.resize_image(icon_path, 256, 256)
            else:
                thumb = artist_info.artist_thumb
        except:
            # Use MP3 Music default thumbnail
            thumb = iconart
        try:
            # Download artist fanart image
            fanart_path = os.path.join(__artist_art__, artistname + '_fanart.jpg')
            if (not os.path.exists(fanart_path) and not artist_info.fanart == None):
                urllib.urlretrieve(artist_info.fanart, fanart_path)
                commontasks.resize_image(icon_path, 1280, 720)
            else:
                fanartimage = artist_info.fanart
        except:
            # Use MP3 Music default fanart
            fanartimage = fanart
    return thumb, fanartimage


def show_artist_info(artist):
    '''
    Show artist image and information
    '''
    try:
        if len(artist) > 0:
            artist_info = ArtistInfo(artist)
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
            get_current_artist_images(artist, artist_info)
            window = xbmcgui.WindowXMLDialog('plugin-audio-mp3music.xml',
                                             __addon__.getAddonInfo('path'))
            win = xbmcgui.Window(10147)
            win.setProperty('HeadingLabel',
                            artist)
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
    except:
        commontasks.message(_unable_to_download_artist_info, _artist_info)


''' Main Sub '''

params = get_params()
url = None
name = None
mode = None
genre = ''
dur = ''

param_names = ('url', 'name', 'iconimage', 'songname', 'artist', 'album',
		       'year', 'genre', 'list', 'dur', 'type', 'mode')
for item in param_names:
    try:
        if param_names.index(item) > 7:
            if item == 'mode':
                locals()[item] = int(params[item])
            else:
                locals()[item] = str(params[item])
        else:
            locals()[item] = urllib.unquote_plus(params[item].encode("utf-8"))
    except:
        pass

# commontasks.message('name: %s\nurl:  %s\nmode: %s' % (name, url, str(mode)), name)

if mode is None or url is None or len(url) < 1:  # Main listing
    CATEGORIES()
elif mode == 4:
    show_artist_info(name)
#elif mode == 4:
#    charts()
elif mode == 5:  # Play specific album or list songs on the album
    if __queue_albums__:
        play_album(name, url, iconimage, 'queue', False, genre)
    else:
        play_album(name, url, iconimage, '', True, genre)
elif mode == 6:
    play_album(name, url, iconimage, '', False, genre)
elif mode == 7:
    play_album(name, url, iconimage, 'browse', False, genre)
elif mode == 8:  # Open settings
    __addon__.openSettings()
    xbmc.executebuiltin("Container.Refresh")
elif mode == 10:  # Play selected song or add song to playlist
    if __queue_songs__:
        play_song(url, name, songname, artist, album, iconimage, dur, False)
    else:
        play_song(url, name,  songname, artist, album, iconimage, dur, True)
elif mode == 11:
    play_song(url, name, songname, artist, album, iconimage, dur, False)
elif mode == 12:
    genres(name, url)
elif mode == 13:
    all_genres(name, url)
elif mode == 14:
    genre_sub_dir(name, url, iconimage)
elif mode == 15:
    list_albums(name, url)
elif mode == 16:
    genre_sub_dir2(name, url, iconimage)
elif mode == 18:
    play_song(url, name, songname, artist, album, iconimage, dur, True)
elif mode == 21:  # List artists
    artists_list(url)
elif mode == 22:  # List albums by selected artist
    list_albums(name, url)
elif mode == 24:  # Seach for specific artist
    search(name, url)
elif mode == 25:
    search_albums(name)
elif mode == 26:
    search_songs(name)
elif mode == 27:
    search_artists(name)
elif mode == 28:
    search_lists()
elif mode == 31:  # List All Artists
    all_artists(name, url)
elif mode == 41:
    sub_dir(name, url, iconimage)
elif mode == 60:
    favourite_lists()
elif mode == 61:  # Add artist to favourites
    add_favourite(name, url, __fav_artist__, _added_to_favourites)
elif mode == 62:
    remove_from_favourites(name, url, __fav_artist__, _removed_from_favourites)
elif mode == 63:
    favourite_artists()
elif mode == 64:
    add_favourite(name, url, __fav_album__, -_added_to_favourites)
elif mode == 65:
    remove_from_favourites(name, url, __fav_album__, _removed_from_favourites)
elif mode == 67:
    add_favourite_song(name, url, __fav_song__, _added_to_favourites)
elif mode == 69:
    favourite_songs()
elif mode == 68:
    remove_from_favourites(name, url, __fav_song__, _removed_from_favourites)
elif mode == 66:
    favourite_albums()
elif mode == 70:
    download_list()
elif mode == 89:
    instant_mix_album()
elif mode == 99:
    instant_mix()
elif mode == 100:  # Clear playlist
    clear_playlist()
#elif mode == 101:
#    charts()
#elif mode == 102:
#    chart_lists(name, url)
elif mode == 201:
    downloads.start_download(url, name, songname, artist, album, iconimage, year, genre, 'song')
elif mode == 202:
    downloads.start_download(url, name, '', '', '', iconimage, year, genre, 'album')
elif mode == 333:
    downloads.clear_lock(download_lock)
elif mode == 400:
    compilations_menu()
elif mode == 401:
    compilations_list(name, url, iconimage, type)
elif mode == 600:  # Start downloading items from download list
    downloads.start_downloads_queue()
    xbmc.executebuiltin("Action(Back)")
elif mode == 610:  # Clear all items from download list
    clear_download_list()
elif mode == 800:  # Remove item from download list
    downloads.remove_from_download_list(name, url, item, _remove)
elif mode == 999:  # Play selected song
    playerMP3.play(sys, params)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
