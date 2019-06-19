#!/bin/python

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import urllib
import urllib2
import re
import sys
import os
#from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
import HTMLParser

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-09-2018
# Description: Addon for showing rss feeds

# Get addon details
__addon_id__ = 'script.rss-reader'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'

#  Variables
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
__rss_feeds_dir__ = xbmc.translatePath( 'special://profile/RssFeeds.xml' )
__tree__ = ET.parse(__rss_feeds_dir__)
__root__ = __tree__.getroot()

def _get_url(url):
    """
    Download url and remove carriage return
    and tab spaces from page
    """
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent',
                       'Mozilla/5.0 (Windows; '
                       'U; Windows NT 5.1; en-GB; '
                       'rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link = response.read()
        response.close()
        return link
    except:
    	 notification("Error!",
                      "Unable to downloads url!",
                      __icon__,
                      5000)


def subscriptions():
    """
    Fetch subscriptions from the users RssFeeds.xml file
    and display a list of the feed subscriptions
    """
    for subscription in __root__.iter('feed'):
        response = _get_url(subscription.text)
        root = ET.fromstring(response)

        for item in root.iter('channel'):
            title = item.find('title').text

        list_item = title
        url = subscription.text
        addDir(list_item,
               url,
               1,
               "",
               "",
               "",
               isFolder=True)


def feeds(url):
    """
    Fetch RSS feeds from url
    """
    response = _get_url(url)
    root = ET.fromstring(response)
    for feed in root.iter('item'):
        title = feed.find('title').text
        list_item = title
        namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
        feed_content = feed.find('content:encoded', namespaces).text
#        feed_content = feed.find('description', namespaces).text
        imgsrc = re.search('img[^<>\\n]+src=[\'"]([^"\']+)[\'"]',feed_content)

        if imgsrc:
            feed_image = imgsrc.group(1)
        else:
            feed_image = __icon__

        addDir(list_item,
               url,
               2,
               feed_image,
               "",
               "",
               isFolder=False)


def  feed(name, url):
    """
    Show Feed
    """
    response = _get_url(url)
    root = ET.fromstring(response)
    for website_details in root.iter('channel'):
        website_title = website_details.find('title').text
        website_link = website_details.find('link').text

    for feed in root.iter('item'):
        feed_title = feed.find('title').text

        if feed_title == name:
            feed_link = feed.find('link').text
            feed_date = feed.find('pubDate').text
            feed_date = feed_date[:feed_date.find(' +')]
            feed_cats = feed.findall('category')
            feed_category = ''

            for cat in feed_cats:
                feed_category = feed_category + ', ' + cat.text

            if len(feed_category) > 0:
                feed_category = feed_category[2:]

            feed_category = feed_category.replace('<![CDATA[', '').replace(']]>', '')
            feed_desc = feed.find('description').text
            namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
            feed_content = feed.find('content:encoded', namespaces).text
#            feed_content = feed.find('description', namespaces).text.replace('\t', '')

            break

    desc = 'n/a'
    desc = feed_content
    imgsrc = re.search('img[^<>\\n]+src=[\'"]([^"\']+)[\'"]',desc)
    if imgsrc:
        feed_image=imgsrc.group(1)
    else:
        feed_image = ""

    #convert news text into plain text
    desc = re.sub('<p[^>\\n]*>','\n\n',desc)
    desc = re.sub('<br[^>\\n]*>','\n',desc)
    desc = re.sub('<li[^>\\n]*>', '      ', desc)
    desc = re.sub('<[^>\\n]+>','',desc)
    desc = re.sub('\\n\\n+','\n\n',desc)
    desc = re.sub('(\\w+,?) *\\n(\\w+)','\\1 \\2',desc)
    desc = desc.replace('<![CDATA[', '').replace(']]>', '')
    desc = HTMLParser.HTMLParser().unescape(desc)
    feed_text = desc
    window = xbmcgui.WindowXMLDialog('script-rss-reader.xml', __addon__.getAddonInfo('path'))
    win = xbmcgui.Window(10147)
    win.setProperty('HeadingLabel', feed_title)
    win.setProperty('FeedImage', feed_image)
    win.setProperty('FeedName', feed_title)
    win.setProperty('FeedCategory', feed_category)
    win.setProperty('PubDate', feed_date)
    win.setProperty('AuthorName', website_title)
    win.setProperty('FeedWebsite', website_link)
    win.setProperty('Description', feed_text)
    window.doModal()
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

    ok = xbmcplugin.addDirectoryItem(handle=__handle__,
                                     url=u,
                                     listitem=liz,
                                     isFolder=isFolder)
    return ok


def notification(message, title, icon, duration):
    # Show message notification
    dialog = xbmcgui.Dialog()
    dialog.notification(title, message, icon, duration)


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
    subscriptions()
elif mode == 1:
	feeds(url)
elif mode == 2:
	feed(name, url)

xbmcplugin.endOfDirectory(__handle__)
