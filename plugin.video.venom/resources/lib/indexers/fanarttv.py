# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

import requests

from resources.lib.modules import control
from resources.lib.modules import log_utils

headers = {'api-key': '9f846e7ec1ea94fad5d8a431d1d26b43'}
client_key = control.setting('fanart.tv.api.key')
if not client_key:
	client_key = 'cf0ebcc2f7b824bd04cf3a318f15c17d'
headers.update({'client-key': client_key})

base_url = "http://webservice.fanart.tv/v3/%s/%s"
lang = control.apiLanguage()['trakt']
error_codes = ['500 Internal Server Error', '502 Bad Gateway', '504 Gateway Timeout']


def get_request(url):
	try:
		try:
			result = requests.get(url, headers=headers, timeout=5)
		except requests.exceptions.SSLError:
			result = requests.get(url, headers=headers, verify=False)
	except requests.exceptions.ConnectionError:
		control.notification(message='FANART.TV server Problems')
		log_utils.error()
		return None

	if '200' in str(result):
		# if '/tt' in url:
			# log_utils.log('requests.get() found - FANART.TV URL: %s (FOUND in IMDB)' % url, log_utils.LOGDEBUG)
		return result.json() 

	elif 'Not found' in str(result.text):
		log_utils.log('requests.get() failed - FANART.TV URL: %s (NOT FOUND)' % url, log_utils.LOGDEBUG)
		return None

	else:
		title = client.parseDOM(result.text, 'title')[0]
		log_utils.log('requests.get() failed - FANART.TV URL: %s (%s)' % (url, title), log_utils.LOGDEBUG)
		return None


def parse_art(img):
	if not img:
		return None
	try:
		ret_img = [(x['url'], x['likes']) for x in img if any(value == x.get('lang') for value in [lang, '00', ''])]
		if not ret_img:
			# log_utils.log('no matching artwork in %s' % img, __name__, log_utils.LOGDEBUG)
			return None
		if len(ret_img) >1:
			ret_img = sorted(ret_img, key=lambda x: int(x[1]), reverse=True)
		ret_img = [x[0] for x in ret_img][0]
	except:
		log_utils.error()
		return None
	return ret_img


def get_movie_art(imdb, tmdb):
	url = base_url % ('movies', tmdb)
	art = get_request(url)

	if art is None:
		url = base_url % ('movies', imdb)
		art = get_request(url)

	if art is None:
		return None

	try:
		if 'movieposter' not in art: raise Exception()
		poster2 = art['movieposter']
		poster2 = parse_art(poster2)
	except:
		poster2 = '0'

	try:
		if 'moviebackground' in art:
			fanart2 = art['moviebackground']
		else:
			if 'moviethumb' not in art: raise Exception()
			fanart2 = art['moviethumb']
		fanart2 = parse_art(fanart2)
	except:
		fanart2 = '0'

	try:
		if 'moviebanner' not in art: raise Exception()
		banner2 = art['moviebanner']
		banner2 = parse_art(banner2)
	except:
		banner2 = '0'

	try:
		if 'hdmovielogo' in art:
			clearlogo = art['hdmovielogo']
		else:
			if 'movielogo' not in art: raise Exception()
			clearlogo = art['movielogo']
		clearlogo = parse_art(clearlogo)
	except:
		clearlogo = '0'

	try:
		if 'hdmovieclearart' in art:
			clearart = art['hdmovieclearart']
		else:
			if 'movieart' not in art: raise Exception()
			clearart = art['movieart']
		clearart = parse_art(clearart)
	except:
		clearart = '0'

	try:
		if 'moviedisc' not in art: raise Exception()
		discart = art['moviedisc']
		discart = parse_art(discart)
	except:
		discart = '0'

	try:
		if 'moviethumb' in art:
			landscape = art['moviethumb']
		else:
			if 'moviebackground' not in art: raise Exception()
			landscape = art['moviebackground']
		landscape = parse_art(landscape)
	except:
		landscape = '0'

	# try:
		# keyart = art['movieposter']
		# keyart = [(x['url'], x['likes']) for x in keyart if any(value in x.get('lang') for value in ['00', 'None', None])]
		# keyart = sorted(keyart, key=lambda x: int(x[1]), reverse=True)
		# keyart = [x[0] for x in keyart][0]
	# except:
		# keyart = '0'

	extended_art = {'extended': True, 'poster2': poster2, 'fanart2': fanart2, 'banner2': banner2, 'clearlogo': clearlogo, 'clearart': clearart, 'discart': discart, 'landscape': landscape}
	# extended_art = {'extended': True, 'poster2': poster2, 'fanart2': fanart2, 'banner2': banner2, 'clearlogo': clearlogo, 'clearart': clearart, 'discart': discart, 'landscape': landscape, 'keyart': keyart}
	return extended_art


def get_tvshow_art(tvdb):
	if tvdb == '0':
		return None

	url = base_url % ('tv', tvdb)
	art = get_request(url)

	if art is None:
		return None

	try:
		if 'tvposter' not in art: raise Exception()
		poster2 = art['tvposter']
		poster2 = parse_art(poster2)
	except:
		poster2 = '0'

	try:
		if 'showbackground' not in art: raise Exception()
		fanart2 = art['showbackground']
		fanart2 = parse_art(fanart2)
	except:
		fanart2= '0'

	try:
		if 'tvbanner' not in art: raise Exception()
		banner2 = art['tvbanner']
		banner2 = parse_art(banner2)
	except:
		banner2 = '0'

	try:
		if 'hdtvlogo' in art:
			clearlogo = art['hdtvlogo']
		else:
			if 'clearlogo' not in art: raise Exception()
			clearlogo = art['clearlogo']
		clearlogo = parse_art(clearlogo)
	except:
		clearlogo = '0'

	try:
		if 'hdclearart' in art:
			clearart = art['hdclearart']
		else:
			if 'clearart' not in art: raise Exception()
			clearart = art['clearart']
		clearart = parse_art(clearart)
	except:
		clearart = '0'

	try:
		if 'tvthumb' in art:
			landscape = art['tvthumb']
		else:
			if 'showbackground' not in art: raise Exception()
			landscape = art['showbackground']
		landscape = parse_art(landscape)
	except:
		landscape = '0'
	extended_art = {'extended': True, 'poster2': poster2, 'banner2': banner2, 'fanart2': fanart2, 'clearlogo': clearlogo, 'clearart': clearart, 'landscape': landscape}
	return extended_art