# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

import copy
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

from resources.lib.modules import cache
from resources.lib.modules import cleangenre
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import playcount
from resources.lib.modules import trakt
from resources.lib.modules import views
from resources.lib.modules import workers
from resources.lib.extensions import tools
from resources.lib.indexers import tvdb_v1

disable_fanarttv = control.setting('disable.fanarttv')


class Episodes:
	def __init__(self, type='show', notifications=True):
		self.count = int(control.setting('page.item.limit'))
		self.list = []
		self.threads = []
		self.type = type
		self.lang = control.apiLanguage()['tvdb']
		self.notifications = notifications

		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours=5))
		self.today_date = (self.datetime).strftime('%Y-%m-%d')

		self.tvdb_key = control.setting('tvdb.api.key')
		self.tvdb_info_link = 'https://thetvdb.com/api/%s/series/%s/all/%s.zip' % (self.tvdb_key.decode('base64'), '%s', '%s')
		self.tvdb_image = 'https://thetvdb.com/banners/'
		self.tvdb_poster = 'https://thetvdb.com/banners/_cache/'

		self.trakt_user = control.setting('trakt.user').strip()
		self.traktCredentials = trakt.getTraktCredentialsInfo()
		self.trakt_link = 'https://api.trakt.tv'
		self.traktlist_link = 'https://api.trakt.tv/users/%s/lists/%s/items/episodes'
		self.traktlists_link = 'https://api.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'https://api.trakt.tv/users/likes/lists?limit=1000000'
		self.traktwatchlist_link = 'https://api.trakt.tv/users/me/watchlist/episodes'
		self.trakthistory_link = 'https://api.trakt.tv/users/me/history/shows?limit=200'
		self.progress_link = 'https://api.trakt.tv/users/me/watched/shows'
		self.hiddenprogress_link = 'https://api.trakt.tv/users/hidden/progress_watched?limit=1000&type=show'
		self.mycalendar_link = 'https://api.trakt.tv/calendars/my/shows/date[30]/31/'
		self.traktunfinished_link = 'https://api.trakt.tv/sync/playback/episodes?limit=40'

		self.tvmaze_link = 'https://api.tvmaze.com'
		self.added_link = 'https://api.tvmaze.com/schedule'
		self.calendar_link = 'https://api.tvmaze.com/schedule?date=%s'

		self.showunaired = control.setting('showunaired') or 'true'
		self.unairedcolor = control.setting('unaired.identify')
		self.unairedcolor = control.getColor(self.unairedcolor)


	def get(self, tvshowtitle, year, imdb, tmdb, tvdb, season=None, episode=None, idx=True):
		from resources.lib.menus import seasons
		try:
			if season is None and episode is None:
				self.list = cache.get(seasons.Seasons().tvdb_list, 1, tvshowtitle, year, imdb, tmdb, tvdb, self.lang, '-1')
			elif episode is None:
				self.list = cache.get(seasons.Seasons().tvdb_list, 1, tvshowtitle, year, imdb, tmdb, tvdb, self.lang, season)
			else:
				self.list = cache.get(seasons.Seasons().tvdb_list, 1, tvshowtitle, year, imdb, tmdb, tvdb, self.lang, '-1')
				num = [x for x, y in enumerate(self.list) if y['season'] == str(season) and y['episode'] == str(episode)][-1]
				self.list = [y for x, y in enumerate(self.list) if x >= num]

			if idx:
				self.episodeDirectory(self.list)
			return self.list
		except:
			log_utils.error()
			if not self.list:
				control.hide()
				if self.notifications:
					control.notification(title=32326, message=33049)


	def unfinished(self, url):
		try:
			try: url = getattr(self, url + '_link')
			except: pass
			activity = trakt.getPausedActivity()
			self.list = []
			if url == self.traktunfinished_link :
				try:
					# if activity > cache.timeout(self.trakt_list, url, self.trakt_user, False):
					if activity > cache.timeout(self.trakt_episodes_list, url, self.trakt_user,self.lang):
						raise Exception()
					# self.list = cache.get(self.trakt_list, 720, url, self.trakt_user, False)
					self.list = cache.get(self.trakt_episodes_list, 720, url, self.trakt_user, self.lang)
				except:
					# self.list = cache.get(self.trakt_list, 0, url, self.trakt_user, False)
					self.list = cache.get(self.trakt_episodes_list, 0, url, self.trakt_user, self.lang)

			self.list = sorted(self.list, key=lambda k: k['paused_at'], reverse=True)
			# self.list = sorted(self.list, key=lambda i: control.datetime_workaround(i['paused_at'][:19],
																				# format="%Y-%m-%dT%H:%M:%S",
																				# date_only=False), reverse=True)
			self.episodeDirectory(self.list, unfinished=True, next=False)
			return self.list
		except:
			log_utils.error()
			if not self.list:
				control.hide()
				if self.notifications:
					control.notification(title=32326, message=33049)


	def calendar(self, url):
		try:
			try: url = getattr(self, url + '_link')
			except: pass
			direct = control.setting('tvshows.direct') == 'true'

			if self.trakt_link in url and url == self.progress_link:
				self.list = cache.get(self.trakt_progress_list, 0, url, self.trakt_user, self.lang, direct)
				self.sort(type='progress')

			elif self.trakt_link in url and url == self.mycalendar_link:
				self.list = cache.get(self.trakt_episodes_list, 0.3, url, self.trakt_user, self.lang)
				self.sort(type='calendar')

			elif self.trakt_link in url and url == self.trakthistory_link:
				self.list = cache.get(self.trakt_episodes_list, 0.3, url, self.trakt_user, self.lang)
				self.sort(type='progress')

			elif self.trakt_link in url and '/users/' in url:
				# self.list = cache.get(self.trakt_list, 0.3, url, self.trakt_user, True)
				# self.list = self.list[::-1]
				self.list = cache.get(self.trakt_episodes_list, 0.3, url, self.trakt_user, self.lang)
				self.sort(type='calendar')

			elif self.trakt_link in url:
				self.list = cache.get(self.trakt_list, 1, url, self.trakt_user, True)

			elif self.tvmaze_link in url and url == self.added_link:
				urls = [i['url'] for i in self.calendars(idx=False)][:5]
				self.list = []
				for url in urls:
					self.list += cache.get(self.tvmaze_list, 720, url, True)

			elif self.tvmaze_link in url:
				self.list = cache.get(self.tvmaze_list, 1, url, False)

			self.episodeDirectory(self.list, unfinished=False, next=False)
			return self.list
		except:
			pass


	def sort(self, type='shows'):
		try:
			if not self.list: return
			attribute = int(control.setting('sort.%s.type' % type))
			reverse = int(control.setting('sort.%s.order' % type)) == 1
			if attribute > 0:
				if attribute == 1:
					try: self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['tvshowtitle'].lower()), reverse=reverse)
					except: self.list = sorted(self.list, key=lambda k: k['title'].lower(), reverse=reverse)
				elif attribute == 2:
					self.list = sorted(self.list, key=lambda k: float(k['rating']), reverse=reverse)
				elif attribute == 3:
					self.list = sorted(self.list, key=lambda k: int(k['votes'].replace(',', '')), reverse=reverse)
				elif attribute == 4:
					for i in range(len(self.list)):
						if 'premiered' not in self.list[i]:
							self.list[i]['premiered'] = ''
					self.list = sorted(self.list, key=lambda k: k['premiered'], reverse=reverse)
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


	def seasonCount(self, items, index):
		if 'seasoncount' not in items[index] or not items[index]['seasoncount']:
			thread = workers.Thread(self._seasonCount, items, index)
			self.threads.append(thread)
			thread.start()


	def seasonCountWait(self):
		[i.join() for i in self.threads]
		self.threads = []


	def _seasonCount(self, items, index):
		try:
			from resources.lib.menus import seasons
			items[index]['seasoncount'] = seasons.Seasons().seasonCount(items[index]['tvshowtitle'],
											items[index]['year'], items[index]['imdb'],
											items[index]['tvdb'], items[index]['season'])
		except:
			log_utils.error()


	def calendars(self, idx=True):
		m = control.lang(32060).split('|')
		try:
			months = [(m[0], 'January'), (m[1], 'February'), (m[2], 'March'), (m[3], 'April'), (m[4], 'May'),
					(m[5], 'June'), (m[6], 'July'), (m[7], 'August'), (m[8], 'September'), (m[9], 'October'),
					(m[10], 'November'), (m[11], 'December')]
		except:
			months = []

		d = control.lang(32061).split('|')
		try:
			days = [(d[0], 'Monday'), (d[1], 'Tuesday'), (d[2], 'Wednesday'), (d[3], 'Thursday'), (d[4], 'Friday'),
					(d[5], 'Saturday'), (d[6], 'Sunday')]
		except:
			days = []
		for i in range(0, 30):
			try:
				name = (self.datetime - datetime.timedelta(days=i))
				name = (control.lang(32062) % (name.strftime('%A'), name.strftime('%d %B'))).encode('utf-8')
				for m in months:
					name = name.replace(m[1], m[0])
				for d in days:
					name = name.replace(d[1], d[0])
				try: name = name.encode('utf-8')
				except: pass
				url = self.calendar_link % (self.datetime - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
				self.list.append({'name': name, 'url': url, 'image': 'calendar.png', 'icon': 'DefaultYear.png', 'action': 'calendar'})
			except:
				pass
		if idx:
			self.addDirectory(self.list)
		return self.list


	def userlists(self):
		userlists = []
		try:
			if not self.traktCredentials:
				raise Exception()
			activity = trakt.getActivity()
		except:
			pass
		try:
			if not self.traktCredentials: raise Exception()
			self.list = []
			try:
				if activity > cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user):
					raise Exception()
				userlists += cache.get(self.trakt_user_list, 720, self.traktlists_link, self.trakt_user)
			except:
				userlists += cache.get(self.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
		except:
			pass
		try:
			if not self.traktCredentials:
				raise Exception()
			self.list = []
			try:
				if activity > cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user):
					raise Exception()
				userlists += cache.get(self.trakt_user_list, 720, self.traktlikedlists_link, self.trakt_user)
			except:
				userlists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)
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

		for i in range(0, len(self.list)): self.list[i].update({'image': 'trakt.png', 'action': 'calendar'})

		# Trakt Watchlist
		if self.traktCredentials:
			self.list.insert(0, {'name': control.lang(32033), 'url': self.traktwatchlist_link, 'image': 'trakt.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})

		self.addDirectory(self.list, queue=True)
		return self.list


	def trakt_user_list(self, url, user):
		try:
			result = trakt.getTrakt(url)
			items = json.loads(result)
		except:
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

				self.list.append({'name': name, 'url': url})
			except:
				log_utils.error()
				pass

		self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
		return self.list


	def trakt_progress_list(self, url, user, lang, direct=False):
		# from resources.lib.menus import seasons
		try:
			url += '?extended=full'
			result = trakt.getTrakt(url)
			result = json.loads(result)
			items = []
		except:
			return

		for item in result:
			try:
				num_1 = 0
				for i in range(0, len(item['seasons'])):
					if item['seasons'][i]['number'] > 0: num_1 += len(item['seasons'][i]['episodes'])
				num_2 = int(item['show']['aired_episodes'])
				if num_1 >= num_2:
					continue

				# trakt sometimes places season0 at end and episodes out of order. So we sort it to be sure.
				season_sort = sorted(item['seasons'][:], key=lambda k: k['number'], reverse=False)
				season = str(season_sort[-1]['number'])
				episode = [x for x in season_sort[-1]['episodes'] if 'number' in x]
				episode = sorted(episode, key=lambda x: x['number'])
				episode = str(episode[-1]['number'])

				try: tvshowtitle = (item['show']['title']).encode('utf-8')
				except: tvshowtitle = item['show']['title']
				if tvshowtitle is None or tvshowtitle == '':
					continue

				year = str(item.get('show').get('year'))

				imdb = str(item.get('show', {}).get('ids', {}).get('imdb', '0'))
				if imdb == '' or imdb is None or imdb == 'None':
					imdb = '0'
				tmdb = str(item.get('show', {}).get('ids', {}).get('tmdb', '0'))
				if tmdb == '' or tmdb is None or tmdb == 'None':
					tmdb = '0'
				tvdb = str(item.get('show', {}).get('ids', {}).get('tvdb', '0'))
				if tvdb == '' or tvdb is None or tvdb == 'None':
					tvdb = '0'

# ### episode IDS
				episodeIDS = {}
				if control.setting('enable.upnext') == 'true':
					episodeIDS = trakt.getEpisodeSummary(imdb, season, episode, full=False) or {}
					if episodeIDS != {}:
						episodeIDS = episodeIDS.get('ids', {})
##------------------

				try: added = item['show']['updated_at']
				except: added = None

				lastplayed = item.get('show').get('last_watched_at') or item.get('last_watched_at')

				studio = item.get('show').get('network', '0')
				status = item.get('show').get('status', '0')

				try: trailer = control.trailer % item['show']['trailer'].split('v=')[1]
				except: trailer = ''

				values = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year, 'snum': season,
								'enum': episode, 'added': added, 'lastplayed': lastplayed, 'studio': studio, 'status': status,
								'trailer': trailer, 'episodeIDS': episodeIDS}
				try:
					air = item['show']['airs']
					values['airday'] = air['day']
					values['airtime'] = air['time']
					values['airzone'] = air['timezone']
				except:
					pass

				items.append(values)
			except:
				pass

		try:
			result = trakt.getTrakt(self.hiddenprogress_link)
			result = json.loads(result)
			result = [str(i['show']['ids']['tvdb']) for i in result]
			items = [i for i in items if i['tvdb'] not in result]
		except:
			pass

		def items_list(i):
			tvshowtitle = i['tvshowtitle']
			year = str(i.get('year'))
			imdb, tmdb, tvdb = i['imdb'], i['tmdb'], i['tvdb']
			trailer = i.get('trailer')
			try:
				url = self.tvdb_info_link % (tvdb, lang)
				data = requests.get(url).content
				zip = zipfile.ZipFile(StringIO.StringIO(data))

				result = zip.read('%s.xml' % lang)
				artwork = zip.read('banners.xml')
				actors = zip.read('actors.xml')
				zip.close()

				result = result.split('<Episode>')
				item = [x for x in result if '<EpisodeNumber>' in x]
				item2 = result[0]

				# TVDB en.xml sort order is by ID now so we resort by season then episode for proper indexing of nextup item to watch.
				try:
					sorted_item = [y for y in item if re.compile('<SeasonNumber>(.+?)</SeasonNumber>').findall(y)[0] == str(i['snum'])]
					sorted_item += [y for y in item if re.compile('<SeasonNumber>(.+?)</SeasonNumber>').findall(y)[0] == str(int(i['snum']) + 1)]
					sorted_item = sorted(sorted_item, key= lambda t:(int(re.compile('<SeasonNumber>(\d+)</SeasonNumber>').findall(t)[-1]), int(re.compile('<EpisodeNumber>(\d+)</EpisodeNumber>').findall(t)[-1])))
					num = [x for x,y in enumerate(sorted_item) if re.compile('<SeasonNumber>(.+?)</SeasonNumber>').findall(y)[0] == str(i['snum']) and re.compile('<EpisodeNumber>(.+?)</EpisodeNumber>').findall(y)[0] == str(i['enum'])][-1]
					item = [y for x,y in enumerate(sorted_item) if x > num][0]
				except:
					return

				artwork = artwork.split('<Banner>')
				artwork = [x for x in artwork if '<Language>en</Language>' in x and '<BannerType>season</BannerType>' in x]
				artwork = [x for x in artwork if not 'seasonswide' in re.findall('<BannerPath>(.+?)</BannerPath>', x)[0]]

				premiered = client.parseDOM(item, 'FirstAired')[0]
				if premiered == '' or '-00' in premiered: premiered = '0'

				try: added = i['added']
				except: added = None

				try: lastplayed = i['lastplayed']
				except: lastplayed = None

				try: episodeIDS = i['episodeIDS']
				except: episodeIDS = {}

				status = i['status'] or client.parseDOM(item2, 'Status')[0]

				unaired = ''
				if status.lower() == 'ended':
					pass
				elif premiered == '0':
					raise Exception()
				elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))):
					unaired = 'true'
					if self.showunaired != 'true':
						raise Exception()

				title = client.parseDOM(item, 'EpisodeName')[0]
				title = client.replaceHTMLCodes(title)
				title = title.encode('utf-8')

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)

				if control.setting('tv.specials') == 'false' and season == '0':
					raise Exception()

				episode = client.parseDOM(item, 'EpisodeNumber')[0]
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))

				seasoncount = '0'
				# seasoncount = seasons.Seasons.seasonCountParse(season=season, items=result)
				# log_utils.log('seasoncount = %s for title = %s' % (str(seasoncount), str(title)), __name__, log_utils.LOGDEBUG)

				poster = client.parseDOM(item2, 'poster')[0]
				if poster and poster != '':
					poster = '%s%s' % (self.tvdb_image, poster)
				else: poster = '0'

				season_poster = [x for x in artwork if client.parseDOM(x, 'Season')[0] == season]
				try: season_poster = client.parseDOM(season_poster[0], 'BannerPath')[0]
				except: season_poster = ''
				if season_poster != '':
					season_poster = '%s%s' % (self.tvdb_image, season_poster)
				else:
					season_poster = '0'
				season_poster = client.replaceHTMLCodes(season_poster)
				season_poster = season_poster.encode('utf-8')

				banner = client.parseDOM(item2, 'banner')[0]
				if banner and banner != '':
					banner = '%s%s' % (self.tvdb_image, banner)
				else: banner = '0'

				fanart = client.parseDOM(item2, 'fanart')[0]
				if fanart and fanart != '':
					fanart = '%s%s' % (self.tvdb_image, fanart)
				else: fanart = '0'

				thumb = client.parseDOM(item, 'filename')[0]
				if thumb and thumb != '':
					thumb = '%s%s' % (self.tvdb_image, thumb)
				else: thumb = '0'

				if poster != '0':
					pass
				elif fanart != '0':
					poster = fanart
				elif banner != '0':
					poster = banner

				if banner != '0':
					pass
				elif fanart != '0':
					banner = fanart
				elif poster != '0':
					banner = poster

				if thumb != '0':
					pass
				elif fanart != '0':
					thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
				elif poster != '0':
					thumb = poster

				studio = i['studio'] or client.parseDOM(item2, 'Network')[0]

				genre = client.parseDOM(item2, 'Genre')[0]
				genre = [x for x in genre.split('|') if x != '']
				genre = ' / '.join(genre)

				duration = client.parseDOM(item2, 'Runtime')[0] or '0'

				rating = client.parseDOM(item, 'Rating')[0]
				votes = client.parseDOM(item2, 'RatingCount')[0]

				mpaa = client.parseDOM(item2, 'ContentRating')[0]

				director = client.parseDOM(item, 'Director')[0]
				director = [x for x in director.split('|') if x != '']
				director = (' / '.join(director)).encode('utf-8')
				director = client.replaceHTMLCodes(director)

				writer = client.parseDOM(item, 'Writer')[0]
				writer = [x for x in writer.split('|') if x != '']
				writer = (' / '.join(writer)).encode('utf-8')
				writer = client.replaceHTMLCodes(writer)

				castandart = tvdb_v1.parseActors(actors) or []

				plot = client.parseDOM(item, 'Overview')[0]
				if not plot:
					plot = client.parseDOM(item2, 'Overview')[0]
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				values = {'title': title, 'seasoncount': seasoncount, 'season': season, 'episode': episode,
								'year': year, 'tvshowtitle': tvshowtitle, 'tvshowyear': year, 'premiered': premiered,
								'added': added, 'lastplayed': lastplayed, 'status': status, 'studio': studio, 'genre': genre,
								'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director,
								'writer': writer, 'castandart': castandart, 'plot': plot, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb,
								'poster': poster, 'season_poster': season_poster,  'banner': banner, 'fanart': fanart, 'thumb': thumb,
								'snum': i['snum'], 'enum': i['enum'], 'unaired': unaired, 'trailer': trailer, 'episodeIDS': episodeIDS, 'traktProgress': True}

				if not direct:
					values['action'] = 'episodes'

				if 'airday' in i and i['airday'] is not None and i['airday'] != '':
					values['airday'] = i['airday']
				if 'airtime' in i and i['airtime'] is not None and i['airtime'] != '':
					values['airtime'] = i['airtime']
				if 'airzone' in i and i['airzone'] is not None and i['airzone'] != '':
					values['airzone'] = i['airzone']
				self.list.append(values)
			except:
				log_utils.error()
				pass

		items = items[:len(items)]
		threads = []
		for i in items:
			threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]

		return self.list


	def trakt_list(self, url, user, count=False):
		try:
			for i in re.findall('date\[(\d+)\]', url):
				url = url.replace('date[%s]' % i, (self.datetime - datetime.timedelta(days=int(i))).strftime('%Y-%m-%d'))
			q = dict(parse_qsl(urlsplit(url).query))
			q.update({'extended': 'full'})
			q = (urlencode(q)).replace('%2C', ',')
			u = url.replace('?' + urlparse(url).query, '') + '?' + q
			itemlist = []
			items = trakt.getTraktAsJson(u)
		except:
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
				if 'show' not in item or 'episode' not in item:
					continue

				try: title = (item['episode']['title']).encode('utf-8')
				except: title = item['episode']['title']
				if title is None or title == '':
					continue

				season = item['episode']['season']
				season = re.sub('[^0-9]', '', '%01d' % int(season))

				if control.setting('tv.specials') == 'false' and season == '0':
					continue

				episode = item['episode']['number']
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))
				if episode == '0':
					continue

				try: tvshowtitle = (item['show']['title']).encode('utf-8')
				except: tvshowtitle = item['show']['title']
				if tvshowtitle is None or tvshowtitle == '':
					continue

				year = str(item.get('show').get('year'))

				try: progress = max(0, min(1, item['progress'] / 100.0))
				except: progress = None

				imdb = item.get('show', {}).get('ids', {}).get('imdb', '0')
				if imdb == '' or imdb is None or imdb == 'None':
					imdb = '0'
				tmdb = str(item.get('show', {}).get('ids', {}).get('tmdb', 0))
				if tmdb == '' or tmdb is None or tmdb == 'None':
					tmdb = '0'
				tvdb = str(item.get('show', {}).get('ids', {}).get('tvdb', 0))
				if tvdb == '' or tvdb is None or tvdb == 'None':
					tvdb = '0'

				episodeIDS = item.get('episode').get('ids', {})

				premiered = item.get('episode').get('first_aired')

				added = item['episode']['updated_at'] or item.get('show').get('updated_at', '0')
				lastplayed = item.get('watched_at', '0')
				paused_at = item.get('paused_at', '0')

				studio = item.get('show').get('network')
 
				genre = []
				for i in item['show']['genres']:
					genre.append(i.title())
				if genre == []: genre = 'NA'

				duration = str(item['episode']['runtime']) or str(item.get('show').get('runtime'))

				rating = str(item.get('episode').get('rating'))
				votes = str(format(int(item.get('episode').get('votes')),',d'))

				mpaa = item.get('show').get('certification')

				plot = item['episode']['overview'] or item['show']['overview']
				try: plot = plot.encode('utf-8')
				except: pass

				if self.lang != 'en':
					try:
						trans_item = trakt.getTVShowTranslation(imdb, lang=self.lang, season=season, episode=episode,  full=True)
						title = trans_item.get('title') or title
						plot = trans_item.get('overview') or plot
						tvshowtitle = trakt.getTVShowTranslation(imdb, lang=self.lang) or tvshowtitle
					except:
						pass

				try: trailer = control.trailer % item['show']['trailer'].split('v=')[1]
				except: trailer = ''

				values = {'title': title, 'season': season, 'episode': episode, 'tvshowtitle': tvshowtitle, 'year': year, 'premiered': premiered,
							'added': added, 'lastplayed': lastplayed, 'progress': progress, 'paused_at': paused_at, 'status': 'Continuing',
							'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'plot': plot,
							'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'trailer': trailer, 'episodeIDS': episodeIDS, 'next': next}

				if 'airday' in item and not item['airday'] is None and item['airday'] != '':
					values['airday'] = item['airday']
				if 'airtime' in item and not item['airtime'] is None and item['airtime'] != '':
					values['airtime'] = item['airtime']
				if 'airzone' in item and not item['airzone'] is None and item['airzone'] != '':
					values['airzone'] = item['airzone']

				try:
					air = item['show']['airs']
					if 'airday' not in item or item['airday'] is None or item['airday'] == '':
						values['airday'] = air['day']
					if 'airtime' not in item or item['airtime'] is None or item['airtime'] == '':
						values['airtime'] = air['time']
					if 'airzone' not in item or item['airzone'] is None or item['airzone'] == '':
						values['airzone'] = air['timezone']
				except:
					log_utils.error()
					pass

				itemlist.append(values)
				if count:
					self.seasonCount(itemlist, len(itemlist) - 1)

			except:
				log_utils.error()
				pass

		if count:
			self.seasonCountWait()

		itemlist = itemlist[::-1]
		return itemlist


	def trakt_episodes_list(self, url, user, lang, direct=True):
		# from resources.lib.menus import seasons
		self.list = []
		items = self.trakt_list(url, user)
		def items_list(i):
			# try:
				# item = [x for x in self.blist if x['tvdb'] == i['tvdb'] and x['season'] == i['season'] and x['episode'] == i['episode']][0]
				# if item['poster'] == '0':
					# raise Exception()
				# self.list.append(item)
				# return
			# except:
				# pass

			tvshowtitle = i['tvshowtitle']
			year = str(i.get('year'))
			imdb, tmdb, tvdb = i['imdb'], i['tmdb'], i['tvdb']
			trailer = i.get('trailer')
			try:
				url = self.tvdb_info_link % (tvdb, lang)
				data = requests.get(url).content
				zip = zipfile.ZipFile(StringIO.StringIO(data))

				result = zip.read('%s.xml' % lang)
				artwork = zip.read('banners.xml')
				actors = zip.read('actors.xml')
				zip.close()

				result = result.split('<Episode>')
				item = [(re.findall('<SeasonNumber>%01d</SeasonNumber>' % int(i['season']), x),
						re.findall('<EpisodeNumber>%01d</EpisodeNumber>' % int(i['episode']), x), x) for x in result]
				item = [x[2] for x in item if len(x[0]) > 0 and len(x[1]) > 0]
				if not item:
					log_utils.log('bad zip for tvshowtitle = %s: season = %s: episode = %s: tvdb_id = %s: url = %s' % \
							(str(tvshowtitle), str(i['season']), str(i['episode']), str(tvdb), url), __name__, log_utils.LOGDEBUG)
					raise Exception()
				item = item[0]
				item2 = result[0]

				artwork = artwork.split('<Banner>')
				artwork = [x for x in artwork if '<Language>en</Language>' in x and '<BannerType>season</BannerType>' in x]
				artwork = [x for x in artwork if not 'seasonswide' in re.findall('<BannerPath>(.+?)</BannerPath>', x)[0]]

				premiered = i['premiered'] or client.parseDOM(item, 'FirstAired')[0]

				status = client.parseDOM(item2, 'Status')[0]
				if not status:
					status = 'Ended'

				title = client.parseDOM(item, 'EpisodeName')[0]
				title = client.replaceHTMLCodes(title)
				title = title.encode('utf-8')

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)

				if control.setting('tv.specials') == 'false' and season == '0':
					raise Exception()

				episode = client.parseDOM(item, 'EpisodeNumber')[0]
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))

				seasoncount = '0'
				# seasoncount = seasons.Seasons.seasonCountParse(season=season, items=result)

				added = i['added']
				lastplayed = i['lastplayed']

				try: progress = i['progress']
				except: progress = None
				paused_at = i['paused_at']

				episodeIDS = i['episodeIDS']

				poster = client.parseDOM(item2, 'poster')[0]
				if poster and poster != '':
					poster = '%s%s' % (self.tvdb_image, poster)
				else: poster = '0'

				banner = client.parseDOM(item2, 'banner')[0]
				if banner and banner != '':
					banner = '%s%s' % (self.tvdb_image, banner)
				else: banner = '0'

				fanart = client.parseDOM(item2, 'fanart')[0]
				if fanart and fanart != '':
					fanart = '%s%s' % (self.tvdb_image, fanart)
				else: fanart = '0'

				thumb = client.parseDOM(item, 'filename')[0]
				if thumb and thumb != '':
					thumb = '%s%s' % (self.tvdb_image, thumb)
				else: thumb = '0'

				season_poster = [x for x in artwork if client.parseDOM(x, 'Season')[0] == season]
				try:
					season_poster = client.parseDOM(season_poster[0], 'BannerPath')[0]
				except:
					season_poster = ''
				if season_poster != '':
					season_poster = '%s%s' % (self.tvdb_image, season_poster)
				else:
					season_poster = '0'
				season_poster = client.replaceHTMLCodes(season_poster)
				season_poster = season_poster.encode('utf-8')

				if poster != '0':
					pass
				elif fanart != '0':
					poster = fanart
				elif banner != '0':
					poster = banner

				if banner != '0':
					pass
				elif fanart != '0':
					banner = fanart
				elif poster != '0':
					banner = poster

				if thumb != '0':
					pass
				elif fanart != '0':
					thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
				elif poster != '0':
					thumb = poster

				studio = i['studio'] or client.parseDOM(item2, 'Network')[0]

				if 'genre' in i and i['genre'] is not None and i['genre'] != 'NA':
					genre = i['genre'] 
				else:
					genre = client.parseDOM(item2, 'Genre')[0]
					genre = [x for x in genre.split('|') if x != '']
					genre = ' / '.join(genre)

				duration = i['duration'] or client.parseDOM(item2, 'Runtime')[0]

				rating = i['rating'] or client.parseDOM(item, 'Rating')[0]
				votes = i['votes'] or client.parseDOM(item2, 'RatingCount')[0]

				mpaa = i['mpaa'] or client.parseDOM(item2, 'ContentRating')[0]

				director = client.parseDOM(item, 'Director')[0]
				director = [x for x in director.split('|') if x != '']
				director = (' / '.join(director)).encode('utf-8')
				director = client.replaceHTMLCodes(director)

				writer = client.parseDOM(item, 'Writer')[0]
				writer = [x for x in writer.split('|') if x != '']
				writer = (' / '.join(writer)).encode('utf-8')
				writer = client.replaceHTMLCodes(writer)

				castandart = tvdb_v1.parseActors(actors) or []

				plot = client.parseDOM(item, 'Overview')[0]
				if not plot:
					plot = client.parseDOM(item2, 'Overview')[0]
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				values = {'title': title, 'seasoncount': seasoncount, 'season': season, 'episode': episode, 'year': year, 'tvshowtitle': tvshowtitle, 'tvshowyear': year,
								'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa,
								'director': director, 'writer': writer, 'castandart': castandart, 'plot': plot, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'added': added, 'lastplayed': lastplayed,
								'progress': progress, 'paused_at': paused_at, 'poster': poster, 'season_poster': season_poster, 'banner': banner, 'fanart': fanart,
								'thumb': thumb, 'trailer': trailer, 'episodeIDS': episodeIDS}

				if not direct:
					values['action'] = 'episodes'

				try:
					if 'airday' in i and i['airday'] is not None and i['airday'] != '':
						values['airday'] = i['airday']
					if 'airtime' in i and i['airtime'] is not None and i['airtime'] != '':
						values['airtime'] = i['airtime']
					if 'airzone' in i and i['airzone'] is not None and i['airzone'] != '':
						values['airzone'] = i['airzone']
				except:
					log_utils.error()
					pass

				self.list.append(values)
			except:
				log_utils.error()
				pass

		items = items[:len(items)]
		threads = []
		for i in items:
			threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]
		return self.list


	def tvmaze_list(self, url, limit, count=False):
		try:
			result = client.request(url, error=True)
			items = json.loads(result)
		except:
			return

		itemlist = []
		for item in items:
			try:
				if not item['show']['language']:
					continue
				if 'english' not in item['show']['language'].lower():
					continue

				if limit and 'scripted' not in item['show']['type'].lower():
					continue

				try: title = (item.get('name')).encode('utf-8')
				except: title = item.get('name')

				season = item['season']
				if not season:
					continue
				season = re.sub('[^0-9]', '', '%01d' % int(season))

				if control.setting('tv.specials') == 'false' and season == '0':
					continue

				episode = item['number']
				if episode is None:
					continue
				episode = re.sub('[^0-9]', '', '%01d' % int(episode))

				premiered = item.get('airdate', '0')

				year = str(item.get('show').get('premiered', '0'))
				year = re.search(r"(\d{4})", year).group(1)

				try: tvshowtitle = (item.get('show', {}).get('name')).encode('utf-8')
				except: tvshowtitle = item.get('show', {}).get('name')

				tvshowyear = item.get('show').get('year') or year

				imdb = item.get('show', {}).get('externals', {}).get('imdb', '0')
				if imdb == '' or imdb is None or imdb == 'None':
					imdb = '0'
				if not imdb.startswith('tt'):
					imdb = '0'
				# TVMaze does not have tmdb in their api
				tmdb = '0'

				tvdb = str(item.get('show').get('externals').get('thetvdb', '0'))
				if tvdb == '' or tvdb is None or tvdb == 'None':
					tvdb = '0'

				if (imdb == '0' or tvdb == '0') and control.setting('tvshows.calendar.extended') == 'true':
					try:
						trakt_ids = trakt.SearchTVShow(quote_plus(tvshowtitle), year, full=False)
						if trakt_ids is None:
							raise Exception()
						trakt_ids = trakt_ids[0]['show']['ids']

						if imdb == '0':
							imdb = trakt_ids.get('imdb', '0')
							if imdb == '' or imdb is None or imdb == 'None':
								imdb = '0'
							if not imdb.startswith('tt'):
								imdb = '0'

						if tmdb == '0':
							tmdb = str(trakt_ids.get('tmdb', '0'))
							if tmdb == '' or tmdb is None or tmdb == 'None':
								tmdb = '0'

						if tvdb == '0':
							tvdb = str(trakt_ids.get('tvdb', '0'))
							if tvdb == '' or tvdb is None or tvdb == 'None':
								tvdb = '0'
					except:
						log_utils.error()
						pass

# ### episode IDS
				episodeIDS = {}
				if control.setting('enable.upnext') == 'true':
					episodeIDS = trakt.getEpisodeSummary(imdb, season, episode, full=False) or {}
					if episodeIDS != {}:
						episodeIDS = episodeIDS.get('ids', {})
##------------------

				try: poster = item['show']['image']['original']
				except: poster = '0'
				try: thumb = item['image']['original']
				except: thumb = '0'

				studio = item.get('show').get('webChannel') or item.get('show').get('network')
				studio = studio.get('name') or None

				genre = []
				for i in item['show']['genres']:
					genre.append(i.title())
				if genre == []: genre = 'NA'

				duration = str(item.get('show', {}).get('runtime', '0'))

				rating = str(item.get('show', {}).get('rating', {}).get('average', '0'))

				try: status = str(item.get('show', {}).get('status', '0'))
				except: status = 'Continuing'

				try:
					plot = item.get('show', {}).get('summary', '0')
					plot = re.sub('<.+?>|</.+?>|\n', '', plot)
				except:
					plot = '0'

				airday = ''
				airtime = item['airtime'] or ''
				# airtime = item['show']['schedule']['time'] or ''
				try:
					airzone = item['show']['network']['country']['timezone']
				except:
					airzone = ''

				values = {'extended': True, 'title': title, 'season': season, 'episode': episode, 'year': year, 'tvshowtitle': tvshowtitle, 'tvshowyear': tvshowyear,
								'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'plot': plot,
								'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'airday': airday, 'airtime': airtime, 'airzone': airzone, 'poster': poster,
								'season_poster': poster, 'thumb': thumb, 'fanart': thumb, 'episodeIDS': episodeIDS, 'ForceAirEnabled': True}

				itemlist.append(values)
				# if count:
					# self.seasonCount(itemlist, len(itemlist) - 1)
			except:
				log_utils.error()
				pass

		# if count:
			# self.seasonCountWait()

		if control.setting('tvshows.calendar.extended') == 'false':
			return itemlist

		def items_list(i):
			self.list = []
			tvshowtitle = i['tvshowtitle']
			premiered = i['premiered']
			year = i['year']
			imdb, tmdb, tvdb = i['imdb'], i['tmdb'], i['tvdb']
			try:
				url = self.tvdb_info_link % (tvdb, self.lang)
				data = requests.get(url).content
				zip = zipfile.ZipFile(StringIO.StringIO(data))
				result = zip.read('%s.xml' % self.lang)
				artwork = zip.read('banners.xml')
				actors = zip.read('actors.xml')
				zip.close()

				result = result.split('<Episode>')
				try:
					item = [(re.findall('<SeasonNumber>%01d</SeasonNumber>' % int(i['season']), x), re.findall('<EpisodeNumber>%01d</EpisodeNumber>' % int(i['episode']), x), x) for x in result]
					item = [x[2] for x in item if len(x[0]) > 0 and len(x[1]) > 0][0]
				except:
					item = None
					pass
				item2 = result[0]

				try:
					artwork = artwork.split('<Banner>')
					artwork = [x for x in artwork if '<Language>en</Language>' in x and '<BannerType>season</BannerType>' in x]
					artwork = [x for x in artwork if not 'seasonswide' in re.findall('<BannerPath>(.+?)</BannerPath>', x)[0]]
				except:
					artwork = '0'

				status = i['status'] or client.parseDOM(item2, 'Status')[0]
				if not status:
					status = 'Ended'

				title = i['title']
				season = i['season']
				episode = i['episode']

				seasoncount = '0'
				# seasoncount = seasons.Seasons.seasonCountParse(season=season, items=result)

				episodeIDS = i['episodeIDS']

				poster = i['poster']
				poster2 = client.parseDOM(item2, 'poster')[0]
				if poster2 and poster2 != '':
					poster2 = '%s%s' % (self.tvdb_image, poster2)
				else: poster2 = None
				poster = poster2 or poster or '0'

				banner = client.parseDOM(item2, 'banner')[0]
				if banner and banner != '':
					banner = '%s%s' % (self.tvdb_image, banner)
				else: banner = '0'

				fanart = client.parseDOM(item2, 'fanart')[0]
				if fanart and fanart != '':
					fanart = '%s%s' % (self.tvdb_image, fanart)
				else: fanart = '0'

				thumb = i['thumb']
				if item:
					thumb2 = client.parseDOM(item, 'filename')[0]
					if thumb2 and thumb2 != '':
						thumb2 = '%s%s' % (self.tvdb_image, thumb2)
					else: thumb2 = None
					thumb = thumb2 or thumb or '0'

				try:
					season_poster = [x for x in artwork if client.parseDOM(x, 'Season')[0] == season]
					season_poster = client.parseDOM(season_poster[0], 'BannerPath')[0]
					season_poster = '%s%s' % (self.tvdb_image, season_poster)
				except:
					season_poster = poster

				if poster != '0': pass
				elif fanart != '0': poster = fanart
				elif banner != '0': poster = banner

				if banner != '0': pass
				elif fanart != '0': banner = fanart
				elif poster != '0': banner = poster

				if thumb != '0': pass
				elif fanart != '0': thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
				elif poster != '0': thumb = poster

				studio = i['studio'] or client.parseDOM(item2, 'Network')[0]

				if 'genre' in i and i['genre'] is not None and i['genre'] != 'NA':
					genre = i['genre'] 
				else:
					genre = client.parseDOM(item2, 'Genre')[0]
					genre = [x for x in genre.split('|') if x != '']
					genre = ' / '.join(genre)

				duration = i['duration'] or client.parseDOM(item2, 'Runtime')[0]

				rating = i['rating']
				votes = client.parseDOM(item2, 'RatingCount')[0]

				mpaa = client.parseDOM(item2, 'ContentRating')[0]

				plot = i['plot']
				director = writer = '0'
				if item:
					premiered = premiered or client.parseDOM(item, 'FirstAired')[0] or '0'

					director = client.parseDOM(item, 'Director')[0]
					director = [x for x in director.split('|') if x != '']
					director = (' / '.join(director)).encode('utf-8')
					director = client.replaceHTMLCodes(director)

					writer = client.parseDOM(item, 'Writer')[0]
					writer = [x for x in writer.split('|') if x != '']
					writer = (' / '.join(writer)).encode('utf-8')
					writer = client.replaceHTMLCodes(writer)

					rating = rating or client.parseDOM(item, 'Rating')[0]

					plot2 = client.parseDOM(item, 'Overview')[0]
					if not plot2:
						plot2 = client.parseDOM(item2, 'Overview')[0]
					plot2 = client.replaceHTMLCodes(plot2)
					plot2 = plot2.encode('utf-8')
					plot = plot2 or plot

				castandart = tvdb_v1.parseActors(actors) or []

				airday = i['airday'] or ''
				airtime = i['airtime'] or client.parseDOM(item2, 'Airs_Time')[0] or ''
				airzone = i['airzone'] or ''

				values = {'extended': True, 'title': title, 'seasoncount': seasoncount, 'season': season, 'episode': episode, 'year': year, 'tvshowtitle': tvshowtitle,
								'tvshowyear': year, 'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating,
								'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'castandart': castandart, 'plot': plot, 'airday': airday, 'airtime': airtime,
								'airzone': airzone, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'poster': poster, 'season_poster': season_poster, 'banner': banner,
								'fanart': fanart, 'thumb': thumb, 'episodeIDS': episodeIDS, 'ForceAirEnabled': True}

				if disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_tvshow_art, 168, tvdb)
					if extended_art:
						values.update(extended_art)
						# meta.update(values)

				# values = dict((k,v) for k, v in values.iteritems() if v != '0')
				self.list.append(values)
			except:
				log_utils.error()
				pass

		items = itemlist[:len(itemlist)]
		threads = []
		for i in items:
			threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]

		self.list = sorted(self.list, key=lambda k: k['airtime'], reverse=False)
		return self.list


	def episodeDirectory(self, items, unfinished=False, next=True):
		if not items:
			control.hide()
			control.notification(title=32326, message=33049)
			sys.exit()

		# Retrieve additional metadata if not super info was retireved (eg: Trakt lists, such as Unfinished and History)
		try:
			if 'extended' not in items[0] or not items[0]['extended']:
				from resources.lib.menus import tvshows
				show = tvshows.TVshows(type=self.type)
				show.list = copy.deepcopy(self.list)
				show.worker()
				for i in range(len(self.list)):
					self.list[i] = dict(show.list[i].items() + self.list[i].items())
		except:
			log_utils.error()
			pass

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		is_widget = 'plugin' not in control.infoLabel('Container.PluginName')
		if not is_widget:
			control.playlist.clear()

		settingFanart = control.setting('fanart')
		addonPoster = control.addonPoster()
		addonFanart = control.addonFanart()
		addonBanner = control.addonBanner()

		traktProgress = False if 'traktProgress' not in items[0] else True
		if traktProgress and control.setting('tvshows.direct') == 'false':
			progressMenu = control.lang(32015)
		else:
			progressMenu = control.lang(32016)

		if traktProgress:
			multi = True
		else:
			try: multi = [i['tvshowtitle'] for i in items]
			except: multi = []
			multi = len([x for y, x in enumerate(multi) if x not in multi[:y]])
			multi = True if multi > 1 else False
			try:
				if '/users/me/history/' in items[0]['next']: multi = True
			except: pass

		try: sysaction = items[0]['action']
		except: sysaction = ''

		# indicators = playcount.getTVShowIndicators()
		indicators = playcount.getTVShowIndicators(refresh=True)

		isFolder = False if sysaction != 'episodes' else True
		isPlayable = 'false'
		if 'plugin' not in control.infoLabel('Container.PluginName'):
			isPlayable = 'true'
		elif control.setting('enable.upnext') == 'true' or control.setting('hosts.mode') != '1' :
			isPlayable = 'true'

		multi_unwatchedEnabled = control.setting('multi.unwatched.enabled') == 'true'
		playlistcreate = control.setting('auto.playlistcreate') == 'true'

		airEnabled = control.setting('tvshows.air.enabled') if 'ForceAirEnabled' not in items[0] else 'true'
		if airEnabled == 'true':
			airZone = control.setting('tvshows.air.zone')
			airLocation = control.setting('tvshows.air.location')
			airFormat = control.setting('tvshows.air.format')
			airFormatDay = control.setting('tvshows.air.day')
			airFormatTime = control.setting('tvshows.air.time')
			airBold = control.setting('tvshows.air.bold')
			airLabel = control.lang(35032)

		if control.setting('hosts.mode') == '2' or control.setting('enable.upnext') == 'true':
			playbackMenu = control.lang(32063)
		else:
			playbackMenu = control.lang(32064)

		if trakt.getTraktIndicatorsInfo():
			watchedMenu = control.lang(32068)
			unwatchedMenu = control.lang(32069)
		else:
			watchedMenu = control.lang(32066)
			unwatchedMenu = control.lang(32067)

		traktManagerMenu = control.lang(32070)

		playlistManagerMenu = control.lang(35522)
		queueMenu = control.lang(32065)

		tvshowBrowserMenu = control.lang(32071)
		addToLibrary = control.lang(32551)

		for i in items:
			try:
				tvshowtitle, title, imdb, tmdb, tvdb = i.get('tvshowtitle'), i.get('title'), i.get('imdb', '0'), i.get('tmdb', '0'), i.get('tvdb', '0')
				year, season, episode, premiered = i['year'], i['season'], i['episode'], i['premiered']
				trailer = i.get('trailer')
				runtime = i.get('duration')
				tvshowyear = i.get('tvshowyear')

				if 'label' not in i: i['label'] = title
				if i['label'] == '0': label = '%sx%02d . %s %s' % (season, int(episode), 'Episode', episode)
				else: label = '%sx%02d . %s' % (season, int(episode), i['label'])

				if multi: label = '%s - %s' % (tvshowtitle, label)
				try: labelProgress = label + '[COLOR %s]  [%s][/COLOR]' % (control.getColor(control.setting('highlight.color')), str(round(float(i['progress'] * 100), 1)) + '%')
				except: labelProgress = label

				try:
					if i['unaired'] == 'true': labelProgress = '[COLOR %s][I]%s[/I][/COLOR]' % (self.unairedcolor, labelProgress)
				except: pass

				systitle = quote_plus(title)
				systvshowtitle = quote_plus(tvshowtitle)
				syspremiered = quote_plus(premiered)

				try: seasoncount = i['seasoncount']
				except: seasoncount = None

				meta = dict((k, v) for k, v in i.iteritems() if v != '0')
				meta.update({'code': imdb, 'imdbnumber': imdb})
				meta.update({'mediatype': 'episode'})
				meta.update({'tag': [imdb, tvdb]})

				# Some descriptions have a link at the end that. Remove it.
				try:
					plot = meta['plot']
					index = plot.rfind('See full summary')
					if index >= 0: plot = plot[:index]
					plot = plot.strip()
					if re.match('[a-zA-Z\d]$', plot): plot += ' ...'
					meta['plot'] = plot
				except: pass

				try: meta.update({'duration': str(int(runtime) * 60)})
				except: pass
				try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
				except: pass
				try: meta.update({'title': i['label']})
				except: pass
				try: meta.update({'year': re.findall('(\d{4})', premiered)[0]}) #careful, arg year and meta year will be different
				except: pass

				try:
					if 'tvshowyear' not in meta:
						meta.update({'tvshowyear': year}) # Kodi uses the year (the year the show started) as the year for the episode. Change it from the premiered date.
				except: pass

				if airEnabled == 'true':
					air = []
					airday = None
					airtime = None
					if 'airday' in meta and not meta['airday'] is None and meta['airday'] != '':
						airday = meta['airday']
					if 'airtime' in meta and not meta['airtime'] is None and meta['airtime'] != '':
						airtime = meta['airtime']
						if 'airzone' in meta and not meta['airzone'] is None and meta['airzone'] != '':
							if airZone == '1':
								zoneTo = meta['airzone']
							elif airZone == '2':
								zoneTo = 'utc'
							else:
								zoneTo = 'local'

							if airFormatTime == '1':
								formatOutput = '%I:%M'
							elif airFormatTime == '2':
								formatOutput = '%I:%M %p'
							else:
								formatOutput = '%H:%M'

							abbreviate = airFormatDay == '1'
							airtime = tools.Time.convert(stringTime=airtime, stringDay=airday, zoneFrom=meta['airzone'],
														zoneTo=zoneTo, abbreviate=abbreviate, formatOutput=formatOutput)
							if airday:
								airday = airtime[1]
								airtime = airtime[0]
					if airday: air.append(airday)
					if airtime: air.append(airtime)
					if len(air) > 0:
						if airFormat == '0':
							air = airtime
						elif airFormat == '1':
							air = airday
						elif airFormat == '2':
							air = air = ' '.join(air)

						if airLocation == '0' or airLocation == '1':
							air = '[COLOR skyblue][%s][/COLOR]' % air
						if airBold == 'true': air = '[B]%s[/B]' % str(air)
						if airLocation == '0':
							labelProgress = '%s %s' % (air, labelProgress)
						elif airLocation == '1':
							labelProgress = '%s %s' % (labelProgress, air)
						elif airLocation == '2':
							meta['plot'] = '%s%s\r\n%s' % (airLabel, air, meta['plot'])
						elif airLocation == '3':
							meta['plot'] = '%s\r\n%s%s' % (meta['plot'], airLabel, air)

				poster1 = meta.get('poster')
				poster2 = meta.get('poster2')
				poster3 = meta.get('poster3')
				poster = poster3 or poster2 or poster1 or addonPoster

				season_poster = meta.get('season_poster') or poster

				fanart = '0'
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
				art.update({'poster': season_poster, 'tvshow.poster': poster, 'season.poster': season_poster, 'fanart': fanart, 'icon': icon,
									'thumb': thumb, 'banner': banner, 'clearlogo': clearlogo, 'clearart': clearart, 'landscape': landscape})

				remove_keys = ('poster2', 'poster3', 'fanart2', 'fanart3', 'banner2', 'banner3', 'trailer')
				for k in remove_keys:
					meta.pop(k, None)
				meta.update({'poster': poster, 'fanart': fanart, 'banner': banner})

####-Context Menu and Overlays-####
				cm = []
				if self.traktCredentials:
					cm.append((traktManagerMenu, 'RunPlugin(%s?action=tools_traktManager&name=%s&imdb=%s&tvdb=%s&season=%s&episode=%s)' % (
										sysaddon, systvshowtitle, imdb, tvdb, season, episode)))
				try:
					overlay = int(playcount.getEpisodeOverlay(indicators, imdb, tvdb, season, episode))
					watched = (overlay == 7)

					# # Skip episodes marked as watched for the unfinished and onDeck lists.
					# try: if unfinished and watched and not i['progress'] is None: continue
					# except: pass

					if watched:
						meta.update({'playcount': 1, 'overlay': 7})
						cm.append((unwatchedMenu, 'RunPlugin(%s?action=playcount_Episode&name=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&query=6)' % (
												sysaddon, systvshowtitle, imdb, tvdb, season, episode)))
					else:
						meta.update({'playcount': 0, 'overlay': 6})
						cm.append((watchedMenu, 'RunPlugin(%s?action=playcount_Episode&name=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&query=7)' % (
												sysaddon, systvshowtitle, imdb, tvdb, season, episode)))
				except: pass

				sysmeta = quote_plus(json.dumps(meta))
				sysart = quote_plus(json.dumps(art))
				syslabelProgress = quote_plus(labelProgress)

				url = '%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&meta=%s' % (
										sysaddon, systitle, year, imdb, tmdb, tvdb, season, episode, systvshowtitle, syspremiered, sysmeta)
				sysurl = quote_plus(url)

				Folderurl = '%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s' % (
										sysaddon, systvshowtitle, year, imdb, tmdb, tvdb, season, episode)
				if isFolder:
					if traktProgress:
						if control.setting('hosts.mode') == '1' and control.setting('enable.upnext') != 'true':
							cm.append((progressMenu, 'RunPlugin(%s)' % url))
						elif control.setting('hosts.mode') != '1' or control.setting('enable.upnext') == 'true':
							cm.append((progressMenu, 'PlayMedia(%s)' % url))
					url = '%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s' % (
										sysaddon, systvshowtitle, year, imdb, tmdb, tvdb, season, episode)

				cm.append((playlistManagerMenu, 'RunPlugin(%s?action=playlist_Manager&name=%s&url=%s&meta=%s&art=%s)' % (
									sysaddon, syslabelProgress, sysurl, sysmeta, sysart)))
				cm.append((queueMenu, 'RunPlugin(%s?action=playlist_QueueItem&name=%s)' % (sysaddon, syslabelProgress)))

				if multi:
					cm.append((tvshowBrowserMenu, 'Container.Update(%s?action=seasons&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s,return)' % (
									sysaddon, systvshowtitle, year, imdb, tvdb)))

				if not isFolder:
					if traktProgress:
						cm.append((progressMenu, 'Container.Update(%s)' % Folderurl))
					cm.append((playbackMenu, 'RunPlugin(%s?action=alterSources&url=%s&meta=%s)' % (sysaddon, sysurl, sysmeta)))
					if control.setting('hosts.mode') == '1' and control.setting('enable.upnext') != 'true':
						cm.append(('Rescrape Item', 'RunPlugin(%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&meta=%s&rescrape=true)' % (
											sysaddon, systitle, year, imdb, tmdb, tvdb, season, episode, systvshowtitle, syspremiered, sysmeta)))
					elif control.setting('hosts.mode') != '1' or control.setting('enable.upnext') == 'true':
						cm.append(('Rescrape Item', 'PlayMedia(%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&meta=%s&rescrape=true)' % (
											sysaddon, systitle, year, imdb, tmdb, tvdb, season, episode, systvshowtitle, syspremiered, sysmeta)))

				if control.setting('library.service.update') == 'true':
					cm.append((addToLibrary, 'RunPlugin(%s?action=library_tvshowToLibrary&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s)' % (
											sysaddon, systvshowtitle, year, imdb, tmdb, tvdb)))
				cm.append((control.lang(32611), 'RunPlugin(%s?action=cache_clearSources&opensettings=false)' % sysaddon))
				cm.append(('PlayAll', 'RunPlugin(%s?action=playAll)' % sysaddon))
				cm.append(('[COLOR red]Venom Settings[/COLOR]', 'RunPlugin(%s?action=tools_openSettings)' % sysaddon))
####################################

				if trailer: meta.update({'trailer': trailer})
				else: meta.update({'trailer': '%s?action=trailer&type=%s&name=%s&year=%s&imdb=%s' % (sysaddon, 'show', quote_plus(label), year, imdb)})

				item = control.item(label=labelProgress)
				if 'castandart' in i: item.setCast(i['castandart'])
				if 'episodeIDS' in i: item.setUniqueIDs(i['episodeIDS'])

				if multi and multi_unwatchedEnabled:
					if 'ForceAirEnabled' not in i:
						count = playcount.getShowCount(indicators, imdb, tvdb)
						if count:
							item.setProperty('TotalEpisodes', str(count['total']))
							item.setProperty('WatchedEpisodes', str(count['watched']))
							item.setProperty('UnWatchedEpisodes', str(count['unwatched']))
				# if 'total_seasons' in meta:
					# item.setProperty('TotalSeasons', str(meta.get('total_seasons')))

				item.setArt(art)
				item.setProperty('IsPlayable', isPlayable)
				if is_widget: item.setProperty('isVenom_widget', 'true')
				item.setProperty('tvshow.tmdb_id', tmdb)

				from resources.lib.modules.player import Bookmarks
				blabel = tvshowtitle + ' S%02dE%02d' % (int(season), int(episode))
				resumetime = Bookmarks().get(name=blabel, imdb=imdb, tmdb=tmdb, tvdb=tvdb, season=season, episode=episode, year=str(year), runtime=runtime, ck=True)
				# item.setProperty('totaltime', str(meta.get('duration'))) # Adding this property causes the Kodi bookmark CM items to be added
				item.setProperty('resumetime', str(resumetime))
				item.setProperty('venom_resumetime', str(resumetime))
				try:
					watched_percent = int(float(resumetime) / float(meta.get('duration', '0')) * 100)
					item.setProperty('percentplayed', str(watched_percent))
				except:
					pass
				item.setInfo(type='video', infoLabels=control.metadataClean(meta))
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				item.addContextMenuItems(cm)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

				if playlistcreate:
					control.playlist.add(url=url, listitem=item)
			except:
				log_utils.error()
				pass

		if next:
			try:
				url = items[0]['next']
				if not url: raise Exception()

				nextMenu = control.lang(32053)
				url_params = dict(parse_qsl(url))

				if 'imdb.com' in url:
					start = int(url_params.get('start'))
					page = '  [I](%s)[/I]' % str(((start - 1) / self.count) + 1)
				else:
					page = url_params.get('page')
					page = '  [I](%s)[/I]' % page
				nextMenu = '[COLOR skyblue]' + nextMenu + page + '[/COLOR]'

				if '/users/me/history/' in url:
					url = '%s?action=calendar&url=%s' % (sysaddon, quote_plus(url))

				item = control.item(label=nextMenu)
				icon = control.addonNext()
				item.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'banner': icon})
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				pass

		# Show multi episodes as show, in order to display unwatched count if enabled.
		if multi and multi_unwatchedEnabled:
			control.content(syshandle, 'tvshows')
			control.directory(syshandle, cacheToDisc=True)
			views.setView('tvshows', {'skin.estuary': 55, 'skin.confluence': 500})
		else:
			control.content(syshandle, 'episodes')
			control.directory(syshandle, cacheToDisc=True)
			views.setView('episodes', {'skin.estuary': 55, 'skin.confluence': 504})


	def addDirectory(self, items, queue=False):
		if not items:
			control.hide()
			control.notification(title=32326, message=33049)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		addonThumb = control.addonThumb()
		artPath = control.artPath()
		queueMenu = control.lang(32065)

		for i in items:
			try:
				name = i['name']

				if i['image'].startswith('http'): thumb = i['image']
				elif artPath: thumb = control.joinPath(artPath, i['image'])
				else: thumb = addonThumb

				icon = i.get('icon', 0)
				if not icon: icon = 'DefaultFolder.png'

				url = '%s?action=%s' % (sysaddon, i['action'])
				try: url += '&url=%s' % quote_plus(i['url'])
				except: pass

				cm = []
				if queue:
					cm.append((queueMenu, 'RunPlugin(%s?action=playlist_QueueItem)' % sysaddon))
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