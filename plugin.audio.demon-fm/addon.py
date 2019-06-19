#!/bin/python

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
import urllib2
import re
import os

# Written by:	Phantom Raspberry Blower
# Date:		    24-11-2017
# Description:	Addon for listening to Demon FM a
#               student radio station for the  
#               Leicester Community.

# Get addon details
__addon_id__ = 'plugin.audio.demon-fm'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = "Phantom Raspberry Blower"
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

# Get localized language words
__language__ = __addon__.getLocalizedString
_demon_fm = __language__(30001)
_status = __language__(30003)
_unplayable_stream = __language__(30004)
_something_wicked_happened = __language__(30005)
_error = __language__(30006)
_please_wait = __language__(30007)
_process_complete = __language__(30008)
_failed_to_download = __language__(30009)

streams_url = "http://www.demonfm.co.uk:8000"

# Define local variables
resources = xbmc.translatePath(os.path.join('special://home/addons/'
	                                        'plugin.audio.demon-fm',
	                                        'resources'))
fanart = xbmc.translatePath(os.path.join(resources, 'fanart.jpg'))
iconart = xbmc.translatePath(os.path.join(resources, 'icon.png'))


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


def get_url(url):
    text = ''
    try:
        content = urllib2.urlopen(url).read()
        return content
    except urllib2.HTTPError, e:
        text = 'HTTPError = ' + str(e.code)
    except urllib2.URLError, e:
        text = 'URLError = ' + str(e.reason)
    except httplib.HTTPException, e:
        text = 'HTTPException'
    except Exception:
        text = _something_wicked_happened

    if len(text) > 0:
        message(text, _error)
    return text


def list_schedule(day):
    days = {'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6}
    # Get schdule for the supplied day
    url = streams_url.replace(':8000', '/schedule')
    listing = []
    is_folder = False
    content = get_url(url)
    content = regex_from_to(content, '<div class="et_pb_all_tabs">', '<!-- .et_pb_all_tabs -->').replace('\n', '')
    days_sched = re.compile('<div class="et_pb_tab(.+?)<!-- .et_pb_tab -->').findall(content)
    match = re.compile('<h4(.+?)</h4(.+?)<blockquote><p>(.+?)</p></blockquote>').findall(days_sched[days[day]])
    for h4, discard, blockquote in match:
        text = h4.replace(' class="show-time">', '').replace('>', '').replace(' &#8211;', ': ').replace('class="show-description"', '').replace(' -', ': ')
        try:
            text2 = regex_from_to(discard, '<h5', '</h5>').replace('class="presenternames">', '')
        except:
            text2 = ''
        if text2.find('</span>') > 0:
            try:
                text2 = regex_from_to(text2, '">', '</span>')
            except:
                text2 = ''
        if blockquote == '&nbsp;':
            text3 = ''
        else:
            text3 = blockquote
        if text3.find('</span>') > 0:
            try:
                text3 = regex_from_to(text3, '">', '</span>')
            except:
                text3 = ''
        url = '{0}?action=description&text={1}'.format(__url__, text3)
        list_item = xbmcgui.ListItem(label='[COLOR red]%s[/COLOR] %s' % (text.replace(':  ', ': ').replace(':  ', ': '), text2.replace('>', '')))
        # Set a fanart and icon images for the list item.
        list_item.setArt({'fanart': fanart,
                          'icon': iconart})
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(__handle__)


def list_schedule_days():
    # Get list of days
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    listing = []
    is_folder = True
    for day in days:
        url = '{0}?action=schedule&day={1}'.format(__url__, day)
        list_item = xbmcgui.ListItem(label=day)
        # Set a fanart and icon images for the list item.
        list_item.setArt({'fanart': fanart,
                          'icon': iconart})
        listing.append((url, list_item, is_folder))

    # Add our listing to Kodi.
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(__handle__)


def list_streams():
    # Get list of live links and channel statistics
    url = ''
    text = ''
    listing = []
    content = get_url(streams_url)
    # Add schedule
    is_folder = True
    url = '{0}?action=schedule&day=all'.format(__url__)
    list_item = xbmcgui.ListItem(label='[COLOR red]Schedule[/COLOR]')
    # Set a fanart and icon images for the list item.
    list_item.setArt({'fanart': fanart,
                      'icon': iconart})
    listing.append((url, list_item, is_folder))

    # Add streams
    match = re.compile('<a class="play" href="(.+?)">(.+?)<td>Stream Name:</td><td>(.+?)</td>').findall(content)
    # is_folder = False means that this item won't open any sub-list.
    is_folder = False
    for m3u_url, discard, stream_name in match:
        if stream_name.find("DemonFM") >= 0:
            audio_url = str(m3u_url)
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=stream_name)
            # Set a fanart and icon images for the list item.
            list_item.setArt({'fanart': fanart,
                              'icon': iconart})
            # Set 'IsPlayable' property to 'true'.
            list_item.setProperty('IsPlayable', 'true')
            # Create a URL for the plugin recursive callback.
            url = '{0}?action=play&audio={1}'.format(__url__, str(streams_url + m3u_url.replace('.m3u', '')))
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

    # Add our listing to Kodi.
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(__handle__)


def play_stream(path):
    """
    Play audio stream with the provided path.
    :param path: str
    :return: None
    """
    if xbmc.Player().isPlayingAudio:
        xbmc.Player().stop()

    liz = xbmcgui.ListItem(path=path, thumbnailImage=iconart)
    # Set a fanart image for the list item.
    liz.setProperty('fanart_image', fanart)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(__handle__, True, listitem=liz)
    xbmc.executebuiltin('Action(Fullscreen)')


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


def notification(heading, message, icon, duration):
    # Show message notification
    dialog = xbmcgui.Dialog()
    dialog.notification(heading, message, icon, duration)


def message(message, title):
    # Display message to user
    dialog = xbmcgui.Dialog()
    dialog.ok(title, message)


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    params=get_params()
    # Check the parameters passed to the plugin
    if params:
        try:
            if params['action'] == 'listing':
                # Display the list of audio streams.
                list_streams()
            elif params['action'] == 'schedule':
                if params['day'] == 'all':
                    # Play a audio stream from a provided URL.
                    list_schedule_days()
                else:
                    list_schedule(params['day'])
            elif params['action'] == 'description':
                if len(str(params['text'])) > 1:
                    message(str(params['text']), 'Description')
                else:
                    message('No description!', 'Description')
            elif params['action'] == 'play':
                # Play a audio stream from a provided URL.
                play_stream(params['audio'])
        except:
            list_streams()
    else:
        list_streams()
