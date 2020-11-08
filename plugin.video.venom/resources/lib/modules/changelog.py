# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

import os.path
import xbmc
import xbmcaddon
import xbmcgui


def get():
	addonInfo = xbmcaddon.Addon().getAddonInfo
	addonPath = xbmc.translatePath(addonInfo('path'))
	changelogfile = os.path.join(addonPath, 'changelog.txt')
	r = open(changelogfile)
	text = r.read()
	r.close()
	xbmcgui.Dialog().textviewer('[COLOR red]Venom[/COLOR] -  v%s - %s' % (xbmcaddon.Addon().getAddonInfo('version'), 'changelog.txt'), text)