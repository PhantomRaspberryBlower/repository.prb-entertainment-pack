# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

import datetime
import json
import re
import requests
import StringIO
import sys
import zipfile
try:
	from urllib import quote_plus, urlencode
	from urlparse import parse_qsl, urlparse, urlsplit
except:
	from urllib.parse import quote_plus, urlencode, parse_qsl, urlparse, urlsplit

from resources.lib.menus import navigator
from resources.lib.modules import cleantitle
from resources.lib.modules import cache
from resources.lib.modules import cleangenre
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import metacache
from resources.lib.modules import playcount
from resources.lib.modules import trakt
from resources.lib.modules import views
from resources.lib.modules import workers
from resources.lib.indexers import tvdb_v1


class TVshows:
	def __init__(self, type='show', notifications=True):
		self.count = int(control.setting('page.item.limit'))
		self.list = []
		self.meta = []
		self.threads = []
		self.type = type
		self.lang = control.apiLanguage()['tvdb']
		self.notifications = notifications
		self.disable_fanarttv = control.setting('disable.fanarttv')
		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
		self.today_date = (self.datetime).strftime('%Y-%m-%d')

		self.tvdb_key = control.setting('tvdb.api.key')

		self.imdb_user = control.setting('imdb.user').replace('ur', '')
		self.user = str(self.imdb_user) + str(self.tvdb_key)

		self.tvdb_info_link = 'https://thetvdb.com/api/%s/series/%s/all/%s.zip' % (self.tvdb_key.decode('base64'), '%s', '%s')
		self.tvdb_by_query = 'https://thetvdb.com/api/GetSeries.php?seriesname=%s'
		self.tvdb_by_imdb = 'https://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%s'
		self.tvdb_image = 'https://thetvdb.com/banners/'

		self.imdb_link = 'https://www.imdb.com'
		self.persons_link = 'https://www.imdb.com/search/name?count=100&name='
		self.personlist_link = 'https://www.imdb.com/search/name?count=100&gender=male,female'
		self.popular_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=100,&release_date=,date[0]&sort=moviemeter,asc&count=%d&start=1' % self.count
		self.airing_link = 'https://www.imdb.com/search/title?title_type=tv_episode&release_date=date[1],date[0]&sort=moviemeter,asc&count=%d&start=1' % self.count
		self.active_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=10,&production_status=active&sort=moviemeter,asc&count=%d&start=1' % self.count
		self.premiere_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&languages=en&num_votes=10,&release_date=date[60],date[0]&sort=release_date,desc&count=%d&start=1' % self.count
		self.rating_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=5000,&release_date=,date[0]&sort=user_rating,desc&count=%d&start=1' % self.count
		self.views_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=100,&release_date=,date[0]&sort=num_votes,desc&count=%d&start=1' % self.count
		self.person_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&release_date=,date[0]&role=%s&sort=year,desc&count=%d&start=1' % ('%s', self.count)
		self.genre_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&release_date=,date[0]&genres=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.count)
		self.keyword_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&release_date=,date[0]&keywords=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.count)
		self.language_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=100,&production_status=released&primary_language=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.count)
		self.certification_link = 'https://www.imdb.com/search/title?title_type=tv_series,mini_series&release_date=,date[0]&certificates=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.count)

		self.imdbwatchlist_link = 'https://www.imdb.com/user/ur%s/watchlist?sort=date_added,desc' % self.imdb_user # only used to get users watchlist ID
		self.imdbwatchlist2_link = 'https://www.imdb.com/list/%s/?view=detail&sort=%s&title_type=tvSeries,tvMiniSeries&start=1' % ('%s', self.imdb_sort(type='shows.watchlist'))
		self.imdblists_link = 'https://www.imdb.com/user/ur%s/lists?tab=all&sort=mdfd&order=desc&filter=titles' % self.imdb_user
		self.imdblist_link = 'https://www.imdb.com/list/%s/?view=detail&sort=%s&title_type=tvSeries,tvMiniSeries&start=1' % ('%s', self.imdb_sort())
		self.imdbratings_link = 'https://www.imdb.com/user/ur%s/ratings?sort=your_rating,desc&mode=detail&start=1' % self.imdb_user # IMDb ratings does not take title_type so filter in imdb_list() function
		self.anime_link = 'https://www.imdb.com/search/keyword?keywords=anime&title_type=tvSeries,miniSeries&sort=moviemeter,asc&count=%d&start=1' % self.count

		self.trakt_user = control.setting('trakt.user').strip()
		self.traktCredentials = trakt.getTraktCredentialsInfo()
		self.trakt_link = 'https://api.trakt.tv'
		self.search_link = 'https://api.trakt.tv/search/show?limit=%d&page=1&query=' % self.count
		self.traktlist_link = 'https://api.trakt.tv/users/%s/lists/%s/items/shows'
		self.traktlists_link = 'https://api.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'https://api.trakt.tv/users/likes/lists?limit=1000000'
		self.traktwatchlist_link = 'https://api.trakt.tv/users/me/watchlist/shows'
		self.traktcollection_link = 'https://api.trakt.tv/users/me/collection/shows'
		self.trakttrending_link = 'https://api.trakt.tv/shows/trending?page=1&limit=%d' % self.count
		self.traktpopular_link = 'https://api.trakt.tv/shows/popular?page=1&limit=%d' % self.count
		self.traktrecommendations_link = 'https://api.trakt.tv/recommendations/shows?limit=40'

		self.tvmaze_link = 'https://www.tvmaze.com'

		self.tmdb_key = control.setting('tmdb.api.key')
		if self.tmdb_key == '' or self.tmdb_key is None:
			self.tmdb_key = '3320855e65a9758297fec4f7c9717698'

		self.tmdb_session_id = control.setting('tmdb.session_id')
		self.tmdb_link = 'https://api.themoviedb.org'
		self.tmdb_userlists_link = 'https://api.themoviedb.org/3/account/{account_id}/lists?api_key=%s&language=en-US&session_id=%s&page=1' % ('%s', self.tmdb_session_id)
		self.tmdb_watchlist_link = 'https://api.themoviedb.org/3/account/{account_id}/watchlist/tv?api_key=%s&session_id=%s&sort_by=created_at.asc&page=1' % ('%s', self.tmdb_session_id)
		self.tmdb_favorites_link = 'https://api.themoviedb.org/3/account/{account_id}/favorite/tv?api_key=%s&session_id=%s&sort_by=created_at.asc&page=1' % ('%s', self.tmdb_session_id) 

		self.tmdb_popular_link = 'https://api.themoviedb.org/3/tv/popular?api_key=%s&language=en-US&region=US&page=1'
		self.tmdb_toprated_link = 'https://api.themoviedb.org/3/tv/top_rated?api_key=%s&language=en-US&region=US&page=1'
		self.tmdb_ontheair_link = 'https://api.themoviedb.org/3/tv/on_the_air?api_key=%s&language=en-US&region=US&page=1'
		self.tmdb_airingtoday_link = 'https://api.themoviedb.org/3/tv/airing_today?api_key=%s&language=en-US&region=US&page=1'


	def timeIt(func):
		import time
		fnc_name = func.__name__
		def wrap(*args, **kwargs):
			started_at = time.time()
			result = func(*args, **kwargs)
			log_utils.log('%s.%s = %s' % (__name__ , fnc_name, time.time() - started_at), log_utils.LOGDEBUG)
			return result
		return wrap


	def get(self, url, idx=True):
		try:
			try: url = getattr(self, url + '_link')
			except: pass
			try: u = urlparse(url).netloc.lower()
			except: pass

			if u in self.trakt_link and '/users/' in url:
				try:
					if '/users/me/' not in url:
						raise Exception()
					if trakt.getActivity() > cache.timeout(self.trakt_list, url, self.trakt_user):
						raise Exception()
					self.list = cache.get(self.trakt_list, 720, url, self.trakt_user)
				except:
					self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)

				if url == self.traktwatchlist_link:
					self.sort(type='shows.watchlist')
				else: self.sort()
				if idx: self.worker()

			elif u in self.trakt_link and self.search_link in url:
				self.list = cache.get(self.trakt_list, 1, url, self.trakt_user)
				if idx: self.worker(level=0)

			elif u in self.trakt_link:
				self.list = cache.get(self.trakt_list, 24, url, self.trakt_user)
				if idx: self.worker()

			elif u in self.imdb_link and ('/user/' in url or '/list/' in url):
				isRatinglink=True if self.imdbratings_link in url else False
				self.list = cache.get(self.imdb_list, 0, url, isRatinglink)
				if idx: self.worker()
				# self.sort() # I switched this to request sorting for imdb

			elif u in self.imdb_link:
				self.list = cache.get(self.imdb_list, 168, url)
				if idx: self.worker()

			if self.list is None:
				self.list = []

			if len(self.list) == 0 and self.search_link in url:
				control.hide()
				if self.notifications:
					control.notification(title=32010, message=33049)

			if idx:
				self.tvshowDirectory(self.list)
			return self.list
		except:
			log_utils.error()
			if not self.list:
				control.hide()
				if self.notifications:
					control.notification(title=32002, message=33049)


	def getTMDb(self, url, idx=True, cached=True):
		try:
			try: url = getattr(self, url + '_link')
			except: pass
			try: u = urlparse(url).netloc.lower()
			except: pass

			if u in self.tmdb_link and '/list/' in url:
				from resources.lib.indexers import tmdb
				self.list = cache.get(tmdb.TVshows().tmdb_collections_list, 0, url)

			elif u in self.tmdb_link and not '/list/' in url:
				from resources.lib.indexers import tmdb
				duration = 168 if cached else 0
				self.list = cache.get(tmdb.TVshows().tmdb_list, duration, url)

			if self.list is None:
				self.list = []
				raise Exception()
			if idx:
				self.tvshowDirectory(self.list)
			return self.list
		except:
			log_utils.error()
			if not self.list:
				control.hide()
				if self.notifications:
					control.notification(title=32002, message=33049)


	def getTVmaze(self, url, idx=True):
		from resources.lib.indexers import tvmaze
		try:
			try: url = getattr(self, url + '_link')
			except: pass

			self.list = cache.get(tvmaze.tvshows().tvmaze_list, 168, url)
			if not self.list:
				raise Exception()
			if idx:
				# self.worker() ## HMM-check why extra info not fetched here.
				self.tvshowDirectory(self.list)
			return self.list
		except:
			log_utils.error()
			if not self.list:
				control.hide()
				if self.notifications:
					control.notification(title=32002, message=33049)


	def sort(self, type='shows'):
		try:
			if not self.list: return
			attribute = int(control.setting('sort.%s.type' % type))
			reverse = int(control.setting('sort.%s.order' % type)) == 1
			if attribute == 0: reverse = False
			if attribute > 0:
				if attribute == 1:
					try: self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['tvshowtitle'].lower()), reverse=reverse)
					except: self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['title'].lower()), reverse=reverse)
				elif attribute == 2:
					self.list = sorted(self.list, key=lambda k: float(k['rating']), reverse=reverse)
				elif attribute == 3:
					self.list = sorted(self.list, key=lambda k: int(k['votes'].replace(',', '')), reverse=reverse)
				elif attribute == 4:
					for i in range(len(self.list)):
						if 'premiered' not in self.list[i]:
							self.list[i]['premiered'] = ''
							self.list = sorted(self.list, key=lambda k: k['year'], reverse=reverse)
						else: self.list = sorted(self.list, key=lambda k: k['premiered'], reverse=reverse)
				elif attribute == 5:
					for i in range(len(self.list)):
						if 'added' not in self.list[i]:
							self.list[i]['added'] = ''
					self.list = sorted(self.list, key=lambda k: k['added'], reverse=reverse)
				elif attribute == 6:
					for i in range(len(self.list)):
						if 'lastplayed' not in self.list[i]:
							self.list[i]['lastplayed'] = ''
					self.list = sorted(self.list, key=lambda k: k['lastplayed'], reverse=reverse)
			elif reverse:
				self.list = reversed(self.list)
		except:
			log_utils.error()
			pass


	def imdb_sort(self, type='shows'):
		sort = int(control.setting('sort.%s.type' % type))
		imdb_sort = 'list_order'
		if sort == 1:
			imdb_sort = 'alpha'
		if sort in [2, 3]:
			imdb_sort = 'user_rating'
		if sort == 4:
			imdb_sort = 'release_date'
		if sort in [5, 6]:
			imdb_sort = 'date_added'
		imdb_sort_order = ',asc' if int(control.setting('sort.%s.order' % type)) == 0 else ',desc'
		sort_string = imdb_sort + imdb_sort_order
		return sort_string


	def episodeCountParse(self, item):
		try:
			split_eps = item.split('<Episode>')
			episodes = [x for x in split_eps if '<EpisodeNumber>' in x]
			if control.setting('tv.specials') == 'true':
				episodes = [x for x in episodes]
			else:
				episodes = [x for x in episodes if not '<SeasonNumber>0</SeasonNumber>' in x]
				episodes = [x for x in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in x]
			unknown_premiered_eps = [x for x in episodes if '<FirstAired></FirstAired>' in x]
			premiered_eps = [x for x in episodes if not '<FirstAired></FirstAired>' in x]
			unaired_eps = [x for x in premiered_eps if int(re.sub('[^0-9]', '', str(client.parseDOM(x, 'FirstAired')))) > int(re.sub('[^0-9]', '', str(self.today_date)))]
			total_episodes = len(episodes) - len(unaired_eps) - len(unknown_premiered_eps)
		except:
			total_episodes = ''
			log_utils.error()
			pass
		return total_episodes


	def search(self):
		navigator.Navigator().addDirectoryItem(32603, 'tvSearchnew', 'search.png', 'DefaultAddonsSearch.png')
		try:
			from sqlite3 import dbapi2 as database
		except:
			from pysqlite2 import dbapi2 as database

		dbcon = database.connect(control.searchFile)
		dbcur = dbcon.cursor()
		try:
			dbcur.executescript("CREATE TABLE IF NOT EXISTS tvshow (ID Integer PRIMARY KEY AUTOINCREMENT, term);")
			dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		dbcur.execute("SELECT * FROM tvshow ORDER BY ID DESC")
		lst = []
		delete_option = False

		for (id, term) in dbcur.fetchall():
			if term not in str(lst):
				delete_option = True
				navigator.Navigator().addDirectoryItem(term, 'tvSearchterm&name=%s' % term, 'search.png', 'DefaultAddonsSearch.png', isSearch=True, table='tvshow')
				lst += [(term)]

		dbcon.close()

		if delete_option:
			navigator.Navigator().addDirectoryItem(32605, 'cache_clearSearch', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		navigator.Navigator().endDirectory()


	def search_new(self):
# need fix for when context menu returns here brings keyboard input back up
		t = control.lang(32010)
		k = control.keyboard('', t)
		k.doModal()
		q = k.getText() if k.isConfirmed() else None

		if (q is None or q == ''):
			return

		try:
			from sqlite3 import dbapi2 as database
		except:
			from pysqlite2 import dbapi2 as database

		dbcon = database.connect(control.searchFile)
		dbcur = dbcon.cursor()
		dbcur.execute("INSERT INTO tvshow VALUES (?,?)", (None, q))
		dbcur.connection.commit()
		dbcon.close()
		url = self.search_link + quote_plus(q)
		if control.getKodiVersion() >= 18:
			self.get(url)
		else:
			url = '%s?action=tvshowPage&url=%s' % (sys.argv[0], quote_plus(url))
			control.execute('Container.Update(%s)' % url)


	def search_term(self, name):
		url = self.search_link + quote_plus(name)
		self.get(url)


	def person(self):
		t = control.lang(32010)
		k = control.keyboard('', t)
		k.doModal()
		q = k.getText().strip() if k.isConfirmed() else None
		if (q is None or q == ''):
			return
		url = self.persons_link + quote_plus(q)
		self.persons(url)


	def genres(self):
		genres = [
			('Action', 'action', True), ('Adventure', 'adventure', True), ('Animation', 'animation', True),
			('Anime', 'anime', False), ('Biography', 'biography', True), ('Comedy', 'comedy', True),
			('Crime', 'crime', True), ('Drama', 'drama', True), ('Family', 'family', True),
			('Fantasy', 'fantasy', True), ('Game-Show', 'game_show', True),
			('History', 'history', True), ('Horror', 'horror', True), ('Music ', 'music', True),
			('Musical', 'musical', True), ('Mystery', 'mystery', True), ('News', 'news', True),
			('Reality-TV', 'reality_tv', True), ('Romance', 'romance', True), ('Science Fiction', 'sci_fi', True),
			('Sport', 'sport', True), ('Talk-Show', 'talk_show', True), ('Thriller', 'thriller', True),
			('War', 'war', True), ('Western', 'western', True)
		]
		for i in genres:
			self.list.append({'name': cleangenre.lang(i[0], self.lang), 'url': self.genre_link % i[1] if i[2] else self.keyword_link % i[1], 'image': 'genres.png', 'icon': 'DefaultGenre.png', 'action': 'tvshows'})
		self.addDirectory(self.list)
		return self.list


	def networks(self):
		if control.setting('tvshows.networks.view') == '0':
			from resources.lib.indexers.tvmaze import networks_this_season as networks
		elif control.setting('tvshows.networks.view') == '1':
			from resources.lib.indexers.tvmaze import networks_view_all as networks
		networks = sorted(networks, key=lambda x: x[0])
		for i in networks:
			self.list.append({'name': i[0], 'url': self.tvmaze_link + i[1], 'image': i[2], 'icon': 'DefaultNetwork.png', 'action': 'tvmazeTvshows'})
		self.addDirectory(self.list)
		return self.list


	def originals(self):
		if control.setting('tvshows.networks.view') == '0':
			from resources.lib.indexers.tvmaze import originals_this_season as originals
		elif control.setting('tvshows.networks.view') == '1':
			from resources.lib.indexers.tvmaze import originals_view_all as originals
		originals = sorted(originals, key=lambda x: x[0])
		for i in originals:
			self.list.append({'name': i[0], 'url': self.tvmaze_link + i[1], 'image': i[2], 'icon': 'DefaultNetwork.png', 'action': 'tvmazeTvshows'})
		self.addDirectory(self.list)
		return self.list


	def languages(self):
		languages = [('Arabic', 'ar'), ('Bosnian', 'bs'), ('Bulgarian', 'bg'), ('Chinese', 'zh'), ('Croatian', 'hr'), ('Dutch', 'nl'),
			('English', 'en'), ('Finnish', 'fi'), ('French', 'fr'), ('German', 'de'), ('Greek', 'el'), ('Hebrew', 'he'), ('Hindi ', 'hi'),
			('Hungarian', 'hu'), ('Icelandic', 'is'), ('Italian', 'it'), ('Japanese', 'ja'), ('Korean', 'ko'), ('Norwegian', 'no'),
			('Persian', 'fa'), ('Polish', 'pl'), ('Portuguese', 'pt'), ('Punjabi', 'pa'), ('Romanian', 'ro'), ('Russian', 'ru'),
			('Serbian', 'sr'), ('Spanish', 'es'), ('Swedish', 'sv'), ('Turkish', 'tr'), ('Ukrainian', 'uk')]
		for i in languages:
			self.list.append({'name': str(i[0]), 'url': self.language_link % i[1], 'image': 'languages.png', 'icon': 'DefaultAddonLanguage.png', 'action': 'tvshows'})
		self.addDirectory(self.list)
		return self.list


	def certifications(self):
		certificates = [
			('Child Audience (TV-Y)', 'TV-Y'),
			('Young Audience (TV-Y7)', 'TV-Y7'),
			('General Audience (TV-G)', 'TV-G'),
			('Parental Guidance (TV-PG)', 'TV-PG'),
			('Youth Audience (TV-14)', 'TV-13', 'TV-14'),
			('Mature Audience (TV-MA)', 'TV-MA')
		]
		for i in certificates:
			self.list.append({'name': str(i[0]), 'url': self.certification_link % self.certificatesFormat(i[1]), 'image': 'certificates.png', 'icon': 'DefaultTVShows.png', 'action': 'tvshows'})
		self.addDirectory(self.list)
		return self.list


	def certificatesFormat(self, certificates):
		base = 'US%3A'
		if not isinstance(certificates, (tuple, list)):
			certificates = [certificates]
		return ','.join([base + i.upper() for i in certificates])


	def persons(self, url):
		if url is None:
			self.list = cache.get(self.imdb_person_list, 24, self.personlist_link)
		else:
			self.list = cache.get(self.imdb_person_list, 1, url)
		if len(self.list) == 0:
			control.hide()
			control.notification(title=32010, message=33049)
		for i in range(0, len(self.list)):
			self.list[i].update({'icon': 'DefaultActor.png', 'action': 'tvshows'})
		self.addDirectory(self.list)
		return self.list


	def tvshowsListToLibrary(self, url):
		url = getattr(self, url + '_link')
		u = urlparse(url).netloc.lower()
		try:
			control.hide()
			if u in self.tmdb_link:
				from resources.lib.indexers import tmdb
				items = tmdb.userlists(url)
			elif u in self.trakt_link:
				items = self.trakt_user_list(url, self.trakt_user)
			items = [(i['name'], i['url']) for i in items]
			message = 32663
			if 'themoviedb' in url: message = 32681
			select = control.selectDialog([i[0] for i in items], control.lang(message))
			list_name = items[select][0]
			if select == -1: return
			link = items[select][1]
			link = link.split('&sort_by')[0]
			from resources.lib.modules import libtools
			libtools.libtvshows().range(link, list_name)
		except:
			log_utils.error()
			return


	def userlists(self):
		userlists = []
		try:
			if not self.traktCredentials:
				raise Exception()
			activity = trakt.getActivity()
			self.list = []
			lists = []
			try:
				if activity > cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user):
					raise Exception()
				lists += cache.get(self.trakt_user_list, 720, self.traktlists_link, self.trakt_user)
			except:
				lists += cache.get(self.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
			for i in range(len(lists)):
				lists[i].update({'image': 'trakt.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})
			userlists += lists
		except:
			pass

		try:
			if not self.traktCredentials:
				raise Exception()
			self.list = []
			lists = []

			try:
				if activity > cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user):
					raise Exception()
				lists += cache.get(self.trakt_user_list, 3, self.traktlikedlists_link, self.trakt_user)
			except:
				lists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)

			for i in range(len(lists)):
				lists[i].update({'image': 'trakt.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})
			userlists += lists
		except:
			pass

		try:
			if self.imdb_user == '':
				raise Exception()
			self.list = []
			lists = cache.get(self.imdb_user_list, 0, self.imdblists_link)
			for i in range(len(lists)):
				lists[i].update({'image': 'imdb.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})
			userlists += lists
		except:
			pass

		try:
			if self.tmdb_session_id == '':
				raise Exception()
			self.list = []
			from resources.lib.indexers import tmdb
			lists = cache.get(tmdb.userlists, 0, self.tmdb_userlists_link)
			for i in range(len(lists)):
				lists[i].update({'image': 'tmdb.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tmdbTvshows'})
			userlists += lists
		except:
			pass

		self.list = []
		# Filter the user's own lists that were
		for i in range(len(userlists)):
			contains = False
			adapted = userlists[i]['url'].replace('/me/', '/%s/' % self.trakt_user)
			for j in range(len(self.list)):
				if adapted == self.list[j]['url'].replace('/me/', '/%s/' % self.trakt_user):
					contains = True
					break
			if not contains:
				self.list.append(userlists[i])

		# for i in range(len(self.list)):
			# self.list[i].update({'action': 'tvshows'})

		# TMDb Favorites
		if self.tmdb_session_id != '':
			self.list.insert(0, {'name': control.lang(32026), 'url': self.tmdb_favorites_link, 'image': 'tmdb.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tmdbTvshows'})

		# TMDb Watchlist
		if self.tmdb_session_id != '':
			self.list.insert(0, {'name': control.lang(32033), 'url': self.tmdb_watchlist_link, 'image': 'tmdb.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tmdbTvshows'})

		# imdb Watchlist
		if self.imdb_user != '':
			self.list.insert(0, {'name': control.lang(32033), 'url': self.imdbwatchlist_link, 'image': 'imdb.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})

		# imdb My Ratings
		if self.imdb_user != '':
			self.list.insert(0, {'name': control.lang(32025), 'url': self.imdbratings_link, 'image': 'imdb.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})

		# Trakt Watchlist
		if self.traktCredentials:
			# trakt_watchlist = self.traktwatchlist_link + 'shows'
			trakt_watchlist = self.traktwatchlist_link
			self.list.insert(0, {'name': control.lang(32033), 'url': trakt_watchlist, 'image': 'trakt.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})

		self.addDirectory(self.list)
		return self.list


	def trakt_list(self, url, user):
		list = []
		try:
			dupes = []
			q = dict(parse_qsl(urlsplit(url).query))
			q.update({'extended': 'full'})
			q = (urlencode(q)).replace('%2C', ',')
			u = url.replace('?' + urlparse(url).query, '') + '?' + q
			if '/related' in u:
				u = u + '&limit=20'
			result = trakt.getTraktAsJson(u)

			if not result:
				return list
			items = []
			for i in result:
				try:
					show = i['show']
					try: show['listed_at'] = i['listed_at'] # for watchlist
					except: pass
					items.append(show)
				except:
					pass
			if len(items) == 0:
				items = result
		except:
			log_utils.error()
			return

		try:
			q = dict(parse_qsl(urlsplit(url).query))
			if int(q['limit']) != len(items):
				raise Exception()
			q.update({'page': str(int(q['page']) + 1)})
			q = (urlencode(q)).replace('%2C', ',')
			next = url.replace('?' + urlparse(url).query, '') + '?' + q
		except:
			next = ''

		for item in items:
			try:
				try: title = item['title'].encode('utf-8')
				except: title = item['title']
				listed_at = item.get('listed_at', '0')

				year = str(item.get('year', '0'))
				if year == 'None' or year == '0':
					continue

				# if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

				imdb = item.get('ids', {}).get('imdb', '0')
				if imdb == '' or imdb is None or imdb == 'None':
					imdb = '0'

				tmdb = str(item.get('ids', {}).get('tmdb', '0'))
				if tmdb == '' or tmdb is None or tmdb == 'None':
					tmdb = '0'

				tvdb = str(item.get('ids', {}).get('tvdb', '0'))
				if tvdb == '' or tvdb is None or tvdb == 'None':
					tvdb = '0'

				if tvdb is None or tvdb == '' or tvdb in dupes:
					continue
				dupes.append(tvdb)

				premiered = item.get('first_aired', '0')
				studio = item.get('network', '0')
				try: trailer = control.trailer % item.get('trailer').split('v=')[1]
				except: trailer = ''

				genre = []
				for i in item['genres']:
					genre.append(i.title())
				if genre == []: genre = 'NA'

				duration = str(item.get('runtime'))

				rating = str(item.get('rating', '0'))
				votes = str(format(int(item.get('votes', '0')),',d'))

				mpaa = item.get('certification', '0')

				plot = item.get('overview')
				try: plot = plot.encode('utf-8')
				except: pass

				list.append({'title': title, 'originaltitle': title, 'added': listed_at, 'year': year, 'premiered': premiered, 'studio': studio, 'trailer': trailer,
									'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'plot': plot, 'imdb': imdb,
									'tmdb': tmdb, 'tvdb': tvdb, 'poster': '0', 'fanart': '0', 'next': next})
			except:
				log_utils.error()
				pass
		return list


	def trakt_user_list(self, url, user):
		list = []
		try:
			result = trakt.getTrakt(url)
			items = json.loads(result)
		except:
			log_utils.error()
			pass

		for item in items:
			try:
				try: name = item['list']['name']
				except: name = item['name']
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')
				try: url = (trakt.slug(item['list']['user']['username']), item['list']['ids']['slug'])
				except: url = ('me', item['ids']['slug'])
				url = self.traktlist_link % url
				url = url.encode('utf-8')
				list.append({'name': name, 'url': url, 'context': url})
			except:
				log_utils.error()
				pass
		list = sorted(list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
		return list


	def imdb_list(self, url, isRatinglink=False):
		list = []
		items = []
		dupes = []
		try:
			for i in re.findall('date\[(\d+)\]', url):
				url = url.replace('date[%s]' % i, (self.datetime - datetime.timedelta(days = int(i))).strftime('%Y-%m-%d'))

			def imdb_watchlist_id(url):
				return client.parseDOM(client.request(url).decode('iso-8859-1').encode('utf-8'), 'meta', ret='content', attrs = {'property': 'pageId'})[0]

			if url == self.imdbwatchlist_link:
				url = cache.get(imdb_watchlist_id, 8640, url)
				url = self.imdbwatchlist2_link % url

			result = client.request(url)
			result = result.replace('\n', ' ')
			result = result.decode('iso-8859-1').encode('utf-8')

			items = client.parseDOM(result, 'div', attrs = {'class': '.+? lister-item'}) + client.parseDOM(result, 'div', attrs = {'class': 'lister-item .+?'})
			items += client.parseDOM(result, 'div', attrs = {'class': 'list_item.+?'})
		except:
			log_utils.error()
			return

		try:
			# HTML syntax error, " directly followed by attribute name. Insert space in between. parseDOM can otherwise not handle it.
			result = result.replace('"class="lister-page-next', '" class="lister-page-next')
			next = client.parseDOM(result, 'a', ret='href', attrs = {'class': 'lister-page-next.+?'})
			if len(next) == 0:
				next = client.parseDOM(result, 'div', attrs = {'class': 'pagination'})[0]
				next = zip(client.parseDOM(next, 'a', ret='href'), client.parseDOM(next, 'a'))
				next = [i[0] for i in next if 'Next' in i[1]]
			next = url.replace(urlparse(url).query, urlparse(next[0]).query)
			next = client.replaceHTMLCodes(next)
			next = next.encode('utf-8')
		except:
			next = ''

		for item in items:
			try:
				title = client.parseDOM(item, 'a')[1]
				title = client.replaceHTMLCodes(title)
				try: title = title.encode('utf-8')
				except: pass

				year = client.parseDOM(item, 'span', attrs = {'class': 'lister-item-year.+?'})
				year += client.parseDOM(item, 'span', attrs = {'class': 'year_type'})
				year = re.findall('(\d{4})', year[0])[0]
				year = year.encode('utf-8')

				if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

				imdb = client.parseDOM(item, 'a', ret='href')[0]
				imdb = re.findall('(tt\d*)', imdb)[0]
				imdb = imdb.encode('utf-8')

				if imdb in dupes:
					raise Exception()
				dupes.append(imdb)

				# parseDOM cannot handle elements without a closing tag.
				# try: poster = client.parseDOM(item, 'img', ret='loadlate')[0]
				# except: poster = '0'
				try:
					from bs4 import BeautifulSoup
					html = BeautifulSoup(item, "html.parser")
					poster = html.find_all('img')[0]['loadlate']
				except:
					poster = '0'

				if '/nopicture/' in poster: poster = '0'
				poster = re.sub('(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', poster)
				poster = client.replaceHTMLCodes(poster)
				poster = poster.encode('utf-8')

				try: genre = client.parseDOM(item, 'span', attrs = {'class': 'genre'})[0]
				except: genre = '0'
				genre = ' / '.join([i.strip() for i in genre.split(',')])
				if genre == '': genre = '0'
				genre = client.replaceHTMLCodes(genre)
				genre = genre.encode('utf-8')

				try: duration = re.findall('(\d+?) min(?:s|)', item)[-1]
				except: duration = '0'
				duration = duration.encode('utf-8')

				rating = '0'
				try: rating = client.parseDOM(item, 'span', attrs = {'class': 'rating-rating'})[0]
				except:
					try: rating = client.parseDOM(rating, 'span', attrs = {'class': 'value'})[0]
					except:
						try: rating = client.parseDOM(item, 'div', ret='data-value', attrs = {'class': '.*?imdb-rating'})[0]
						except: pass
				if rating == '' or rating == '-': rating = '0'
				rating = client.replaceHTMLCodes(rating)
				rating = rating.encode('utf-8')

				votes = '0'
				try:
					votes = client.parseDOM(item, 'span', attrs = {'name': 'nv'})[0]
				except:
					try:
						votes = client.parseDOM(item, 'div', ret='title', attrs = {'class': '.*?rating-list'})[0]
					except:
						try:
							votes = re.findall('\((.+?) vote(?:s|)\)', votes)[0]
						except:
							pass
				if votes == '':
					votes = '0'
				votes = client.replaceHTMLCodes(votes)
				votes = votes.encode('utf-8')

				try:
					mpaa = client.parseDOM(item, 'span', attrs = {'class': 'certificate'})[0]
				except:
					mpaa = '0'
				if isRatinglink:
					if mpaa in ['G', 'PG', 'PG-13', 'R', 'NC-17']:
						raise Exception()
				if mpaa == '' or mpaa == 'NOT_RATED':
					mpaa = '0'
				mpaa = mpaa.replace('_', '-')
				mpaa = client.replaceHTMLCodes(mpaa)
				mpaa = mpaa.encode('utf-8')

				plot = '0'
				try:
					plot = client.parseDOM(item, 'p', attrs = {'class': 'text-muted'})[0]
				except:
					try:
						plot = client.parseDOM(item, 'div', attrs = {'class': 'item_description'})[0]
					except:
						plot = client.parseDOM(item, 'p', attrs = {'class': '""'})[0]
						pass
				plot = plot.rsplit('<span>', 1)[0].strip()
				plot = re.sub('<.+?>|</.+?>', '', plot)
				if plot == '':
					plot = '0'
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				list.append({'title': title, 'originaltitle': title, 'year': year, 'genre': genre, 'duration': duration,
									'rating': rating, 'votes': votes, 'mpaa': mpaa, 'plot': plot, 'imdb': imdb, 'tmdb': '0',
									'tvdb': '0', 'poster': poster, 'next': next})
			except:
				log_utils.error()
				pass
		return list


	def imdb_person_list(self, url):
		list = []
		try:
			result = client.request(url)
			items = client.parseDOM(result, 'div', attrs = {'class': '.+? mode-detail'})
		except:
			log_utils.error()
			return

		for item in items:
			try:
				name = client.parseDOM(item, 'img', ret='alt')[0]
				name = name.encode('utf-8')

				url = client.parseDOM(item, 'a', ret='href')[0]
				url = re.findall('(nm\d*)', url, re.I)[0]
				url = self.person_link % url
				url = client.replaceHTMLCodes(url)
				url = url.encode('utf-8')

				image = client.parseDOM(item, 'img', ret='src')[0]
				image = re.sub('(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', image)
				image = client.replaceHTMLCodes(image)
				image = image.encode('utf-8')

				list.append({'name': name, 'url': url, 'image': image})
			except:
				log_utils.error()
				pass
		return list


	def imdb_user_list(self, url):
		list = []
		try:
			result = client.request(url)
			result = result.decode('iso-8859-1').encode('utf-8')
			items = client.parseDOM(result, 'li', attrs={'class': 'ipl-zebra-list__item user-list'})
			# Gaia uses this but breaks the IMDb user list
			# items = client.parseDOM(result, 'div', attrs = {'class': 'list_name'})
		except:
			log_utils.error()
			pass

		for item in items:
			try:
				name = client.parseDOM(item, 'a')[0]
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')

				url = client.parseDOM(item, 'a', ret='href')[0]
				url = url = url.split('/list/', 1)[-1].strip('/')
				# url = url.split('/list/', 1)[-1].replace('/', '')
				url = self.imdblist_link % url
				url = client.replaceHTMLCodes(url)
				url = url.encode('utf-8')

				list.append({'name': name, 'url': url, 'context': url})
			except:
				log_utils.error()
				pass

		list = sorted(list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
		return list


	def worker(self, level = 1):
		try:
			if not self.list: return
			self.meta = []
			total = len(self.list)
			for i in range(0, total): 
				self.list[i].update({'metacache': False})
			self.list = metacache.fetch(self.list, self.lang, self.user)
			for r in range(0, total, 40):
				threads = []
				for i in range(r, r + 40):
					if i < total:
						threads.append(workers.Thread(self.super_info, i))
				[i.start() for i in threads]
				[i.join() for i in threads]
			if self.meta:
				metacache.insert(self.meta)
			self.list = [i for i in self.list if i['tvdb'] != '0']
		except:
			log_utils.error()


	# @timeIt
	def super_info(self, i):
		try:
			if self.list[i]['metacache']:
				return
			imdb = self.list[i]['imdb'] if 'imdb' in self.list[i] else '0'
			tmdb = self.list[i]['tmdb'] if 'tmdb' in self.list[i] else '0'
			tvdb = self.list[i]['tvdb'] if 'tvdb' in self.list[i] else '0'

			if (tvdb == '0' or tmdb == '0') and imdb != '0':
				try:
					trakt_ids = trakt.IdLookup('imdb', imdb, 'show')
					if trakt_ids:
						if tvdb == '0':
							tvdb = str(trakt_ids.get('tvdb', '0'))
							if tvdb == '' or tvdb is None or tvdb == 'None':
								tvdb = '0'
						if tmdb == '0':
							tmdb = str(trakt_ids.get('tmdb', '0'))
							if tmdb == '' or tmdb is None or tmdb == 'None':
								tmdb = '0'
				except:
					log_utils.error()
					pass

			if imdb == '0' or tmdb == '0' or tvdb == '0':
				try:
					trakt_ids = trakt.SearchTVShow(quote_plus(self.list[i]['title']), self.list[i]['year'], full=False)[0]
					if not trakt_ids: raise Exception
					trakt_ids = trakt_ids.get('show', '0')
					if imdb == '0':
						imdb = trakt_ids.get('ids', {}).get('imdb', '0')
						if imdb == '' or imdb is None or imdb == 'None':
							imdb = '0'
						if not imdb.startswith('tt'):
							imdb = '0'
					if tmdb == '0':
						tmdb = str(trakt_ids.get('ids', {}).get('tmdb', '0'))
						if tmdb == '' or tmdb is None or tmdb == 'None':
							tmdb = '0'
					if tvdb == '0':
						tvdb = str(trakt_ids.get('ids', {}).get('tvdb', '0'))
						if tvdb == '' or tvdb is None or tvdb == 'None':
							tvdb = '0'
				except:
					log_utils.error()
					pass

###--Check TVDb by seriesname
			if tvdb == '0' or imdb == '0':
				try:
					url = self.tvdb_by_query % (quote_plus(self.list[i]['title']))
					result = requests.get(url).content
					result = re.sub(r'[^\x00-\x7F]+', '', result)
					result = client.replaceHTMLCodes(result)
					result = client.parseDOM(result, 'Series')
					result = [(client.parseDOM(x, 'SeriesName'), client.parseDOM(x, 'FirstAired'), client.parseDOM(x, 'seriesid'), client.parseDOM(x, 'IMDB_ID'), client.parseDOM(x, 'AliasNames')) for x in result]
					year = self.list[i]['year']
					years = [str(year), str(int(year)+1), str(int(year)-1)]
					item = [(x[0], x[1], x[2], x[3], x[4]) for x in result if cleantitle.get(self.list[i]['title']) == cleantitle.get(str(x[0][0])) and any(y in str(x[1][0]) for y in years)]
					if item == []:
						item = [(x[0], x[1], x[2], x[3], x[4]) for x in result if cleantitle.get(self.list[i]['title']) == cleantitle.get(str(x[4][0]))]
					if item == []:
						item = [(x[0], x[1], x[2], x[3], x[4]) for x in result if cleantitle.get(self.list[i]['title']) == cleantitle.get(str(x[0][0]))]
					if item == []:
						raise Exception()
					if tvdb == '0':
						tvdb = item[0][2]
						tvdb = tvdb[0] or '0'
					if imdb == '0':
						imdb = item[0][3]
						imdb = imdb[0] or '0'
				except:
					log_utils.error()
					pass
#################################

			if tvdb == '0' or tvdb is None:
				return

			url = self.tvdb_info_link % (tvdb, 'en')
			data = requests.get(url).content # sometimes one api key pulls empty xml while another does not
			zip = zipfile.ZipFile(StringIO.StringIO(data))
			item = zip.read('en.xml')
			actors = zip.read('actors.xml')
			zip.close()

			if imdb == '0':
				try: imdb = client.parseDOM(item, 'IMDB_ID')[0] or '0'
				except: pass

			try: title = client.parseDOM(item, 'SeriesName')[0] or '0'
			except: title = '0'
			title = client.replaceHTMLCodes(title)
			title = title.encode('utf-8')

			if 'year' not in self.list[i] or self.list[i]['year'] == '0':
				year = client.parseDOM(item, 'FirstAired')[0]
				year = re.compile('(\d{4})').findall(year)[0]
			else:
				year = self.list[i]['year']

			if 'premiered' not in self.list[i] or self.list[i]['premiered'] == '0':
				premiered = client.parseDOM(item, 'FirstAired')[0]
			else:
				premiered = self.list[i]['premiered']

			if 'studio' not in self.list[i] or self.list[i]['studio'] == '0':
				studio = client.parseDOM(item, 'Network')[0]
			else:
				studio = self.list[i]['studio']

			if 'genre' not in self.list[i] or self.list[i]['genre'] == '0':
				genre = client.parseDOM(item, 'Genre')[0]
				genre = [x for x in genre.split('|') if x != '']
				genre = ' / '.join(genre)
			else:
				genre = self.list[i]['genre']

			if 'duration' not in self.list[i] or self.list[i]['duration'] == '0':
				try: duration = client.parseDOM(item, 'Runtime')[0]
				except: duration = '0'
			else:
				duration = self.list[i]['duration']

			if 'rating' not in self.list[i] or self.list[i]['rating'] == '0':
				rating = client.parseDOM(item, 'Rating')[0]
			else:
				rating = self.list[i]['rating']

			if 'votes' not in self.list[i] or self.list[i]['votes'] == '0':
				votes = client.parseDOM(item, 'RatingCount')[0]
			else:
				votes = self.list[i]['votes']

			if 'mpaa' not in self.list[i] or self.list[i]['mpaa'] == '0':
				mpaa = client.parseDOM(item, 'ContentRating')[0]
			else:
				mpaa = self.list[i]['mpaa']

			try:
				seasons = client.parseDOM(item, 'SeasonNumber')
				seasons_list = [] 
				[seasons_list.append(x) for x in seasons if x not in seasons_list and x != '0'] 
				total_seasons = len(seasons_list)
			except:
				total_seasons = ''
				log_utils.error()
				pass

			if 'castandart' not in self.list[i] or self.list[i]['castandart'] == []:
				# castandart = cache.get(tvdb_v1.parseActors, 168, actors) or []
				castandart = tvdb_v1.parseActors(actors) or []
			else:
				castandart = self.list[i]['castandart']

			try: plot = client.parseDOM(item, 'Overview')[0] or '0'
			except: plot = '0'
			plot = client.replaceHTMLCodes(plot)
			try: plot = plot.encode('utf-8')
			except: pass

			if self.lang != 'en':
				try:
					trans_item = trakt.getTVShowTranslation(imdb, self.lang, full=True)
					title = trans_item.get('title') or title
					plot = trans_item.get('overview') or plot
				except:
					pass

			status = client.parseDOM(item, 'Status')[0]
			if not status:
				status = 'Ended'

			if 'poster' not in self.list[i] or self.list[i]['poster'] == '0':
				poster = client.parseDOM(item, 'poster')[0]
				if poster and poster != '':
					poster = '%s%s' % (self.tvdb_image, poster)
				else: poster = '0'
			else:
				poster = self.list[i]['poster']

			banner = client.parseDOM(item, 'banner')[0]
			if banner and banner != '':
				banner = '%s%s' % (self.tvdb_image, banner)
			else: banner = '0'

			if 'fanart' not in self.list[i] or self.list[i]['fanart'] == '0':
				fanart = client.parseDOM(item, 'fanart')[0]
				if fanart and fanart != '':
					fanart = '%s%s' % (self.tvdb_image, fanart)
				else: fanart = '0'
			else:
				fanart = self.list[i]['fanart']

			item = {'extended': True, 'title': title, 'tvshowyear': year, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb,
						'total_seasons': total_seasons, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating,
						'votes': votes, 'mpaa': mpaa, 'castandart': castandart, 'plot': plot, 'status': status, 'poster': poster, 'poster2': '0', 'poster3': '0',
						'banner': banner, 'banner2': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0',
						'landscape': fanart, 'metacache': False}
			meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'lang': self.lang, 'user': self.user, 'item': item}

			if self.disable_fanarttv != 'true':
				if tvdb is not None and tvdb != '0':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_tvshow_art, 168, tvdb)
					# extended_art = fanarttv.get_tvshow_art(tvdb)
					if extended_art:
						item.update(extended_art)
						meta.update(item)

			if (self.disable_fanarttv == 'true' and (poster == '0' or fanart == '0')) or (
				self.disable_fanarttv != 'true' and ((poster == '0' and item.get('poster2') == '0') or (
				fanart == '0' and item.get('fanart2') == '0'))):
				from resources.lib.indexers.tmdb import TVshows
				tmdb_art = cache.get(TVshows().get_art, 168, tmdb)
				# tmdb_art = TVshows().get_art(tmdb)
				if tmdb_art:
					item.update(tmdb_art)
					if item.get('landscape', '0') == '0':
						landscape = item.get('fanart3', '0')
						item.update({'landscape': landscape})
					meta.update(item)

			item = dict((k,v) for k, v in item.iteritems() if v != '0')
			self.list[i].update(item)

			self.meta.append(meta)
		except:
			log_utils.error()
			pass


	def tvshowDirectory(self, items, next=True):
		if not items:
			control.hide()
			control.notification(title=32002, message=33049)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		is_widget = 'plugin' not in control.infoLabel('Container.PluginName')
		settingFanart = control.setting('fanart')
		addonPoster = control.addonPoster()
		addonFanart = control.addonFanart()
		addonBanner = control.addonBanner()
		indicators = playcount.getTVShowIndicators()
		unwatchedEnabled = control.setting('tvshows.unwatched.enabled') == 'true'
		flatten = control.setting('flatten.tvshows') == 'true'

		if trakt.getTraktIndicatorsInfo():
			watchedMenu = control.lang(32068)
			unwatchedMenu = control.lang(32069)
		else:
			watchedMenu = control.lang(32066)
			unwatchedMenu = control.lang(32067)

		traktManagerMenu = control.lang(32070)
		# playlistManagerMenu = control.lang(35522)
		queueMenu = control.lang(32065)
		showPlaylistMenu = control.lang(35517)
		clearPlaylistMenu = control.lang(35516)
		playRandom = control.lang(32535)
		addToLibrary = control.lang(32551)

		for i in items:
			try:
				imdb, tmdb, tvdb, year = i.get('imdb', '0'), i.get('tmdb', '0'), i.get('tvdb', '0'), i.get('year', '0')
				try: title = i['originaltitle']
				except: title = i['title']
				label = title
				systitle = quote_plus(title)

				meta = dict((k, v) for k, v in i.iteritems() if v != '0')
				meta.update({'code': imdb, 'imdbnumber': imdb})
				meta.update({'mediatype': 'tvshow'})
				meta.update({'tag': [imdb, tvdb]})

				# Some descriptions have a link at the end that. Remove it.
				try:
					plot = meta['plot']
					index = plot.rfind('See full summary')
					if index >= 0: plot = plot[:index]
					plot = plot.strip()
					if re.match('[a-zA-Z\d]$', plot): plot += ' ...'
					meta['plot'] = plot
				except:
					pass

				try: meta.update({'duration': str(int(meta['duration']) * 60)})
				except: pass
				try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
				except: pass
				try:
					if 'tvshowtitle' not in meta: meta.update({'tvshowtitle': title})
				except: pass
				try:
					if 'tvshowyear' not in meta: meta.update({'tvshowyear': year})
				except: pass

				poster1 = meta.get('poster')
				poster2 = meta.get('poster2')
				poster3 = meta.get('poster3')
				poster = poster3 or poster2 or poster1 or addonPoster

				fanart = ''
				if settingFanart:
					fanart1 = meta.get('fanart')
					fanart2 = meta.get('fanart2')
					fanart3 = meta.get('fanart3')
					fanart = fanart3 or fanart2 or fanart1 or addonFanart

				landscape = meta.get('landscape')
				thumb = meta.get('thumb') or poster or landscape
				icon = meta.get('icon') or poster

				banner1 = meta.get('banner')
				banner2 = meta.get('banner2')
				banner3 = meta.get('banner3')
				banner = banner3 or banner2 or banner1 or addonBanner

				clearlogo = meta.get('clearlogo')
				clearart = meta.get('clearart')

				art = {}
				art.update({'poster': poster, 'tvshow.poster': poster, 'season.poster': poster, 'fanart': fanart, 'icon': icon,
									'thumb': thumb, 'banner': banner, 'clearlogo': clearlogo, 'clearart': clearart, 'landscape': landscape})

				if flatten:
					url = '%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s' % (sysaddon, systitle, year, imdb, tmdb, tvdb)
				else:
					url = '%s?action=seasons&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s' % (sysaddon, systitle, year, imdb, tmdb, tvdb)

####-Context Menu and Overlays-####
				cm = []
				if self.traktCredentials:
					cm.append((traktManagerMenu, 'RunPlugin(%s?action=tools_traktManager&name=%s&imdb=%s&tvdb=%s)' % (sysaddon, systitle, imdb, tvdb)))

				try:
					overlay = int(playcount.getTVShowOverlay(indicators, imdb, tvdb))
					watched = overlay == 7
					if watched:
						meta.update({'playcount': 1, 'overlay': 7})
						cm.append((unwatchedMenu, 'RunPlugin(%s?action=playcount_TVShow&name=%s&imdb=%s&tvdb=%s&query=6)' % (sysaddon, systitle, imdb, tvdb)))
					else:
						meta.update({'playcount': 0, 'overlay': 6})
						cm.append((watchedMenu, 'RunPlugin(%s?action=playcount_TVShow&name=%s&imdb=%s&tvdb=%s&query=7)' % (sysaddon, systitle, imdb, tvdb)))
				except:
					pass

				cm.append(('Find similar', 'ActivateWindow(10025,%s?action=tvshows&url=https://api.trakt.tv/shows/%s/related,return)' % (sysaddon, imdb)))
				cm.append((playRandom, 'RunPlugin(%s?action=random&rtype=season&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s)' % (
									sysaddon, systitle, year, imdb, tvdb)))

				cm.append((queueMenu, 'RunPlugin(%s?action=playlist_QueueItem&name=%s)' % (sysaddon, systitle)))
				cm.append((showPlaylistMenu, 'RunPlugin(%s?action=playlist_Show)' % sysaddon))
				cm.append((clearPlaylistMenu, 'RunPlugin(%s?action=playlist_Clear)' % sysaddon))
				if control.setting('library.service.update') == 'true':
					cm.append((addToLibrary, 'RunPlugin(%s?action=library_tvshowToLibrary&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s)' % (sysaddon, systitle, year, imdb, tmdb, tvdb)))
				cm.append(('[COLOR red]Venom Settings[/COLOR]', 'RunPlugin(%s?action=tools_openSettings)' % sysaddon))
####################################

				if not i.get('trailer'):
					meta.update({'trailer': '%s?action=trailer&type=%s&name=%s&year=%s&imdb=%s' % (sysaddon, 'show', quote_plus(label), year, imdb)})

				item = control.item(label=label)
				if 'castandart' in i:
					item.setCast(i['castandart'])

				if unwatchedEnabled:
					count = playcount.getShowCount(indicators, imdb, tvdb)
					if count: # for some reason count at times is 'None' but back up and go back in and count has new value
						item.setProperty('TotalEpisodes', str(count['total']))
						item.setProperty('WatchedEpisodes', str(count['watched']))
						item.setProperty('UnWatchedEpisodes', str(count['unwatched']))

				if 'total_seasons' in meta:
					item.setProperty('TotalSeasons', str(meta.get('total_seasons')))

				item.setArt(art)
				item.setProperty('IsPlayable', 'false')
				item.setProperty('tmdb_id', tmdb)
				if is_widget:
					item.setProperty('isVenom_widget', 'true')
				item.setInfo(type='video', infoLabels=control.metadataClean(meta))
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				item.addContextMenuItems(cm)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				log_utils.error()
				pass

		if next:
			try:
				url = items[0]['next']
				if url == '':
					raise Exception()

				nextMenu = control.lang(32053)
				url_params = dict(parse_qsl(url))

				if 'imdb.com' in url:
					start = int(url_params.get('start'))
					page = '  [I](%s)[/I]' % str(((start - 1) / self.count) + 1)
				else:
					page = url_params.get('page')
					page = '  [I](%s)[/I]' % page

				nextMenu = '[COLOR skyblue]' + nextMenu + page + '[/COLOR]'

				u = urlparse(url).netloc.lower()
				if u in self.imdb_link or u in self.trakt_link:
					url = '%s?action=tvshowPage&url=%s' % (sysaddon, quote_plus(url))
				elif u in self.tmdb_link:
					url = '%s?action=tmdbTvshowPage&url=%s' % (sysaddon, quote_plus(url))
				elif u in self.tvmaze_link:
					url = '%s?action=tvmazeTvshowPage&url=%s' % (sysaddon, quote_plus(url))

				item = control.item(label=nextMenu)
				icon = control.addonNext()
				item.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'banner': icon})
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				log_utils.error()
				pass

		control.content(syshandle, 'tvshows')
		control.directory(syshandle, cacheToDisc=True)
		# control.sleep(500)
		views.setView('tvshows', {'skin.estuary': 55, 'skin.confluence': 500})


	def addDirectory(self, items, queue=False):
		if not items: 
			control.hide()
			control.notification(title=32002, message=33049)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		addonThumb = control.addonThumb()
		artPath = control.artPath()

		queueMenu = control.lang(32065)
		playRandom = control.lang(32535)
		addToLibrary = control.lang(32551)

		for i in items:
			try:
				name = i['name']
				if i['image'].startswith('http'):
					thumb = i['image']
				elif artPath:
					thumb = control.joinPath(artPath, i['image'])
				else:
					thumb = addonThumb

				icon = i.get('icon', 0)
				if not icon:
					icon = 'DefaultFolder.png'

				url = '%s?action=%s' % (sysaddon, i['action'])
				try: url += '&url=%s' % quote_plus(i['url'])
				except: pass

				cm = []
				cm.append((playRandom, 'RunPlugin(%s?action=random&rtype=show&url=%s)' % (sysaddon, quote_plus(i['url']))))
				if queue:
					cm.append((queueMenu, 'RunPlugin(%s?action=playlist_QueueItem)' % sysaddon))
				try:
					if control.setting('library.service.update') == 'true':
						cm.append((addToLibrary, 'RunPlugin(%s?action=library_tvshowsToLibrary&url=%s&name=%s)' % (sysaddon, quote_plus(i['context']), name)))
				except: pass
				cm.append(('[COLOR red]Venom Settings[/COLOR]', 'RunPlugin(%s?action=tools_openSettings)' % sysaddon))

				item = control.item(label=name)
				item.setProperty('IsPlayable', 'false')
				item.setArt({'icon': icon, 'poster': thumb, 'thumb': thumb, 'fanart': control.addonFanart(), 'banner': thumb})
				item.addContextMenuItems(cm)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				log_utils.error()
				pass

		control.content(syshandle, 'addons')
		control.directory(syshandle, cacheToDisc=True)