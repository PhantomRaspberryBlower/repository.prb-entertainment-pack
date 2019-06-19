#!/bin/python

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from xml.etree import ElementTree
import sys
import urllib2
import datetime
import re

# Written by:	Phantom Raspberry Blower
# Date:		21-02-2017
# Description:	Addon for listening to Leicester Community Radio live broadcasts

# Get addon details
__addon_id__ = 'plugin.audio.leicester-community-radio'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = "Phantom Raspberry Blower"
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

# Get localized language words
__language__ = __addon__.getLocalizedString
_stats = __language__(30002)
_ustream_stats = __language__(30003)
_last_broadcast = __language__(30005)
_followers = __language__(30006)
_viewer_total = __language__(30007)
_viewers = __language__(30008)
_something_wicked_happened = __language__(30010)
_error = __language__(30011)
_failed_to_download = __language__(30014)
_Leic_comm_radio_not_broadcasting = __language__(30015)
_off_air = __language__(30016)

#playable_url = 'http://leiccomradio.radioca.st/streams/320kbps'
#playable_url = 'http://icecast.maxxwave.co.uk:8000/lcrstudio'
#playable_url = 'http://titan.shoutca.st:9122/stream'
#playable_url = 'http://icecast.maxxwave.co.uk/LCR_AAC'
playable_url = 'http://icecast.maxxwave.co.uk/lcr_aac'

def clean_html(raw_html):
    # Remove all HTML tags from text
    regex = re.compile('<.*?>')
    cleantext = re.sub(regex, '', raw_html)
    return cleantext

def get_channel_info():
    # Get list of live links and channel statistics
    url = "https://api.ustream.tv/channels/19612614.xml"
    try:
        content = urllib2.urlopen(url).read()
        tree = ElementTree.fromstring(str(content))
        channel = tree.find('channel')
        last_broadcast_at = datetime.datetime.fromtimestamp(int(channel.find('last_broadcast_at').text)).strftime('%d %b %Y %H:%M:%S')
        if channel.find('status').text == 'live':
            stats = channel.find('stats')
            thumbnail = channel.find('thumbnail')
            stream = playable_url
            return {'id': channel.find('id').text,
                    'title': channel.find('title').text,
                    'description': clean_html(channel.find('description').text.replace("&amp;", "&")),
                    'status': channel.find('status').text,
                    'last_broadcast_at': last_broadcast_at,
                    'follower': stats.find('follower').text,
                    'viewer_total': stats.find('viewer_total').text,
                    'viewer': stats.find('viewer').text,
                    'thumbnail': thumbnail.find('live').text,
                    'stream': stream}
        elif channel.find('status').text == 'offair':
            stats = channel.find('stats')
            thumbnail = channel.find('thumbnail')
            stream = playable_url
            try:
                viewer = stats.find('viewer').text
            except:
                viewer = '0'
            return {'id': channel.find('id').text,
                    'title': channel.find('title').text,
                    'description': clean_html(channel.find('description').text.replace("&amp;", "&")),
                    'status': channel.find('status').text,
                    'last_broadcast_at': last_broadcast_at,
                    'follower': stats.find('follower').text,
                    'viewer_total': stats.find('viewer_total').text,
                    'viewer': viewer,
                    'thumbnail': thumbnail.find('live').text,
                    'stream': stream}
        else:
            message(_Leic_comm_radio_not_broadcasting + last_broadcast_at, _off_air)
            return 0
    except:
        msg_notification(_error, _failed_to_download, xbmcgui.NOTIFICATION_ERROR, 3000)
        return 0


def list_audio():
    """
    Create the list of playable videos in the Kodi interface.
    :return: None
    """
    channel_info = get_channel_info()
    listing = []
    title = __addonname__ + ' - Live'
    if channel_info <> 0:
        try:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=channel_info['thumbnail'])
            # Set a fanart image for the list item.
            list_item.setProperty('fanart_image', __fanart__)
            # Set additional info for the list item.
            list_item.setInfo('audio', {'title': title,
                'album': __addonname__,
                'genre': 'Internet Radio',
                'year': 2015
                })
            list_item.setInfo('video', {'title': title,
                'genre': 'Internet Radio',
                'plot': channel_info['description'],
                'year': 2015,
                'status': channel_info['status'],
                'mediatype': 'musicvideo'
                })
            # Set 'IsPlayable' property to 'true'.
            list_item.setProperty('IsPlayable', 'true')
            # Create a URL for the plugin recursive callback.
            url = '{0}?action=play&audio={1}'.format(__url__, channel_info['stream'])
            # is_folder = False means that this item won't open any sub-list.
            is_folder = False
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))
            # Add context menu for statistics
            list_item.addContextMenuItems([ (_ustream_stats, 'XBMC.RunPlugin({0}?action=statistics)'.format(__url__)) ])
            # Add our listing to Kodi.
            xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
            # Add a sort method for the virtual folder items (alphabetically, ignore articles)
            xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
            # Finish creating a virtual folder.
            xbmcplugin.endOfDirectory(__handle__)
        except:
            pass


def play_audio(path):
    """
    Play audio stream by the provided path.
    :param path: str
    :return: None
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(__handle__, True, listitem=play_item)
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


def show_ustream_stats():
    # Show waiting dialog (like hourglass)
    xbmc.executebuiltin('ActivateWindow(busydialog)')
    # Show statistics
    info = get_channel_info()
    try:
        # Remove waiting dialog (like hourglass)
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        message('[COLOR blue]%s:[/COLOR] %s\n[COLOR blue]'
            '%s:[/COLOR] %s\n[COLOR blue]'
            '%s:[/COLOR] %s\n[COLOR blue]'
            '%s:[/COLOR] %s\n' % (_last_broadcast,
            info['last_broadcast_at'],
            _followers,
            info['follower'],
            _viewer_total,
            info['viewer_total'],
            _viewers,
            info['viewer']),
            '%s - %s' % (_ustream_stats,
            info['status']))
    except:
        msg_notification(_error, _failed_to_download, xbmcgui.NOTIFICATION_ERROR, 3000)


def msg_notification(heading, message, icon, duration):
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
                # Display the list of videos in a provided category.
                list_audio()
            elif params['action'] == 'play':
                # Play audio stream from a provided URL.
                play_audio(params['audio'])
            elif params['action'] == 'statistics':
                # Show statistics
                show_ustream_stats()
        except:
            list_audio()
    else:
        list_audio()