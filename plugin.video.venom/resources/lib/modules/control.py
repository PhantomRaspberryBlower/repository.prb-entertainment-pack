# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

from datetime import datetime
import glob
import os
import re
import string
from sys import argv
import time
import json

try:
	from urllib import urlencode
except:
	from urllib.parse import urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
import xml.etree.ElementTree as ET

def getKodiVersion():
	return int(xbmc.getInfoLabel("System.BuildVersion")[:2])

addon = xbmcaddon.Addon
AddonID = xbmcaddon.Addon().getAddonInfo('id')
addonInfo = xbmcaddon.Addon().getAddonInfo
addonName = addonInfo('name')
addonVersion = addonInfo('version')

getLangString = xbmcaddon.Addon().getLocalizedString
# setting = xbmcaddon.Addon().getSetting
# setSetting = xbmcaddon.Addon().setSetting
item = xbmcgui.ListItem
listControl = xbmcgui.ControlList
labelControl = xbmcgui.ControlLabel
homeWindow = xbmcgui.Window(10000)

windowDialog = xbmcgui.WindowDialog()
dialog = xbmcgui.Dialog()
progressDialog = xbmcgui.DialogProgress()
progressDialogBG = xbmcgui.DialogProgressBG()
getCurrentDialogId = xbmcgui.getCurrentWindowDialogId()
button = xbmcgui.ControlButton
image = xbmcgui.ControlImage

addItem = xbmcplugin.addDirectoryItem
directory = xbmcplugin.endOfDirectory
content = xbmcplugin.setContent
property = xbmcplugin.setProperty
resolve = xbmcplugin.setResolvedUrl

condVisibility = xbmc.getCondVisibility
execute = xbmc.executebuiltin
infoLabel = xbmc.getInfoLabel
legalFilename = xbmc.makeLegalFilename if getKodiVersion() < 19 else xbmcvfs.makeLegalFilename
keyboard = xbmc.Keyboard
monitor = xbmc.Monitor()
skin = xbmc.getSkinDir()

player = xbmc.Player()
player2 = xbmc.Player
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

jsonrpc = xbmc.executeJSONRPC
skinPath = xbmc.translatePath('special://skin/')

joinPath = os.path.join
isfilePath = os.path.isfile

deleteDir = xbmcvfs.rmdir
deleteFile = xbmcvfs.delete
existsPath = xbmcvfs.exists
listDir = xbmcvfs.listdir
makeFile = xbmcvfs.mkdir
makeDirs = xbmcvfs.mkdirs
openFile = xbmcvfs.File
transPath = xbmc.translatePath

SETTINGS_PATH = xbmc.translatePath(os.path.join(addonInfo('path'), 'resources', 'settings.xml'))

try:
	dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')
except:
	dataPath = xbmc.translatePath(addonInfo('profile'))

settingsFile = os.path.join(dataPath, 'settings.xml')
viewsFile = os.path.join(dataPath, 'views.db')
bookmarksFile = os.path.join(dataPath, 'bookmarks.db')
providercacheFile = os.path.join(dataPath, 'providers.db')
metacacheFile = os.path.join(dataPath, 'metadata.db')
searchFile = os.path.join(dataPath, 'search.db')
libcacheFile = os.path.join(dataPath, 'library.db')
cacheFile = os.path.join(dataPath, 'cache.db')
traktSyncFile = os.path.join(dataPath, 'traktSync.db')
trailer = 'plugin://plugin.video.youtube/play/?video_id=%s'


def syncMyAccounts(silent=False):
	import myaccounts
	all_acct = myaccounts.getAll()
	trakt_acct = all_acct.get('trakt')
	if setting('trakt.username') != trakt_acct.get('username'):
		setSetting('trakt.isauthed', 'true')
		setSetting('trakt.token', trakt_acct.get('token'))
		setSetting('trakt.username', trakt_acct.get('username'))
		setSetting('trakt.refresh', trakt_acct.get('refresh'))
		setSetting('trakt.expires', trakt_acct.get('expires'))

	ad_acct = all_acct.get('alldebrid')
	if setting('alldebrid.username') != ad_acct.get('username'):
		setSetting('alldebrid.token', ad_acct.get('token'))
		setSetting('alldebrid.username', ad_acct.get('username'))

	pm_acct = all_acct.get('premiumize')
	if setting('premiumize.username') != pm_acct.get('username'):
		setSetting('premiumize.token', pm_acct.get('token'))
		setSetting('premiumize.username', pm_acct.get('username'))

	rd_acct = all_acct.get('realdebrid')
	if setting('realdebrid.username') != rd_acct.get('username'):
		setSetting('realdebrid.token', rd_acct.get('token'))
		setSetting('realdebrid.username', rd_acct.get('username'))
		setSetting('realdebrid.client_id', rd_acct.get('client_id'))
		setSetting('realdebrid.refresh', rd_acct.get('refresh'))
		setSetting('realdebrid.secret', rd_acct.get('secret'))

	fanart_acct = all_acct.get('fanart_tv')
	if setting('fanart.tv.api.key') != fanart_acct.get('api_key'):
		setSetting('fanart.tv.api.key', fanart_acct.get('api_key'))

	tmdb_acct = all_acct.get('tmdb')
	if setting('tmdb.api.key') != tmdb_acct.get('api_key'):
		setSetting('tmdb.api.key', tmdb_acct.get('api_key'))
	if setting('tmdb.username') != tmdb_acct.get('username'):
		setSetting('tmdb.username', tmdb_acct.get('username'))
	if setting('tmdb.password') != tmdb_acct.get('password'):
		setSetting('tmdb.password', tmdb_acct.get('password'))
	if setting('tmdb.session_id') != tmdb_acct.get('session_id'):
		setSetting('tmdb.session_id', tmdb_acct.get('session_id'))

	tvdb_acct = all_acct.get('tvdb')
	if setting('tvdb.api.key') != tvdb_acct.get('api_key'):
		setSetting('tvdb.api.key', tvdb_acct.get('api_key'))

	imdb_acct = all_acct.get('imdb')
	if setting('imdb.user') != imdb_acct.get('user'):
		setSetting('imdb.user', imdb_acct.get('user'))
	if not silent:
		notification(message=32114)


def setting(id, fallback=None):
	try: settings_dict = json.loads(homeWindow.getProperty('venom_settings'))
	except: settings_dict = make_settings_dict()
	if settings_dict is None: settings_dict = settings_fallback(id)
	value = settings_dict.get(id, '')
	if fallback is None: return value
	if value == '': return fallback
	return value


def settings_fallback(id):
	return {id: xbmcaddon.Addon().getSetting(id)}


def setSetting(id, value):
	from xbmcaddon import Addon
	Addon().setSetting(id, value)


def make_settings_dict():
	try:
		kodi_version = getKodiVersion()
		profile_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.venom/')
		settings_xml = os.path.join(profile_dir, 'settings.xml')
		root = ET.parse(settings_xml).getroot()
		# root = ET.parse(settingsFile).getroot()
		settings_dict = {}
		for item in root:
			dict_item = {}
			setting_id = item.get('id')
			if kodi_version >= 18: setting_value = item.text
			else: setting_value = item.get('value')
			if setting_value is None: setting_value = ''
			dict_item = {setting_id: setting_value}
			settings_dict.update(dict_item)
		homeWindow.setProperty('venom_settings', json.dumps(settings_dict))
		return settings_dict
	except:
		return None


def lang(language_id):
	text = getLangString(language_id)
	if getKodiVersion() < 19:
		text = text.encode('utf-8', 'replace')
	return text


def display_string(object):
	try:
		if type(object) is str or type(object) is unicode:
			return deaccentString(object)
	except NameError:
		if type(object) is str:
			return deaccentString(object)
	if type(object) is int:
		return '%s' % object
	if type(object) is bytes:
		object = ''.join(chr(x) for x in object)
		return object


def deaccentString(text):
	try:
		if isinstance(text, bytes):
			text = text.decode('utf-8')
	except UnicodeDecodeError:
		text = u'%s' % text
	text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
	return text


def strip_non_ascii_and_unprintable(text):
	result = ''.join(char for char in text if char in string.printable)
	return result.encode('ascii', errors='ignore').decode('ascii', errors='ignore')


def sleep(time):  # Modified `sleep`(in milli secs) command that honors a user exit request
	while time > 0 and not monitor.abortRequested():
		xbmc.sleep(min(100, time))
		time = time - 100


def getCurrentViewId():
	win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
	return str(win.getFocusId())


def check_version_numbers(current, new):
	# Compares version numbers and return True if new version is newer
	current = current.split('.')
	new = new.split('.')
	step = 0
	for i in current:
		if int(new[step]) > int(i):
			return True
		if int(i) > int(new[step]):
			return False
		if int(i) == int(new[step]):
			step += 1
			continue
	return False


def getVenomVersion():
	return xbmcaddon.Addon('plugin.video.venom').getAddonInfo('version')


def addonVersion(addon):
	return xbmcaddon.Addon(addon).getAddonInfo('version')


def get_plugin_url(queries):
	try:
		query = urlencode(queries)
	except UnicodeEncodeError:
		for k in queries:
			if isinstance(queries[k], unicode):
				queries[k] = queries[k].encode('utf-8')
		query = urlencode(queries)
	addon_id = argv[0]
	if not addon_id:
		addon_id = addonId()
	return addon_id + '?' + query


def addonId():
	return addonInfo('id')


def addonName():
	return addonInfo('name')


def addonPath(addon):
	try: addonID = xbmcaddon.Addon(addon)
	except: addonID = None
	if addonID is None: return ''
	else:
		try: return xbmc.translatePath(addonID.getAddonInfo('path').decode('utf-8'))
		except: return xbmc.translatePath(addonID.getAddonInfo('path'))


def artPath():
	theme = appearance()
	return os.path.join(xbmcaddon.Addon('plugin.video.venom').getAddonInfo('path'), 'resources', 'artwork', theme)


def appearance():
	appearance = setting('appearance.1').lower()
	return appearance


def addonIcon():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']):
		return os.path.join(art, 'icon.png')
	return addonInfo('icon')


def addonThumb():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']):
		return os.path.join(art, 'poster.png')
	elif theme == '-':
		return 'DefaultFolder.png'
	return addonInfo('icon')


def addonPoster():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']):
		return os.path.join(art, 'poster.png')
	return 'DefaultVideo.png'


def addonBanner():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']):
		return os.path.join(art, 'banner.png')
	return 'DefaultVideo.png'


def addonFanart():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']):
		return os.path.join(art, 'fanart.jpg')
	return addonInfo('fanart')


def addonNext():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']):
		return os.path.join(art, 'next.png')
	return 'DefaultVideo.png'


# def metaFile():
	# # if condVisibility('System.HasAddon(script.venom.metadata)'):
		# # return os.path.join(xbmcaddon.Addon('script.venom.metadata').getAddonInfo('path'), 'resources', 'data', 'meta.db')
	# return os.path.join(dataPath, 'metadata.db')


def metadataClean(metadata):
	if not metadata: return metadata
	allowed = ['genre', 'country', 'year', 'episode', 'season', 'sortepisode', 'sortseason', 'episodeguide', 'showlink',
					'top250', 'setid', 'tracknumber', 'rating', 'userrating', 'watched', 'playcount', 'overlay', 'cast',
					'castandrole', 'director', 'mpaa', 'plot', 'plotoutline', 'title', 'originaltitle', 'sorttitle',
					'duration', 'studio', 'tagline', 'writer', 'tvshowtitle', 'premiered', 'status', 'set', 'setoverview',
					'tag', 'imdbnumber', 'code', 'aired', 'credits', 'lastplayed', 'album', 'artist', 'votes', 'path',
					'trailer', 'dateadded', 'mediatype', 'dbid']
	return {k: v for k, v in metadata.iteritems() if k in allowed}


####################################################
# --- Dialogs
####################################################
def notification(title=None, message=None, icon=None, time=3000, sound=(setting('notification.sound') == 'true')):
	if title == 'default' or title is None:
		title = addonName()
	if isinstance(title, (int, long)):
		heading = lang(title)
	else:
		heading = str(title)
	if isinstance(message, (int, long)):
		body = lang(message)
	else:
		body = str(message)
	if icon is None or icon == '' or icon == 'default':
		icon = addonIcon()
	elif icon == 'INFO':
		icon = xbmcgui.NOTIFICATION_INFO
	elif icon == 'WARNING':
		icon = xbmcgui.NOTIFICATION_WARNING
	elif icon == 'ERROR':
		icon = xbmcgui.NOTIFICATION_ERROR
	dialog.notification(heading, body, icon, time, sound=sound)


def yesnoDialog(line1, line2, line3, heading=addonInfo('name'), nolabel='', yeslabel=''):
	return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)


def selectDialog(list, heading=addonInfo('name')):
	return dialog.select(heading, list)


def okDialog(title=None, message=None):
	if title == 'default' or title is None:
		title = addonName()
	if isinstance(title, (int, long)):
		heading = lang(title)
	else:
		heading = str(title)
	if isinstance(message, (int, long)):
		body = lang(message)
	else:
		body = str(message)
	return dialog.ok(heading, body)


def context(items=None, labels=None):
	if items:
		labels = [i[0] for i in items]
		choice = xbmcgui.Dialog().contextmenu(labels)
		if choice >= 0: return items[choice][1]()
		else: return False
	else:
		return xbmcgui.Dialog().contextmenu(labels)


def busy():
	if getKodiVersion() >= 18:
		return execute('ActivateWindow(busydialognocancel)')
	else:
		return execute('ActivateWindow(busydialog)')


def hide():
	if getKodiVersion() >= 18 and condVisibility('Window.IsActive(busydialognocancel)'):
		return execute('Dialog.Close(busydialognocancel)')
	else:
		return execute('Dialog.Close(busydialog)')


def closeAll():
	return execute('Dialog.Close(all, true)')


def closeOk():
	return execute('Dialog.Close(okdialog, true)')


def cancelPlayback():
	playlist.clear()
	syshandle = int(argv[1])
	resolve(syshandle, False, item())
	closeOk()


def visible():
	if getKodiVersion() >= 18 and xbmc.getCondVisibility('Window.IsActive(busydialognocancel)') == 1:
		return True
	return xbmc.getCondVisibility('Window.IsActive(busydialog)') == 1
########################


def refresh():
	return execute('Container.Refresh')


def queueItem():
	return execute('Action(Queue)')


def openSettings(query=None, id=addonInfo('id')):
	try:
		hide()
		execute('Addon.OpenSettings(%s)' % id)
		if not query: return
		c, f = query.split('.')
		if getKodiVersion() >= 18:
			execute('SetFocus(%i)' % (int(c) - 100))
			execute('SetFocus(%i)' % (int(f) - 80))
		else:
			execute('SetFocus(%i)' % (int(c) + 100))
			execute('SetFocus(%i)' % (int(f) + 200))
	except:
		import traceback
		traceback.print_exc()
		return


def apiLanguage(ret_name=None):
	langDict = {'Bulgarian': 'bg', 'Chinese': 'zh', 'Croatian': 'hr', 'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl',
						'English': 'en', 'Finnish': 'fi', 'French': 'fr', 'German': 'de', 'Greek': 'el', 'Hebrew': 'he',
						'Hungarian': 'hu', 'Italian': 'it', 'Japanese': 'ja', 'Korean': 'ko', 'Norwegian': 'no', 'Polish': 'pl',
						'Portuguese': 'pt', 'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr', 'Slovak': 'sk',
						'Slovenian': 'sl', 'Spanish': 'es', 'Swedish': 'sv', 'Thai': 'th', 'Turkish': 'tr', 'Ukrainian': 'uk'}
	trakt = ['bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'he', 'hr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl',
				'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'th', 'tr', 'uk', 'zh']
	tvdb = ['en', 'sv', 'no', 'da', 'fi', 'nl', 'de', 'it', 'es', 'fr', 'pl', 'hu', 'el', 'tr', 'ru', 'he', 'ja', 'pt',
				'zh', 'cs', 'sl', 'hr', 'ko']
	youtube = ['gv', 'gu', 'gd', 'ga', 'gn', 'gl', 'ty', 'tw', 'tt', 'tr', 'ts', 'tn', 'to', 'tl', 'tk', 'th', 'ti',
						'tg', 'te', 'ta', 'de', 'da', 'dz', 'dv', 'qu', 'zh', 'za', 'zu', 'wa', 'wo', 'jv', 'ja', 'ch', 'co',
						'ca', 'ce', 'cy', 'cs', 'cr', 'cv', 'cu', 'ps', 'pt', 'pa', 'pi', 'pl', 'mg', 'ml', 'mn', 'mi', 'mh',
						'mk', 'mt', 'ms', 'mr', 'my', 've', 'vi', 'is', 'iu', 'it', 'vo', 'ii', 'ik', 'io', 'ia', 'ie', 'id',
						'ig', 'fr', 'fy', 'fa', 'ff', 'fi', 'fj', 'fo', 'ss', 'sr', 'sq', 'sw', 'sv', 'su', 'st', 'sk', 'si',
						'so', 'sn', 'sm', 'sl', 'sc', 'sa', 'sg', 'se', 'sd', 'lg', 'lb', 'la', 'ln', 'lo', 'li', 'lv', 'lt',
						'lu', 'yi', 'yo', 'el', 'eo', 'en', 'ee', 'eu', 'et', 'es', 'ru', 'rw', 'rm', 'rn', 'ro', 'be', 'bg',
						'ba', 'bm', 'bn', 'bo', 'bh', 'bi', 'br', 'bs', 'om', 'oj', 'oc', 'os', 'or', 'xh', 'hz', 'hy', 'hr',
						'ht', 'hu', 'hi', 'ho', 'ha', 'he', 'uz', 'ur', 'uk', 'ug', 'aa', 'ab', 'ae', 'af', 'ak', 'am', 'an',
						'as', 'ar', 'av', 'ay', 'az', 'nl', 'nn', 'no', 'na', 'nb', 'nd', 'ne', 'ng', 'ny', 'nr', 'nv', 'ka',
						'kg', 'kk', 'kj', 'ki', 'ko', 'kn', 'km', 'kl', 'ks', 'kr', 'kw', 'kv', 'ku', 'ky']
	name = None
	name = setting('api.language')
	if not name:
		name = 'AUTO'
	if name[-1].isupper():
		try: name = xbmc.getLanguage(xbmc.ENGLISH_NAME).split(' ')[0]
		except: pass
	try: name = langDict[name]
	except: name = 'en'
	lang = {'trakt': name} if name in trakt else {'trakt': 'en'}
	lang['tvdb'] = name if name in tvdb else 'en'
	lang['youtube'] = name if name in youtube else 'en'
	if ret_name:
		lang['trakt'] = [i[0] for i in langDict.iteritems() if i[1] == lang['trakt']][0]
		lang['tvdb'] = [i[0] for i in langDict.iteritems() if i[1] == lang['tvdb']][0]
		lang['youtube'] = [i[0] for i in langDict.iteritems() if i[1] == lang['youtube']][0]
	return lang


def cdnImport(uri, name):
	import imp
	from resources.lib.modules import client
	path = os.path.join(dataPath, 'py' + name)
	path = path.decode('utf-8')
	deleteDir(os.path.join(path, ''), force=True)
	makeFile(dataPath)
	makeFile(path)
	r = client.request(uri)
	p = os.path.join(path, name + '.py')
	f = openFile(p, 'w');
	f.write(r);
	f.close()
	m = imp.load_source(name, p)
	deleteDir(os.path.join(path, ''), force=True)
	return m


###---start adding TMDb to params
def autoTraktSubscription(tvshowtitle, year, imdb, tvdb):
	from resources.lib.modules import libtools
	libtools.libtvshows().add(tvshowtitle, year, imdb, tvdb)


def getSettingDefault(id):
	try:
		settings = open(SETTINGS_PATH, 'r')
		value = ' '.join(settings.readlines())
		value.strip('\n')
		settings.close()
		value = re.findall(r'id=\"%s\".*?default=\"(.*?)\"' % (id), value)[0]
		return value
	except:
		return None


def getColor(n):
	colorChart = ['blue', 'red', 'yellow', 'deeppink', 'cyan', 'lawngreen', 'gold', 'magenta', 'yellowgreen',
						'skyblue', 'lime', 'limegreen', 'deepskyblue', 'white', 'whitesmoke', 'nocolor']
	if not n: n = '8'
	color = colorChart[int(n)]
	return color


def getMenuEnabled(menu_title):
	is_enabled = setting(menu_title).strip()
	if (is_enabled == '' or is_enabled == 'false'):
		return False
	return True


def trigger_widget_refresh():
	import time
	timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
	homeWindow.setProperty("widgetreload", timestr)
	homeWindow.setProperty('widgetreload-tvshows', timestr)
	homeWindow.setProperty('widgetreload-episodes', timestr)
	homeWindow.setProperty('widgetreload-movies', timestr)


def get_video_database_path():
	database_path = os.path.abspath(os.path.join(dataPath, '..', '..', 'Database', ))
	if getKodiVersion() == 17:
		database_path = os.path.join(database_path, 'MyVideos107.db')
	elif getKodiVersion() == 18:
		database_path = os.path.join(database_path, 'MyVideos116.db')
	return database_path


def datetime_workaround(string_date, format="%Y-%m-%d", date_only=True):
	sleep(200)
	try:
		if string_date == '':
			return None
		try:
			if date_only:
				res = datetime.strptime(string_date, format).date()
			else:
				res = datetime.strptime(string_date, format)
		except TypeError:
			if date_only:
				res = datetime(*(time.strptime(string_date, format)[0:6])).date()
			else:
				res = datetime(*(time.strptime(string_date, format)[0:6]))
		return res
	except:
		import traceback
		traceback.print_exc()
		pass


def add_source(source_name, source_path, source_content, source_thumbnail, type='video'):
	xml_file = xbmc.translatePath('special://profile/sources.xml')
	if not os.path.exists(xml_file):
		with open(xml_file, 'w') as f:
			f.write(
'''
<sources>
	<programs>
		<default pathversion="1"/>
	</programs>
	<video>
		<default pathversion="1"/>
	</video>
	<music>
		<default pathversion="1"/>
	</music>
	<pictures>
		<default pathversion="1"/>
	</pictures>
	<files>
		<default pathversion="1"/>
	</files>
	<games>
		<default pathversion="1"/>
	</games>
</sources>
''')
	existing_source = _get_source_attr(xml_file, source_name, 'path', type=type)
	if existing_source and existing_source != source_path and source_content != '':
		_remove_source_content(existing_source)
	if _add_source_xml(xml_file, source_name, source_path, source_thumbnail, type=type) and source_content != '':
		_remove_source_content(source_path) # Added to also rid any remains because manual delete sources and kodi leaves behind a record in MyVideos*.db
		_set_source_content(source_content)


def _add_source_xml(xml_file, name, path, thumbnail, type='video'):
	tree = ET.parse(xml_file)
	root = tree.getroot()
	sources = root.find(type)
	existing_source = None
	for source in sources.findall('source'):
		xml_name = source.find('name').text
		xml_path = source.find('path').text
		if source.find('thumbnail') is not None:
			xml_thumbnail = source.find('thumbnail').text
		else:
			xml_thumbnail = ''
		if xml_name == name or xml_path == path:
			existing_source = source
			break
	if existing_source is not None:
		xml_name = source.find('name').text
		xml_path = source.find('path').text
		if source.find('thumbnail') is not None:
			xml_thumbnail = source.find('thumbnail').text
		else:
			xml_thumbnail = ''
		if xml_name == name and xml_path == path and xml_thumbnail == thumbnail:
			return False
		elif xml_name == name:
			source.find('path').text = path
			source.find('thumbnail').text = thumbnail
		elif xml_path == path:
			source.find('name').text = name
			source.find('thumbnail').text = thumbnail
		else:
			source.find('path').text = path
			source.find('name').text = name
	else:
		new_source = ET.SubElement(sources, 'source')
		new_name = ET.SubElement(new_source, 'name')
		new_name.text = name
		new_path = ET.SubElement(new_source, 'path')
		new_thumbnail = ET.SubElement(new_source, 'thumbnail')
		new_allowsharing = ET.SubElement(new_source, 'allowsharing')
		new_path.attrib['pathversion'] = '1'
		new_thumbnail.attrib['pathversion'] = '1'
		new_path.text = path
		new_thumbnail.text = thumbnail
		new_allowsharing.text = 'true'
	_indent_xml(root)
	tree.write(xml_file)
	return True


def _indent_xml(elem, level=0):
	i = '\n' + level*'\t'
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + '\t'
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			_indent_xml(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i


def _get_source_attr(xml_file, name, attr, type='video'):
	tree = ET.parse(xml_file)
	root = tree.getroot()
	sources = root.find(type)
	for source in sources.findall('source'):
		xml_name = source.find('name').text
		if xml_name == name:
			return source.find(attr).text
	return None


def _db_execute(db_name, command):
	databaseFile = _get_database(db_name)
	if not databaseFile:
		return False
	try:
		from sqlite3 import dbapi2
	except:
		from pysqlite2 import dbapi2
	dbcon = dbapi2.connect(databaseFile)
	dbcur = dbcon.cursor()
	dbcur.execute(command)
	dbcon.commit()
	dbcon.close()
	return True


def _get_database(db_name):
	path_db = 'special://profile/Database/%s' % db_name
	filelist = glob.glob(xbmc.translatePath(path_db))
	if filelist:
		return filelist[-1]
	return None


def _remove_source_content(path):
	q = 'DELETE FROM path WHERE strPath LIKE "%{0}%"'.format(path)
	return _db_execute('MyVideos*.db', q)


def _set_source_content(content):
	q = 'INSERT OR REPLACE INTO path (strPath,strContent,strScraper,strHash,scanRecursive,useFolderNames,strSettings,noUpdate,exclude,dateAdded,idParentPath) VALUES '
	q += content
	return _db_execute('MyVideos*.db', q)


def clean_settings():
	def _make_content(dict_object):
		if kodi_version >= 18:
			content = '<settings version="2">'
			for item in dict_object:
				if item['id'] in active_settings:
					if 'default' in item and 'value' in item: content += '\n    <setting id="%s" default="%s">%s</setting>' % (item['id'], item['default'], item['value'])
					elif 'default' in item: content += '\n    <setting id="%s" default="%s"></setting>' % (item['id'], item['default'])
					elif 'value' in item: content += '\n    <setting id="%s">%s</setting>' % (item['id'], item['value'])
					else: content += '\n    <setting id="%s"></setting>'
				else: removed_settings.append(item)
		else:
			content = '<settings>'
			for item in dict_object:
				if item['id'] in active_settings:
					if 'value' in item: content += '\n    <setting id="%s" value="%s" />' % (item['id'], item['value'])
					else: content += '\n    <setting id="%s" value="" />' % item['id']
				else: removed_settings.append(item)
		content += '\n</settings>'
		return content
	kodi_version = getKodiVersion()
	for addon_id in ('plugin.video.venom', 'script.module.fenomscrapers'):
		try:
			removed_settings = []
			active_settings = []
			current_user_settings = []
			addon = xbmcaddon.Addon(id=addon_id)
			addon_name = addon.getAddonInfo('name')
			addon_dir = xbmc.translatePath(addon.getAddonInfo('path'))
			profile_dir = xbmc.translatePath(addon.getAddonInfo('profile'))
			active_settings_xml = os.path.join(addon_dir, 'resources', 'settings.xml')
			root = ET.parse(active_settings_xml).getroot()
			for item in root.findall('./category/setting'):
				setting_id = item.get('id')
				if setting_id:
					active_settings.append(setting_id)
			settings_xml = os.path.join(profile_dir, 'settings.xml')
			root = ET.parse(settings_xml).getroot()
			for item in root:
				dict_item = {}
				setting_id = item.get('id')
				setting_default = item.get('default')
				if kodi_version >= 18:
					setting_value = item.text
				else: setting_value = item.get('value')
				dict_item['id'] = setting_id
				if setting_value:
					dict_item['value'] = setting_value
				if setting_default:
					dict_item['default'] = setting_default
				current_user_settings.append(dict_item)
			new_content = _make_content(current_user_settings)
			nfo_file = xbmcvfs.File(settings_xml, 'w')
			nfo_file.write(new_content)
			nfo_file.close()
			sleep(200)
			notification(title=addon_name, message=lang(32084).format(str(len(removed_settings))))
		except:
			import traceback
			traceback.print_exc()
			notification(title=addon_name, message=32115)


def set_reuselanguageinvoker():
	if getKodiVersion() < 18:
		notification(message=32116)
		return
	try:
		addon_xml = joinPath(addonPath('plugin.video.venom'), 'addon.xml')
		tree = ET.parse(addon_xml)
		root = tree.getroot()
		for item in root.iter('reuselanguageinvoker'):
			current_value = str(item.text)
		if current_value:
			new_value = 'true' if current_value == 'false' else 'false'
			if not yesnoDialog(lang(33018) % (current_value, new_value), '', ''):
				return openSettings(query='12.6')
			if new_value == 'true':
				if not yesnoDialog(lang(33019), '', ''): return
			item.text = new_value
			hash_start = gen_file_hash(addon_xml)
			tree.write(addon_xml)
			hash_end = gen_file_hash(addon_xml)
			if hash_start != hash_end:
				setSetting('reuse.languageinvoker', new_value)
				okDialog(message=lang(33017) % new_value)
			else:
				return okDialog(message=33021)
			current_profile = infoLabel('system.profilename')
			okDialog(message=33020)
			execute('LoadProfile(%s)' % current_profile)
	except:
		import traceback
		traceback.print_exc()


def gen_file_hash(file):
	try:
		import hashlib
		md5_hash = hashlib.md5()
		with open(file, 'rb') as afile:
			buf = afile.read()
			md5_hash.update(buf)
			return md5_hash.hexdigest()
	except:
		import traceback
		traceback.print_exc()