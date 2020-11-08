# -*- coding: utf-8 -*-

"""
	Venom
"""

import threading
import xbmc

from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import trakt

window = control.homeWindow


class CheckSettingsFile():
	def run(self):
		try:
			xbmc.log('[ plugin.video.venom ]  CheckSettingsFile Service Starting...', 2)
			window.clearProperty('venom_settings')
			profile_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.venom/')
			if not control.existsPath(profile_dir):
				success = control.makeDirs(profile_dir)
				if success:
					xbmc.log('%s : created successfully' % profile_dir, 2)
			else:
				xbmc.log('%s : already exists' % profile_dir, 2)
			settings_xml = control.joinPath(profile_dir, 'settings.xml')
			if not control.existsPath(settings_xml):
				control.setSetting('trakt.message1', '')
				xbmc.log('%s : created successfully' % settings_xml, 2)
			else:
				xbmc.log('%s : already exists' % settings_xml, 2)
			return xbmc.log('[ plugin.video.venom ]  Finished CheckSettingsFile Service', 2)
		except:
			import traceback
			traceback.print_exc()
			pass


class SettingsMonitor(xbmc.Monitor):
	def __init__ (self):
		xbmc.Monitor.__init__(self)
		xbmc.log('[ plugin.video.venom ]  Settings Monitor Service Starting...', 2)

	def onSettingsChanged(self):
		window.clearProperty('venom_settings')
		xbmc.sleep(50)
		refreshed = control.make_settings_dict()


class SyncMyAccounts:
	def run(self):
		xbmc.log('[ plugin.video.venom ]  Sync "My Accounts" Service Starting...', 2)
		control.syncMyAccounts(silent=True)
		return xbmc.log('[ plugin.video.venom ]  Finished Sync "My Accounts" Service', 2)


class ReuseLanguageInvokerCheck:
	def run(self):
		if control.getKodiVersion() < 18: return
		xbmc.log("[ plugin.video.venom ]  ReuseLanguageInvokerCheck Service Starting...", 2)
		try:
			import xml.etree.ElementTree as ET
			addon_xml = control.joinPath(control.addonPath('plugin.video.venom'), 'addon.xml')
			tree = ET.parse(addon_xml)
			root = tree.getroot()
			current_addon_setting = control.addon('plugin.video.venom').getSetting('reuse.languageinvoker')
			try: current_xml_setting = [str(i.text) for i in root.iter('reuselanguageinvoker')][0]
			except: return xbmc.log("[ plugin.video.venom ]  ReuseLanguageInvokerCheck failed to get settings.xml value", 2)
			if current_addon_setting == '':
				current_addon_setting = 'true'
				control.setSetting('reuse.languageinvoker', current_addon_setting)
			if current_xml_setting == current_addon_setting: return
			if not control.yesnoDialog(control.lang(33018) % (current_xml_setting, current_addon_setting), '', ''):
				return control.setSetting('reuse.languageinvoker', 'true')
			for item in root.iter('reuselanguageinvoker'):
				item.text = current_addon_setting
				hash_start = control.gen_file_hash(addon_xml)
				tree.write(addon_xml)
				hash_end = control.gen_file_hash(addon_xml)
				if hash_start != hash_end:
					control.okDialog(message=33020)
					current_profile = control.infoLabel('system.profilename')
					control.execute('LoadProfile(%s)' % current_profile)
				else:
					control.okDialog(message=33022)
			xbmc.log("[ plugin.video.venom ]  ReuseLanguageInvokerCheck Service finished", 2)
			return
		except:
			log_utils.error()
			pass


class AddonCheckUpdate:
	def run(self):
		xbmc.log('[ plugin.video.venom ]  Addon checking available updates', 2)
		try:
			import re
			import requests
			repo_xml = requests.get('https://raw.githubusercontent.com/123Venom/zips/master/addons.xml')
			if not repo_xml.status_code == 200:
				xbmc.log('[ plugin.video.venom ]  Could not connect to remote repo XML: status code = %s' % repo_xml.status_code, 2)
				return
			repo_version = re.findall(r'<addon id=\"plugin.video.venom\".+version=\"(\d*.\d*.\d*)\"', repo_xml.text)[0]
			local_version = control.getVenomVersion()
			if control.check_version_numbers(local_version, repo_version):
				while control.condVisibility('Library.IsScanningVideo'):
					control.sleep(10000)
				xbmc.log('[ plugin.video.venom ]  A newer version is available. Installed Version: v%s, Repo Version: v%s' % (local_version, repo_version), 2)
				control.notification(message=control.lang(35523) % repo_version)
			return xbmc.log('[ plugin.video.venom ]  Addon update check complete', 2)
		except:
			log_utils.error()
			pass


class LibraryService:
	def run(self):
		xbmc.log('[ plugin.video.venom ]  Library Update Service Starting (Update check every 6hrs)...', 2)
		control.execute('RunPlugin(plugin://%s)' % control.get_plugin_url({'action': 'library_service'})) # library_service contains xbmc.Monitor().waitForAbort() while loop every 6hrs


class SyncTraktCollection:
	def run(self):
		xbmc.log('[ plugin.video.venom ]  Trakt Collection Sync Starting...', 2)
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=library_tvshowsToLibrarySilent&url=traktcollection')
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=library_moviesToLibrarySilent&url=traktcollection')
		xbmc.log('[ plugin.video.venom ]  Trakt Collection Sync Complete', 2)


class SyncTraktWatched:
	def run(self):
		xbmc.log('[ plugin.video.venom ]  Trakt Watched Sync Starting...', 2)
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=tools_cachesyncTVShows&timeout=720')
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=tools_cachesyncMovies&timeout=720')
		xbmc.log('[ plugin.video.venom ]  Trakt Watched Sync Complete', 2)


class SyncTraktProgress:
	def run(self):
		xbmc.log('[ plugin.video.venom ]  Trakt Progress Sync Service Starting (sync check every 15min)...', 2)
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=tools_syncTraktProgress') # trakt.sync_progress() contains xbmc.Monitor().waitForAbort() while loop every 15min

try:
	AddonVersion = control.addon('plugin.video.venom').getAddonInfo('version')
	RepoVersion = control.addon('repository.venom').getAddonInfo('version')
	log_utils.log('#####   CURRENT VENOM VERSIONS REPORT   #####', log_utils.LOGNOTICE)
	log_utils.log('########   VENOM PLUGIN VERSION: %s   ########' % str(AddonVersion), log_utils.LOGNOTICE)
	log_utils.log('#####   VENOM REPOSITORY VERSION: %s   #######' % str(RepoVersion), log_utils.LOGNOTICE)
except:
	log_utils.log('################# CURRENT Venom VERSIONS REPORT ################', log_utils.LOGNOTICE)
	log_utils.log('# ERROR GETTING Venom VERSION - Missing Repo of failed Install #', log_utils.LOGNOTICE)


def main():
	while not control.monitor.abortRequested():
		xbmc.log('[ plugin.video.venom ]  Service Started', 2)
		syncProgress = None
		schedTrakt = None
		libraryService = None
		CheckSettingsFile().run()
		SyncMyAccounts().run()
		ReuseLanguageInvokerCheck().run()
		if control.setting('library.service.update') == 'true':
			libraryService = True
			LibraryService().run()
		if control.setting('general.checkAddonUpdates') == 'true':
			AddonCheckUpdate().run()
		if trakt.getTraktCredentialsInfo() is True:
			SyncTraktWatched().run()
			if control.setting('bookmarks') == 'true' and control.setting('resume.source') == '1':
				syncProgress = True
				SyncTraktProgress().run()
			if control.setting('autoTraktOnStart') == 'true':
				SyncTraktCollection().run()
			if int(control.setting('schedTraktTime')) > 0:
				log_utils.log('#################### STARTING TRAKT SCHEDULING ################', log_utils.LOGNOTICE)
				log_utils.log('#################### SCHEDULED TIME FRAME '+ control.setting('schedTraktTime')  + ' HOURS ###############', log_utils.LOGNOTICE)
				timeout = 3600 * int(control.setting('schedTraktTime'))
				schedTrakt = threading.Timer(timeout, SyncTraktCollection().run) # this only runs once at the designated interval time to wait...not repeating
				schedTrakt.start()
		break
	SettingsMonitor().waitForAbort()
	xbmc.log('[ plugin.video.venom ]  Settings Monitor Service Stopping...', 2)
	if syncProgress:
		xbmc.log('[ plugin.video.venom ]  Trakt Progress Sync Service Stopping...', 2)
	if libraryService:
		xbmc.log('[ plugin.video.venom ]  Library Update Service Stopping...', 2)
	if schedTrakt:
		schedTrakt.cancel()
		# xbmc.log('[ plugin.video.venom ]  Trakt Collection Sync Stopping...', 2)

	xbmc.log('[ plugin.video.venom ]  Service Stopped', 2)


main()