# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

from datetime import datetime, timedelta
import json
import re
# Import _strptime to workaround python 2 bug with threads
import _strptime
import sys
import time

try:
	from urllib import quote_plus, unquote
	from urlparse import parse_qsl
except:
	from urllib.parse import quote_plus, parse_qsl, unquote

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import debrid
from resources.lib.modules import log_utils
from resources.lib.modules import metacache
from resources.lib.modules import providerscache
from resources.lib.modules import source_utils
from resources.lib.modules import trakt
from resources.lib.modules import workers

from resources.lib.debrid import alldebrid
from resources.lib.debrid import premiumize
from resources.lib.debrid import realdebrid
try:
	from sqlite3 import dbapi2 as database
except:
	from pysqlite2 import dbapi2 as database


class Sources:
	def __init__(self):
		self.time = datetime.now()
		self.single_expiry = timedelta(hours=6)
		self.season_expiry = timedelta(hours=48)
		self.show_expiry = timedelta(hours=48)
		self.getConstants()
		self.sources = []
		self.scraper_sources = []
		self.uncached_sources = []
		self.sourceFile = control.providercacheFile
		self.dev_mode = control.setting('dev.mode.enable') == 'true'
		self.dev_disable_single = control.setting('dev.disable.single') == 'true'
		# self.dev_disable_single_filter = control.setting('dev.disable.single.filter') == 'true'
		self.dev_disable_season_packs = control.setting('dev.disable.season.packs') == 'true'
		self.dev_disable_season_filter = control.setting('dev.disable.season.filter') == 'true'
		self.dev_disable_show_packs = control.setting('dev.disable.show.packs') == 'true'
		self.dev_disable_show_filter = control.setting('dev.disable.show.filter') == 'true'


	def timeIt(func):
		import time
		fnc_name = func.__name__
		def wrap(*args, **kwargs):
			started_at = time.time()
			result = func(*args, **kwargs)
			log_utils.log('%s.%s = %s' % (__name__ , fnc_name, time.time() - started_at), log_utils.LOGDEBUG)
			return result
		return wrap


	def play(self, title, year, imdb, tmdb, tvdb, season, episode, tvshowtitle, premiered, meta, select, rescrape=None):
		gdriveEnabled = control.addon('script.module.fenomscrapers').getSetting('gdrive.cloudflare_url') != ''
		if not self.debrid_resolvers and not gdriveEnabled:
			control.sleep(200)
			control.hide()
			control.notification(message=33034)
			return
		control.busy()
		try:
			control.homeWindow.clearProperty(self.metaProperty)
			control.homeWindow.setProperty(self.metaProperty, meta)
			control.homeWindow.clearProperty(self.seasonProperty)
			control.homeWindow.setProperty(self.seasonProperty, season)
			control.homeWindow.clearProperty(self.episodeProperty)
			control.homeWindow.setProperty(self.episodeProperty, episode)
			control.homeWindow.clearProperty(self.titleProperty)
			control.homeWindow.setProperty(self.titleProperty, title)
			control.homeWindow.clearProperty(self.imdbProperty)
			control.homeWindow.setProperty(self.imdbProperty, imdb)
			control.homeWindow.clearProperty(self.tmdbProperty)
			control.homeWindow.setProperty(self.tmdbProperty, tmdb)
			control.homeWindow.clearProperty(self.tvdbProperty)
			control.homeWindow.setProperty(self.tvdbProperty, tvdb)

			url = None
			self.mediatype = 'movie'

			external_caller = 'plugin.video.venom' not in control.infoLabel('Container.PluginName')
			isSTRM = control.infoLabel('ListItem.FileExtension') == 'strm'

			#check IMDB for year since TMDB and Trakt differ on a ratio of 1 in 20 and year is off by 1 and some meta titles mismatch
			if tvshowtitle is None:
				year, title = self.movie_chk_imdb(imdb, title, year)

			# fix incorect year passed from TMDBHelper. Need series premiered not variable season premiered.
			# TMDBHelper added "{showyear}" for player files 7/29/20. Check on removing this
			if external_caller and tvshowtitle is not None:
				year = self.tmdbhelper_fix(imdb, year)

			# get "total_season" to satisfy showPack scrapers. 1st=passed meta, 2nd=matacache check, 3rd=trakt.getSeasons() request
			# also get "is_airing" status of season for showPack scrapers. 1st=passed meta, 2nd=matacache check, 3rd=tvdb v1 xml request
			if tvshowtitle is not None:
				self.mediatype = 'episode'
				self.total_seasons, self.is_airing = self.get_season_info(imdb, tvdb, meta, season)

			if rescrape :
				self.clr_item_providers(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)

			if isSTRM or external_caller:
				items = self.getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
				# items, uncached_items = self.getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
			else:
				items = providerscache.get(self.getSources, 48, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
				# items, uncached_items = providerscache.get(self.getSources, 48, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)

			if not items:
				self.url = url
				return self.errorForSources()

			if select is None:
				if episode is not None and control.setting('enable.upnext') == 'true':
					select = '2'
				else:
					select = control.setting('hosts.mode')
					if control.condVisibility("Window.IsActive(script.extendedinfo-DialogVideoInfo-Netflix.xml)") or \
							control.condVisibility("Window.IsActive(script.extendedinfo-DialogVideoInfo-Estuary.xml)") or \
							control.condVisibility("Window.IsActive(script.extendedinfo-DialogVideoInfo-Aura.xml)") or \
							control.condVisibility("Window.IsActive(script.extendedinfo-DialogVideoInfo.xml)") and select == '1':
						select = '0'
			else:
				select = select

			title = tvshowtitle if tvshowtitle is not None else title
			if len(items) > 0:
				if select == '1' and 'plugin' in control.infoLabel('Container.PluginName'):
					control.homeWindow.clearProperty(self.itemProperty)
					control.homeWindow.setProperty(self.itemProperty, json.dumps(items))
					control.sleep(200)
					control.hide()
					return control.execute('Container.Update(%s?action=addItem&title=%s)' % (sys.argv[0], quote_plus(title)))
				elif select == '0' or select == '1':
					url = self.sourcesDialog(items)
				else:
					url = self.sourcesAutoPlay(items)

			if url == 'close://' or url is None:
				self.url = url
				return self.errorForSources()

			try: meta = json.loads(unquote(meta.replace('%22', '\\"')))
			except: pass

			from resources.lib.modules import player
			control.sleep(200) # added 5/14
			control.hide()
			player.Player().play_source(title, year, season, episode, imdb, tmdb, tvdb, url, meta, select)
		except:
			log_utils.error()
			pass


	# @timeIt
	def addItem(self, title):
		control.sleep(200)
		control.hide()

		def sourcesDirMeta(metadata):
			if not metadata: return metadata
			allowed = ['poster', 'season_poster', 'fanart', 'thumb', 'title', 'year', 'tvshowtitle', 'season', 'episode']
			return {k: v for k, v in metadata.iteritems() if k in allowed}

		control.playlist.clear()
		items = control.homeWindow.getProperty(self.itemProperty)
		items = json.loads(items)

		if not items:
			control.sleep(200) # added 5/14
			control.hide()
			sys.exit()

		meta = json.loads(unquote(control.homeWindow.getProperty(self.metaProperty).replace('%22', '\\"')))
		meta = sourcesDirMeta(meta)

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])

		downloads = True if control.setting('downloads') == 'true' and (control.setting(
			'movie.download.path') != '' or control.setting('tv.download.path') != '') else False

		systitle = sysname = quote_plus(title)

		poster = meta.get('poster') or control.addonPoster()
		if 'tvshowtitle' in meta and 'season' in meta and 'episode' in meta:
			poster = meta.get('season_poster') or poster or control.addonPoster()
			sysname += quote_plus(' S%02dE%02d' % (int(meta['season']), int(meta['episode'])))
		elif 'year' in meta:
			sysname += quote_plus(' (%s)' % meta['year'])

		fanart = meta.get('fanart')
		if control.setting('fanart') != 'true': fanart = '0'

		resquality_icons = control.setting('enable.resquality.icons') == 'true'
		artPath = control.artPath()

		sysimage = quote_plus(poster.encode('utf-8'))
		downloadMenu = control.lang(32403)

		multiline = control.setting('sourcelist.multiline') == 'true'

		for i in range(len(items)):
			try:
				if multiline: label = str(items[i]['multiline_label'])
				else: label = str(items[i]['label'])

				syssource = quote_plus(json.dumps([items[i]]))
				sysurl = '%s?action=playItem&title=%s&source=%s' % (sysaddon, systitle, syssource)

				cm = []
				type = 'pack' if 'package' in items[i] else 'single'
				isCached = True if re.match(r'^cached.*torrent', items[i]['source']) else False
				if downloads and (isCached or items[i]['direct'] == True or (items[i]['debridonly'] == True and 'magnet:' not in items[i]['url'])):
					try: new_sysname = quote_plus(items[i]['name'])
					except: new_sysname = sysname
					cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&source=%s&caller=sources&title=%s)' %
										(sysaddon, new_sysname, sysimage, syssource, sysname)))

				if type == 'pack' and isCached:
					cm.append(('[B]Browse Debrid Pack[/B]', 'RunPlugin(%s?action=showDebridPack&caller=%s&name=%s&url=%s&source=%s)' %
									(sysaddon, quote_plus(items[i]['debrid']), quote_plus(items[i]['name']), quote_plus(items[i]['url']), quote_plus(items[i]['hash']))))

				if not isCached and 'magnet:' in items[i]['url']:
					d = self.debrid_abv(items[i]['debrid'])
					if d in ('PM', 'RD', 'AD'):
						try: seeders = int(items[i]['seeders'])
						except: seeders = 0
						cm.append(('[B]Cache to %s Cloud (seeders=%s)[/B]' % (d, seeders), 'RunPlugin(%s?action=cacheTorrent&caller=%s&type=%s&url=%s)' %
											(sysaddon, d, type, quote_plus(items[i]['url']))))

				if resquality_icons:
					quality = items[i]['quality']
					thumb = '%s%s' % (quality, '.png')
					thumb = control.joinPath(artPath, thumb) if artPath else ''
				else:
					thumb = meta.get('thumb')
					thumb = thumb or poster or fanart or control.addonThumb()

				item = control.item(label=label)
				item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'fanart': fanart})
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				item.addContextMenuItems(cm)

				# item.setProperty('IsPlayable', 'true') # test
				item.setProperty('IsPlayable', 'false')

				item.setInfo(type='video', infoLabels=control.metadataClean(meta))
				control.addItem(handle=syshandle, url=sysurl, listitem=item, isFolder=False)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def playItem(self, title, source):
		try:
			meta = json.loads(unquote(control.homeWindow.getProperty(self.metaProperty).replace('%22', '\\"')))
			year = meta['year'] if 'year' in meta else None
			if 'tvshowtitle' in meta:
				year = meta['tvshowyear'] if 'tvshowyear' in meta else year #year was changed to year of premiered in episodes module so can't use that, need original shows year.

			season = meta['season'] if 'season' in meta else None
			episode = meta['episode'] if 'episode' in meta else None
			imdb = meta['imdb'] if 'imdb' in meta else None
			tmdb = meta['tmdb'] if 'tmdb' in meta else None
			tvdb = meta['tvdb'] if 'tvdb' in meta else None

			next = [] ; prev = [] ; total = []
			for i in range(1, 1000):
				try:
					u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
					if u in total: raise Exception()
					total.append(u)
					u = dict(parse_qsl(u.replace('?', '')))
					u = json.loads(u['source'])[0]
					next.append(u)
				except: break
			for i in range(-1000, 0)[::-1]:
				try:
					u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
					if u in total: raise Exception()
					total.append(u)
					u = dict(parse_qsl(u.replace('?', '')))
					u = json.loads(u['source'])[0]
					prev.append(u)
				except:
					break

			items = json.loads(source)
			items = [i for i in items + next + prev][:40]

			header = control.addonInfo('name') + ': Resolving...'
			progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
			progressDialog.create(header, '')

			block = None
			for i in range(len(items)):
				try:
					try:
						if progressDialog.iscanceled(): break
						progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']))
					except:
						progressDialog.update(int((100 / float(len(items))) * i), str(header) + '[CR]' + str(items[i]['label']))
						pass

					if items[i]['source'] == block: raise Exception()
					w = workers.Thread(self.sourcesResolve, items[i])
					w.start()

					if items[i].get('source') in self.hostcapDict: offset = 60 * 2
					elif 'torrent' in items[i].get('source'): offset = float('inf')
					else: offset = 0

					m = ''
					for x in range(3600):
						try:
							if control.monitor.abortRequested():
								return sys.exit()
							if progressDialog.iscanceled():
								return progressDialog.close()
						except: pass

						k = control.condVisibility('Window.IsActive(virtualkeyboard)')
						if k: m += '1' ; m = m[-1]
						if (not w.is_alive() or x > 30 + offset) and not k: break
						k = control.condVisibility('Window.IsActive(yesnoDialog)')
						if k: m += '1' ; m = m[-1]
						if (not w.is_alive() or x > 30 + offset) and not k: break
						time.sleep(0.5)

					for x in range(30):
						try:
							if control.monitor.abortRequested():
								return sys.exit()
							if progressDialog.iscanceled():
								return progressDialog.close()
						except: pass

						if m == '': break
						if not w.is_alive(): break
						time.sleep(0.5)

					if w.is_alive(): block = items[i]['source']
					if not self.url: raise Exception()
					try: progressDialog.close()
					except: pass

					control.sleep(200)
					control.execute('Dialog.Close(virtualkeyboard)')
					control.execute('Dialog.Close(yesnoDialog)')

					from resources.lib.modules import player
					control.sleep(200) # added 5/14
					control.hide()
					player.Player().play_source(title, year, season, episode, imdb, tmdb, tvdb, self.url, meta, select='1')
					return self.url
				except:
					log_utils.error()
					pass
			try: progressDialog.close()
			except: pass
			del progressDialog

			self.errorForSources()
		except:
			log_utils.error()
			pass


	# @timeIt
	def getSources(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, quality='HD', timeout=30):
		control.sleep(200)
		control.hide()
		progressDialog = control.progressDialog if control.setting(
			'progress.dialog') == '0' else control.progressDialogBG
		progressDialog.create(control.addonInfo('name'), '')
		self.prepareSources()
		sourceDict = self.sourceDict
		progressDialog.update(0, control.lang(32600))

		content = 'movie' if tvshowtitle is None else 'episode'
		if content == 'movie':
			sourceDict = [(i[0], i[1], getattr(i[1], 'movie', None)) for i in sourceDict]
		else:
			sourceDict = [(i[0], i[1], getattr(i[1], 'tvshow', None)) for i in sourceDict]
		sourceDict = [(i[0], i[1]) for i in sourceDict if i[2] is not None]

		if control.setting('cf.disable') == 'true':
			sourceDict = [(i[0], i[1]) for i in sourceDict if not any(x in i[0] for x in self.sourcecfDict)]

		sourceDict = [(i[0], i[1], i[1].priority) for i in sourceDict]
		sourceDict = sorted(sourceDict, key=lambda i: i[2]) # sorted by scraper priority num

		threads = []
		if content == 'movie':
			title = self.getTitle(title)
			aliases = self.getAliasTitles(imdb, content)
			for i in sourceDict:
				threads.append(workers.Thread(self.getMovieSource, title, aliases, year, imdb, i[0], i[1]))
		else:
			tvshowtitle = self.getTitle(tvshowtitle)
			aliases = self.getAliasTitles(imdb, content)
			for i in sourceDict:
				threads.append(workers.Thread(self.getEpisodeSource, title, year, imdb, tvdb, season,
											episode, tvshowtitle, aliases, premiered, i[0], i[1]))

		s = [i[0] + (i[1],) for i in zip(sourceDict, threads)]
		s = [(i[3].getName(), i[0], i[2]) for i in s]
		sourcelabelDict = dict([(i[0], i[1].upper()) for i in s])
		[i.start() for i in threads]

		pdpc = control.getColor(control.setting('progress.dialog.prem.color'))

		string1 = control.lang(32404) # msgid "[COLOR cyan]Time elapsed:[/COLOR]  %s seconds"
		string2 = control.lang(32405) # msgid "%s seconds"
		string3 = control.lang(32406) # msgid "[COLOR cyan]Remaining providers:[/COLOR] %s"
		string4 = control.lang(32601) # msgid "[COLOR cyan]Total:[/COLOR]"

		try: timeout = int(control.setting('scrapers.timeout.1'))
		except: pass
		start_time = time.time()

		quality = control.setting('hosts.quality')
		if quality == '': quality = '0'
		line1 = line2 = line3 = ""

		pre_emp = str(control.setting('preemptive.termination'))
		pre_emp_limit = int(control.setting('preemptive.limit'))
		pre_emp_res = str(control.setting('preemptive.res'))
		source_4k = source_1080 = source_720 = source_sd = total = 0
		total_format = '[COLOR %s][B]%s[/B][/COLOR]'
		pdiag_format = '4K:  %s  |  1080p:  %s  |  720p:  %s  |  SD:  %s'

		for i in list(range(0, 2 * timeout)):
			try:
				if control.monitor.abortRequested(): return sys.exit()
				try:
					if progressDialog.iscanceled(): break
				except: pass

				if pre_emp == 'true':
					if pre_emp_res == '0':
						if (source_4k) >= pre_emp_limit: break
					elif pre_emp_res == '1':
						if (source_1080) >= pre_emp_limit: break
					elif pre_emp_res == '2':
						if (source_720) >= pre_emp_limit: break
					elif pre_emp_res == '3':
						if (source_sd) >= pre_emp_limit: break
					else:
						if (source_sd) >= pre_emp_limit: break

				if len(self.scraper_sources) > 0:
					if quality == '0':
						source_4k = len([e for e in self.scraper_sources if e['quality'] == '4K'])
						source_1080 = len([e for e in self.scraper_sources if e['quality'] == '1080p'])
						source_720 = len([e for e in self.scraper_sources if e['quality'] in ['720p', 'HD']])
						source_sd = len([e for e in self.scraper_sources if e['quality'] in ['SD', 'SCR', 'CAM']])
					elif quality == '1':
						source_1080 = len([e for e in self.scraper_sources if e['quality'] == '1080p'])
						source_720 = len([e for e in self.scraper_sources if e['quality'] in ['720p', 'HD']])
						source_sd = len([e for e in self.scraper_sources if e['quality'] in ['SD', 'SCR', 'CAM']])
					elif quality == '2':
						source_720 = len([e for e in self.scraper_sources if e['quality'] in ['720p', 'HD']])
						source_sd = len([e for e in self.scraper_sources if e['quality'] in ['SD', 'SCR', 'CAM']])
					else:
						source_sd = len([e for e in self.scraper_sources if e['quality'] in ['SD', 'SCR', 'CAM']])
					total = source_4k + source_1080 + source_720 + source_sd
				source_4k_label = total_format % ('red', source_4k) if source_4k == 0 else total_format % (pdpc, source_4k)
				source_1080_label = total_format % ('red', source_1080) if source_1080 == 0 else total_format % (pdpc, source_1080)
				source_720_label = total_format % ('red', source_720) if source_720 == 0 else total_format % (pdpc, source_720)
				source_sd_label = total_format % ('red', source_sd) if source_sd == 0 else total_format % (pdpc, source_sd)
				source_total_label = total_format % ('red', total) if total == 0 else total_format % (pdpc, total)

				try:
					info = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() == True]
					line1 = pdiag_format % (source_4k_label, source_1080_label, source_720_label, source_sd_label)
					line2 = string4 % source_total_label + '     ' + string1 % round(time.time() - start_time, 1)

					if len(info) > 6: line3 = string3 % str(len(info))
					elif len(info) > 0: line3 = string3 % (', '.join(info))

					percent = int(100 * float(i) / (2 * timeout) + 0.5)
					if progressDialog != control.progressDialogBG:
						progressDialog.update(max(1, percent), line1, line2, line3)
					else: progressDialog.update(max(1, percent), line1 + string3 % str(len(info)))
					if len(info) == 0: break
				except:
					log_utils.error()
					break
				time.sleep(0.5)
			except:
				log_utils.error()
				pass
		try: progressDialog.close()
		except: pass
		del progressDialog
		del threads[:] # Make sure any remaining providers are stopped.

		self.sources.extend(self.scraper_sources)

		if len(self.sources) > 0:
			self.sourcesFilter()
		return self.sources
		# return self.sources, self.uncached_sources


	# @timeIt
	def prepareSources(self):
		try:
			control.makeFile(control.dataPath)
			dbcon = database.connect(self.sourceFile)
			dbcur = dbcon.cursor()
			dbcur.execute(
				"CREATE TABLE IF NOT EXISTS rel_url (""source TEXT, ""imdb_id TEXT, ""season TEXT, ""episode TEXT, ""rel_url TEXT, ""UNIQUE(source, imdb_id, season, episode)"");")
			dbcur.execute(
				"CREATE TABLE IF NOT EXISTS rel_src (""source TEXT, ""imdb_id TEXT, ""season TEXT, ""episode TEXT, ""hosts TEXT, ""added TEXT, ""UNIQUE(source, imdb_id, season, episode)"");")
			dbcur.connection.commit()
			dbcon.close()
		except:
			log_utils.error()
			pass


	# @timeIt
	def getMovieSource(self, title, aliases, year, imdb, source, call):
		try:
			dbcon = database.connect(self.sourceFile, timeout=60)
			dbcur = dbcon.cursor()
		except: pass
		''' Fix to stop items passed with a 0 IMDB id pulling old unrelated sources from the database. '''
		if imdb == '0':
			try:
				dbcur.execute(
					"DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, '', ''))
				dbcur.execute(
					"DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, '', ''))
				dbcur.connection.commit()
			except:
				log_utils.error()
				pass
		''' END '''

		try:
			sources = []
			dbcur.execute(
				"SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, '', ''))
			db_movie = dbcur.fetchone()
			if db_movie:
				timestamp = control.datetime_workaround(str(db_movie[5]), '%Y-%m-%d %H:%M:%S.%f', False)
				db_movie_valid = abs(self.time - timestamp) < self.single_expiry
				if db_movie_valid:
					sources = eval(db_movie[4].encode('utf-8'))
					return self.scraper_sources.extend(sources)
		except:
			log_utils.error()
			pass

		try:
			url = None
			dbcur.execute(
				"SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, '', ''))
			url = dbcur.fetchone()
			if url:
				url = eval(url[4].encode('utf-8'))
		except:
			log_utils.error()
			pass

		try:
			if not url:
				url = call.movie(imdb, title, aliases, year)
			if url:
				dbcur.execute("INSERT OR REPLACE INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
				dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
			sources = []
			sources = call.sources(url, self.hostprDict)
			if sources:
				sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
				for i in sources:
					i.update({'provider': source})
				self.scraper_sources.extend(sources)
				dbcur.execute("INSERT OR REPLACE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, '', '', repr(sources), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
				dbcur.connection.commit()
		except:
			log_utils.error()
			pass
		dbcon.close()


	# @timeIt
	def getEpisodeSource(self, title, year, imdb, tvdb, season, episode, tvshowtitle, aliases, premiered, source, call):
		try:
			dbcon = database.connect(self.sourceFile, timeout=60)
			self.dbcon = dbcon
			dbcur = dbcon.cursor()
		except:
			pass

# consider adding tvdb_id table column for better matching of cases where imdb_id not available. Wheeler Dealer BS shows..lol
		''' Fix to stop items passed with a 0 IMDB id pulling old unrelated sources from the database. '''
		if imdb == '0':
			try:
				dbcur.execute(
					"DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, season, episode))
				dbcur.execute(
					"DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, season, ''))
				dbcur.execute(
					"DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, '', ''))
				dbcur.execute(
					"DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, season, episode))
				dbcur.execute(
					"DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, '', ''))
				dbcur.connection.commit()
			except:
				log_utils.error()
				pass
		''' END '''

		try:
			# singleEpisodes db check
			db_singleEpisodes_valid = False
			if self.dev_mode and self.dev_disable_single:
				raise Exception()
			sources = []
			dbcur.execute(
				"SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, season, episode))
			db_singleEpisodes = dbcur.fetchone()
			if db_singleEpisodes:
				timestamp = control.datetime_workaround(str(db_singleEpisodes[5]), '%Y-%m-%d %H:%M:%S.%f', False)
				db_singleEpisodes_valid = abs(self.time - timestamp) < self.single_expiry
				if db_singleEpisodes_valid:
					sources = eval(db_singleEpisodes[4].encode('utf-8'))
					self.scraper_sources.extend(sources)
		except:
			log_utils.error()
			pass

		try:
			# seasonPacks db check
			db_seasonPacks_valid = False
			if self.is_airing:
				raise Exception()
			if self.dev_mode and self.dev_disable_season_packs:
				raise Exception()
			sources = []
			dbcur.execute(
				"SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, season, ''))
			db_seasonPacks = dbcur.fetchone()
			if db_seasonPacks:
				timestamp = control.datetime_workaround(str(db_seasonPacks[5]), '%Y-%m-%d %H:%M:%S.%f', False)
				db_seasonPacks_valid = abs(self.time - timestamp) < self.season_expiry
				if db_seasonPacks_valid:
					sources = eval(db_seasonPacks[4].encode('utf-8'))
					self.scraper_sources.extend(sources)
		except:
			log_utils.error()
			pass

		try:
			# # showPacks db check
			db_showPacks_valid = False
			if self.dev_mode and self.dev_disable_show_packs: raise Exception()
			sources = []
			dbcur.execute(
				"SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, '', ''))
			db_showPacks = dbcur.fetchone()
			if db_showPacks:
				timestamp = control.datetime_workaround(str(db_showPacks[5]), '%Y-%m-%d %H:%M:%S.%f', False)
				db_showPacks_valid = abs(self.time - timestamp) < self.show_expiry
				if db_showPacks_valid:
					sources = eval(db_showPacks[4].encode('utf-8'))
					sources = [i for i in sources if i.get('last_season') >= int(season)] # filter out range items that do not apply to current season
					self.scraper_sources.extend(sources)
					if db_singleEpisodes_valid and db_seasonPacks_valid:
						return self.scraper_sources
		except:
			log_utils.error()
			pass

		try:
			url = None
			dbcur.execute(
				"SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
			url = dbcur.fetchone()
			if url: url = eval(url[4].encode('utf-8'))
		except:
			log_utils.error()
			pass

		try:
			if not url:
				url = call.tvshow(imdb, tvdb, tvshowtitle, aliases, year)
			if url:
				dbcur.execute("INSERT OR REPLACE INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
				dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
			ep_url = None
			dbcur.execute(
				"SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, season, episode))
			ep_url = dbcur.fetchone()
			if ep_url: ep_url = eval(ep_url[4].encode('utf-8'))
		except:
			log_utils.error()
			pass

		try:
			if url:
				if not ep_url:
					ep_url = call.episode(url, imdb, tvdb, title, premiered, season, episode)
				if ep_url:
					dbcur.execute("INSERT OR REPLACE INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(ep_url)))
					dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
			# singleEpisodes scraper call
			if self.dev_mode and self.dev_disable_single:
				raise Exception()
			if db_singleEpisodes_valid:
				raise Exception()
			sources = []
			sources = call.sources(ep_url, self.hostprDict)
			if sources:
				sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
				for i in sources:
					i.update({'provider': source})
				self.scraper_sources.extend(sources)
				dbcur.execute("INSERT OR REPLACE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(sources), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
				dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
		# seasonPacks scraper call
			if self.dev_mode and self.dev_disable_season_packs:
				raise Exception()
			if self.is_airing:
				raise Exception()
			if source in self.packDict:
				if db_seasonPacks_valid:
					raise Exception()
				sources = []
				sources = call.sources_packs(ep_url, self.hostprDict, bypass_filter=self.dev_disable_season_filter)
				if sources:
					sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
					for i in sources:
						i.update({'provider': source})
					self.scraper_sources.extend(sources)
					dbcur.execute("INSERT OR REPLACE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, season,'', repr(sources), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
					dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
		# showPacks scraper call
			if self.dev_mode and self.dev_disable_show_packs:
				raise Exception()
			if source in self.packDict:
				if db_showPacks_valid:
					raise Exception()
				sources = []
				sources = call.sources_packs(ep_url, self.hostprDict, search_series=True, total_seasons=self.total_seasons, bypass_filter=self.dev_disable_show_filter)
				if sources:
					sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
					for i in sources:
						i.update({'provider': source})
					sources = [i for i in sources if i.get('last_season') >= int(season)] # filter out range items that do not apply to current season
					self.scraper_sources.extend(sources)
					dbcur.execute("INSERT OR REPLACE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, '', '', repr(sources), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
					dbcur.connection.commit()
		except:
			log_utils.error()
			pass
		dbcon.close()


	def alterSources(self, url, meta):
		try:
			if control.setting('hosts.mode') == '2' or (control.setting('enable.upnext') == 'true' and 'episode' in meta): url += '&select=1'
			else: url += '&select=2'
			# control.execute('RunPlugin(%s)' % url)
			control.execute('PlayMedia(%s)' % url)
		except:
			log_utils.error()
			pass


	# @timeIt
	def sourcesFilter(self):
		control.busy()
		quality = control.setting('hosts.quality')
		if quality == '': quality = '0'

		if control.setting('remove.duplicates') == 'true':
			self.sources = self.filter_dupes()

		if control.setting('source.enablesizelimit') == 'true':
			self.sources = [i for i in self.sources if i.get('size', 0) <= int(control.setting('source.sizelimit'))]

		if control.setting('remove.hevc') == 'true':
			self.sources = [i for i in self.sources if 'HEVC' not in i.get('info', '')] # scrapers write HEVC to info

		if control.setting('remove.CamSd.sources') == 'true':
			if any(i for i in self.sources if any(value in i['quality'] for value in ['4K', '1080p', '720p'])): #only remove CAM and SD if better quality does exist
				self.sources = [i for i in self.sources if not any(value in i['quality'] for value in ['CAM', 'SD'])]

		if control.setting('remove.3D.sources') == 'true':
			self.sources = [i for i in self.sources if '3D' not in i.get('info', '')]

		if control.setting('hosts.sort.provider') == 'true':
			self.sources = sorted(self.sources, key=lambda k: k['provider'])

		if self.mediatype == 'episode':
			self.sources = self.calc_pack_size()

		if control.setting('torrent.size.sort') == 'true':
			filter = []
			filter += [i for i in self.sources if 'magnet:' in i['url']]
			filter.sort(key=lambda k: k.get('size', 0), reverse=True)
			filter += [i for i in self.sources if 'magnet:' not in i['url']]
			self.sources = filter

		local = [i for i in self.sources if 'local' in i and i['local'] is True]
		self.sources = [i for i in self.sources if not i in local]

		filter = []
		from copy import deepcopy
		for d in self.debrid_resolvers:
			valid_hoster = set([i['source'] for i in self.sources])
			valid_hoster = [i for i in valid_hoster if d.valid_url(i)]

			if d.name == 'Premiumize.me' and control.setting('premiumize.enable') == 'true':
				try:
					pmTorrent_List = deepcopy(self.sources)
					pmTorrent_List = [i for i in pmTorrent_List if 'magnet:' in i['url']]
					if pmTorrent_List == []: raise Exception()
					pmCached = self.pm_cache_chk_list(pmTorrent_List, d)
					# self.uncached_sources += [dict(i.items() + [('debrid', d.name)]) for i in pmCached if re.match(r'^uncached.*torrent', i['source'])]
					if control.setting('pm.remove.uncached') == 'true':
						filter += [dict(i.items() + [('debrid', d.name)]) for i in pmCached if re.match(r'^cached.*torrent', i['source'])]
					else: filter += [dict(i.items() + [('debrid', d.name)]) for i in pmCached if 'magnet:' in i['url']]
				except:
					log_utils.error()
					pass
				filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster and 'magnet:' not in i['url']]

			if d.name == 'Real-Debrid' and control.setting('realdebrid.enable') == 'true':
				try:
					rdTorrent_List = deepcopy(self.sources)
					rdTorrent_List = [i for i in rdTorrent_List if 'magnet:' in i['url']]
					if rdTorrent_List == []: raise Exception()
					rdCached = self.rd_cache_chk_list(rdTorrent_List, d)
					# self.uncached_sources += [dict(i.items() + [('debrid', d.name)]) for i in rdCached if re.match(r'^uncached.*torrent', i['source'])]
					if control.setting('rd.remove.uncached') == 'true':
						filter += [dict(i.items() + [('debrid', d.name)]) for i in rdCached if re.match(r'^cached.*torrent', i['source'])]
					else: filter += [dict(i.items() + [('debrid', d.name)]) for i in rdCached if 'magnet:' in i['url']]
				except:
					log_utils.error()
					pass
				filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster and 'magnet:' not in i['url']]

			if d.name == 'AllDebrid' and control.setting('alldebrid.enable') == 'true':
				try:
					adTorrent_List = deepcopy(self.sources)
					adTorrent_List = [i for i in adTorrent_List if 'magnet:' in i['url']]
					if adTorrent_List == []: raise Exception()
					adCached = self.ad_cache_chk_list(adTorrent_List, d)
					# self.uncached_sources += [dict(i.items() + [('debrid', d.name)]) for i in adCached if re.match(r'^uncached.*torrent', i['source'])]
					if control.setting('ad.remove.uncached') == 'true':
						filter += [dict(i.items() + [('debrid', d.name)]) for i in adCached if re.match(r'^cached.*torrent', i['source'])]
					else: filter += [dict(i.items() + [('debrid', d.name)]) for i in adCached if 'magnet:' in i['url']]
				except:
					log_utils.error()
					pass
				filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster and 'magnet:' not in i['url']]

		filter += [i for i in self.sources if i['direct'] == True]
		self.sources = filter

		if control.setting('torrent.group.sort') == '1':
			filter = []
			filter += [i for i in self.sources if 'torrent' in i['source']]	 #torrents first
			if control.setting('torrent.size.sort') == 'true':
				filter.sort(key=lambda k: k.get('size', 0), reverse=True)
			filter += [i for i in self.sources if 'torrent' not in i['source'] and i['debridonly'] is True]  #prem. next
			filter += [i for i in self.sources if 'torrent' not in i['source'] and i['debridonly'] is False]  #free hosters fucking last
			self.sources = filter
		filter = []
		filter += local

		if quality in ['0']:
			filter += [i for i in self.sources if i['quality'] == '4K' and 'debrid' in i]
			filter += [i for i in self.sources if i['quality'] == '4K' and not 'debrid' in i]
		if quality in ['0', '1']:
			filter += [i for i in self.sources if i['quality'] == '1080p' and 'debrid' in i]
			filter += [i for i in self.sources if i['quality'] == '1080p' and not 'debrid' in i]
		if quality in ['0', '1', '2']:
			filter += [i for i in self.sources if i['quality'] == '720p' and 'debrid' in i]
			filter += [i for i in self.sources if i['quality'] == '720p' and not 'debrid' in i]
		filter += [i for i in self.sources if i['quality'] == 'SCR']
		filter += [i for i in self.sources if i['quality'] == 'SD']
		filter += [i for i in self.sources if i['quality'] == 'CAM']
		self.sources = filter

		if control.setting('remove.captcha') == 'true':
			self.sources = [i for i in self.sources if not (i['source'] in self.hostcapDict and not 'debrid' in i)]

		self.sources = [i for i in self.sources if not i['source'] in self.hostblockDict]
		self.sources = self.sources[:4000]

		extra_info = control.setting('sources.extrainfo')
		prem_identify = control.getColor(control.setting('prem.identify'))
		torr_identify = control.getColor(control.setting('torrent.identify'))
		sec_identify = control.getColor(control.setting('sec.identify'))
		sec_identify2 = control.setting('sec.identify2')

		for i in range(len(self.sources)):
			if extra_info == 'true': t = source_utils.getFileType(self.sources[i]['url'])
			else: t = ''
			u = self.sources[i]['url']
			q = self.sources[i]['quality']
			p = self.sources[i]['provider'].upper()
			s = self.sources[i]['source'].upper()
			s = s.rsplit('.', 1)[0]
			try: f = (' / '.join(['%s ' % info.strip() for info in self.sources[i]['info'].split('|')]))
			except: f = ''
			if 'debrid' in self.sources[i]: d = self.debrid_abv(self.sources[i]['debrid'])
			else: d = self.sources[i]['debrid'] = ''

			prem_color = 'nocolor'
			if d:
				if 'TORRENT' in s and torr_identify != 'nocolor':
					prem_color = torr_identify
				elif 'TORRENT' not in s and prem_identify != 'nocolor':
					prem_color = prem_identify

			if d != '': label = '[COLOR %s]%02d  |  [B]%s[/B]  |  %s  |  %s  |  [B]%s[/B][/COLOR]' % (prem_color, int(i + 1), q, d, p, s)
			else: label = '%02d  |  %s  |  %s  |  %s' % (int(i + 1), q, p, s)
			multiline_label = label
			l1 = label

			if t != '':
				if f != '' and f != '0 ' and f != ' ':
					multiline_label += '\n       [COLOR %s][I]%s / %s[/I][/COLOR]' % (sec_identify, f, t)
					label += '[COLOR %s] / %s / %s[/COLOR]' % (prem_color, f, t)
				else:
					multiline_label += '\n       [COLOR %s][I]%s[/I][/COLOR]' % (sec_identify, t)
					label += '[COLOR %s] / %s[/COLOR]' % (prem_color, t)
			else:
				if f != '' and f != '0 ' and f != ' ':
					multiline_label += '\n       [COLOR %s][I]%s[/I][/COLOR]' % (sec_identify, f)
					label += '[COLOR %s] / %s[/COLOR]' % (prem_color, f)

			if sec_identify2 == 'magnet title':
				if 'magnet:' in u:
					link_title = self.sources[i]['name']
					size = ''
					if f:
						size = f.split(' /', 1)[0]
						l1 += '[COLOR %s]  |  %s[/COLOR]' % (prem_color, size)
						l1l = len(l1)-58
						l2 = '\n       [COLOR %s][I]%s[/I][/COLOR]' % (sec_identify, link_title)
						l2l = len(l2)-27
						if l2l > l1l:
							adjust = l2l - l1l
							l1 = l1.ljust(l1l+76+adjust)
					multiline_label = l1 + l2

			self.sources[i]['multiline_label'] = multiline_label
			# self.uncached_sources[i]['multiline_label'] = multiline_label
			self.sources[i]['label'] = label
			# self.uncached_sources[i]['label'] = label

		# self.sources = [i for i in self.sources if 'label' or 'multiline_label' in i['label']]
		return self.sources
		# return self.sources, self.uncached_sources


	def sourcesResolve(self, item):
		url = item['url']
		self.url = None
		debrid_provider = item['debrid']
		if 'magnet:' in url:
			if not 'uncached' in item['source']:
				try:
					meta = control.homeWindow.getProperty(self.metaProperty)
					if meta:
						meta = json.loads(unquote(meta.replace('%22', '\\"')))
						season = meta.get('season')
						episode = meta.get('episode')
						title = meta.get('title')
					else:
						season = control.homeWindow.getProperty(self.seasonProperty)
						episode = control.homeWindow.getProperty(self.episodeProperty)
						title = control.homeWindow.getProperty(self.titleProperty)
					if debrid_provider == 'Real-Debrid':
						from resources.lib.debrid.realdebrid import RealDebrid as debrid_function
					elif debrid_provider == 'Premiumize.me':
						from resources.lib.debrid.premiumize import Premiumize as debrid_function
					elif debrid_provider == 'AllDebrid':
						from resources.lib.debrid.alldebrid import AllDebrid as debrid_function
					else: return
					url = debrid_function().resolve_magnet(url, item['hash'], season, episode, title)
					self.url = url
					return url
				except:
					log_utils.error()
					return
		else:
			direct = item['direct']
			call = [i[1] for i in self.sourceDict if i[0] == item['provider']][0]
			if direct:
				self.url = call.resolve(url)
				return url
			else:
				try:
					if debrid_provider == 'Real-Debrid':
						from resources.lib.debrid.realdebrid import RealDebrid as debrid_function
					elif debrid_provider == 'Premiumize.me':
						from resources.lib.debrid.premiumize import Premiumize as debrid_function
					elif debrid_provider == 'AllDebrid':
						from resources.lib.debrid.alldebrid import AllDebrid as debrid_function
					u = url = call.resolve(url)
					url = debrid_function().unrestrict_link(url)
					self.url = url
					return url
				except:
					log_utils.error()
					return


	# @timeIt
	def sourcesDialog(self, items):
		try:
			multiline = control.setting('sourcelist.multiline') == 'true'
			if multiline: labels = [i['multiline_label'] for i in items]
			else: labels = [i['label'] for i in items]

			select = control.selectDialog(labels)
			if select == -1: return 'close://'

			tot_items = len(items)
			next = [y for x, y in enumerate(items) if x >= select]
			prev = [y for x, y in enumerate(items) if x < select][::-1]

			items = [items[select]]
			# items = [i for i in items + next + prev][:40]
			items = [i for i in items + next + prev][:tot_items]

			header = control.addonInfo('name') + ': Resolving...'
			progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
			progressDialog.create(header, '')

			block = None
			for i in range(len(items)):
				try:
					if items[i]['source'] == block:
						raise Exception()
					w = workers.Thread(self.sourcesResolve, items[i])
					w.start()
					try:
						if progressDialog.iscanceled(): break
						progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']))
					except:
						progressDialog.update(int((100 / float(len(items))) * i), str(header) + '[CR]' + str(items[i]['label']))
						pass

					if items[i].get('source') in self.hostcapDict: offset = 60 * 2
					elif 'torrent' in items[i].get('source'): offset = float('inf')
					else: offset = 0

					m = ''
					for x in range(3600):
						try:
							if control.monitor.abortRequested():
								control.notification(message=32400)
								return sys.exit()
							if progressDialog.iscanceled():
								control.notification(message=32400)
								return progressDialog.close()
						except: pass

						k = control.condVisibility('Window.IsActive(virtualkeyboard)')
						if k: m += '1' ; m = m[-1]
						if (not w.is_alive() or x > 30 + offset) and not k: break
						k = control.condVisibility('Window.IsActive(yesnoDialog)')
						if k: m += '1' ; m = m[-1]
						if (not w.is_alive() or x > 30 + offset) and not k: break
						time.sleep(0.5)

					for x in range(30):
						try:
							if control.monitor.abortRequested():
								control.notification(message=32400)
								return sys.exit()
							if progressDialog.iscanceled():
								control.notification(message=32400)
								return progressDialog.close()
						except:
							log_utils.error()
							pass

						if m == '': break
						if not w.is_alive(): break
						time.sleep(0.5)

					if w.is_alive(): block = items[i]['source']
					if not self.url: raise Exception()
					self.selectedSource = items[i]['label']

					try: progressDialog.close()
					except: pass

					control.execute('Dialog.Close(virtualkeyboard)')
					control.execute('Dialog.Close(yesnoDialog)')
					return self.url
				except:
					log_utils.error()
					pass

			try: progressDialog.close()
			except: pass
			del progressDialog

		except Exception as e:
			try: progressDialog.close()
			except: pass
			log_utils.log('Error %s' % str(e), __name__, log_utils.LOGNOTICE)


	# @timeIt
	def sourcesAutoPlay(self, items):
		filter = [i for i in items if i['source'] in self.hostcapDict and i['debrid'] == '']
		items = [i for i in items if not i in filter]
		filter = [i for i in items if i['source'] in self.hostblockDict]# and i['debrid'] == '']
		items = [i for i in items if not i in filter]

		if control.setting('autoplay.sd') == 'true':
			items = [i for i in items if not i['quality'] in ['4K', '1080p', '720p', 'HD']]

		u = None
		header = control.addonInfo('name') + ': Resolving...'

		try:
			control.sleep(1000)
			if control.setting('progress.dialog') == '0':
				progressDialog = control.progressDialog
			else:
				progressDialog = control.progressDialogBG
			progressDialog.create(header, '')
		except: pass

		for i in range(len(items)):
			try:
				if progressDialog.iscanceled(): break
				progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']))
			except:
				progressDialog.update(int((100 / float(len(items))) * i), str(header) + '[CR]' + str(items[i]['label']))
				pass
			try:
				if control.monitor.abortRequested():
					return sys.exit()
				url = self.sourcesResolve(items[i])
				if not u: u = url
				if url: break
			except: pass
		try: progressDialog.close()
		except: pass
		del progressDialog
		return u


	def debridPackDialog(self, provider, name, magnet_url, info_hash):
		try:
			if provider == 'Real-Debrid':
				from resources.lib.debrid.realdebrid import RealDebrid as debrid_function
			elif provider == 'Premiumize.me':
				from resources.lib.debrid.premiumize import Premiumize as debrid_function
			elif provider == 'AllDebrid':
				from resources.lib.debrid.alldebrid import AllDebrid as debrid_function
			else: return
			debrid_files = None
			control.busy()
			try: debrid_files = debrid_function().display_magnet_pack(magnet_url, info_hash)
			except: pass
			if not debrid_files:
				control.hide()
				return control.notification(message=32399)
			debrid_files = sorted(debrid_files, key=lambda k: k['filename'].lower())
			display_list = ['%02d | [B]%.2f GB[/B] | [I]%s[/I]' % \
							(count, i['size'], i['filename'].upper()) for count, i in enumerate(debrid_files, 1)]
			control.hide()
			chosen = control.selectDialog(display_list, heading=name)
			if chosen < 0: return None
			control.busy()
			chosen_result = debrid_files[chosen]
			if provider	 == 'Real-Debrid':
				self.url = debrid_function().unrestrict_link(chosen_result['link'])
			elif provider == 'Premiumize.me':
				self.url = debrid_function().add_headers_to_url(chosen_result['link'])
			elif provider == 'AllDebrid':
				self.url = debrid_function().unrestrict_link(chosen_result['link'])
			from resources.lib.modules import player
			from resources.lib.modules.source_utils import seas_ep_filter
			meta = json.loads(unquote(control.homeWindow.getProperty(self.metaProperty).replace('%22', '\\"')))
			title = meta['tvshowtitle']
			year = meta['year'] if 'year' in meta else None

			if 'tvshowtitle' in meta:
				year = meta['tvshowyear'] if 'tvshowyear' in meta else year
			season = meta['season'] if 'season' in meta else None
			episode = meta['episode'] if 'episode' in meta else None
			imdb = meta['imdb'] if 'imdb' in meta else None
			tmdb = meta['tmdb'] if 'tmdb' in meta else None
			tvdb = meta['tvdb'] if 'tvdb' in meta else None
			release_title = chosen_result['filename']
			control.hide()
			if seas_ep_filter(season, episode, release_title):
				return player.Player().play_source(title, year, season, episode, imdb, tmdb, tvdb, self.url, meta, select='1')
			else:
				return player.Player().play(self.url)
		except Exception as e:
			control.hide()
			log_utils.log('Error debridPackDialog %s' % str(e), __name__, log_utils.LOGNOTICE)


	def errorForSources(self):
		try:
			control.sleep(200) # added 5/14
			control.hide()
			if self.url == 'close://':
				control.notification(message=32400)
			else:
				control.notification(message=32401)
			control.cancelPlayback()
		except:
			log_utils.error()


	def getAliasTitles(self, imdb, content):
		lang = 'en'
		try:
			t = trakt.getMovieAliases(imdb) if content == 'movie' else trakt.getTVShowAliases(imdb)
			if not t: return []
			t = [i for i in t if i.get('country', '').lower() in [lang, '', 'us']]
			# log_utils.log('t = %s' % t, __name__, log_utils.LOGDEBUG)
			return json.dumps(t)
		except:
			log_utils.error()
			return []


	def getTitle(self, title):
		title = cleantitle.normalize(title)
		return title


	# @timeIt
	def getConstants(self):
		self.itemProperty = 'plugin.video.venom.container.items'
		self.metaProperty = 'plugin.video.venom.container.meta'
		self.seasonProperty = 'plugin.video.venom.container.season'
		self.episodeProperty = 'plugin.video.venom.container.episode'
		self.titleProperty = 'plugin.video.venom.container.title'
		self.imdbProperty = 'plugin.video.venom.container.imdb'
		self.tmdbProperty = 'plugin.video.venom.container.tmdb'
		self.tvdbProperty = 'plugin.video.venom.container.tvdb'

		from fenomscrapers import sources
		self.sourceDict = sources()

		from fenomscrapers import pack_sources
		self.packDict = pack_sources()

		self.hostprDict  = []
		try:
			self.debrid_resolvers = debrid.debrid_resolvers()
			for d in self.debrid_resolvers:
				hosts = d.get_hosts()[d.name]
				self.hostprDict += hosts
			self.hostprDict  = list(set(self.hostprDict))
		except:
			self.hostprDict = ['1fichier.com', '2shared.com', '4shared.com', 'alfafile.net', 'alterupload.com', 'bayfiles.com', 'clicknupload.me',
										'clicknupload.co', 'clicknupload.com', 'clicknupload.link', 'clicknupload.org', 'clipwatching.com''cosmobox.org',
										'dailymotion.com', 'dailyuploads.net', 'ddl.to', 'ddownload.com', 'dl4free.com', 'dropapk.to', 'earn4files.com',
										'filefactory.com', 'filefreak.com', 'hexupload.net', 'mega.nz', 'multiup.org', 'nitroflare.com', 'oboom.com',
										'rapidgator.net', 'rg.to', 'rockfile.co', 'rockfile.eu', 'speed-down.org', 'turbobit.net', 'uploaded.net', 'uploaded.to',
										'uploadgig.com', 'ul.to', 'uploadrocket.net', 'usersdrive.com']

		self.hostcapDict = ['flashx.tv', 'flashx.to', 'flashx.sx', 'flashx.bz', 'flashx.cc', 'hugefiles.cc', 'hugefiles.net', 'jetload.net', 'jetload.tv',
									'jetload.to''kingfiles.net', 'streamin.to', 'thevideo.me', 'torba.se', 'uptobox.com', 'uptostream.com', 'vidup.io',
									'vidup.me', 'vidup.tv', 'vshare.eu', 'vshare.io', 'vev.io']

		self.hostblockDict = ['divxme.com', 'divxstage.eu', 'estream.to', 'facebook.com', 'oload.download', 'oload.fun', 'oload.icu', 'oload.info',
									'oload.life', 'oload.space', 'oload.stream', 'oload.tv', 'oload.win', 'openload.co', 'openload.io', 'openload.pw', 'rapidvideo.com',
									'rapidvideo.is', 'rapidvid.to', 'streamango.com', 'streamcherry.com', 'twitch.tv', 'youtube.com', 'zippyshare.com']

		self.sourcecfDict = ['ganool', 'maxrls', 'mkvhub', 'rapidmoviez', 'rlsbb', 'scenerls', 'tvdownload', 'btdb',
									'extratorrent', 'limetorrents', 'moviemagnet', 'torrentgalaxy', 'torrentz']


	# @timeIt
	def filter_dupes(self):
		filter = []
		for i in self.sources:
			a = i['url'].lower()
			for sublist in filter:
				try:
					b = sublist['url'].lower()
					if 'magnet:' in a:
						info_hash = i['hash'].lower()
						if info_hash:
							if info_hash in b:
								filter.remove(sublist)
								if control.setting('remove.duplicates.logging') != 'true':
									log_utils.log('Removing %s - %s (DUPLICATE TORRENT) ALREADY IN :: %s' % (sublist['provider'], b, i['provider']), log_utils.LOGDEBUG)
								break
					elif a == b:
						filter.remove(sublist)
						if control.setting('remove.duplicates.logging') != 'true':
							log_utils.log('Removing %s - %s (DUPLICATE LINK) ALREADY IN :: %s' % (sublist['source'], i['url'], i['provider']), log_utils.LOGDEBUG)
						break
				except:
					log_utils.error()
					pass
			filter.append(i)
		control.notification(message='Removed %s duplicate sources from list' % (len(self.sources) - len(filter)))
		log_utils.log('Removed %s duplicate sources from list' % (len(self.sources) - len(filter)), log_utils.LOGDEBUG)
		self.sources = filter
		return self.sources

	# @timeIt
	def calc_pack_size(self):
		seasoncount = None
		counts = None
		try:
			meta = control.homeWindow.getProperty(self.metaProperty)
			if meta:
				meta = json.loads(unquote(meta.replace('%22', '\\"')))
				seasoncount = meta.get('seasoncount', None)
				counts = meta.get('counts', None)
		except:
			log_utils.error()
			pass

		# check metacache, 2nd fallback
		if not seasoncount or not counts:
			try:
				imdb_user = control.setting('imdb.user').replace('ur', '')
				tvdb_key = control.setting('tvdb.api.key')

				user = str(imdb_user) + str(tvdb_key)
				meta_lang = control.apiLanguage()['tvdb']
				if meta:
					imdb = meta.get('imdb')
					tvdb = meta.get('tvdb')
				else:
					imdb = control.homeWindow.getProperty(self.imdbProperty)

					tmdb = control.homeWindow.getProperty(self.tmdbProperty)

					tvdb = control.homeWindow.getProperty(self.tvdbProperty)
				# ids = [{'imdb': imdb, 'tvdb': tvdb}]
				ids = [{'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb}]

				meta2 = metacache.fetch(ids, meta_lang, user)[0]
				if not seasoncount: seasoncount = meta2.get('seasoncount', None)
				if not counts: counts = meta2.get('counts', None)
			except:
				log_utils.error()
				pass

		# make request, 3rd fallback
		if not seasoncount or not counts:
			try:
				if meta: season = meta.get('season')
				else: season = control.homeWindow.getProperty(self.seasonProperty)
				from resources.lib.indexers import tvdb_v1
				counts = tvdb_v1.get_counts(tvdb)
				seasoncount = counts[season]
			except:
				log_utils.error()
				return self.sources

		for i in self.sources:
			try:
				if 'package' in i:
					dsize = i.get('size')
					if not dsize: continue
					if i['package'] == 'season':
						divider = int(seasoncount)
						if not divider: continue
					else:
						if not counts: continue
						season_count = 1
						divider = 0
						while season_count <= int(i['last_season']):
							divider += int(counts[str(season_count)])
							season_count += 1
					float_size = float(dsize) / divider
					if round(float_size, 2) == 0: continue
					str_size = '%.2f GB' % float_size
					info = i['info']
					try: info = [i['info'].split(' | ', 1)[1]]
					except: info = []
					info.insert(0, str_size)
					info = ' | '.join(info)
					i.update({'size': float_size, 'info': info})
				else:
					continue
			except:
				log_utils.error()
				continue
		return self.sources


	# @timeIt
	def ad_cache_chk_list(self, torrent_List, d):
		if len(torrent_List) == 0: return
		try:
			hashList = [i['hash'] for i in torrent_List]
			cached = alldebrid.AllDebrid().check_cache(hashList)
			if not cached: return None
			cached = cached['magnets']
			count = 0
			for i in torrent_List:
				if 'error' in cached[count]:
					count += 1
					continue
				if cached[count]['instant'] is False:
					if 'package' in i: i.update({'source': 'uncached (pack) torrent'})
					else: i.update({'source': 'uncached torrent'})
				else:
					if 'package' in i: i.update({'source': 'cached (pack) torrent'})
					else: i.update({'source': 'cached torrent'})
				count += 1
			return torrent_List
		except:
			log_utils.error()
			pass


	# @timeIt
	def pm_cache_chk_list(self, torrent_List, d):
		if len(torrent_List) == 0: return
		try:
			hashList = [i['hash'] for i in torrent_List]
			cached = premiumize.Premiumize().check_cache_list(hashList)
			count = 0
			for i in torrent_List:
				if cached[count] is False:
					if 'package' in i: i.update({'source': 'uncached (pack) torrent'})
					else: i.update({'source': 'uncached torrent'})
				else:
					if 'package' in i: i.update({'source': 'cached (pack) torrent'})
					else: i.update({'source': 'cached torrent'})
				count += 1
			return torrent_List
		except:
			log_utils.error()
			pass


	# @timeIt
	def rd_cache_chk_list(self, torrent_List, d):
		if len(torrent_List) == 0: return
		try:
			hashList = [i['hash'] for i in torrent_List]
			cached = realdebrid.RealDebrid().check_cache_list(hashList)
			for i in torrent_List:
				if 'rd' not in cached.get(i['hash'].lower(), {}):
					if 'package' in i: i.update({'source': 'uncached (pack) torrent'})
					else: i.update({'source': 'uncached torrent'})
					continue
				elif len(cached[i['hash'].lower()]['rd']) >= 1:
					if 'package' in i: i.update({'source': 'cached (pack) torrent'})
					else: i.update({'source': 'cached torrent'})
				else:
					if 'package' in i: i.update({'source': 'uncached (pack) torrent'})
					else: i.update({'source': 'uncached torrent'})
			return torrent_List
		except:
			log_utils.error()
			pass


	def clr_item_providers(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered):
		providerscache.remove(self.getSources, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered) # function cache removal of item
		# if not season:
			# season = episode = ''
		try:
			dbcon = database.connect(self.sourceFile)
			dbcur = dbcon.cursor()
			dbcur.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='rel_url'")
			if dbcur.fetchone()[0] == 1: # table exists so both all will
				dbcur.execute(
					"DELETE FROM rel_url WHERE imdb_id = '%s'" % imdb)
				dbcur.execute(
					"DELETE FROM rel_src WHERE imdb_id = '%s'" % imdb)
				dbcur.connection.commit()
				dbcon.close()
		except:
			log_utils.error()
			pass


	# @timeIt
	def movie_chk_imdb(self, imdb, title, year):
		try:
			if not imdb or imdb == '0': return year, title
			result = client.request('https://v2.sg.media-imdb.com/suggestion/t/{}.json'.format(imdb))
			result = json.loads(result)['d'][0]
			year_ck = str(result['y'])
			title_ck = result['l'].encode('utf-8')
			if not year_ck or not title_ck: return year, title
			if year != year_ck: year = year_ck
			if title != title_ck: title = title_ck
			return year, title
		except:
			log_utils.error()
			return year, title


	def tmdbhelper_fix(self, imdb, year):
		try:
			if not imdb or imdb == '0':
				raise Exception()
			result = client.request('https://v2.sg.media-imdb.com/suggestion/t/{}.json'.format(imdb))
			result = json.loads(result)['d'][0]
			year_ck = result['y']
			if not year_ck:
				raise Exception()
			if year != year_ck:
				year = year_ck
			return year
		except:
			log_utils.error()
			return year


	def get_season_info(self, imdb, tvdb, meta, season):
		total_seasons = None
		is_airing = None
		try:
			meta = json.loads(unquote(meta.replace('%22', '\\"')))
			total_seasons = meta.get('total_seasons', None)
			is_airing = meta.get('is_airing', None)
		except:
			pass

		# check metacache, 2nd fallback
		if not total_seasons or not is_airing:
			try:
				imdb_user = control.setting('imdb.user').replace('ur', '')
				tvdb_key = control.setting('tvdb.api.key')
				user = str(imdb_user) + str(tvdb_key)
				meta_lang = control.apiLanguage()['tvdb']
				ids = [{'imdb': imdb, 'tvdb': tvdb}]
				meta2 = metacache.fetch(ids, meta_lang, user)[0]
				if not total_seasons:
					total_seasons = meta2.get('total_seasons', None)
				if not is_airing:
					is_airing = meta2.get('is_airing', None)
			except:
				log_utils.error()
				pass

		# make request, 3rd fallback
		if not total_seasons:
			try:
				total_seasons = trakt.getSeasons(imdb, full=False)
				if total_seasons:
					total_seasons = [i['number'] for i in total_seasons]
					season_special = True if 0 in total_seasons else False
					total_seasons = len(total_seasons)
					if season_special:
						total_seasons = total_seasons - 1
			except:
				log_utils.error()
				pass

		if not is_airing:
			try:
				from resources.lib.indexers import tvdb_v1
				is_airing = tvdb_v1.get_is_airing(tvdb, season)
			except:
				log_utils.error()
				pass
		return total_seasons, is_airing


	def debrid_abv(self, debrid):
		try:
			d_dict = {'AllDebrid': 'AD', 'Premiumize.me': 'PM', 'Real-Debrid': 'RD'}
			d = d_dict[debrid]
		except:
			log_utils.error()
			d = ''
			pass
		return d