import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
import urllib
import datetime
import re

# Written by:	Phantom Raspberry Blower
# Date:		21-02-2017
# Description:	Addon for listening to BBC Radio live broadcasts

# Get addon details
__addon_id__ = 'plugin.audio.bbc-radio'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = "Phantom Raspberry Blower"
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

# Get localized language words
__language__ = __addon__.getLocalizedString
_national_radio = __language__(30001)
_nations_and_regions = __language__(30002)
_local_radio = __language__(30003)
_nationwide_radio_stations = __language__(30004)
_national_and_regional_radio_stations = __language__(30005)
_local_radio_stations = __language__(30006)
_bbc_radio_1_desc = __language__(30007)
_bbc_radio_1_extra_desc = __language__(30008)
_bbc_radio_2_desc = __language__(30009)
_bbc_radio_3_desc = __language__(30010)
_bbc_radio_4_desc = __language__(30011)
_bbc_radio_4_extra_desc = __language__(30012)
_bbc_radio_5_live_desc = __language__(30013)
_bbc_radio_5_live_extra_desc = __language__(30014)
_bbc_radio_6_music_desc = __language__(30015)
_bbc_asian_network_desc = __language__(30016)
_bbc_radio_cymru_desc = __language__(30017)
_bbc_radio_foyle_desc = __language__(30018)
_bbc_radio_nan_gaidheal_desc = __language__(30019)
_bbc_radio_scotland_desc = __language__(30020)
_bbc_radio_ulster_desc = __language__(30021)
_bbc_radio_wales_desc = __language__(30022)
_internet_radio = __language__(30023)


_something_wicked_happened = __language__(30721)
_error = __language__(30722)

image_path = 'special://home/addons/' + __addon_id__ + '/resources/media/'

category_list = [_national_radio,
                 _nations_and_regions,
                 _local_radio]

station_list_nr = ['BBC Radio 1',
                   'BBC Radio 1xtra',
                   'BBC Radio 2',
                   'BBC Radio 3',
                   'BBC Radio 4',
                   'BBC Radio 4 Extra',
                   'BBC Radio 5 Live',
                   'BBC Radio 5 Live Sports Extra',
                   'BBC Radio 6 Music',
                   'BBC Asian Network',
                   'BBC World Service UK',
                   'BBC World Service',
                   'BBC World News']

station_list_nar = ['Radio Cymru',
                    'BBC Radio Foyle',
                    'BBC Radio nan Gaidheal',
                    'BBC Radio Scotland',
                    'BBC Radio Ulster',
                    'BBC Radio Wales']

station_list_lr = ['BBC Radio Berkshire',
                   'BBC Radio Bristol',
                   'BBC Radio Cambridgeshire',
                   'BBC Radio Cornwall',
                   'BBC Coventry & Warwickshire',
                   'BBC Radio Cumbria',
                   'BBC Radio Derby',
                   'BBC Radio Devon',
                   'BBC Essex',
                   'BBC Radio Gloucestershire',
                   'BBC Radio Guernsey',
                   'BBC Hereford & Worcester',
                   'BBC Radio Humberside',
                   'BBC Radio Jersey',
                   'BBC Radio Kent',
                   'BBC Radio Lancashire',
                   'BBC Radio Leeds',
                   'BBC Radio Leicester',
                   'BBC Radio Lincolnshire',
                   'BBC Radio London',
                   'BBC Radio Manchester',
                   'BBC Radio Merseyside',
                   'BBC Newcastle',
                   'BBC Radio Norfolk',
                   'BBC Radio Northampton',
                   'BBC Radio Nottingham',
                   'BBC Radio Oxford',
                   'BBC Radio Sheffield',
                   'BBC Radio Shropshire',
                   'BBC Radio Solent',
                   'BBC Somerset',
                   'BBC Radio Stoke',
                   'BBC Radio Suffolk',
                   'BBC Surrey',
                   'BBC Sussex',
                   'BBC Tees',
                   'BBC Three Counties Radio',
                   'BBC Wiltshire',
                   'BBC WM 95.6',
                   'BBC Radio York']

categories = {_national_radio: {'thumb': image_path + 'bbc-national-radio-logo.png',
                                 'fanart': image_path + 'bbc-national-radio.jpg',
                                 'desc': _nationwide_radio_stations
                                 },
              _nations_and_regions: {'thumb': image_path + 'bbc-nations-radio-logo.png',
                                      'fanart': image_path + 'bbc-nations-radio.jpg',
                                      'desc': _national_and_regional_radio_stations
                                      },
              _local_radio: {'thumb': image_path + 'bbc-local-radio-logo.png',
                              'fanart': image_path + 'bbc-local-radio.jpg',
                              'desc': _local_radio_stations}
              }

stations = {'BBC Radio 1': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1_mf_p',
                            'thumb': image_path + 'bbc-radio-1-logo.png',
                            'fanart': image_path + 'bbc-radio-1.jpg',
                            'desc': _bbc_radio_1_desc},
            'BBC Radio 1xtra': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1xtra_mf_p',
                                  'thumb': image_path + 'bbc-radio-1xtra-logo.png',
                                  'fanart': image_path + 'bbc-radio-1xtra.jpg',
                                  'desc': _bbc_radio_1_extra_desc},
            'BBC Radio 2': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio2_mf_p',
                            'thumb': image_path + 'bbc-radio-2-logo.png',
                            'fanart': image_path + 'bbc-radio-2.jpg',
                            'desc': _bbc_radio_2_desc},
            'BBC Radio 3': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio3_mf_p',
                            'thumb': image_path + 'bbc-radio-3-logo.png',
                            'fanart': image_path + 'bbc-radio-3.jpg',
                            'desc': _bbc_radio_3_desc},
            'BBC Radio 4': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4fm_mf_p',
                            'thumb': image_path + 'bbc-radio-4-logo.png',
                            'fanart': image_path + 'bbc-radio-4.jpg',
                            'desc': _bbc_radio_4_desc},
            'BBC Radio 4 Extra': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4extra_mf_p',
                                  'thumb': image_path + 'bbc-radio-4-extra-logo.png',
                                  'fanart': image_path + 'bbc-radio-4-extra.jpg',
                                  'desc': _bbc_radio_4_extra_desc},
            'BBC Radio 5 Live': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5live_mf_p',
                                 'thumb': image_path + 'bbc-radio-5-live-logo.png',
                                 'fanart': image_path + 'bbc-radio-5-live.jpg',
                                 'desc': _bbc_radio_5_live_desc},
            'BBC Radio 5 Live Sports Extra': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5extra_mf_p',
                                              'thumb': image_path + 'bbc-radio-5-live-sports-extra-logo.png',
                                              'fanart': image_path + 'bbc-radio-5-live-sports-extra.jpg',
                                              'desc': _bbc_radio_5_live_extra_desc},
            'BBC Radio 6 Music': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_6music_mf_p',
                                  'thumb': image_path + 'bbc-radio-6-music-logo.png',
                                  'fanart': image_path + 'bbc-radio-6-music.jpg',
                                  'desc': _bbc_radio_6_music_desc},
            'BBC Asian Network': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_asianet_mf_p',
                                  'thumb': image_path + 'bbc-asian-network-logo.png',
                                  'fanart': image_path + 'bbc-asian-network.jpg',
                                  'desc': _bbc_asian_network_desc},
            'BBC World Service UK': {'url': 'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-eieuk',
                                     'thumb': image_path + 'bbc-world-service-uk-logo.png',
                                     'fanart': image_path + 'bbc-world-service.jpg',
                                     'desc': ''},
            'BBC World News': {'url': 'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-einws',
                               'thumb': image_path + 'bbc-world-news-logo.png',
                               'fanart': image_path + 'bbc-world-news.jpg',
                               'desc': ''},
            'BBC World Service': {'url': 'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-eie',
                                  'thumb': image_path + 'bbc-world-service-logo.png',
                                  'fanart': image_path + 'bbc-world-service.jpg',
                                  'desc': ''},
            'Radio Cymru': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_cymru_mf_p',
                            'thumb': image_path + 'radio-cymru-logo.png',
                            'fanart': image_path + 'radio-cymru.jpg',
                            'desc': _bbc_radio_cymru_desc},
            'BBC Radio Foyle': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_foyle_mf_p',
                                'thumb': image_path + 'bbc-radio-foyle-logo.png',
                                'fanart': image_path + 'bbc-radio-foyle.jpg',
                                'desc': _bbc_radio_foyle_desc},
            'BBC Radio nan Gaidheal': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_nangaidheal_mf_p',
                                       'thumb': image_path + 'bbc-radio-nan-gaidheal-logo.png',
                                       'fanart': image_path + 'bbc-radio-nan-gaidheal.jpg',
                                       'desc': _bbc_radio_nan_gaidheal_desc},
            'BBC Radio Scotland': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_scotlandfm_mf_p',
                                   'thumb': image_path + 'bbc-radio-scotland-logo.png',
                                   'fanart': image_path + 'bbc-radio-scotland.jpg',
                                   'desc': _bbc_radio_scotland_desc},
            'BBC Radio Ulster': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_ulster_mf_p',
                                 'thumb': image_path + 'bbc-radio-ulster-logo.png',
                                 'fanart': image_path + 'bbc-radio-ulster.jpg',
                                 'desc': _bbc_radio_ulster_desc},
            'BBC Radio Wales': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_walesmw_mf_p',
                                'thumb': image_path + 'bbc-radio-wales-logo.png',
                                'fanart': image_path + 'bbc-radio-wales.jpg',
                                'desc': _bbc_radio_wales_desc},
            'BBC Radio Berkshire': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrberk_mf_p',
                                    'thumb': image_path + 'bbc-radio-berkshire-logo.png',
                                    'fanart': image_path + 'bbc-radio-berkshire.jpg',
                                    'desc': ''},
            'BBC Radio Bristol': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrbris_mf_p',
                                  'thumb': image_path + 'bbc-radio-bristol-logo.png',
                                  'fanart': image_path + 'bbc-radio-bristol.jpg',
                                  'desc': ''},
            'BBC Radio Cambridgeshire': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrcambs_mf_p',
                                         'thumb': image_path + 'bbc-radio-cambridgeshire-logo.png',
                                         'fanart': image_path + 'bbc-radio-cambridgeshire.jpg',
                                         'desc': ''},
            'BBC Radio Cornwall': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrcorn_mf_p',
                                   'thumb': image_path + 'bbc-radio-cornwall-logo.png',
                                   'fanart': image_path + 'bbc-radio-cornwall.jpg',
                                   'desc': ''},
            'BBC Coventry & Warwickshire': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrwmcandw_mf_p',
                                            'thumb': image_path + 'bbc-coventry-warwickshire-logo.png',
                                            'fanart': image_path + 'bbc-coventry-warwickshire.jpg',
                                            'desc': ''},
            'BBC Radio Cumbria': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrcumbria_mf_p',
                                  'thumb': image_path + 'bbc-radio-cumbria-logo.png',
                                  'fanart': image_path + 'bbc-radio-cumbria.jpg',
                                  'desc': ''},
            'BBC Radio Derby': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrderby_mf_p',
                                'thumb': image_path + 'bbc-radio-derby-logo.png',
                                'fanart': image_path + 'bbc-radio-derby.jpg',
                                'desc': ''},
            'BBC Radio Devon': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrdevon_mf_p',
                                'thumb': image_path + 'bbc-radio-devon-logo.png',
                                'fanart': image_path + 'bbc-radio-devon.jpg',
                                'desc': ''},
            'BBC Essex': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lressex_mf_p',
                          'thumb': image_path + 'bbc-essex-logo.png',
                          'fanart': image_path + 'bbc-essex.jpg',
                          'desc': ''},
            'BBC Radio Gloucestershire': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrgloucs_mf_p',
                                          'thumb': image_path + 'bbc-radio-gloucestershire-logo.png',
                                          'fanart': image_path + 'bbc-radio-gloucestershire.jpg',
                                          'desc': ''},
            'BBC Radio Guernsey': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrguern_mf_p',
                                   'thumb': image_path + 'bbc-radio-guernsey-logo.png',
                                   'fanart': image_path + 'bbc-radio-guernsey.jpg',
                                   'desc': ''},
            'BBC Hereford & Worcester': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrhandw_mf_p',
                                         'thumb': image_path + 'bbc-hereford-worcester-logo.png',
                                         'fanart': image_path + 'bbc-hereford-worcester.jpg',
                                         'desc': ''},
            'BBC Radio Humberside': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrhumber_mf_p',
                                     'thumb': image_path + 'bbc-radio-humberside-logo.png',
                                     'fanart': image_path + 'bbc-radio-humberside.jpg',
                                     'desc': ''},
            'BBC Radio Jersey': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrjersey_mf_p',
                                 'thumb': image_path + 'bbc-radio-jersey-logo.png',
                                 'fanart': image_path + 'bbc-radio-jersey.jpg',
                                 'desc': ''},
            'BBC Radio Kent': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrkent_mf_p',
                               'thumb': image_path + 'bbc-radio-kent-logo.png',
                               'fanart': image_path + 'bbc-radio-kent.jpg',
                               'desc': ''},
            'BBC Radio Lancashire': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrlancs_mf_p',
                                     'thumb': image_path + 'bbc-radio-lancashire-logo.png',
                                     'fanart': image_path + 'bbc-radio-lancashire.jpg',
                                     'desc': ''},
            'BBC Radio Leeds': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrleeds_mf_p',
                                'thumb': image_path + 'bbc-radio-leeds-logo.png',
                                'fanart': image_path + 'bbc-radio-leeds.jpg',
                                'desc': ''},
            'BBC Radio Leicester': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrleics_mf_p',
                                    'thumb': image_path + 'bbc-radio-leicester-logo.png',
                                    'fanart': image_path + 'bbc-radio-leicester.jpg',
                                    'desc': ''},
            'BBC Radio Lincolnshire': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrlincs_mf_p',
                                       'thumb': image_path + 'bbc-radio-lincolnshire-logo.png',
                                       'fanart': image_path + 'bbc-radio-lincolnshire.jpg',
                                       'desc': ''},
            'BBC Radio London': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrldn_mf_p',
                                 'thumb': image_path + 'bbc-radio-london-logo.png',
                                 'fanart': image_path + 'bbc-radio-london.jpg',
                                 'desc': ''},
            'BBC Radio Manchester': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrmanc_mf_p',
                                     'thumb': image_path + 'bbc-radio-manchester-logo.png',
                                     'fanart': image_path + 'bbc-radio-manchester.jpg',
                                     'desc': ''},
            'BBC Radio Merseyside': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrmersey_mf_p',
                                     'thumb': image_path + 'bbc-radio-merseyside-logo.png',
                                     'fanart': image_path + 'bbc-radio-merseyside.jpg',
                                     'desc': ''},
            'BBC Newcastle': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnewc_mf_p',
                              'thumb': image_path + 'bbc-newcastle-logo.png',
                              'fanart': image_path + 'bbc-newcastle.jpg',
                              'desc': ''},
            'BBC Radio Norfolk': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnorfolk_mf_p',
                                  'thumb': image_path + 'bbc-radio-norfolk-logo.png',
                                  'fanart': image_path + 'bbc-radio-norfolk.jpg',
                                  'desc': ''},
            'BBC Radio Northampton': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnthhnts_mf_p',
                                      'thumb': image_path + 'bbc-radio-northampton-logo.png',
                                      'fanart': image_path + 'bbc-radio-northampton.jpg',
                                      'desc': ''},
            'BBC Radio Nottingham': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnotts_mf_p',
                                     'thumb': image_path + 'bbc-radio-nottingham-logo.png',
                                     'fanart': image_path + 'bbc-radio-nottingham.jpg',
                                     'desc': ''},
            'BBC Radio Oxford': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lroxford_mf_p',
                                 'thumb': image_path + 'bbc-radio-oxford-logo.png',
                                 'fanart': image_path + 'bbc-radio-oxford.jpg',
                                 'desc': ''},
            'BBC Radio Sheffield': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsheff_mf_p',
                                    'thumb': image_path + 'bbc-radio-sheffield-logo.png',
                                    'fanart': image_path + 'bbc-radio-sheffield.jpg',
                                    'desc': ''},
            'BBC Radio Shropshire': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrshrops_mf_p',
                                     'thumb': image_path + 'bbc-radio-shropshire-logo.png',
                                     'fanart': image_path + 'bbc-radio-shropshire.jpg',
                                     'desc': ''},
            'BBC Radio Solent': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsolent_mf_p',
                                 'thumb': image_path + 'bbc-radio-solent-logo.png',
                                 'fanart': image_path + 'bbc-radio-solent.jpg',
                                 'desc': ''},
            'BBC Somerset': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsomer_mf_p',
                             'thumb': image_path + 'bbc-somerset-logo.png',
                             'fanart': image_path + 'bbc-somerset.jpg',
                             'desc': ''},
            'BBC Radio Stoke': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsomer_mf_p',
                                'thumb': image_path + 'bbc-radio-stoke-logo.png',
                                'fanart': image_path + 'bbc-radio-stoke.jpg',
                                'desc': ''},
            'BBC Radio Suffolk': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsuffolk_mf_p',
                                  'thumb': image_path + 'bbc-radio-suffolk-logo.png',
                                  'fanart': image_path + 'bbc-radio-suffolk.jpg',
                                  'desc': ''},
            'BBC Surrey': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsurrey_mf_p',
                           'thumb': image_path + 'bbc-surrey-logo.png',
                           'fanart': image_path + 'bbc-surrey.jpg',
                           'desc': ''},
            'BBC Sussex': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsussex_mf_p',
                           'thumb': image_path + 'bbc-sussex-logo.png',
                           'fanart': image_path + 'bbc-sussex.jpg',
                           'desc': ''},
            'BBC Tees': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrtees_mf_p',
                         'thumb': image_path + 'bbc-tees-logo.png',
                         'fanart': image_path + 'bbc-tees.jpg',
                         'desc': ''},
            'BBC Three Counties Radio': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lr3cr_mf_p',
                                         'thumb': image_path + 'bbc-three-counties-radio-logo.png',
                                         'fanart': image_path + 'bbc-three-counties-radio.jpg',
                                         'desc': ''},
            'BBC Wiltshire': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrwilts_mf_p',
                              'thumb': image_path + 'bbc-wiltshire-logo.png',
                              'fanart': image_path + 'bbc-wiltshire.jpg',
                              'desc': ''},
            'BBC WM 95.6': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrwm_mf_p',
                            'thumb': image_path + 'bbc-wm956-logo.png',
                            'fanart': image_path + 'bbc-wm956.jpg',
                            'desc': ''},
            'BBC Radio York': {'url': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lryork_mf_p',
                               'thumb': image_path + 'bbc-radio-york-logo.png',
                               'fanart': image_path + 'bbc-radio-york.jpg',
                               'desc': ''}
           }

def list_categories():
    """
    Create the list of playable videos in the Kodi interface.
    :return: None
    """
    for item in category_list:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=item)
        addDir(item,
               __url__,
               1,
               categories[item]['thumb'],
               categories[item]['fanart'],
               categories[item]['desc'],
               isFolder=True)


def get_links(name, url, icon, fanart):
    """
    Create the list of playable audio links
    """
    if name == _national_radio:
        cur_list = station_list_nr
    elif name == _nations_and_regions:
        cur_list = station_list_nar
    elif name == _local_radio:
        cur_list = station_list_lr

    for item in cur_list:
        # Create a list ite with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=item)
        addDir(item,
               stations[item]['url'],
               2,
               stations[item]['thumb'],
               stations[item]['fanart'],
               stations[item]['desc'],
               isFolder=False)


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


def addDir(name, url, mode, icon, fanart, desc, isFolder=False):
    """
    Display a list of links
    """
    u = (sys.argv[0] + '?url=' + urllib.quote_plus(url) +
         '&mode=' + str(mode) + '&name=' + urllib.quote_plus(name) +
         '&icon=' + str(icon) + '&fanart=' + str(fanart))
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
    list_categories()
elif mode == 1:
    _default_image = fanart
    get_links(name, url, icon, fanart)
elif mode == 2:
    play_audio(name, url, icon, fanart)

xbmcplugin.endOfDirectory(__handle__)
