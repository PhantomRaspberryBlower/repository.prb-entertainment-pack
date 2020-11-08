# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

from sys import argv
import xbmcaddon

try:
	from urlparse import parse_qsl
	from urllib import quote_plus
except:
	from urllib.parse import parse_qsl, quote_plus

from resources.lib.modules import control

params = dict(parse_qsl(argv[2].replace('?','')))

action = params.get('action')
id = params.get('id')
name = params.get('name')
title = params.get('title')
year = params.get('year')
imdb = params.get('imdb')
tmdb = params.get('tmdb')
tvdb = params.get('tvdb')
season = params.get('season')
episode = params.get('episode')
tvshowtitle = params.get('tvshowtitle')
type = params.get('type')
url = params.get('url')
query = params.get('query')
source = params.get('source')

windowedtrailer = params.get('windowedtrailer')
windowedtrailer = int(windowedtrailer) if windowedtrailer in ("0","1") else 0

playAction = xbmcaddon.Addon('plugin.video.venom').getSetting('hosts.mode')
autoPlay = 'true' if playAction == '2' else ''
control.homeWindow.setProperty('plugin.video.venom.autoPlay', autoPlay)


if action is None:
	from resources.lib.menus import navigator
	from resources.lib.modules import cache
	run = control.setting('first.info')
	if run == '':
		run = 'true' #clean install scenerio
	if cache._find_cache_version():
		run = 'true'
	if run == 'true':
		control.execute('RunPlugin(plugin://plugin.video.venom/?action=tools_cleanSettings)')
		from resources.lib.modules import changelog
		changelog.get()
		control.setSetting(id='first.info', value='false')
	cache.cache_version_check()
	navigator.Navigator().root()


####################################################
#---MOVIES
####################################################
elif action == 'movieNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().movies()

elif action == 'movieliteNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().movies(lite=True)

elif action == 'mymovieNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().mymovies()

elif action == 'mymovieliteNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().mymovies(lite=True)

elif action == 'movies':
	from resources.lib.menus import movies
	movies.Movies().get(url)

elif action == 'moviePage':
	from resources.lib.menus import movies
	movies.Movies().get(url)

elif action == 'tmdbmovies':
	from resources.lib.menus import movies
	movies.Movies().getTMDb(url)

elif action == 'tmdbmoviePage':
	from resources.lib.menus import movies
	movies.Movies().getTMDb(url)

elif action == 'movieSearch':
	from resources.lib.menus import movies
	movies.Movies().search()

elif action == 'movieSearchnew':
	from resources.lib.menus import movies
	movies.Movies().search_new()

elif action == 'movieSearchterm':
	from resources.lib.menus import movies
	movies.Movies().search_term(name)

elif action == 'moviePerson':
	from resources.lib.menus import movies
	movies.Movies().person()

elif action == 'movieGenres':
	from resources.lib.menus import movies
	movies.Movies().genres()

elif action == 'movieLanguages':
	from resources.lib.menus import movies
	movies.Movies().languages()

elif action == 'movieCertificates':
	from resources.lib.menus import movies
	movies.Movies().certifications()

elif action == 'movieYears':
	from resources.lib.menus import movies
	movies.Movies().years()

elif action == 'moviePersons':
	from resources.lib.menus import movies
	movies.Movies().persons(url)

elif action == 'moviesUnfinished':
	from resources.lib.menus import movies
	movies.Movies().unfinished(url)

elif action == 'movieUserlists':
	from resources.lib.menus import movies
	movies.Movies().userlists()


####################################################
#---Collections
####################################################
if action and action.startswith('collections'):
	if action == 'collections_Navigator':
		from resources.lib.menus import collections
		collections.Collections().collections_Navigator()

	elif action == 'collections_Boxset':
		from resources.lib.menus import collections
		collections.Collections().collections_Boxset()

	elif action == 'collections_Kids':
		from resources.lib.menus import collections
		collections.Collections().collections_Kids()

	elif action == 'collections_BoxsetKids':
		from resources.lib.menus import collections
		collections.Collections().collections_BoxsetKids()

	elif action == 'collections_Superhero':
		from resources.lib.menus import collections
		collections.Collections().collections_Superhero()

	elif action == 'collections_MartialArts':
		from resources.lib.menus import collections
		collections.Collections().collections_martial_arts()

	elif action == 'collections_MartialArtsActors':
		from resources.lib.menus import collections
		collections.Collections().collections_martial_arts_actors()

	elif action == 'collections':
		from resources.lib.menus import collections
		collections.Collections().get(url)


####################################################
#---Furk
####################################################
if action and action.startswith('furk'):
	if action == "furkNavigator":
		from resources.lib.menus import navigator
		navigator.Navigator().furk()

	elif action == "furkMetaSearch":
		from resources.lib.menus import furk
		furk.Furk().furk_meta_search(url)

	elif action == "furkSearch":
		from resources.lib.menus import furk
		furk.Furk().search()

	elif action == "furkUserFiles":
		from resources.lib.menus import furk
		furk.Furk().user_files()

	elif action == "furkSearchNew":
		from resources.lib.menus import furk
		furk.Furk().search_new()


####################################################
# TV Shows
####################################################
# if action and action.startswith('tv_'):
if action == 'tvNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().tvshows()

elif action == 'tvliteNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().tvshows(lite=True)

elif action == 'mytvNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().mytvshows()

elif action == 'mytvliteNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().mytvshows(lite=True)

elif action == 'tvshows':
	from resources.lib.menus import tvshows
	tvshows.TVshows().get(url)

elif action == 'tvshowPage':
	from resources.lib.menus import tvshows
	tvshows.TVshows().get(url)

elif action == 'tmdbTvshows':
	from resources.lib.menus import tvshows
	tvshows.TVshows().getTMDb(url)

elif action == 'tmdbTvshowPage':
	from resources.lib.menus import tvshows
	tvshows.TVshows().getTMDb(url)

elif action == 'tvmazeTvshows':
	from resources.lib.menus import tvshows
	tvshows.TVshows().getTVmaze(url)

elif action == 'tvmazeTvshowPage':
	from resources.lib.menus import tvshows
	tvshows.TVshows().getTVmaze(url)

elif action == 'tvSearch':
	from resources.lib.menus import tvshows
	tvshows.TVshows().search()

elif action == 'tvSearchnew':
	from resources.lib.menus import tvshows
	tvshows.TVshows().search_new()

elif action == 'tvSearchterm':
	from resources.lib.menus import tvshows
	tvshows.TVshows().search_term(name)

elif action == 'tvPerson':
	from resources.lib.menus import tvshows
	tvshows.TVshows().person()

elif action == 'tvGenres':
	from resources.lib.menus import tvshows
	tvshows.TVshows().genres()

elif action == 'tvNetworks':
	from resources.lib.menus import tvshows
	tvshows.TVshows().networks()

elif action == 'tvLanguages':
	from resources.lib.menus import tvshows
	tvshows.TVshows().languages()

elif action == 'tvCertificates':
	from resources.lib.menus import tvshows
	tvshows.TVshows().certifications()

elif action == 'tvPersons':
	from resources.lib.menus import tvshows
	tvshows.TVshows().persons(url)

elif action == 'tvUserlists':
	from resources.lib.menus import tvshows
	tvshows.TVshows().userlists()

elif action == 'tvOriginals':
	from resources.lib.menus import tvshows
	tvshows.TVshows().originals()


####################################################
#---SEASONS
####################################################
if action and action.startswith('seasons'):
	if action == 'seasons':
		from resources.lib.menus import seasons
		seasons.Seasons().get(tvshowtitle, year, imdb, tmdb, tvdb)

	elif action == 'seasonsUserlists':
		from resources.lib.indexers import seasons
		seasons.Seasons().userlists()

	elif action == 'seasonsList':
		from resources.lib.menus import seasons
		seasons.Seasons().seasonList(url)


####################################################
#---EPISODES
####################################################
if action == 'playEpisodesList':
	import json
	from resources.lib.menus import episodes
	items = episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, episode, idx=False)
	control.playlist.clear()
	for i in items:
		title = i['title']
		systitle = quote_plus(title)
		year = i['year']
		imdb = i['imdb']
		tmdb = i['tmdb']
		tvdb = i['tvdb']
		season = i['season']
		episode = i['episode']
		tvshowtitle = i['tvshowtitle']
		systvshowtitle = quote_plus(tvshowtitle)
		premiered = i['premiered']
		sysmeta = quote_plus(json.dumps(i))
		url = 'plugin://plugin.video.venom/?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&meta=%s&select="2"' % (
								systitle, year, imdb, tmdb, tvdb, season, episode, systvshowtitle, premiered, sysmeta)
		item = control.item(label=title)
		control.playlist.add(url=url, listitem=item)
	control.player2().play(control.playlist)

elif action == 'episodes':
	from resources.lib.menus import episodes
	episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, episode)

elif action == 'episodesPage':
	from resources.lib.menus import episodes
	episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, episode)

elif action == 'calendar':
	from resources.lib.menus import episodes
	episodes.Episodes().calendar(url)

elif action == 'calendars':
	from resources.lib.menus import episodes
	episodes.Episodes().calendars()

elif action == 'episodesUnfinished':
	from resources.lib.menus import episodes
	episodes.Episodes().unfinished(url)

elif action == 'episodesUserlists':
	from resources.lib.menus import episodes
	episodes.Episodes().userlists()


####################################################
#---Premium Services
####################################################
elif action == 'premiumNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().premium_services()

if action and action.startswith('pm_'):
	if action == 'pm_ServiceNavigator':
		from resources.lib.menus import navigator
		navigator.Navigator().premiumize_service()

	elif action == 'pm_AccountInfo':
		from resources.lib.debrid import premiumize
		premiumize.Premiumize().account_info_to_dialog()

	# elif action == 'pm_Authorize':
		# from resources.lib.debrid import premiumize
		# premiumize.Premiumize().auth()

	elif action == 'pm_MyFiles':
		from resources.lib.debrid import premiumize
		premiumize.Premiumize().my_files_to_listItem(id, name)

	elif action == 'pm_Transfers':
		from resources.lib.debrid import premiumize
		premiumize.Premiumize().user_transfers_to_listItem()

	elif action == 'pm_Rename':
		from resources.lib.debrid import premiumize
		premiumize.Premiumize().rename(type, id, name)

	elif action == 'pm_Delete':
		from resources.lib.debrid import premiumize
		premiumize.Premiumize().delete(type, id, name)

	elif action == 'pm_DeleteTransfer':
		from resources.lib.debrid import premiumize
		premiumize.Premiumize().delete_transfer(id, name)

	elif action == 'pm_ClearFinishedTransfers': # disabled for now till PM fixes
		from resources.lib.debrid import premiumize
		premiumize.Premiumize().clear_finished_transfers()

if action and action.startswith('rd_'):
	if action == 'rd_ServiceNavigator':
		from resources.lib.menus import navigator
		navigator.Navigator().realdebrid_service()

	elif action == 'rd_AccountInfo':
		from resources.lib.debrid import realdebrid
		realdebrid.RealDebrid().account_info_to_dialog()

	# elif action == 'rd_Authorize':
		# from resources.lib.debrid import realdebrid
		# realdebrid.RealDebrid().auth()

	elif action == 'rd_UserTorrentsToListItem':
		from resources.lib.debrid import realdebrid
		realdebrid.RealDebrid().user_torrents_to_listItem()

	elif action == 'rd_MyDownloads':
		from resources.lib.debrid import realdebrid
		realdebrid.RealDebrid().my_downloads_to_listItem(int(query))

	elif action == 'rd_BrowseUserTorrents':
		from resources.lib.debrid import realdebrid
		realdebrid.RealDebrid().browse_user_torrents(id)

	elif action == 'rd_DeleteUserTorrent':
		from resources.lib.debrid import realdebrid
		realdebrid.RealDebrid().delete_user_torrent(id, name)

	elif action == 'rd_DeleteDownload':
		from resources.lib.debrid import realdebrid
		realdebrid.RealDebrid().delete_download(id, name)

if action and action.startswith('ad_'):
	if action == 'ad_ServiceNavigator':
		from resources.lib.menus import navigator
		navigator.Navigator().alldebrid_service()

	elif action == 'ad_AccountInfo':
		from resources.lib.debrid import alldebrid
		alldebrid.AllDebrid().account_info_to_dialog()

	# elif action == 'ad_Authorize':
		# from resources.lib.debrid import alldebrid
		# alldebrid.AllDebrid().auth()

	elif action == 'ad_Transfers':
		from resources.lib.debrid import alldebrid
		alldebrid.AllDebrid().user_transfers_to_listItem()

	elif action == 'ad_CloudStorage':
		from resources.lib.debrid import alldebrid
		alldebrid.AllDebrid().user_cloud_to_listItem()

	elif action == 'ad_BrowseUserCloud':
		from resources.lib.debrid import alldebrid
		alldebrid.AllDebrid().browse_user_cloud(source)

	elif action == 'ad_DeleteTransfer':
		from resources.lib.debrid import alldebrid
		alldebrid.AllDebrid().delete_transfer(id, name, silent=False)

	elif action == 'ad_RestartTransfer':
		from resources.lib.debrid import alldebrid
		alldebrid.AllDebrid().restart_transfer(id, name, silent=False)


####################################################
#---Anime
####################################################
if action and action.startswith('anime_'):
	if action == 'anime_Navigator':
		from resources.lib.menus import navigator
		navigator.Navigator().anime()

	elif action == 'anime_Movies':
		from resources.lib.menus import movies
		movies.Movies().get(url)

	elif action == 'anime_TVshows':
		from resources.lib.menus import tvshows
		tvshows.TVshows().get(url)


####################################################
#---YouTube
####################################################
if action == 'youtube':
	from resources.lib.menus import youtube
	if id is None: youtube.yt_index().root(action)
	else: youtube.yt_index().get(action, id)

elif action == 'sectionItem':
	pass # Placeholder. This is a non-clickable menu item for notes, etc.


####################################################
#---Download
####################################################
if action and action.startswith('download'):
	if action == 'downloadNavigator':
		from resources.lib.menus import navigator
		navigator.Navigator().downloads()

	elif action == 'download':
		caller = params.get('caller')
		image = params.get('image')
		if caller == 'sources':
			control.busy()
			try:
				import json
				from resources.lib.modules import sources
				from resources.lib.modules import downloader
				downloader.download(name, image, sources.Sources().sourcesResolve(json.loads(source)[0], True), title)
			except:
				import traceback
				traceback.print_exc()
				pass
		if caller == 'premiumize':
			control.busy()
			try:
				from resources.lib.modules import downloader
				from resources.lib.debrid import premiumize
				downloader.download(name, image, premiumize.Premiumize().add_headers_to_url(url.replace(' ', '%20')))
			except:
				import traceback
				traceback.print_exc()
				pass
		if caller == 'realdebrid':
			control.busy()
			try:
				from resources.lib.modules import downloader
				from resources.lib.debrid import realdebrid
				if type == 'unrestrict':
					downloader.download(name, image, realdebrid.RealDebrid().unrestrict_link(url.replace(' ', '%20')))
				else:
					downloader.download(name, image, url.replace(' ', '%20'))
			except:
				import traceback
				traceback.print_exc()
				pass
		if caller == 'alldebrid':
			control.busy()
			try:
				from resources.lib.modules import downloader
				from resources.lib.debrid import alldebrid
				downloader.download(name, image, alldebrid.AllDebrid().unrestrict_link(url.replace(' ', '%20')))
			except:
				import traceback
				traceback.print_exc()
				pass


####################################################
#---Tools
####################################################
if action and action.startswith('tools_'):
	if action == 'tools_ShowNews':
		from resources.lib.modules import newsinfo
		newsinfo.news()

	elif action == 'tools_ShowChangelog':
		from resources.lib.modules import changelog
		changelog.get()

	elif action == 'tools_ShowHelp':
		from resources.help import help
		help.get(name)

	elif action == 'tools_LanguageInvoker':
		control.set_reuselanguageinvoker()

	elif action == 'tools_toolNavigator':
		from resources.lib.menus import navigator
		navigator.Navigator().tools()

	elif action == 'tools_searchNavigator':
		from resources.lib.menus import navigator
		navigator.Navigator().search()

	elif action == 'tools_viewsNavigator':
		from resources.lib.menus import navigator
		navigator.Navigator().views()

	elif action == 'tools_addView':
		from resources.lib.modules import views
		content = params.get('content')
		views.addView(content)

	elif action == 'tools_resetViewTypes':
		from resources.lib.modules import views
		views.clearViews()

	elif action == 'tools_cleanSettings':
		control.clean_settings()

	elif action == 'tools_openMyAccount':
		from myaccounts import openMASettings
		openMASettings(query)
		control.sleep(500)
		while control.condVisibility('Window.IsVisible(addonsettings)') or control.homeWindow.getProperty('myaccounts.active') == 'true':
			control.sleep(500)
		control.sleep(100)
		control.syncMyAccounts()
		control.sleep(100)
		if params.get('opensettings') == 'true':
			control.openSettings('8.0', 'plugin.video.venom')

	elif action == 'tools_syncMyAccount':
		control.syncMyAccounts()
		if params.get('opensettings') == 'true':
			control.openSettings(query, 'plugin.video.venom')

	elif action == 'tools_traktAcctMyAccounts':
		control.execute('RunScript(script.module.myaccounts, action=traktAcct)')

	elif action == 'tools_adAcctMyAccounts':
		control.execute('RunScript(script.module.myaccounts, action=alldebridAcct)')

	elif action == 'tools_pmAcctMyAccounts':
		control.execute('RunScript(script.module.myaccounts, action=premiumizeAcct)')

	elif action == 'tools_rdAcctMyAccounts':
		control.execute('RunScript(script.module.myaccounts, action=realdebridAcct)')

	elif action == 'tools_openSettings':
		control.openSettings(query)

	elif action == 'tools_contextVenomSettings':
		control.openSettings('0.0', 'context.venom')
		control.trigger_widget_refresh()

	elif action == 'tools_UpNextSettings':
		control.openSettings('0.0', 'service.upnext')
		control.sleep(500)
		while control.condVisibility('Window.IsVisible(addonsettings)'):
			control.sleep(500)
		control.sleep(100)
		if params.get('opensettings') == 'true':
			control.openSettings(query, 'plugin.video.venom')

	elif action == 'tools_fenomscrapersSettings':
		control.openSettings('0.0', 'script.module.fenomscrapers')

	elif action == 'tools_traktManager':
		from resources.lib.modules import trakt
		trakt.manager(name, imdb, tvdb, season, episode)

	elif action == 'tools_cachesyncMovies':
		from resources.lib.modules import trakt
		trakt.cachesyncMovies(int(params.get('timeout')))

	elif action == 'tools_cachesyncTVShows':
		from resources.lib.modules import trakt
		trakt.cachesyncTVShows(int(params.get('timeout')))

	elif action == 'tools_syncTraktProgress':
		from resources.lib.modules import trakt
		trakt.sync_progress()

####################################################
#---Play
####################################################
if action == 'play':
	# control.player. playselected(1)
	# control.player.playnext()
	# control.player2().play(control.playlist)
	# xbmc.executebuiltin('RunPlugin(plugin://plugin.video.venom/?action=playAll)')
	# xbmc.executebuiltin('PlayMedia(plugin://plugin.video.venom/?action=playAll)')

	from resources.lib.modules import sources
	premiered = params.get('premiered')
	meta = params.get('meta')
	select = params.get('select')
	rescrape = params.get('rescrape')
	sources.Sources().play(title, year, imdb, tmdb, tvdb, season, episode, tvshowtitle, premiered, meta, select, rescrape)

elif action == 'playAll':
	control.player2().play(control.playlist)

elif action == 'playURL':
	caller = params.get('caller')
	if caller == 'realdebrid':
		from resources.lib.debrid import realdebrid
		if type == 'unrestrict': control.player.play(realdebrid.RealDebrid().unrestrict_link(url.replace(' ', '%20')))
		else: control.player.play(url.replace(' ', '%20'))
	elif caller == 'alldebrid':
		from resources.lib.debrid import alldebrid
		if type == 'unrestrict': control.player.play(alldebrid.AllDebrid().unrestrict_link(url.replace(' ', '%20')))
		else: control.player.play(url.replace(' ', '%20'))
	else: control.player.play(url.replace(' ', '%20'))

elif action == 'playItem':
	from resources.lib.modules import sources
	sources.Sources().playItem(title, source)

elif action == 'addItem':
	from resources.lib.modules import sources
	sources.Sources().addItem(title)

elif action == 'alterSources':
	from resources.lib.modules import sources
	meta = params.get('meta')
	sources.Sources().alterSources(url, meta)

elif action == 'trailer':
	from resources.lib.modules import trailer
	trailer.Trailer().play(type, name, year, url, imdb, windowedtrailer)

elif action == 'showDebridPack':
	from resources.lib.modules.sources import Sources
	caller = params.get('caller')
	Sources().debridPackDialog(caller, name, url, source)

elif action == 'cacheTorrent':
	caller = params.get('caller')
	pack = True if type == 'pack' else False
	if caller == 'RD':
		from resources.lib.debrid.realdebrid import RealDebrid as debrid_function
	elif caller == 'PM':
		from resources.lib.debrid.premiumize import Premiumize as debrid_function
	elif caller == 'AD':
		from resources.lib.debrid.alldebrid import AllDebrid as debrid_function
	debrid_function().add_uncached_torrent(url, pack=pack)

elif action == 'random':
	rtype = params.get('rtype')
	if rtype == 'movie':
		from resources.lib.menus import movies
		rlist = movies.Movies().get(url, idx=False)
		r = argv[0]+"?action=play"

	elif rtype == 'episode':
		from resources.lib.menus import episodes
		rlist = episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, idx=False)
		r = argv[0]+"?action=play"

	elif rtype == 'season':
		from resources.lib.menus import seasons
		rlist = seasons.Seasons().get(tvshowtitle, year, imdb, tmdb, tvdb, idx=False)
		r = argv[0]+"?action=random&rtype=episode"

	elif rtype == 'show':
		from resources.lib.menus import tvshows
		rlist = tvshows.TVshows().get(url, idx=False)
		r = argv[0]+"?action=random&rtype=season"

	from random import randint
	import json

	try:
		rand = randint(1,len(rlist))-1
		for p in ['title', 'year', 'imdb', 'tvdb', 'season', 'episode', 'tvshowtitle', 'premiered', 'select']:
			if rtype == "show" and p == "tvshowtitle":
				try: r += '&'+p+'='+quote_plus(rlist[rand]['title'])
				except: pass
			else:
				try: r += '&'+p+'='+quote_plus(rlist[rand][p])
				except: pass
		try: r += '&meta='+quote_plus(json.dumps(rlist[rand]))
		except: r += '&meta='+quote_plus("{}")
		if rtype == "movie":
			try: control.notification(title=32536, message=rlist[rand]['title'])
			except: pass
		elif rtype == "episode":
			try: control.notification(title=32536, message=rlist[rand]['tvshowtitle']+" - Season "+rlist[rand]['season']+" - "+rlist[rand]['title'])
			except: pass
		control.execute('RunPlugin(%s)' % r)
	except:
		control.notification(message=32537)


####################################################
#---Playlist
####################################################
if action and action.startswith('playlist_'):
	if action == 'playlist_Manager':
		from resources.lib.modules import playlist
		art = params.get('art')
		meta = params.get('meta')
		playlist.playlistManager(name, url, meta, art)

	elif action == 'playlist_Show':
		from resources.lib.modules import playlist
		playlist.playlistShow()

	elif action == 'playlist_Clear':
		from resources.lib.modules import playlist
		playlist.playlistClear()

	elif action == 'playlist_QueueItem':
		control.queueItem()
		if name is None:
			control.notification(title=35515, message=35519)
		else:
			control.notification(title=name, message=35519)


####################################################
#---Playcount
####################################################
if action and action.startswith('playcount_'):
	if action == 'playcount_Movie':
		from resources.lib.modules import playcount
		playcount.movies(name, imdb, query)

	elif action == 'playcount_Episode':
		from resources.lib.modules import playcount
		playcount.episodes(name, imdb, tvdb, season, episode, query)

	elif action == 'playcount_TVShow':
		from resources.lib.modules import playcount
		playcount.tvshows(name, imdb, tvdb, season, query)


####################################################
#---Library Actions
####################################################
if action and action.startswith('library_'):
	if action == 'library_Navigator':
		from resources.lib.menus import navigator
		navigator.Navigator().library()

	elif action == 'library_movieToLibrary':
		from resources.lib.modules import libtools
		libtools.libmovies().add(name, title, year, imdb, tmdb)

	elif action == 'library_moviesToLibrary':
		from resources.lib.modules import libtools
		libtools.libmovies().range(url, name)

	elif action == 'library_moviesListToLibrary':
		from resources.lib.menus import movies
		movies.Movies().moviesListToLibrary(url)

	elif action == 'library_moviesToLibrarySilent':
		from resources.lib.modules import libtools
		libtools.libmovies().silent(url)

	elif action == 'library_tvshowToLibrary':
		from resources.lib.modules import libtools
		libtools.libtvshows().add(tvshowtitle, year, imdb, tmdb, tvdb)

	elif action == 'library_tvshowsToLibrary':
		from resources.lib.modules import libtools
		libtools.libtvshows().range(url, name)

	elif action == 'library_tvshowsListToLibrary':
		from resources.lib.menus import tvshows
		tvshows.TVshows().tvshowsListToLibrary(url)

	elif action == 'library_tvshowsToLibrarySilent':
		from resources.lib.modules import libtools
		libtools.libtvshows().silent(url)

	elif action == 'library_update':
		control.notification(message=32085)
		from resources.lib.modules import libtools
		libtools.libepisodes().update()
		libtools.libmovies().list_update()
		libtools.libtvshows().list_update()
		while True:
			if control.condVisibility('Library.IsScanningVideo'):
				control.sleep(3000)
				continue
			else:
				break
		control.sleep(1000)
		control.notification(message=32086)

	elif action == 'library_clean':
		from resources.lib.modules import libtools
		libtools.lib_tools().clean()

	elif action == 'library_setup':
		from resources.lib.modules import libtools
		libtools.lib_tools().total_setup()

	elif action == 'library_service':
		from resources.lib.modules import libtools
		libtools.lib_tools().service()


####################################################
#---Cache
####################################################
if action and action.startswith('cache_'):
	if action == 'cache_Navigator':
		from resources.lib.menus import navigator
		navigator.Navigator().cf()

	elif action == 'cache_clearAll':
		from resources.lib.menus import navigator
		navigator.Navigator().clearCacheAll()

	elif action == 'cache_clearSources':
		from resources.lib.menus import navigator
		navigator.Navigator().clearCacheProviders()

	elif action == 'cache_clearMeta':
		from resources.lib.menus import navigator
		navigator.Navigator().clearCacheMeta()

	elif action == 'cache_clearCache':
		from resources.lib.menus import navigator
		navigator.Navigator().clearCache()

	elif action == 'cache_clearSearch':
		from resources.lib.menus import navigator
		navigator.Navigator().clearCacheSearch() 

	elif action == 'cache_clearSearchPhrase':
		from resources.lib.menus import navigator
		navigator.Navigator().clearCacheSearchPhrase(source, name)

	elif action == 'cache_clearBookmarks':
		from resources.lib.menus import navigator
		navigator.Navigator().clearBookmarks()

	elif action == 'cache_clearBookmark':
		from resources.lib.menus import navigator
		navigator.Navigator().clearBookmark(name, year)

	elif action == 'cache_clearKodiBookmark': # context.venom action call only
		from resources.lib.modules import cache
		cache.clear_local_bookmark(url)