# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

try:
	from sqlite3 import dbapi2 as database
except:
	from pysqlite2 import dbapi2 as database

from resources.lib.modules import cleandate
from resources.lib.modules import control
from resources.lib.modules import log_utils


def fetch_bookmarks(imdb, tmdb='', tvdb='', season=None, episode=None):
	try:
		if not control.existsPath(control.dataPath):
			control.makeFile(control.dataPath)
		dbcon = database.connect(control.traktSyncFile)
		dbcur = dbcon.cursor()
		dbcur.execute("CREATE TABLE IF NOT EXISTS bookmarks (""imdb TEXT, ""tmdb TEXT, ""tvdb TEXT, ""season TEXT, ""episode TEXT, ""percent_played TEXT, ""paused_at TEXT"", UNIQUE(imdb, tmdb, tvdb, season, episode)"");")
		dbcur.connection.commit()
	except:
		log_utils.error()
		try: dbcon.close()
		except: pass
		return items

	progress = '0'
	type = 'episode' if episode else 'movie'
	try:
		if type == 'movie':
			try:
				# Lookup both IMDb and TMDb for more accurate match.
				dbcur.execute("SELECT * FROM bookmarks WHERE (imdb = '%s' and tmdb = '%s' and not imdb = '' and not tmdb = '')" % (imdb, tmdb))
				match = dbcur.fetchone()
				progress = match[5]
				# if match: progress = eval(match[5].encode('utf-8'))
				# log_utils.log('progress = %s' % str(progress), __name__, log_utils.LOGDEBUG)
			except:
				try:
					dbcur.execute("SELECT * FROM bookmarks WHERE (imdb = '%s' AND not imdb = '')" % imdb)
					match = dbcur.fetchone()
					progress = match[5]
					# if match: progress = eval(match[5].encode('utf-8'))
				except:
					pass
		else:
			try:
				# Lookup both IMDb and TVDb for more accurate match.
				dbcur.execute("SELECT * FROM bookmarks WHERE (imdb = '%s' and tvdb = '%s' and season = '%s' and episode = '%s' and not imdb = '' and not tvdb = '')" % (imdb, tvdb, season, episode))
				match = dbcur.fetchone()
				progress = match[5]
				# if match: progress = eval(match[5].encode('utf-8'))
			except:
				try:
					dbcur.execute("SELECT * FROM bookmarks WHERE (tvdb = '%s' and season = '%s' and episode = '%s' and not tvdb = '')" % (tvdb, season, episode))
					match = dbcur.fetchone()
					progress = match[5]
					# if match: progress = eval(match[5].encode('utf-8'))
				except: pass
	except:
		log_utils.error()
		pass
	try: dbcon.close()
	except: pass
	return progress


def insert_bookmarks(items):
	try:
		if not control.existsPath(control.dataPath):
			control.makeFile(control.dataPath)
		dbcon = database.connect(control.traktSyncFile)
		dbcur = dbcon.cursor()
		dbcur.execute("CREATE TABLE IF NOT EXISTS bookmarks (""imdb TEXT, ""tmdb TEXT, ""tvdb TEXT, ""season TEXT, ""episode TEXT, ""percent_played TEXT, ""paused_at TEXT"", UNIQUE(imdb, tmdb, tvdb, season, episode)"");")
		for i in items:
			imdb, tmdb, tvdb, season, episode = '', '', '', '', ''
			if i.get('type') == 'episode':
				ids = i.get('show').get('ids')
				imdb, tmdb, tvdb, season, episode = str(ids.get('imdb', '')), str(ids.get('tmdb', '')), str(ids.get('tvdb', '')), str(i.get('episode').get('season')), str(i.get('episode').get('number'))
			else:
				ids = i.get('movie').get('ids')
				imdb, tmdb = str(ids.get('imdb', '')), str(ids.get('tmdb', ''))
			try: dbcur.execute("INSERT OR REPLACE INTO bookmarks Values (?, ?, ?, ?, ?, ?, ?)", (imdb, tmdb, tvdb, season, episode, i.get('progress', ''), i.get('paused_at', '')))
			except:
				log_utils.error()
				pass
		dbcur.connection.commit()
	except:
		log_utils.error()
		pass
	try: dbcon.close()
	except: pass
	return


def delete_bookmark(items):
	try:
		if not control.existsPath(control.dataPath):
			control.makeFile(control.dataPath)
		dbcon = database.connect(control.traktSyncFile)
		dbcur = dbcon.cursor()
		dbcur.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='bookmarks';")
		ck_table = dbcur.fetchone()
		if not ck_table:
			dbcur.execute("CREATE TABLE IF NOT EXISTS bookmarks (""imdb TEXT, ""tmdb TEXT, ""tvdb TEXT, ""season TEXT, ""episode TEXT, ""percent_played TEXT, ""paused_at TEXT"", UNIQUE(imdb, tmdb, tvdb, season, episode)"");")
			dbcur.connection.commit()
			cursor.close()
			return
		for i in items:
			if i.get('type') == 'episode':
				ids = i.get('show').get('ids')
				imdb, tvdb, season, episode, = str(ids.get('imdb', '')), str(ids.get('tvdb', '')), str(i.get('episode').get('season')), str(i.get('episode').get('number'))
			else:
				tvdb, season, episode = '', '', ''
				ids = i.get('movie').get('ids')
				imdb = str(ids.get('imdb', ''))
			try: dbcur.execute("DELETE FROM bookmarks WHERE imdb = '%s' AND tvdb = '%s' AND season = '%s' AND episode = '%s'" % (imdb, tvdb, season, episode))
			except:
				log_utils.error()
				pass
		dbcur.connection.commit()
	except:
		log_utils.error()
		pass
	try: dbcon.close()
	except: pass
	return



def last_paused_at():
	try:
		if not control.existsPath(control.dataPath):
			control.makeFile(control.dataPath)
		dbcon = database.connect(control.traktSyncFile)
		dbcur = dbcon.cursor()
		dbcur.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='bookmarks';")
		ck_table = dbcur.fetchone()
		if not ck_table:
			dbcur.execute("CREATE TABLE IF NOT EXISTS bookmarks (""imdb TEXT, ""tmdb TEXT, ""tvdb TEXT, ""season TEXT, ""episode TEXT, ""percent_played TEXT, ""paused_at TEXT"", UNIQUE(imdb, tmdb, tvdb, season, episode)"");")
			dbcur.connection.commit()
			cursor.close()
			return 0
		match = dbcur.execute("SELECT * FROM bookmarks ORDER BY paused_at DESC LIMIT 1").fetchone()
		return int(cleandate.iso_2_utc(match[6]))
	except:
		log_utils.error()
		try: dbcon.close()
		except: pass
		return 0
