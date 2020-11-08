# -*- coding: UTF-8 -*-

"""
	Venom Add-on
"""

import os
import xbmc
import xbmcaddon
import xbmcgui

try:
	from urllib.request import urlopen, Request
except ImportError:
	from urllib2 import urlopen, Request

ADDON_ID = xbmcaddon.Addon().getAddonInfo('id')
HOMEPATH = xbmc.translatePath('special://home/')
ADDONSPATH = os.path.join(HOMEPATH, 'addons')
THISADDONPATH = os.path.join(ADDONSPATH, ADDON_ID)
NEWSFILE = 'https://raw.githubusercontent.com/123Venom/zips/master/plugin.video.venom/newsinfo.txt'
LOCALNEWS = os.path.join(THISADDONPATH, 'newsinfo.txt')


def news():
	message = open_news_url(NEWSFILE)
	compfile = open(LOCALNEWS).read()
	if len(message) > 1:
		if compfile == message: pass
		else:
			text_file = open(LOCALNEWS, "w")
			text_file.write(message)
			text_file.close()
			compfile = message
	showText('[B][COLOR red]News and Info[/COLOR][/B]', compfile)


def open_news_url(url):
	req = Request(url)
	req.add_header('User-Agent', 'klopp')
	response = urlopen(req)
	link = response.read()
	response.close()
	return link


def news_local():
	compfile = open(LOCALNEWS).read()
	showText('[B]News and Info[/B]', compfile)


def showText(heading, text):
	return xbmcgui.Dialog().textviewer(heading, text)

