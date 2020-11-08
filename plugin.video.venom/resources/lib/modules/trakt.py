# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

import json
import imp
import re
import threading
import time
try:
	from urlparse import urljoin
except:
	from urllib.parse import urljoin

from resources.lib.modules import cache
from resources.lib.modules import cleandate
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import utils

from resources.lib.extensions import database

BASE_URL = 'https://api.trakt.tv'
V2_BASE_URL = 'https://api-v2launch.trakt.tv'

# Venom trakt app
# V2_API_KEY = 'c622fa66e6cdd783b23f2fc1a1abedc1f1e6ea739d8755248487d1dcfeda66e5'
# CLIENT_SECRET = '3430dbd20bd3eb55c0f4e3dc05c7cbbadaf1fd4b8e2a572f4200e482a2041bd8'

# My Accounts trakt app
V2_API_KEY = '1ff09b52d009f286be2d9bdfc0314c688319cbf931040d5f8847e7694a01de42'
CLIENT_SECRET = '0c5134e5d15b57653fefed29d813bfbd58d73d51fb9bcd6442b5065f30c4d4dc'

REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

databaseName = control.cacheFile
databaseTable = 'trakt'


def getTrakt(url, post=None, cache=True, check=False, timestamp=None, extended=False, direct=False, authentication=None):
	try:
		if not url.startswith(BASE_URL):
			url = urljoin(BASE_URL, url)

		if authentication:
			valid = True
			token = authentication['token']
			refresh = authentication['refresh']
		else:
			valid = getTraktCredentialsInfo()
			token = control.setting('trakt.token')
			refresh = control.setting('trakt.refresh')

		headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': '2'}
		if post: post = json.dumps(post)
		if direct or not valid:
			result = client.request(url, post=post, headers=headers)
			return result

		headers['Authorization'] = 'Bearer %s' % token
		result = client.request(url, post=post, headers=headers, output='extended', error=True)
		if result and not (result[1] == '401' or result[1] == '405'):
			if check: _cacheCheck()
			if extended: return result[0], result[2]
			else: return result[0]

		try: code = str(result[1])
		except: code = ''
		if code.startswith('5') or (result and isinstance(result, basestring) and '<html' in result) or not result:
			return _error(url=url, post=post, timestamp=timestamp, message=33676)

		oauth = urljoin(BASE_URL, '/oauth/token')
		opost = {'client_id': V2_API_KEY, 'client_secret': CLIENT_SECRET, 'redirect_uri': REDIRECT_URI, 'grant_type': 'refresh_token', 'refresh_token': refresh}

		result = client.request(oauth, post=json.dumps(opost), headers=headers, error=True)
		try: code = str(result[1])
		except: code = ''

		if code.startswith('5') or not result or (result and isinstance(result, basestring) and '<html' in result):
			return _error(url=url, post=post, timestamp=timestamp, message=33676)
		elif result and code in ['404']:
			return _error(url=url, post=post, timestamp=timestamp, message=33786)
		elif result and code in ['401', '405']:
			return _error(url=url, post=post, timestamp=timestamp, message=33677)

		result = json.loads(result)
		if 'error' in result and result['error'] == 'invalid_grant':
			return _error(url=url, post=post, timestamp=timestamp, message='Please Re-Authorize Trakt')

		token, refresh = result['access_token'], result['refresh_token']
		control.setSetting(id='trakt.token', value=token)
		control.setSetting(id='trakt.refresh', value=refresh)

		control.addon('script.module.myaccounts').setSetting('trakt.token', token)
		control.addon('script.module.myaccounts').setSetting('trakt.refresh', refresh)

		headers['Authorization'] = 'Bearer %s' % token
		result = client.request(url, post=post, headers=headers, output='extended')
		if check:
			_cacheCheck()

		if extended:
			return result[0], result[2]
		else: return result[0]
	except:
		log_utils.error()
	return None


def getTraktAsJson(url, post=None, authentication=None):
	try:
		res_headers = {}
		r = getTrakt(url=url, post=post, extended=True, authentication=authentication)
		if isinstance(r, tuple) and len(r) == 2:
			res_headers = r[1]
			r = r[0]
		# log_utils.log('r = %s' % r, __name__, log_utils.LOGDEBUG)
		if not r:	return
		r = utils.json_loads_as_str(r)
		res_headers = dict((k.lower(), v) for k, v in res_headers.iteritems())
		if 'x-sort-by' in res_headers and 'x-sort-how' in res_headers:
			r = sort_list(res_headers['x-sort-by'], res_headers['x-sort-how'], r)
		return r
	except:
		log_utils.error()
		pass


def _error(url, post, timestamp, message):
	# log_utils.log('message = %s' % message, __name__, log_utils.LOGDEBUG)
	try:
		_cache(url=url, post=post, timestamp=timestamp)
		if control.setting('trakt.server.notifications') == 'true':
			control.notification(title=32315, message=message)
		control.hide()
		return None
	except:
		log_utils.error()
		pass


def _cache(url, post=None, timestamp=None):
	try:
		# Only cache the requests that change something on the Trakt account.
		# Trakt uses JSON post data to set things and only uses GET parameters to retrieve things.
		if not post: return None
		data = database.Database(databaseName, connect=True)
		_cacheCreate(data)
		# post parameter already json.dumps from getTrakt.
		post = ('"%s"' % post.replace('"', '""').replace("'", "''")) if post else data._null()

		if not timestamp:
			timestamp = int(time.time())

		data._insert('''
			INSERT INTO %s (time, link, data)
			VALUES (%d, "%s", %s);
			''' % (databaseTable, timestamp, url, post)
			, commit = True
		)
		data._close()
	except:
		log_utils.error()


def _cacheCreate(data):
	try:
		data._create('''
		CREATE TABLE IF NOT EXISTS %s
		(
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			time INTEGER,
			link TEXT,
			data TEXT
			);
			''' % (databaseTable)
		)
	except:
		log_utils.error()
		pass


def _cacheCheck():
	thread = threading.Thread(target=_cacheProcess)
	thread.start()


def _cacheProcess():
	data = database.Database(databaseName, connect=True)
	data._lock()
	_cacheCreate(data)
	data._unlock()
	try:
		while True:
			# Execute the select and delete as atomic operations.
			data._lock()
			result = data._selectSingle('SELECT id, time, link, data FROM %s ORDER BY time ASC LIMIT 1;' % (databaseTable))
			if not result: raise Exception()
			data._delete('DELETE FROM %s WHERE id IS %d;' % (databaseTable, result[0]), commit = True)
			data._unlock()
			result = getTrakt(url = result[2], post = json.loads(result[3]) if result[3] else None, cache=True, check=False, timestamp=result[1])
	except:
		data._unlock()
	data._close()


def _cacheClear():
	try:
		data = database.Database(databaseName, connect=True)
		data._drop(databaseTable, commit=True)
		data._close()
	except:
		log_utils.error()


def authTrakt():
	try:
		if getTraktCredentialsInfo():
			if control.yesnoDialog(control.lang(32511), control.lang(32512), '', 'Trakt'):
				control.setSetting(id='trakt.isauthed', value='')
				control.setSetting(id='trakt.username', value='')
				control.setSetting(id='trakt.token', value='')
				control.setSetting(id='trakt.refresh', value='')
			raise Exception()

		result = getTraktAsJson('/oauth/device/code', {'client_id': V2_API_KEY})
		verification_url = (control.lang(32513) % result['verification_url']).encode('utf-8')
		user_code = (control.lang(32514) % result['user_code']).encode('utf-8')
		expires_in = int(result['expires_in'])
		device_code = result['device_code']
		interval = result['interval']
		progressDialog = control.progressDialog
		progressDialog.create('Trakt', verification_url, user_code)

		for i in range(0, expires_in):
			try:
				if progressDialog.iscanceled(): break
				time.sleep(1)
				if not float(i) % interval == 0:
					continue
				r = getTraktAsJson('/oauth/device/token', {'client_id': V2_API_KEY, 'client_secret': CLIENT_SECRET, 'code': device_code})
				if not r: continue
				if 'access_token' in r: break
			except:
				log_utils.error()
				pass
		try: progressDialog.close()
		except: pass

		token, refresh = r['access_token'], r['refresh_token']
		headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': 2, 'Authorization': 'Bearer %s' % token}

		result = client.request(urljoin(BASE_URL, '/users/me'), headers=headers)
		result = utils.json_loads_as_str(result)

		username = result['username']

		control.setSetting(id='trakt.isauthed', value='true')
		control.setSetting(id='trakt.username', value=username)
		control.setSetting(id='trakt.token', value=token)
		control.setSetting(id='trakt.refresh', value=refresh)
		raise Exception()
	except:
		log_utils.error()
		pass


def getTraktCredentialsInfo():
	username = control.setting('trakt.username').strip()
	token = control.setting('trakt.token')
	refresh = control.setting('trakt.refresh')
	if (username == '' or token == '' or refresh == ''):
		return False
	return True


def getTraktIndicatorsInfo():
	indicators = control.setting('indicators') if not getTraktCredentialsInfo() else control.setting('indicators.alt')
	indicators = True if indicators == '1' else False
	return indicators


def getTraktAddonMovieInfo():
	try: scrobble = control.addon('script.trakt').getSetting('scrobble_movie')
	except: scrobble = ''
	try: ExcludeHTTP = control.addon('script.trakt').getSetting('ExcludeHTTP')
	except: ExcludeHTTP = ''
	try: authorization = control.addon('script.trakt').getSetting('authorization')
	except: authorization = ''
	if scrobble == 'true' and ExcludeHTTP == 'false' and authorization != '':
		return True
	else: return False


def getTraktAddonEpisodeInfo():
	try: scrobble = control.addon('script.trakt').getSetting('scrobble_episode')
	except: scrobble = ''
	try: ExcludeHTTP = control.addon('script.trakt').getSetting('ExcludeHTTP')
	except: ExcludeHTTP = ''
	try: authorization = control.addon('script.trakt').getSetting('authorization')
	except: authorization = ''
	if scrobble == 'true' and ExcludeHTTP == 'false' and authorization != '':
		return True
	else: return False


def watch(name, imdb=None, tvdb=None, season=None, episode=None, refresh=True):
	if not tvdb: 
		markMovieAsWatched(imdb)
		cachesyncMovies()
	elif episode:
		markEpisodeAsWatched(imdb, tvdb, season, episode)
		cachesyncTV(imdb)
	elif season:
		markSeasonAsWatched(imdb, tvdb, season)
		cachesyncTV(imdb)
	elif tvdb:
		markTVShowAsWatched(imdb, tvdb)
		cachesyncTV(imdb)
	else:
		markMovieAsWatched(imdb)
		cachesyncMovies()
	if refresh:
		control.refresh()
	control.trigger_widget_refresh()
	if control.setting('trakt.general.notifications') == 'true':
		if season and not episode:
			name = '%s-Season%s...' % (name, season)
		if season and episode:
			name = '%s-S%sxE%02d...' % (name, season, int(episode))
		control.notification(title=32315, message=control.lang(35502) % name)


def unwatch(name, imdb=None, tvdb=None, season=None, episode=None, refresh=True):
	if not tvdb:
		markMovieAsNotWatched(imdb)
		cachesyncMovies()
	elif episode:
		markEpisodeAsNotWatched(imdb, tvdb, season, episode)
		cachesyncTV(imdb)
	elif season:
		markSeasonAsNotWatched(imdb, tvdb, season)
		cachesyncTV(imdb)
	elif tvdb:
		markTVShowAsNotWatched(imdb, tvdb)
		cachesyncTV(imdb)
	else:
		markMovieAsNotWatched(imdb)
		cachesyncMovies()
	if refresh:
		control.refresh()
	control.trigger_widget_refresh()
	if control.setting('trakt.general.notifications') == 'true':
		if season and not episode:
			name = '%s-Season%s...' % (name, season)
		if season and episode:
			name = '%s-S%sxE%02d...' % (name, season, int(episode))
		control.notification(title=32315, message=control.lang(35503) % name)


def rate(imdb=None, tvdb=None, season=None, episode=None):
	return _rating(action='rate', imdb=imdb, tvdb=tvdb, season=season, episode=episode)


def unrate(imdb=None, tvdb=None, season=None, episode=None):
	return _rating(action='unrate', imdb=imdb, tvdb=tvdb, season=season, episode=episode)


def rateShow(imdb=None, tvdb=None, season=None, episode=None):
	if control.setting('trakt.rating') == 1:
		rate(imdb=imdb, tvdb=tvdb, season=season, episode=episode)


def _rating(action, imdb=None, tvdb=None, season=None, episode=None):
	try:
		addon = 'script.trakt'
		if control.condVisibility('System.HasAddon(%s)' % addon):
			data = {}
			data['action'] = action
			if tvdb:
				data['video_id'] = tvdb
				if episode:
					data['media_type'] = 'episode'
					data['dbid'] = 1
					data['season'] = int(season)
					data['episode'] = int(episode)
				elif season:
					data['media_type'] = 'season'
					data['dbid'] = 5
					data['season'] = int(season)
				else:
					data['media_type'] = 'show'
					data['dbid'] = 2
			else:
				data['video_id'] = imdb
				data['media_type'] = 'movie'
				data['dbid'] = 4
			script = control.joinPath(control.addonPath(addon), 'resources', 'lib', 'sqlitequeue.py')
			sqlitequeue = imp.load_source('sqlitequeue', script)
			data = {'action': 'manualRating', 'ratingData': data}
			sqlitequeue.SqliteQueue().append(data)
		else:
			control.notification(title=32315, message=33659)
	except:
		log_utils.error()
		pass


def hideItem(name, imdb=None, tvdb=None, season=None, episode=None, refresh=True):
	sections = ['progress_watched', 'calendar']
	sections_display = [control.lang(40072), control.lang(40073)]
	selection = control.selectDialog([i for i in sections_display], heading=control.addonInfo('name') + ' - ' + control.lang(40074))
	if selection == -1: return
	section = sections[selection]
	if episode: post = {"shows": [{"ids": {"tvdb": tvdb}}]}
	else: post = {"movies": [{"ids": {"imdb": imdb}}]}
	getTrakt('users/hidden/%s' % section, post=post)[0]
	if refresh:
		control.refresh()
	control.trigger_widget_refresh()
	if control.setting('trakt.general.notifications') == 'true':
		control.notification(title=32315, message=control.lang(33053) % (name, sections_display[selection]))


def manager(name, imdb=None, tvdb=None, season=None, episode=None, refresh=True):
	lists = []
	try:
		if season: season = int(season)
		if episode: episode = int(episode)
		if tvdb: media_type = 'Show'
		else: media_type = 'Movie'

		items = [(control.lang(33651), 'watch')]
		items += [(control.lang(33652), 'unwatch')]
		items += [(control.lang(33653), 'rate')]
		items += [(control.lang(33654), 'unrate')]
		items += [(control.lang(40075) % media_type, 'hideItem')]
		items += [(control.lang(40076), 'scrobbleReset')]
		items += [(control.lang(33575), '/sync/collection')]
		items += [(control.lang(33576), '/sync/collection/remove')]
		if season or episode:
			items += [(control.lang(33573), '/sync/watchlist')]
			items += [(control.lang(33574), '/sync/watchlist/remove')]
		items += [(control.lang(33577), '/sync/watchlist')]
		items += [(control.lang(33578), '/sync/watchlist/remove')]
		items += [(control.lang(33579), '/users/me/lists/%s/items')]

		result = getTraktAsJson('/users/me/lists')
		lists = [(i['name'], i['ids']['slug']) for i in result]
		lists = [lists[i//2] for i in range(len(lists)*2)]

		for i in range(0, len(lists), 2):
			lists[i] = ((control.lang(33580) % lists[i][0]).encode('utf-8'), '/users/me/lists/%s/items' % lists[i][1])

		for i in range(1, len(lists), 2):
			lists[i] = ((control.lang(33581) % lists[i][0]).encode('utf-8'), '/users/me/lists/%s/items/remove' % lists[i][1])
		items += lists

		control.hide()
		select = control.selectDialog([i[0] for i in items], heading=control.addonInfo('name') + ' - ' + control.lang(32515))

		if select == -1:
			return
		if select >= 0:
			if items[select][0] == control.lang(33651):
				control.busy()
				watch(name, imdb=imdb, tvdb=tvdb, season=season, episode=episode, refresh=refresh)
				control.hide()
			elif items[select][0] == control.lang(33652):
				control.busy()
				unwatch(name, imdb=imdb, tvdb=tvdb, season=season, episode=episode, refresh=refresh)
				control.hide()
			elif items[select][0] == control.lang(33653):
				control.busy()
				rate(imdb=imdb, tvdb=tvdb, season=season, episode=episode)
				control.hide()
			elif items[select][0] == control.lang(33654):
				control.busy()
				unrate(imdb=imdb, tvdb=tvdb, season=season, episode=episode)
				control.hide()
			elif items[select][0] == control.lang(40075) % media_type:
				control.busy()
				hideItem(name=name, imdb=imdb, tvdb=tvdb, season=season, episode=episode)
				control.hide()
			elif items[select][0] == control.lang(40076):
				control.busy()
				scrobbleReset(imdb=imdb, tvdb=tvdb, season=season, episode=episode)
				control.hide()
			else:
				if not tvdb:
					post = {"movies": [{"ids": {"imdb": imdb}}]}
				else:
					if episode:
						if items[select][0] == control.lang(33573) or items[select][0] == control.lang(33574):
							post = {"shows": [{"ids": {"tvdb": tvdb}}]}
						else:
							post = {"shows": [{"ids": {"tvdb": tvdb}, "seasons": [{"number": season, "episodes": [{"number": episode}]}]}]}
							name = name + ' - ' + '%sx%02d' % (season, episode)
					elif season:
						if items[select][0] == control.lang(33573) or items[select][0] == control.lang(33574):
							post = {"shows": [{"ids": {"tvdb": tvdb}}]}
						else:
							post = {"shows": [{"ids": {"tvdb": tvdb}, "seasons": [{"number": season}]}]}
							name = name + ' - ' + 'Season %s' % season
					else:
						post = {"shows": [{"ids": {"tvdb": tvdb}}]}

				if items[select][0] == control.lang(33579):
					slug = listAdd(successNotification=True)
					if slug:
						getTrakt(items[select][1] % slug, post=post)[0]
				else:
					getTrakt(items[select][1], post=post)[0]

				control.hide()
				message = 33583 if 'remove' in items[select][1] else 33582

				if refresh:
					control.refresh()
				control.trigger_widget_refresh()
				if control.setting('trakt.general.notifications') == 'true':
					control.notification(title=name, message=message)
	except:
		log_utils.error()
		control.hide()


def listAdd(successNotification=True):
	t = control.lang(32520)
	k = control.keyboard('', t) ; k.doModal()
	new = k.getText() if k.isConfirmed() else None
	if not new: return
	result = getTrakt('/users/me/lists', post = {"name" : new, "privacy" : "private"})
	try:
		slug = json.loads(result)['ids']['slug']
		if successNotification:
			control.notification(title=32070, message=33661)
		return slug
	except:
		control.notification(title=32070, message=33584)
		return None


def lists(id=None):
	return cache.get(getTraktAsJson, 48, 'https://api.trakt.tv/users/me/lists' + ('' if not id else ('/' + str(id))))


def list(id):
	return lists(id=id)


def slug(name):
	name = name.strip()
	name = name.lower()
	name = re.sub('[^a-z0-9_]', '-', name) # check apostrophe
	name = re.sub('--+', '-', name)
	return name


def verify(authentication=None):
	try:
		if getTraktAsJson('/sync/last_activities', authentication=authentication): return True
	except:
		log_utils.error()
		pass
	return False


def getActivity():
	try:
		i = getTraktAsJson('/sync/last_activities')
		activity = []
		activity.append(i['movies']['watched_at']) # added 8/30/20
		activity.append(i['movies']['collected_at'])
		activity.append(i['movies']['watchlisted_at'])
		activity.append(i['movies']['paused_at']) # added 8/30/20
		activity.append(i['episodes']['watched_at']) # added 8/30/20
		activity.append(i['episodes']['collected_at'])
		activity.append(i['episodes']['watchlisted_at'])
		activity.append(i['episodes']['paused_at']) # added 8/30/20
		activity.append(i['shows']['watchlisted_at'])
		activity.append(i['seasons']['watchlisted_at'])
		activity.append(i['lists']['liked_at'])
		activity.append(i['lists']['updated_at'])
		activity = [int(cleandate.iso_2_utc(i)) for i in activity]
		activity = sorted(activity, key=int)[-1]
		return activity
	except:
		log_utils.error()
		pass


def getWatchedActivity():
	try:
		i = getTraktAsJson('/sync/last_activities')
		activity = []
		activity.append(i['movies']['watched_at'])
		activity.append(i['episodes']['watched_at'])
		activity = [int(cleandate.iso_2_utc(i)) for i in activity]
		activity = sorted(activity, key=int)[-1]
		return activity
	except:
		log_utils.error()
		pass


def getPausedActivity():
	try:
		i = getTraktAsJson('/sync/last_activities')
		activity = []
		activity.append(i['movies']['paused_at'])
		activity.append(i['episodes']['paused_at'])
		activity = [int(cleandate.iso_2_utc(i)) for i in activity]
		activity = sorted(activity, key=int)[-1]
		return activity
	except:
		log_utils.error()
		pass


def getCollectedActivity():
	try:
		i = getTraktAsJson('/sync/last_activities')
		activity = []
		activity.append(i['movies']['collected_at'])
		activity.append(i['episodes']['collected_at'])
		activity = [int(cleandate.iso_2_utc(i)) for i in activity]
		activity = sorted(activity, key=int)[-1]
		return activity
	except:
		log_utils.error()
		pass


def cachesyncMovies(timeout=0):
	indicators = cache.get(syncMovies, timeout)
	return indicators


def timeoutsyncMovies():
	timeout = cache.timeout(syncMovies)
	return timeout


def syncMovies():
	try:
		if not getTraktCredentialsInfo(): return
		indicators = getTraktAsJson('/users/me/watched/movies')
		indicators = [i['movie']['ids'] for i in indicators]
		indicators = [str(i['imdb']) for i in indicators if 'imdb' in i]
		return indicators
	except:
		log_utils.error()
		pass


def watchedMovies():
	try:
		if not getTraktCredentialsInfo(): return
		return getTraktAsJson('/users/me/watched/movies?extended=full')
	except:
		log_utils.error()
		pass


def watchedMoviesTime(imdb):
	try:
		imdb = str(imdb)
		items = watchedMovies()
		for item in items:
			if str(item['movie']['ids']['imdb']) == imdb:
				return item['last_watched_at']
	except:
		log_utils.error()
		pass


def cachesyncTV(imdb):
	threads = [threading.Thread(target=cachesyncTVShows), threading.Thread(target=cachesyncSeason, args=(imdb,))]
	[i.start() for i in threads]
	[i.join() for i in threads]


def cachesyncTVShows(timeout=0):
	indicators = cache.get(syncTVShows, timeout)
	return indicators


def timeoutsyncTVShows():
	timeout = cache.timeout(syncTVShows)
	return timeout


def syncTVShows():
	try:
		if not getTraktCredentialsInfo(): return
		indicators = getTraktAsJson('/users/me/watched/shows?extended=full')
		indicators = [(i['show']['ids']['tvdb'], i['show']['aired_episodes'], sum([[(s['number'], e['number']) for e in s['episodes']] for s in i['seasons']], [])) for i in indicators]
		indicators = [(str(i[0]), int(i[1]), i[2]) for i in indicators]
		return indicators
	except:
		log_utils.error()
		pass


def watchedShows():
	try:
		if not getTraktCredentialsInfo(): return
		return getTraktAsJson('/users/me/watched/shows?extended=full')
	except:
		log_utils.error()
		pass


def watchedShowsTime(tvdb, season, episode):
	try:
		tvdb = str(tvdb)
		season = int(season)
		episode = int(episode)
		items = watchedShows()
		for item in items:
			if str(item['show']['ids']['tvdb']) == tvdb:
				seasons = item['seasons']
				for s in seasons:
					if s['number'] == season:
						episodes = s['episodes']
						for e in episodes:
							if e['number'] == episode:
								return e['last_watched_at']
	except:
		log_utils.error()
		pass


def cachesyncSeason(imdb, timeout=0):
	indicators = cache.get(syncSeason, timeout, imdb)
	return indicators


def timeoutsyncSeason(imdb):
	timeout = cache.timeout(syncSeason, imdb)
	return timeout


def syncSeason(imdb):
	try:
		if not getTraktCredentialsInfo(): return
		if control.setting('tv.specials') == 'true':
			indicators = getTraktAsJson('/shows/%s/progress/watched?specials=true&hidden=true' % imdb)
		else:
			indicators = getTraktAsJson('/shows/%s/progress/watched?specials=false&hidden=false' % imdb)
		if not indicators: return None
		indicators = indicators['seasons']
		indicators = [(i['number'], [x['completed'] for x in i['episodes']]) for i in indicators]
		indicators = ['%01d' % int(i[0]) for i in indicators if False not in i[1]]
		return indicators
	except:
		log_utils.error()
		return None


def showCount(imdb, refresh=True, wait=False):
	try:
		if not imdb: return None
		if not imdb.startswith('tt'): return None
		result = {'total': 0, 'watched': 0, 'unwatched': 0}
		indicators = seasonCount(imdb=imdb, refresh=refresh, wait=wait)
		if not indicators: return None
		for indicator in indicators:
			result['total'] += indicator['total']
			result['watched'] += indicator['watched']
			result['unwatched'] += indicator['unwatched']
		return result
	except:
		log_utils.error()
		return None


def seasonCount(imdb, refresh=True, wait=False):
	try:
		if not imdb: return None
		if not imdb.startswith('tt'): return None
		indicators = cache.cache_existing(_seasonCountRetrieve, imdb)
		if refresh:
			# NB: Do not retrieve a fresh count, otherwise loading show/season menus are slow.
			thread = threading.Thread(target=_seasonCountCache, args=(imdb,))
			thread.start()
			if wait:
				thread.join()
				indicators = cache.cache_existing(_seasonCountRetrieve, imdb)
		return indicators
	except:
		log_utils.error()
		return None


def _seasonCountCache(imdb):
	return cache.get(_seasonCountRetrieve, 0, imdb)


	# indicators = getTraktAsJson('/users/me/watched/shows?extended=full')
def _seasonCountRetrieve(imdb):
	try:
		if not getTraktCredentialsInfo(): return
		if control.setting('tv.specials') == 'true':
			indicators = getTraktAsJson('/shows/%s/progress/watched?specials=true&hidden=false&count_specials=true' % imdb)
		else:
			indicators = getTraktAsJson('/shows/%s/progress/watched?specials=false&hidden=false' % imdb)
		if not indicators: return None
		seasons = indicators['seasons']
		return [{'total': season['aired'], 'watched': season['completed'], 'unwatched': season['aired'] - season['completed']} for season in seasons]
		# return [{season['number']: {'total': season['aired'], 'watched': season['completed'], 'unwatched': season['aired'] - season['completed']} for season in seasons}]
	except:
		log_utils.error()
		return None


def markMovieAsWatched(imdb):
	if not imdb.startswith('tt'):
		imdb = 'tt' + imdb
	return getTrakt('/sync/history', {"movies": [{"ids": {"imdb": imdb}}]})[0]


def markMovieAsNotWatched(imdb):
	if not imdb.startswith('tt'):
		imdb = 'tt' + imdb
	return getTrakt('/sync/history/remove', {"movies": [{"ids": {"imdb": imdb}}]})[0]


def markTVShowAsWatched(imdb, tvdb):
	if imdb and not imdb.startswith('tt'):
		imdb = 'tt' + imdb
	result = getTrakt('/sync/history', {"shows": [{"ids": {"tvdb": tvdb}}]})[0]
	seasonCount(imdb)
	return result


def markTVShowAsNotWatched(imdb, tvdb):
	if imdb and not imdb.startswith('tt'):
		imdb = 'tt' + imdb
	result = getTrakt('/sync/history/remove', {"shows": [{"ids": {"tvdb": tvdb}}]})[0]
	seasonCount(imdb)
	return result


def markSeasonAsWatched(imdb, tvdb, season):
	if imdb and not imdb.startswith('tt'):
		imdb = 'tt' + imdb
	season = int('%01d' % int(season))
	result = getTrakt('/sync/history', {"shows": [{"seasons": [{"number": season}], "ids": {"tvdb": tvdb}}]})[0]
	seasonCount(imdb)
	return result


def markSeasonAsNotWatched(imdb, tvdb, season):
	if imdb and not imdb.startswith('tt'):
		imdb = 'tt' + imdb
	season = int('%01d' % int(season))
	result = getTrakt('/sync/history/remove', {"shows": [{"seasons": [{"number": season}], "ids": {"tvdb": tvdb}}]})[0]
	seasonCount(imdb)
	return result


def markEpisodeAsWatched(imdb, tvdb, season, episode):
	if imdb and not imdb.startswith('tt'):
		imdb = 'tt' + imdb
	season, episode = int('%01d' % int(season)), int('%01d' % int(episode))
	result = getTrakt('/sync/history', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"tvdb": tvdb}}]})[0]
	seasonCount(imdb)
	return result


def markEpisodeAsNotWatched(imdb, tvdb, season, episode):
	if imdb and not imdb.startswith('tt'):
		imdb = 'tt' + imdb
	season, episode = int('%01d' % int(season)), int('%01d' % int(episode))
	result = getTrakt('/sync/history/remove', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"tvdb": tvdb}}]})[0]
	seasonCount(imdb)
	return result


def getMovieTranslation(id, lang, full=False):
	url = '/movies/%s/translations/%s' % (id, lang)
	try:
		item = cache.get(getTraktAsJson, 48, url)[0]
		result = item if full else item.get('title')
		return None if result == 'none' else result
	except:
		log_utils.error()
		pass


def getTVShowTranslation(id, lang, season=None, episode=None, full=False):
	if season and episode: url = '/shows/%s/seasons/%s/episodes/%s/translations/%s' % (id, season, episode, lang)
	else: url = '/shows/%s/translations/%s' % (id, lang)
	try:
		item = cache.get(getTraktAsJson, 48, url)[0]
		result = item if full else item.get('title')
		return None if result == 'none' else result
	except:
		log_utils.error()
		pass


def getMovieSummary(id, full=True):
	try:
		url = '/movies/%s' % id
		if full: url += '?extended=full'
		return cache.get(getTraktAsJson, 48, url)
	except:
		log_utils.error()


def getTVShowSummary(id, full=True):
	try:
		url = '/shows/%s' % id
		if full: url += '?extended=full'
		return cache.get(getTraktAsJson, 48, url)
	except:
		log_utils.error()


def getEpisodeSummary(id, season, episode, full=True):
	try:
		url = '/shows/%s/seasons/%s/episodes/%s' % (id, season, episode)
		if full: url += '&extended=full'
		return cache.get(getTraktAsJson, 48, url)
	except:
		log_utils.error()


def getSeasons(id, full=True):
	try:
		url = '/shows/%s/seasons' % (id)
		if full: url += '&extended=full'
		return cache.get(getTraktAsJson, 48, url)
	except:
		log_utils.error()


def sort_list(sort_key, sort_direction, list_data):
	reverse = False if sort_direction == 'asc' else True
	if sort_key == 'rank':
		return sorted(list_data, key=lambda x: x['rank'], reverse=reverse)
	elif sort_key == 'added':
		return sorted(list_data, key=lambda x: x['listed_at'], reverse=reverse)
	elif sort_key == 'title':
		return sorted(list_data, key=lambda x: utils.title_key(x[x['type']].get('title')), reverse=reverse)
	elif sort_key == 'released':
		return sorted(list_data, key=lambda x: _released_key(x[x['type']]), reverse=reverse)
	elif sort_key == 'runtime':
		return sorted(list_data, key=lambda x: x[x['type']].get('runtime', 0), reverse=reverse)
	elif sort_key == 'popularity':
		return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
	elif sort_key == 'percentage':
		return sorted(list_data, key=lambda x: x[x['type']].get('rating', 0), reverse=reverse)
	elif sort_key == 'votes':
		return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
	else:
		return list_data


def getMovieAliases(id):
	try:
		return cache.get(getTraktAsJson, 48, '/movies/%s/aliases' % id)
	except:
		log_utils.error()
		return []


def getTVShowAliases(id):
	try:
		return cache.get(getTraktAsJson, 48, '/shows/%s/aliases' % id)
	except:
		log_utils.error()
		return []


def getPeople(id, content_type, full=True):
	try:
		url = '/%s/%s/people' % (content_type, id)
		if full: url += '?extended=full'
		return cache.get(getTraktAsJson, 48, url)
	except:
		log_utils.error()


def SearchAll(title, year, full=True):
	try:
		return SearchMovie(title, year, full) + SearchTVShow(title, year, full)
	except:
		log_utils.error()
		return


def SearchMovie(title, year, full=True):
	try:
		url = '/search/movie?query=%s' % title
		if year: url += '&year=%s' % year
		if full: url += '&extended=full'
		return cache.get(getTraktAsJson, 48, url)
	except:
		log_utils.error()
		return


def SearchTVShow(title, year, full=True):
	try:
		url = '/search/show?query=%s' % title
		if year: url += '&year=%s' % year
		if full: url += '&extended=full'
		return cache.get(getTraktAsJson, 48, url)
	except:
		log_utils.error()
		return


def SearchEpisode(title, season, episode, full=True):
	try:
		url = '/search/%s/seasons/%s/episodes/%s' % (title, season, episode)
		if full:
			url += '&extended=full'
		return cache.get(getTraktAsJson, 48, url)
	except:
		log_utils.error()
		return


def getGenre(content, type, type_id):
	try:
		r = '/search/%s/%s?type=%s&extended=full' % (type, type_id, content)
		r = cache.get(getTraktAsJson, 96, r)
		r = r[0].get(content, {}).get('genres', [])
		return r
	except:
		log_utils.error()
		return []


def IdLookup(id_type, id, type):
	try:
		r = '/search/%s/%s?type=%s' % (id_type, id, type)
		r = cache.get(getTraktAsJson, 96, r)
		if not r: return None
		return r[0].get(type).get('ids')
	except:
		log_utils.error()
		return None


def scrobbleReset(imdb, tvdb=None, season=None, episode=None, refresh=True):
	try:
		from resources.lib.modules import traktsync
		type = 'movie' if not episode else 'episode'
		if type == 'movie':
			items = [{'type': 'movie', 'movie': {'ids': {'imdb': imdb}}}]
			getTrakt('/scrobble/start', {"movie": {"ids": {"imdb": imdb}}, "progress": 0})
		else:
			items = [{'type': 'episode', 'episode': {'season': season, 'number': episode}, 'show': {'ids': {'imdb': imdb, 'tvdb': tvdb}}}]
			getTrakt('/scrobble/start', {"show": {"ids": {"tvdb": tvdb}}, "episode": {"season": season, "number": episode}, "progress": 0})
		traktsync.delete_bookmark(items)
		if refresh:
			control.refresh()
	except:
		log_utils.error()


def scrobbleMovie(imdb, tmdb, watched_percent):
	try:
		if not imdb.startswith('tt'): imdb = 'tt' + imdb
		from datetime import datetime
		timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
		from resources.lib.modules import traktsync
		items = [{'progress': watched_percent, 'paused_at': timestamp, 'type': 'movie', 'movie': {'ids': {'imdb': imdb, 'tmdb': tmdb}}}]
		traktsync.insert_bookmarks(items)
		return getTrakt('/scrobble/pause', {"movie": {"ids": {"imdb": imdb}}, "progress": watched_percent})
	except:
		log_utils.error()


def scrobbleEpisode(imdb, tmdb, tvdb, season, episode, watched_percent):
	try:
		season, episode = int('%01d' % int(season)), int('%01d' % int(episode))
		from datetime import datetime
		timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
		# log_utils.log('timestamp = %s' % str(timestamp), __name__, log_utils.LOGDEBUG)
		from resources.lib.modules import traktsync
		items = [{'progress': watched_percent, 'paused_at': timestamp, 'type': 'episode', 'episode': {'season': season, 'number': episode}, 'show': {'ids': {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb}}}]
		traktsync.insert_bookmarks(items)
		return getTrakt('/scrobble/pause', {"show": {"ids": {"tvdb": tvdb}}, "episode": {"season": season, "number": episode}, "progress": watched_percent})
	except:
		log_utils.error()


def _scrobbleType(type):
	if type == 'show' or type == 'season' or type == 'episode':
		return 'episode'
	else:
		return 'movie'

# no longer used 
def scrobbleProgress(type, imdb=None, tmdb=None, tvdb=None, season=None, episode=None):
	try:
		type = _scrobbleType(type)
		if imdb: imdb = str(imdb)
		if tmdb: tmdb = str(tmdb)
		if tvdb: tvdb = int(tvdb)
		if episode: episode = int(episode)
		if season: season = int(season)

		# link = '/sync/playback/%s' % type + 's'
		# # items = getTraktAsJson(link)
		# items = cache.get(getTraktAsJson, 0.0833, link) #5min cache for faster menu load time

		try:
			# from resources.lib.modules import traktsync
			progress = traktsync.fetch_bookmarks(imdb, tmdb, tvdb, season, episode)
			return progress
		except:
			log_utils.error()
			pass

		if type == 'episode':
			if imdb and items:
				for item in items:
					if 'show' in item and 'imdb' in item['show']['ids'] and item['show']['ids']['imdb'] == imdb:
						if item['episode']['season'] == season and item['episode']['number'] == episode:
							return item['progress']
			if tvdb:
				for item in items:
					if 'show' in item and 'tvdb' in item['show']['ids'] and item['show']['ids']['tvdb'] == tvdb:
						if item['episode']['season'] == season and item['episode']['number'] == episode:
							return item['progress']
		else:
			if imdb and items:
				for item in items:
					if 'movie' in item and 'imdb' in item['movie']['ids'] and item['movie']['ids']['imdb'] == imdb:
						return item['progress']
	except:
		log_utils.error()
	return 0


def sync_progress():
	try:
		from resources.lib.modules import traktsync
		while not control.monitor.abortRequested():
			db_last_paused = traktsync.last_paused_at()
			activity = getPausedActivity()
			if activity - db_last_paused > 10:
				log_utils.log('Trakt Progress Sync Update...(local db latest "paused_at" = %s, trakt api latest "paused_at" = %s)' % \
									(str(db_last_paused), str(activity)), __name__, log_utils.LOGDEBUG)
				link = '/sync/playback/'
				items = getTraktAsJson(link)
				from resources.lib.modules import traktsync
				traktsync.insert_bookmarks(items)
			if control.monitor.waitForAbort(60*15):
				break
	except:
		log_utils.error()
		pass


def scrobbleUpdate(action, type, imdb=None, tvdb=None, season=None, episode=None, progress=0):
	try:
		if action:
			type = _scrobbleType(type)
			if imdb: imdb = str(imdb)
			if tvdb: tvdb = int(tvdb)
			if season: season = int(season)
			if episode: episode = int(episode)
			if imdb: link = '/search/imdb/' + str(imdb)
			elif tvdb: link = '/search/tvdb/' + str(tvdb)
			if type == 'episode': link += '?type=show'
			else: link += '?type=movie'
			items = cache.get(getTraktAsJson, 760, link)
			if len(items) > 0:
				item = items[0]
				if type == 'episode':
					slug = item['show']['ids']['slug']
					link = '/shows/%s/seasons/%d/episodes/%d' % (slug, season, episode)
					item = cache.get(getTraktAsJson, 760, link)
				else:
					item = item['movie']
				if item:
					link = '/scrobble/' + action
					data = {
						type: item,
						'progress': progress,
						'app_version': control.addonVersion(addon='plugin.video.venom'),
					}
					result = getTrakt(url=link, post=data)
					return 'progress' in result
	except:
		log_utils.error()
		pass
	return False


def _released_key(item):
	if 'released' in item:
		return item['released']
	elif 'first_aired' in item:
		return item['first_aired']
	else:
		return 0