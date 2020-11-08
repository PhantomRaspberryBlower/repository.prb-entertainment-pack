# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

import datetime
from json import loads
import re
# Import _strptime to workaround python 2 bug with threads
import _strptime
import sys
try:
	from sqlite3 import dbapi2 as database
except:
	from pysqlite2 import dbapi2 as database

try:
	from urlparse import parse_qsl
	from urllib import quote_plus
except:
	from urllib.parse import parse_qsl, quote_plus

from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import log_utils

folder_setup = False
service_update = control.setting('library.service.update') == 'true'
service_notification = control.setting('library.service.notification') == 'true'
general_notification = control.setting('library.general.notification') == 'true'
tmdb_session_id = control.setting('tmdb.session_id')


class lib_tools:

	@staticmethod
	def create_folder(folder):
		try:
			folder = control.legalFilename(folder)
			control.makeFile(folder)
			try:
				if 'ftp://' not in folder:
					raise Exception()
				from ftplib import FTP
				ftparg = re.compile('ftp://(.+?):(.+?)@(.+?):?(\d+)?/(.+/?)').findall(folder)
				ftp = FTP(ftparg[0][2], ftparg[0][0], ftparg[0][1])
				try: ftp.cwd(ftparg[0][4])
				except: ftp.mkd(ftparg[0][4])
				ftp.quit()
			except:
				log_utils.error()
				pass
		except:
			log_utils.error()
			pass


	@staticmethod
	def write_file(path, content):
		try:
			path = control.legalFilename(path)
			if not isinstance(content, basestring):
				content = str(content)
			file = control.openFile(path, 'w')
			file.write(str(content))
			file.close()
		except:
			log_utils.error()
			pass


	@staticmethod
	def nfo_url(media_string, ids):
		tvdb_url = 'https://thetvdb.com/?tab=series&id=%s'
		imdb_url = 'https://www.imdb.com/title/%s/'
		tmdb_url = 'https://www.themoviedb.org/%s/%s'
		if 'tvdb' in ids:
			return tvdb_url % (str(ids['tvdb']))
		elif 'imdb' in ids:
			return imdb_url % (str(ids['imdb']))
		elif 'tmdb' in ids:
			return tmdb_url % (media_string, str(ids['tmdb']))
		else:
			return ''


	@staticmethod
	def check_sources(title, year, imdb, tvdb=None, season=None, episode=None, tvshowtitle=None, premiered=None):
		try:
			from resources.lib.modules import sources
			src = sources.Sources().getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
			return src and len(src) > 5
		except:
			return False


	@staticmethod
	def legal_filename(filename):
		try:
			filename = filename.strip()
			filename = re.sub(r'(?!%s)[^\w\-_\.]', '.', filename)
			filename = re.sub('\.+', '.', filename)
			filename = re.sub(re.compile('(CON|PRN|AUX|NUL|COM\d|LPT\d)\.', re.I), '\\1_', filename)
			control.legalFilename(filename)
			# filename = control.legalFilename(filename)
			return filename
		except:
			log_utils.error()
			return filename


	@staticmethod
	def make_path(base_path, title, year = '', season = ''):
		show_folder = re.sub(r'[^\w\-_\. ]', '_', title)
		show_folder = '%s (%s)' % (show_folder, year) if year else show_folder
		path = control.joinPath(base_path, show_folder)
		if season:
			path = control.joinPath(path, 'Season %s' % season)
		return path


	@staticmethod
	def clean():
		control.execute('CleanLibrary(video)')


	@staticmethod
	def total_setup():
		try:
			# control.execute('CleanLibrary(video)')
			libmovies().auto_movie_setup()
			libtvshows().auto_tv_setup()
			control.notification(message=32110)
		except:
			log_utils.error()
			control.notification(message=32111)


	def ckKodiSources(self, paths=None):
		contains = False
		try:
			if paths is None:
				paths = []
				movie_LibraryFolder = control.joinPath(control.transPath(control.setting('library.movie')), '')
				special_movie_LibraryFolder = control.joinPath(control.setting('library.movie'), '')

				paths.append(movie_LibraryFolder)
				paths.append(special_movie_LibraryFolder)

				tvShows_LibraryFolder = control.joinPath(control.transPath(control.setting('library.tv')),'')
				speical_tvShows_LibraryFolder = control.joinPath(control.setting('library.tv'),'')

				paths.append(tvShows_LibraryFolder)
				paths.append(speical_tvShows_LibraryFolder)

			paths = [i.rstrip('/').rstrip('\\') for i in paths]

			result = control.jsonrpc('{"jsonrpc": "2.0", "method": "Files.GetSources", "params": {"media" : "video"}, "id": 1}')
			result = unicode(result, 'utf-8', errors='ignore')
			result = loads(result)['result']['sources']

			for i in result:
				if i['file'].rstrip('/').rstrip('\\') in paths:
					contains = True
					break
		except:
			log_utils.error()

		if not contains:
			try:
				global folder_setup
				global service_update
				if control.setting('library.service.update') == 'false' or service_update is False:
					return contains
				if folder_setup:
					contains = True
					return contains
				msg = 'Your Library Folders do not exist in Kodi Sources.  Would you like to run full setup of Library Folders to Kodi Sources now?'
				if control.yesnoDialog(msg, '', ''):
					lib_tools.total_setup()
					folder_setup = True
					contains = True
				else:
					msg = 'Would you like to turn off Library Auto Update Service?'
					if control.yesnoDialog(msg, '', ''):
						service_update = False
						control.setSetting('library.service.update', 'false')
						contains = False
						control.notification(message=32112)
						# control.refresh()
			except:
				log_utils.error()
				pass
		return contains


	def service(self):
		self.property = '%s_service_property' % control.addonInfo('name').lower()
		try:
			lib_tools.create_folder(control.joinPath(control.transPath(control.setting('library.movie')), ''))
			lib_tools.create_folder(control.joinPath(control.transPath(control.setting('library.tv')), ''))
		except:
			pass
		try:
			control.makeFile(control.dataPath)
			dbcon = database.connect(control.libcacheFile)
			dbcur = dbcon.cursor()
			dbcur.execute("CREATE TABLE IF NOT EXISTS service (""setting TEXT, ""value TEXT, ""UNIQUE(setting)"");")
			dbcur.connection.commit()
			dbcur.execute("SELECT * FROM service WHERE setting = 'last_run'")
			fetch = dbcur.fetchone()
			if fetch is None:
				last_service = "1970-01-01 23:59:00.000000"
				dbcur.execute("INSERT INTO service Values (?, ?)", ('last_run', last_service ))
				dbcur.connection.commit()
			else:
				last_service = str(fetch[1])
			dbcon.close()
		except:
			log_utils.error()
			try: return dbcon.close()
			except: return

		try:
			control.homeWindow.setProperty(self.property, last_service)
		except:
			log_utils.error()
			return

		while not control.monitor.abortRequested():
			try:
				last_service = control.homeWindow.getProperty(self.property)
				t1 = datetime.timedelta(hours=6)
				t2 = control.datetime_workaround(str(last_service), '%Y-%m-%d %H:%M:%S.%f', False)
				t3 = datetime.datetime.now()
				check = abs(t3 - t2) >= t1
				if not check: continue
				if (control.player.isPlaying() or control.condVisibility('Library.IsScanningVideo')): continue

				last_service = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
				control.homeWindow.setProperty(self.property, last_service)
				try:
					dbcon = database.connect(control.libcacheFile)
					dbcur = dbcon.cursor()
					dbcur.execute("CREATE TABLE IF NOT EXISTS service (""setting TEXT, ""value TEXT, ""UNIQUE(setting)"");")
					dbcur.execute("INSERT OR REPLACE INTO service Values (?, ?)", ('last_run', last_service))
					dbcur.connection.commit()
					dbcon.close()
				except:
					log_utils.error()
					try: dbcon.close()
					except: pass

				if control.setting('library.service.update') == 'false' or service_update is False: continue

				libepisodes().update()
				libmovies().list_update()
				libtvshows().list_update()

				if control.monitor.waitForAbort(60*15):
					break
			except:
				log_utils.error()
				continue


class libmovies:
	def __init__(self):
		self.library_folder = control.joinPath(control.transPath(control.setting('library.movie')), '')
		self.check_setting = control.setting('library.check_movie') or 'false'
		self.library_update = control.setting('library.update') or 'true' 
		self.dupe_chk = control.setting('library.check') or 'true'


	def auto_movie_setup(self):
		try:
			control.makeFile(self.library_folder)
			icon = 'DefaultMovies.png'
			source_name = 'Venom Movies'
			source_content = "('%s','movies','metadata.themoviedb.org','',2147483647,1,'<settings version=\"2\"><setting id=\"certprefix\" default=\"true\">Rated </setting><setting id=\"fanart\">true</setting><setting id=\"imdbanyway\">true</setting><setting id=\"keeporiginaltitle\" default=\"true\">false</setting><setting id=\"language\" default=\"true\">en</setting><setting id=\"RatingS\" default=\"true\">TMDb</setting><setting id=\"tmdbcertcountry\" default=\"true\">us</setting><setting id=\"trailer\">true</setting></settings>',0,0,NULL,NULL)" % self.library_folder
			control.add_source(source_name, self.library_folder, source_content, icon)
		except:
			log_utils.error()


	def list_update(self):
		contains = lib_tools().ckKodiSources()
		if not contains:
			return
		try:
			if not control.existsPath(control.dataPath):
				control.makeFile(control.dataPath)
			dbcon = database.connect(control.libcacheFile)
			dbcur = dbcon.cursor()
			dbcur.execute("CREATE TABLE IF NOT EXISTS lists (""type TEXT, ""list_name TEXT, ""url TEXT, ""UNIQUE(type, list_name, url)"");")
			dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
			dbcur.execute("SELECT * FROM lists WHERE type='movies'")
			results = dbcur.fetchall()
			if results == []:
				dbcon.close()
				control.notification(message=32113)
				return
			dbcon.close()
		except:
			log_utils.error()
			try: dbcon.close()
			except: return

		for list in results:
			type = list[0]
			list_name = list[1]
			url = list[2]

			try:
				if 'trakt' in url:
					from resources.lib.menus import movies
					items = movies.Movies().trakt_list(url, control.setting('trakt.user').strip())
				if 'themoviedb' in url:
					if '/list/' not in url:
						from resources.lib.indexers import tmdb
						items = tmdb.Movies().tmdb_list(url)
					else:
						from resources.lib.indexers import tmdb
						items = tmdb.Movies().tmdb_collections_list(url)
			except:
				log_utils.error()
				pass

			if not items:
				continue

			if service_notification and not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
				control.notification(title='list...' + list_name + ' - ' + type, message=32552)

			total_added = 0
			for i in items:
				if control.monitor.abortRequested():
					return sys.exist()
				try:
					files_added = self.add('%s (%s)' % (i['title'], i['year']), i['title'], i['year'], i['imdb'], i['tmdb'], range=True)
					if general_notification and files_added > 0:
						control.notification(title='%s (%s)' % (i['title'], i['year']), message=32554)
					if files_added > 0:
						total_added += 1
				except:
					log_utils.error()
					pass

		if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and total_added > 0:
			if contains:
				control.sleep(10000)
				control.execute('UpdateLibrary(video)')
			elif service_notification:
				control.notification(message=32103)


	def add(self, name, title, year, imdb, tmdb, range=False):
		try:
			contains = lib_tools().ckKodiSources()
			if general_notification:
				if not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
					control.notification(title=name, message=32552)

			try:
				if not self.dupe_chk == 'true':
					raise Exception()
				id = [imdb, tmdb] if tmdb != '0' else [imdb]
				lib = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["imdbnumber", "title", "originaltitle", "year"]}, "id": 1}' % (year, str(int(year)+1), str(int(year)-1)))
				lib = unicode(lib, 'utf-8', errors = 'ignore')
				lib = loads(lib)['result']['movies']
				lib = [i for i in lib if str(i['imdbnumber']) in id or (cleantitle.get(title) in [cleantitle.get(i['title'].encode('utf-8')), cleantitle.get(i['originaltitle'].encode('utf-8'))] and str(i['year']) == year)]
			except:
				lib = []

			files_added = 0
			try:
				if lib != []:
					raise Exception()

				if self.check_setting == 'true':
					src = lib_tools.check_sources(title, year, imdb, None, None, None, None, None)
					if not src:
						raise Exception()

				self.strmFile({'name': name, 'title': title, 'year': year, 'imdb': imdb, 'tmdb': tmdb})
				files_added += 1
			except:
				pass

			if files_added == 0 and general_notification:
				control.notification(title=name, message=32652)

			# if range is True:
			if range:
				return files_added

			if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and files_added > 0:
				if contains:
					if general_notification:
						control.notification(title=name, message=32554)
					control.sleep(10000)
					control.execute('UpdateLibrary(video)')
				elif general_notification:
					control.notification(title=name, message=32104)
		except: pass


	def silent(self, url):
		control.hide()
		contains = lib_tools().ckKodiSources()
		if service_notification and not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
			control.notification(message=32645)

		from resources.lib.menus import movies
		items = movies.Movies().get(url, idx=False)
		if items is None:
			items = []

		total_added = 0
		for i in items:
			try:
				if control.monitor.abortRequested():
					return sys.exit()
				files_added = self.add('%s (%s)' % (i['title'], i['year']), i['title'], i['year'], i['imdb'], i['tmdb'], range=True)
				if general_notification and files_added > 0:
					control.notification(title='%s (%s)' % (i['title'], i['year']), message=32554)
				if files_added > 0:
					total_added += 1
			except:
				log_utils.error()
				pass

		if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and total_added > 0:
			if contains:
				control.sleep(10000)
				control.execute('UpdateLibrary(video)')
			elif general_notification:
				control.notification(message=32103)

		if service_notification:
			control.notification(message=32105)


	def range(self, url, list_name):
		control.hide()
		if not control.yesnoDialog(control.lang(32555), '', ''): return
		try:
			if 'traktcollection' in url:
				message = 32661
			elif 'traktwatchlist' in url:
				message = 32662
			elif all(i in url for i in ['trakt', '/me/', '/lists/']):
				message = 32663
			elif all(i in url for i in ['trakt', '/lists/']) and '/me/' not in url:
				message = 32664
			elif 'tmdb_watchlist' in url:
				message = 32679
			elif 'tmdb_favorites' in url:
				message = 32680
			elif all(i in url for i in ['themoviedb', '/list/']):
				message = 32681
			else:
				message = 'list import'
		except:
			log_utils.error()
			pass

		if general_notification:
			if not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
				control.notification(message=message)

		items = []
		try:
			if 'trakt' in url:
				if 'traktcollection' in url:
					url = 'https://api.trakt.tv/users/me/collection/movies'
				if 'traktwatchlist' in url:
					url = 'https://api.trakt.tv/users/me/watchlist/movies'
				from resources.lib.menus import movies
				items = movies.Movies().trakt_list(url, control.setting('trakt.user').strip())

			if 'tmdb' in url:
				if 'tmdb_watchlist' in url:
					url = 'https://api.themoviedb.org/3/account/{account_id}/watchlist/movies?api_key=%s&session_id=%s' % ('%s', tmdb_session_id)
				if 'tmdb_favorites' in url: 
					url = 'https://api.themoviedb.org/3/account/{account_id}/favorite/movies?api_key=%s&session_id=%s' % ('%s', tmdb_session_id) 
				from resources.lib.indexers import tmdb
				items = tmdb.Movies().tmdb_list(url)

			if (all(i in url for i in ['themoviedb', '/list/'])):
				url = url.split('&sort_by')[0]
				from resources.lib.indexers import tmdb
				items = tmdb.Movies().tmdb_collections_list(url)
		except:
			log_utils.error()
			pass

		if items is None or items == []:
			if general_notification:
				control.notification(title=message, message=33049)
			return

		contains = lib_tools().ckKodiSources()

		total_added = 0
		for i in items:
			if control.monitor.abortRequested():
				return sys.exist()
			try:
				files_added = self.add('%s (%s)' % (i['title'], i['year']), i['title'], i['year'], i['imdb'], i['tmdb'], range=True)
				if general_notification and files_added > 0:
					control.notification(title='%s (%s)' % (i['title'], i['year']), message=32554)
				if files_added > 0:
					total_added += 1
			except:
				log_utils.error()
				pass

		try:
			type = 'movies'
			control.makeFile(control.dataPath)
			dbcon = database.connect(control.libcacheFile)
			dbcur = dbcon.cursor()
			dbcur.execute("CREATE TABLE IF NOT EXISTS lists (""type TEXT, ""list_name TEXT, ""url TEXT, ""UNIQUE(type, list_name, url)"");")
			dbcur.execute("INSERT OR REPLACE INTO lists Values (?, ?, ?)", (type, list_name, url))
			dbcur.connection.commit()
			dbcon.close()
		except:
			log_utils.error()
			try: dbcon.close()
			except: pass
			pass

		if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and total_added > 0:
			if contains:
				control.sleep(10000)
				control.execute('UpdateLibrary(video)')
			elif general_notification:
				control.notification(message=32103)


	def strmFile(self, i):
		try:
			title, year, imdb, tmdb = i['title'], i['year'], i['imdb'], i['tmdb']
			systitle = quote_plus(title)
			transtitle = cleantitle.normalize(title.translate(None, '\/:*?"<>|'))
			content = '%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s' % (sys.argv[0], systitle, year, imdb, tmdb)
			folder = lib_tools.make_path(self.library_folder, transtitle, year)
			lib_tools.create_folder(folder)
			lib_tools.write_file(control.joinPath(folder, lib_tools.legal_filename(transtitle) + '.' + year + '.strm'), content)
			lib_tools.write_file(control.joinPath(folder, lib_tools.legal_filename(transtitle) + '.' + year + '.nfo'), lib_tools.nfo_url('movie', i))
		except:
			log_utils.error()
			pass


class libtvshows:
	def __init__(self):
		self.library_folder = control.joinPath(control.transPath(control.setting('library.tv')),'')
		self.check_setting = control.setting('library.check_episode') or 'false'
		self.library_update = control.setting('library.update') or 'true'
		self.dupe_chk = control.setting('library.check') or 'true'
		self.include_unknown = control.setting('library.include_unknown') or 'true'
		self.showunaired = control.setting('showunaired') or 'true'
		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
		if control.setting('library.importdelay') != 'true':
			self.date = self.datetime.strftime('%Y%m%d')
		else:
			self.date = (self.datetime - datetime.timedelta(hours = 24)).strftime('%Y%m%d')
		self.block = False


	def auto_tv_setup(self):
		try:
			control.makeFile(self.library_folder)
			icon = control.joinPath(control.artPath(), 'libtv.png')
			icon = 'DefaultTVShows.png'
			source_name = 'Venom TV Shows'
			# TVDb scraper
			source_content = "('%s','tvshows','metadata.tvdb.com','',0,0,'<settings version=\"2\"><setting id=\"absolutenumber\" default=\"true\">false</setting><setting id=\"alsoimdb\">true</setting><setting id=\"dvdorder\" default=\"true\">false</setting><setting id=\"fallback\">true</setting><setting id=\"fallbacklanguage\">es</setting><setting id=\"fanart\">true</setting><setting id=\"language\" default=\"true\">en</setting><setting id=\"RatingS\" default=\"true\">TheTVDB</setting><setting id=\"usefallbacklanguage1\">true</setting></settings>',0,0,NULL,NULL)" % self.library_folder
			# TMDb scraper
			# source_content = "('%s','tvshows','metadata.tvshows.themoviedb.org','',0,0,'<settings version=\"2\"><setting id=\"alsoimdb\" default=\"true\">false</setting><setting id=\"certprefix\" default=\"true\"></setting><setting id=\"fallback\">true</setting><setting id=\"fanarttvart\">true</setting><setting id=\"keeporiginaltitle\" default=\"true\">false</setting><setting id=\"language\" default=\"true\">en</setting><setting id=\"RatingS\" default=\"true\">Themoviedb</setting><setting id=\"tmdbart\">true</setting><setting id=\"tmdbcertcountry\" default=\"true\">us</setting></settings>',0,0,NULL,NULL)" % self.library_folder
			control.add_source(source_name, self.library_folder, source_content, icon)
		except:
			log_utils.error()


	def list_update(self):
		contains = lib_tools().ckKodiSources()
		if not contains:
			return
		try:
			if not control.existsPath(control.dataPath):
				control.makeFile(control.dataPath)
			dbcon = database.connect(control.libcacheFile)
			dbcur = dbcon.cursor()
			dbcur.execute("CREATE TABLE IF NOT EXISTS lists (""type TEXT, ""list_name TEXT, ""url TEXT, ""UNIQUE(type, list_name, url)"");")
			dbcur.connection.commit()
		except:
			log_utils.error()
			pass
		try:
			dbcur.execute("SELECT * FROM lists WHERE type='tvshows'")
			results = dbcur.fetchall()
			if results == []:
				dbcon.close()
				return
			dbcon.close()
		except:
			log_utils.error()
			try: dbcon.close()
			except: return

		for list in results:
			type = list[0]
			list_name = list[1]
			url = list[2]

			try:
				if 'trakt' in url:
					from resources.lib.menus import tvshows
					items = tvshows.TVshows().trakt_list(url, control.setting('trakt.user').strip())

				if 'themoviedb' in url:
					if '/list/' not in url:
						from resources.lib.indexers import tmdb
						items = tmdb.TVshows().tmdb_list(url)
					else:
						from resources.lib.indexers import tmdb
						items = tmdb.TVshows().tmdb_collections_list(url)
			except:
				log_utils.error()
				pass

			if not items:
				continue

			if service_notification and not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
				control.notification(title='list...' + list_name + ' - ' + type, message=32552)

			total_added = 0
			for i in items:
				if control.monitor.abortRequested():
					return sys.exist()
				try:
					files_added = self.add(i['title'], i['year'], i['imdb'], i['tmdb'], i['tvdb'], range=True)
					if general_notification and files_added > 0:
						control.notification(title=i['title'], message=32554)
					if files_added > 0:
						total_added += 1
				except:
					log_utils.error()
					pass

		if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and total_added > 0:
			if contains:
				control.sleep(10000)
				control.execute('UpdateLibrary(video)')
			elif service_notification:
				control.notification(message=32103)


	def add(self, tvshowtitle, year, imdb, tmdb, tvdb, range=False):
		try:
			contains = lib_tools().ckKodiSources()
			if general_notification:
				if not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
					control.notification(title=tvshowtitle, message=32552)

			try:
				# from resources.lib.menus import episodes
				# items = episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, idx=False)
				from resources.lib.menus import seasons
				items = seasons.Seasons().tvdb_list(tvshowtitle, year, imdb, tmdb, tvdb, control.apiLanguage()['tvdb'], '-1') # fetch new meta (uncached)
			except:
				log_utils.error()
				return

			status = items[0]['status'].lower()

			try: items = [{'title': i['title'], 'year': i['year'], 'imdb': i['imdb'], 'tmdb': i['tmdb'], 'tvdb': i['tvdb'], 'season': i['season'], 'episode': i['episode'], 'tvshowtitle': i['tvshowtitle'], 'premiered': i['premiered']} for i in items]
			except: items = []
			if items == []: return

			try:
				if self.dupe_chk != 'true':
					raise Exception()

				id = [items[0]['imdb'], items[0]['tvdb']]
				# lib = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties" : ["imdbnumber", "title", "year"]}, "id": 1}')
				lib = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties": ["imdbnumber", "title", "year"]}, "id": 1}' % (year, str(int(year)+1), str(int(year)-1)))
				lib = unicode(lib, 'utf-8', errors='ignore')
				lib = loads(lib)['result']['tvshows']
				lib = [i['title'].encode('utf-8') for i in lib if str(i['imdbnumber']) in id or (i['title'].encode('utf-8') == items[0]['tvshowtitle'] and str(i['year']) == items[0]['year'])][0]
				lib = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "tvshow", "operator": "is", "value": "%s"}]}, "properties": ["season", "episode"]}, "id": 1}' % lib)
				lib = unicode(lib, 'utf-8', errors='ignore')
				lib = loads(lib)['result']['episodes']
				lib = ['S%02dE%02d' % (int(i['season']), int(i['episode'])) for i in lib]
				items = [i for i in items if not 'S%02dE%02d' % (int(i['season']), int(i['episode'])) in lib]
			except:
				lib = []
				pass
			files_added = 0
			for i in items:
				if lib != []:
					continue
				if control.monitor.abortRequested():
					return sys.exist()
				try:
					if self.check_setting == 'true':
						if i['episode'] == '1':
							self.block = True
							src = lib_tools.check_sources(i['title'], i['year'], i['imdb'], i['tvdb'], i['season'], i['episode'], i['tvshowtitle'], i['premiered'])
							if src:
								self.block = False
						if self.block:
							continue

					# Show Season Special(Season0).
					if str(i.get('season')) == '0' and control.setting('tv.specials') == 'false':
						continue

					premiered = i.get('premiered', '0')

					# Show Unaired or Unknown items.
					if premiered == '0' and self.include_unknown == 'false':
						continue
					elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.date))):
						if self.showunaired != 'true':
							continue

					self.strmFile(i)
					files_added += 1
				except:
					log_utils.error()
					pass

			if files_added == 0 and general_notification:
				control.notification(title=tvshowtitle, message=32652)

			# if range is True:
			if range:
				return files_added

			if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and files_added > 0:
				if contains:
					if general_notification:
						control.notification(title=tvshowtitle, message=32554)
					control.execute('UpdateLibrary(video)')
				elif general_notification:
					control.notification(title=tvshowtitle, message=32104)
		except:
			pass


	def silent(self, url):
		control.hide()
		contains = lib_tools().ckKodiSources()
		if service_notification and not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
			control.notification(message=32645)

		from resources.lib.menus import tvshows
		items = tvshows.TVshows().get(url, idx=False)
		if items is None:
			items = []

		total_added = 0
		for i in items:
			if control.monitor.abortRequested():
				return sys.exist()
			try:
				files_added = self.add(i['title'], i['year'], i['imdb'], i['tmdb'], i['tvdb'], range=True)
				if general_notification and files_added > 0:
					control.notification(title=i['title'], message=32554)
				if files_added > 0:
					total_added += 1
			except:
				log_utils.error()
				pass

		if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and total_added > 0:
			if contains:
				control.sleep(10000)
				control.execute('UpdateLibrary(video)')
			elif service_notification:
				control.notification(message=32103)

		if service_notification:
			control.notification(message='Trakt TV Show Sync Complete')


	def range(self, url, list_name):
		control.hide()
		if not control.yesnoDialog(control.lang(32555), '', ''): return
		try:
			if 'traktcollection' in url:
				message = 32661
			elif 'traktwatchlist' in url:
				message = 32662
			elif all(i in url for i in ['trakt', '/me/', '/lists/']):
				message = 32663
			elif all(i in url for i in ['trakt', '/lists/']) and '/me/' not in url:
				message = 32664
			elif 'tmdb_watchlist' in url:
				message = 32679
			elif 'tmdb_favorites' in url:
				message = 32680
			elif all(i in url for i in ['themoviedb', '/list/']):
				message = 32681
			else:
				message = 'list import'
		except:
				log_utils.error()
				pass

		if general_notification:
			if not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
				control.notification(message=message)

		items = []
		try:
			if 'trakt' in url:
				if 'traktcollection' in url:
					url = 'https://api.trakt.tv/users/me/collection/shows'
				if 'traktwatchlist' in url:
					url = 'https://api.trakt.tv/users/me/watchlist/shows'
				from resources.lib.menus import tvshows
				items = tvshows.TVshows().trakt_list(url, control.setting('trakt.user').strip())

			if 'tmdb' in url:
				if 'tmdb_watchlist' in url:
					url = 'https://api.themoviedb.org/3/account/{account_id}/watchlist/tv?api_key=%s&session_id=%s' % ('%s', tmdb_session_id)
				if 'tmdb_favorites' in url: 
					url = 'https://api.themoviedb.org/3/account/{account_id}/favorite/tv?api_key=%s&session_id=%s' % ('%s', tmdb_session_id) 
				from resources.lib.indexers import tmdb
				items = tmdb.TVshows().tmdb_list(url)

			if (all(i in url for i in ['themoviedb', '/list/'])):
				url = url.split('&sort_by')[0]
				from resources.lib.indexers import tmdb
				items = tmdb.TVshows().tmdb_collections_list(url)
		except:
			log_utils.error()
			pass

		if items is None or items == []:
			if general_notification:
				control.notification(title=message, message=33049)
			return

		contains = lib_tools().ckKodiSources()

		total_added = 0
		for i in items:
			if control.monitor.abortRequested():
				return sys.exist()
			try:
				files_added = self.add(i['title'], i['year'], i['imdb'], i['tmdb'], i['tvdb'], range=True)
				if general_notification and files_added > 0:
					control.notification(title=i['title'], message=32554)
				if files_added > 0:
					total_added += 1
			except:
				log_utils.error()
				pass

		try:
			type = 'tvshows'
			control.makeFile(control.dataPath)
			dbcon = database.connect(control.libcacheFile)
			dbcur = dbcon.cursor()
			dbcur.execute("CREATE TABLE IF NOT EXISTS lists (""type TEXT, ""list_name TEXT, ""url TEXT, ""UNIQUE(type, list_name, url)"");")
			dbcur.execute("INSERT OR REPLACE INTO lists Values (?, ?, ?)", (type, list_name, url))
			dbcur.connection.commit()
			dbcon.close()
		except:
			log_utils.error()
			try: dbcon.close()
			except: pass
			pass

		if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and total_added > 0:
			if contains:
				control.sleep(10000)
				control.execute('UpdateLibrary(video)')
			elif general_notification:
				control.notification(message=32103)


	def strmFile(self, i):
		try:
			title, year, imdb, tmdb, tvdb, season, episode, tvshowtitle, premiered = i['title'], i['year'], i['imdb'], i['tmdb'], i['tvdb'], i['season'], i['episode'], i['tvshowtitle'], i['premiered']

			episodetitle = quote_plus(title)
			systitle, syspremiered = quote_plus(tvshowtitle), quote_plus(premiered)

			transtitle = cleantitle.normalize(tvshowtitle.translate(None, '\/:*?"<>|'))

			content = '%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s' % (
							sys.argv[0], episodetitle, year, imdb, tmdb, tvdb, season, episode, systitle, syspremiered)

			folder = lib_tools.make_path(self.library_folder, transtitle, year)
			if not control.isfilePath(control.joinPath(folder, 'tvshow.nfo')):
				lib_tools.create_folder(folder)
				lib_tools.write_file(control.joinPath(folder, 'tvshow.nfo'), lib_tools.nfo_url('tv', i))

			folder = lib_tools.make_path(self.library_folder, transtitle, year, season)
			lib_tools.create_folder(folder)
			lib_tools.write_file(control.joinPath(folder, lib_tools.legal_filename('%s S%02dE%02d' % (transtitle, int(season), int(episode))) + '.strm'), content)
		except:
			log_utils.error()
			pass


class libepisodes:
	def __init__(self):
		self.library_folder = control.joinPath(control.transPath(control.setting('library.tv')),'')
		self.library_update = control.setting('library.update') or 'true'
		self.include_unknown = control.setting('library.include_unknown') or 'true'
		self.showunaired = control.setting('showunaired') or 'true'
		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
		if control.setting('library.importdelay') != 'true':
			self.date = self.datetime.strftime('%Y%m%d')
		else:
			self.date = (self.datetime - datetime.timedelta(hours = 24)).strftime('%Y%m%d')


	def update(self):
		if control.setting('library.service.update') == 'false':
			control.notification(message=32106)
		contains = lib_tools().ckKodiSources()
		if not contains:
			control.notification(message=32107)
			return

		try:
			items = []
			season, episode = [], []
			show = [control.joinPath(self.library_folder, i) for i in control.listDir(self.library_folder)[0]]

			if show == []:
				control.notification(message=32108)
				return

			for s in show:
				try: season += [control.joinPath(s, i) for i in control.listDir(s)[0]]
				except: pass

			for s in season:
				try: episode.append([control.joinPath(s, i) for i in control.listDir(s)[1] if i.endswith('.strm')][-1])
				except: pass

			for file in episode:
				try:
					file = control.openFile(file)
					read = file.read()
					read = read.encode('utf-8')
					file.close()

					if not read.startswith(sys.argv[0]):
						continue

					params = dict(parse_qsl(read.replace('?','')))

					try: tvshowtitle = params['tvshowtitle']
					except: tvshowtitle = None

					try: tvshowtitle = params['show']
					except: pass

					if tvshowtitle is None or tvshowtitle == '':
						continue

					year, imdb, tvdb = params['year'], params['imdb'], params['tvdb']
					imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
					tmdb = params.get('tmdb', '0')

					items.append({'tvshowtitle': tvshowtitle, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb})
				except:
					pass

			items = [i for x, i in enumerate(items) if i not in items[x + 1:]]

			if len(items) == 0:
				return
		except:
			log_utils.error()
			return

		try:
			lib = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties": ["imdbnumber", "title", "year"]}, "id": 1 }')
			# lib = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties": ["imdbnumber", "title", "year"]}, "id": 1}' % (year, str(int(year)+1), str(int(year)-1)))
			lib = unicode(lib, 'utf-8', errors='ignore')
			lib = loads(lib)['result']['tvshows']
		except:
			log_utils.error()
			return

		if service_notification and not control.condVisibility('Window.IsVisible(infodialog)') and not control.condVisibility('Player.HasVideo'):
			control.notification(message=32553)

		try:
			control.makeFile(control.dataPath)
			dbcon = database.connect(control.libcacheFile)
			dbcur = dbcon.cursor()
			dbcur.execute("CREATE TABLE IF NOT EXISTS tvshows (""id TEXT, ""items TEXT, ""UNIQUE(id)"");")
			dbcur.connection.commit()
		except:
			log_utils.error()
			try: dbcon.close()
			except: pass
			return

		try:
			# from resources.lib.menus import episodes
			from resources.lib.menus import seasons
		except:
			log_utils.error()
			return

		files_added = 0

		# __init__ doesn't get called from services so self.date never gets updated and new episodes are not added to the library
		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
		if control.setting('library.importdelay') != 'true':
			self.date = self.datetime.strftime('%Y%m%d')
		else:
			self.date = (self.datetime - datetime.timedelta(hours = 24)).strftime('%Y%m%d')

		for item in items:
			it = None
			if control.monitor.abortRequested():
				try: dbcon.close()
				except: pass
				return sys.exit()

			try:
				dbcur.execute("SELECT * FROM tvshows WHERE id = '%s'" % item['tvdb'])
				fetch = dbcur.fetchone()
				if fetch: it = eval(fetch[1].encode('utf-8'))
			except:
				log_utils.error()
				pass

			try:
				if it: raise Exception()
				# it = episodes.Episodes().get(item['tvshowtitle'], item['year'], item['imdb'], item['tmdb'], item['tvdb'], idx=False)
				it = seasons.Seasons().tvdb_list(item['tvshowtitle'], item['year'], item['imdb'], item['tmdb'], item['tvdb'], control.apiLanguage()['tvdb'], '-1') # fetch new meta (uncached)
				# log_utils.log('it = %s' % it, log_utils.LOGDEBUG)
				if not it:
					continue

				status = it[0]['status'].lower()
				it = [{'title': i['title'], 'year': i['year'], 'imdb': i['imdb'], 'tmdb': i['tmdb'], 'tvdb': i['tvdb'], 'season': i['season'], 'episode': i['episode'], 'tvshowtitle': i['tvshowtitle'], 'premiered': i['premiered']} for i in it]

				if status == 'continuing': raise Exception()
				dbcur.execute("INSERT INTO tvshows Values (?, ?)", (item['tvdb'], repr(it)))
				dbcur.connection.commit()
			except:
				log_utils.error()
				pass

			try:
				id = [item['imdb'], item['tvdb']]
				if item['tmdb'] != '0':
					id += [item['tmdb']]
				ep = [x['title'].encode('utf-8') for x in lib if str(x['imdbnumber']) in id or (x['title'].encode('utf-8') == item['tvshowtitle'] and str(x['year']) == item['year'])][0]
				ep = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "tvshow", "operator": "is", "value": "%s"}]}, "properties": ["season", "episode"]}, "id": 1}' % ep)
				ep = unicode(ep, 'utf-8', errors = 'ignore')
				ep = loads(ep).get('result', {}).get('episodes', {})
				ep = [{'season': int(i['season']), 'episode': int(i['episode'])} for i in ep]
				ep = sorted(ep, key = lambda x: (x['season'], x['episode']))[-1]
				num = [x for x,y in enumerate(it) if str(y['season']) == str(ep['season']) and str(y['episode']) == str(ep['episode'])][-1]
				it = [y for x,y in enumerate(it) if x > num]
				if len(it) == 0:
					continue
			except:
				# log_utils.error()
				continue

			for i in it:
				if control.monitor.abortRequested():
					return sys.exist()
				try:
					# Show Season Special(Season0).
					if str(i.get('season')) == '0' and control.setting('tv.specials') == 'false':
						continue

					premiered = i.get('premiered', '0')
					# Show Unaired items.
					if premiered == '0' and self.include_unknown == 'false':
						continue
					elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.date))):
						if self.showunaired != 'true':
							continue

					libtvshows().strmFile(i)
					files_added += 1
					if service_notification :
						control.notification(title=item['tvshowtitle'], message=32678)
				except:
					log_utils.error()
					pass

		try: dbcon.close()
		except: pass

		if files_added == 0 and service_notification :
			control.notification(message=32109)

		if self.library_update == 'true' and not control.condVisibility('Library.IsScanningVideo') and files_added > 0:
			if contains:
				if service_notification:
					control.notification(message=32554)
				control.sleep(10000)
				control.execute('UpdateLibrary(video)')
			elif service_notification:
				control.notification(message=32103)