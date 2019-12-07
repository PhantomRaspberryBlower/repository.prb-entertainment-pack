 #!/usr/bin/python

import xbmcplugin
import xbmcaddon
import xbmcgui
import sys
import os

import sportsreplay

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 11-06-2019
# Description: Streams MotoGP, Moto2, Moto3, MotoE races since 2014

# Get addon details
__addon_id__ = u'plugin.video.sports-replay'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = u'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

# Define local variables
__search_list__ = xbmc.translatePath(os.path.join('special://home/addons/',
                                     __addon_id__ + '/resources/search.list'))
image_path = xbmc.translatePath(os.path.join('special://home/addons/',
                                __addon_id__ + '/resources/media/'))
thumbs = {'Africa Cup 2015': image_path + 'Africa_Cup_2015.png',
          'Bundesliga Germany': image_path + 'Bundesliga.png',
          'Champions League': image_path + 'Champions_League.png',
          'Copa America': image_path + 'Copa_America.png',
          'Europa League': image_path + 'Europa_League.png',
          'EURO 2016': image_path + 'Euro_2016.png',
          'EURO 2020': image_path + 'Euro_2020.png',
          'F1': image_path + 'F1.png',
          'Formula 1': image_path + 'F1_Replay.png',
          'Friendly Match': image_path + 'Friendly_Match.png',
          'Football': image_path + 'Full_Match_Replay.png',
          'La Liga Spain': image_path + 'La_Liga.png',
          'Ligue 1 France': image_path + 'Ligue_1.png',
          'MLB': image_path + 'MLB_Replay.png',
          'Moto GP': image_path + 'MotoGP_Replay.png',
          'MotoGP': image_path + 'MotoGP.png',
          'Moto2': image_path + 'Moto2.png',
          'Moto3': image_path + 'Moto3.png',
          'MotoE': image_path + 'MotoE.png',
          'NBA': image_path + 'NBA_Replay.png',
          'NFL': image_path + 'NFL_Replay.png',
          'Premier League': image_path + 'Premier_League.png',
          'Serie A Italy': image_path + 'Serie_A.png',
          'UEFA Nations League': image_path + 'Nations_League.png',
          'UFC': image_path + 'UFC_Replay.png',
          'World Cup 2018': image_path + 'World_Cup_2018.png',
          'World Cup 2014': image_path + 'World_Cup_2014.png',
          'Search': image_path + 'search.png'}
fanarts = {'Africa Cup 2015': image_path + 'Full_Match_fanart.jpg',
           'Bundesliga Germany': image_path + 'Full_Match_fanart.jpg',
           'Champions League': image_path + 'Full_Match_fanart.jpg',
           'Copa America': image_path + 'Full_Match_fanart.jpg',
           'Europa League': image_path + 'Full_Match_fanart.jpg',
           'EURO 2016': image_path + 'Full_Match_fanart.jpg',
           'EURO 2020': image_path + 'Full_Match_fanart.jpg',
           'F1': image_path + 'F1_fanart.jpg',
           'Formula 1': image_path + 'F1_fanart.jpg',
           'Friendly Match': image_path + 'Full_Match_fanart.jpg',
           'Football': image_path + 'Full_Match_fanart.jpg',
           'La Liga Spain': image_path + 'Full_Match_fanart.jpg',
           'Ligue 1 France': image_path + 'Full_Match_fanart.jpg',
           'MLB': image_path + 'MLB_fanart.jpg',
           'Moto GP': image_path + 'MotoGP_fanart.jpg',
           'MotoGP': image_path + 'MotoGP_fanart.jpg',
           'Moto2': image_path + 'Moto2_fanart.jpg',
           'Moto3': image_path + 'Moto3_fanart.jpg',
           'MotoE': image_path + 'MotoE_fanart.jpg',
           'NBA': image_path + 'NBA_fanart.jpg',
           'NFL': image_path + 'NFL_fanart.jpg',
           'Premier League': image_path + 'Full_Match_fanart.jpg',
           'Serie A Italy': image_path + 'Full_Match_fanart.jpg',
           'UEFA Nations League': image_path + 'Full_Match_fanart.jpg',
           'UFC': image_path + 'UFC_fanart.jpg',
           'World Cup 2018': image_path + 'Full_Match_fanart.jpg',
           'World Cup 2014': image_path + 'Full_Match_fanart.jpg'}
menu_items = {'Football': {'mode': sportsreplay.Mode.SUBMAIN_MENU,
                           'title': 'Football',
                           'menuname': 'Full Match Replay',
                           'url': 'http://fullmatchsports.com/',
                           'thumb': thumbs['Football'],
                           'fanart': fanarts['Football'],
                           'desc': 'Full match football replays from around the world.',
                           'itemsperpage': 36},
              'Formula 1':{'mode': sportsreplay.Mode.SUBMAIN_MENU,
                            'title': 'Formula 1',
                            'menuname': 'Formula 1 Race',
                            'url': 'http://fullmatchsports.com/',
                            'thumb': thumbs['Formula 1'],
                            'fanart': fanarts['Formula 1'],
                            'desc': 'Formula 1 race replays.',
                            'itemsperpage': 36},
              'MLB': {'mode': sportsreplay.Mode.SUB_MENU,
                      'title': 'MLB',
                      'menuname': 'MLB ',
                      'url': 'http://fullmatch.net/mlb-full-game-replay/',
                      'thumb': thumbs['MLB'],
                      'fanart': fanarts['MLB'],
                      'desc': 'Major League Baseball game replays.',
                      'itemsperpage': 48},
              'MotoGP': {'mode': sportsreplay.Mode.SUBMAIN_MENU,
                         'title': 'MotoGP',
                         'menuname': 'MotoGP Race',
                         'url': 'http://fullmatchsports.com/',
                         'thumb': thumbs['Moto GP'],
                         'fanart': fanarts['Moto GP'],
                         'desc': 'MotoGP, Moto2, Moto3 and MotoE race replays.',
                         'itemsperpage': 36},
              'NBA': {'mode': sportsreplay.Mode.SUBMAIN_MENU,
                      'title': 'NBA',
                      'menuname': 'NBA ',
                      'url': 'http://fullmatch.net/',
                      'thumb': thumbs['NBA'],
                      'fanart': fanarts['NBA'],
                      'desc': 'National Basketball Association game replays.',
                      'itemsperpage': 36},
              'NFL': {'mode': sportsreplay.Mode.SUBMAIN_MENU,
                      'title': 'NFL',
                      'menuname': 'NFL ',
                      'url': 'http://fullmatch.net/',
                      'thumb': thumbs['NFL'],
                      'fanart': fanarts['NFL'],
                      'desc': 'National Football League game replays.',
                      'itemsperpage': 48},
              'UFC': {'mode': sportsreplay.Mode.SUB_MENU,
                      'title': 'UFC',
                      'menuname': 'UFC ',
                      'url': 'http://fullmatch.net/ufc-full-fights/',
                      'thumb': thumbs['UFC'],
                      'fanart': fanarts['UFC'],
                      'desc': 'Ultimate Fightig Championship fight replays.',
                      'itemsperpage': 48},
              'Search': {'mode': sportsreplay.Mode.SEARCH,
                      'title': 'Search',
                      'menuname': '',
                      'url': 'http://fullmatchsports.com/',
                      'thumb': thumbs['Search'],
                      'fanart': __fanart__,
                      'desc': 'Search for replay of a specific sporting event.',
                      'itemsperpage': 48}}

def main_menu():
    for item in sorted(menu_items.keys()):
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=item)
        addDir(item,
               menu_items[item]['url'],
               menu_items[item]['mode'],
               menu_items[item]['thumb'],
               menu_items[item]['fanart'],
               {'title': menu_items[item]['desc'],
                'plot': menu_items[item]['desc']})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

# Treat like main menu
def submain_menu(name, thumb, fanart):
    # Shows menu items
    menuname = menu_items[name]['menuname']
    for url, title, mode in sportsreplay.main_menu(menuname):
        if name == 'Football':
            # Footbal menu needs extra submenu for showing leagues
            if title in thumbs.keys():
                addDir(title,
                       url,
                       sportsreplay.Mode.SEASONS_MENU,
                       thumbs[title],
                       fanart,
                       {'title': title,
                        'plot': title})
        elif name == 'NBA' or name == 'NFL':
            # NBA and NFL some menu items need a submenu
            if 'All Star' in title or 'Bowl' in title:
                # Some items do not require a submenu
                mode = sportsreplay.Mode.GET_STREAMS
            addDir(title,
                   url,
                   mode,
                   thumbs[name],
                   fanart,
                   {'title': title,
                    'plot': title})
        elif name == 'Formula 1' or name =='MotoGP':
            # F1 and MotoGP require submenus
            addDir(title,
                   url,
                   sportsreplay.Mode.SUB_MENU,
                   thumb,
                   fanart,
                   {'title': title,
                    'plot': title})
        else:
            # MLB and UFC do not require submenus
            addDir(title,
                   url,
                   mode,
                   thumb,
                   fanart,
                   {'title': title,
                    'plot': title})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def seasons(league, thumb, fanart):
    # Shows seasons for Football
    for url, name, mode in sportsreplay.seasons(league):
        addDir(name,
               url,
               sportsreplay.Mode.SUB_MENU,
               thumb,
               fanart,
               {'title': name,
                'plot': name})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def submenu(name, url, thumb, fanart):
    # Display submenus with pagination 
    for href, title, img, mode in sportsreplay.submenu(url,
                                                       thumb,
                                                       items_per_page=36,
                                                       currmode=sportsreplay.Mode.SUB_MENU):
        addDir(title.strip(),
            href,
            mode,
            img,
            fanart,
            {'title': title,
             'plot': title})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_links(name, url, thumb, fanart):
    try:
        for href, title in sportsreplay.get_links(url):
            if 'MotoGP' in title:
                menu_icon = thumbs['MotoGP']
                menu_fanart = fanarts['MotoGP']
            elif 'Moto2' in title:
                menu_icon = thumbs['Moto2']
                menu_fanart = fanarts['Moto2']
            elif 'Moto3' in title:
                menu_icon = thumbs['Moto3']
                menu_fanart = fanarts['Moto3']
            elif 'MotoE' in title:
                menu_icon = thumbs['MotoE']
                menu_fanart = fanarts['MotoE']
            elif 'MotoGP' in name:
                menu_icon = thumbs['Moto GP']
                menu_fanart = fanarts['MotoGP']
            elif ('F1' in name) or ('F1' in title):
                menu_icon = thumbs['F1']
                menu_fanart = fanarts['F1']
            else:
                if len(thumb) > 0:
                    menu_icon = thumb
                else:
                    menu_icon = __icon__
                if len(fanart) > 0:
                    menu_fanart = fanart
                else:
                    menu_fanart = __fanart__
            label = '%s %s' % (name, title.strip())
            addDir(label,
                   url + href,
                   sportsreplay.Mode.GET_STREAMS,
                   menu_icon,
                   menu_fanart,
                   {'title': label,
                    'plot': label})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    except:
        get_streams(name, url, thumb, fanart)


def get_streams(name, url, thumb, fanart):
    name = name.replace(' HD 720p', '').replace(' HD 1080p', '')
    streams = sportsreplay.get_streams(url)
    for href, label in streams:
        if 'MotoGP' in name:
            menu_fanart = fanarts['MotoGP']
        elif 'Moto2' in name:
            menu_fanart = fanarts['Moto2']
        elif 'Moto3' in name:
            menu_fanart = fanarts['Moto3']
        elif 'MotoE' in name:
            menu_fanart = fanarts['MotoE']
        else:
            menu_fanart = fanart
        addDir('%s %s' % (name, label.strip()),
               href,
               sportsreplay.Mode.PLAY_STREAM,
               thumb,
               menu_fanart,
               {'title': name,
                'plot': name})
    if streams:
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def search(name, url, thumb, fanart):
    query = sportsreplay.ct.keyboard(text='', heading='Search', hidden=False)
    if query:
        submenu(name, 'http://fullmatchsports.com/?s=%s#' % query, thumb, fanart)


def addDir(name, url, mode, thumb, fanart=False, infoLabels=True):
    u = sys.argv[0] + "?url=" + sportsreplay.quote_plus(url) + "&mode=" + str(mode) + "&name=" + sportsreplay.quote_plus(name) + "&thumb=" + str(thumb) + "&fanart=" + str(fanart)
    ok = True
    liz = xbmcgui.ListItem(name)
    if not infoLabels:
        infoLabels =  {'title': name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    if not fanart:
        fanart = __fanart__
    liz.setArt({'fanart': fanart,
                'thumb': thumb})
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
mode = None
url = None
name = None
thumb = None
fanart = None

try:
    mode = int(params['mode'])
except:
    pass
try:
    url = sportsreplay.unquote_plus(params['url'])
except:
    pass
try:
    name = sportsreplay.unquote_plus(params['name'])
except:
    pass
try:
    thumb = sportsreplay.unquote(params['thumb'])
except:
    pass
try:
    fanart = sportsreplay.unquote(params['fanart'])
except:
    pass

# Message below used to test addon
#sportsreplay.ct.message("Mode: %s\nURL: %s\nName: %s" % (mode, url, name), "Test")

if mode == None or url == None or len(url) < 1:
    # Display Main Menu Items
    main_menu()
elif mode == sportsreplay.Mode.SUBMAIN_MENU:
    # Display Main Submenu Items
    submain_menu(name, thumb, fanart)
elif mode == sportsreplay.Mode.SEASONS_MENU:
    # Display Seasons Items
    seasons(name, thumb, fanart)
elif mode == sportsreplay.Mode.SUB_MENU:
    # Display Submenu Items
    submenu(name, url, thumb, fanart)
elif mode == sportsreplay.Mode.GET_LINKS:
    # Display Links
    get_links(name, url, thumb, fanart)
elif mode == sportsreplay.Mode.GET_STREAMS:
    # Display Streams
    get_streams(name, url, thumb, fanart)
elif mode == sportsreplay.Mode.PLAY_STREAM:
    # Play Stream
    sportsreplay.play_stream(name, url, thumb)
elif mode == sportsreplay.Mode.SEARCH:
    # Search Streams
    search(name, url, thumb, fanart)
