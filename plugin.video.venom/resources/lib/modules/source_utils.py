# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

import re

try:
	from urllib import unquote, unquote_plus
except:
	from urllib.parse import unquote, unquote_plus

from resources.lib.modules import log_utils

HDCAM = ['hdcam', '.hd.cam.', 'hdts', '.hd.ts.', '.hdtc.', '.hd.tc.', '.hctc.', 'hc.tc.']

CODEC_H265 = ['hevc', 'h265', 'h.265', 'x265', 'x.265']
CODEC_H264 = ['avc', 'h264', 'h.264', 'x264', 'x.264']
CODEC_XVID = ['xvid', 'x.vid']
CODEC_DIVX = ['divx', 'divx ', 'div2', 'div2 ', 'div3']
CODEC_MPEG = ['mpeg', 'm4v', 'mpg', 'mpg1', 'mpg2', 'mpg3', 'mpg4', 'mp4 ', '.mp.4.', 'msmpeg', 'msmpeg4',
							'msmpeg.4.', 'mpegurl']
CODEC_MKV = ['mkv', '.mkv', 'matroska']

AUDIO_8CH = ['ch8.', '8ch.', '.7.1.']
AUDIO_7CH = ['ch7.', '7ch.', '.6.1.']
AUDIO_6CH = ['ch6.', '6ch.', '.5.1.']
AUDIO_2CH = ['ch2.', '2ch.', '2.0', 'audio.2.0.', 'stereo']

MULTI_LANG = ['hindi.eng', 'ara.eng', 'ces.eng', 'chi.eng', 'cze.eng', 'dan.eng', 'dut.eng', 'ell.eng', 'esl.eng',
			  'esp.eng', 'fin.eng', 'fra.eng', 'fre.eng', 'frn.eng', 'gai.eng', 'ger.eng', 'gle.eng', 'gre.eng',
			  'gtm.eng', 'heb.eng', 'hin.eng', 'hun.eng', 'ind.eng', 'iri.eng', 'ita.eng', 'jap.eng', 'jpn.eng', 'kor.eng',
			  'lat.eng', 'lebb.eng', 'lit.eng', 'nor.eng', 'pol.eng', 'por.eng', 'rus.eng', 'som.eng', 'spa.eng', 'sve.eng',
			  'swe.eng', 'tha.eng', 'tur.eng', 'uae.eng', 'ukr.eng', 'vie.eng', 'zho.eng', 'dual.audio', 'multi']

SUBS = ['subita', 'subfrench', 'subs', 'subspanish', 'subtitula', 'swesub']
ADDS = ['1xbet', 'betwin']


def seas_ep_filter(season, episode, release_title, split=False):
	try:
		release_title = re.sub('[^A-Za-z0-9-]+', '.', unquote(release_title).replace('\'', '')).lower()
		string1 = '(s<<S>>e<<E>>)|' \
				'(s<<S>>\.e<<E>>)|' \
				'(s<<S>>ep<<E>>)|' \
				'(s<<S>>\.ep<<E>>)'
		string2 = '(season\.<<S>>\.episode\.<<E>>)|' \
				'(season<<S>>\.episode<<E>>)|' \
				'(season<<S>>episode<<E>>)|' \
				'(s<<S>>e\(<<E>>\))|' \
				'(s<<S>>\.e\(<<E>>\))|' \
				'(<<S>>x<<E>>\.)|' \
				'(<<S>>\.<<E>>\.)'
		string3 = '(<<S>><<E>>\.)'
		string4 = '(s<<S>>e<<E1>>e<<E2>>)|' \
				'(s<<S>>e<<E1>>-e<<E2>>)|' \
				'(s<<S>>e<<E1>>\.e<<E2>>)|' \
				'(s<<S>>e<<E1>>-<<E2>>)|' \
				'(s<<S>>e<<E1>>\.<<E2>>)|' \
				'(s<<S>>e<<E1>><<E2>>)'
		string_list = []
		string_list.append(string1.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string1.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string2.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string2.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string2.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode)))
		string_list.append(string2.replace('<<S>>', str(season)).replace('<<E>>', str(episode)))
		string_list.append(string3.replace('<<S>>', str(season).zfill(2)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string3.replace('<<S>>', str(season)).replace('<<E>>', str(episode).zfill(2)))
		string_list.append(string4.replace('<<S>>', str(season).zfill(2)).replace('<<E1>>', str(int(episode)-1).zfill(2)).replace('<<E2>>', str(episode).zfill(2)))
		string_list.append(string4.replace('<<S>>', str(season).zfill(2)).replace('<<E1>>', str(episode).zfill(2)).replace('<<E2>>', str(int(episode)+1).zfill(2)))
		final_string = '|'.join(string_list)
		# log_utils.log('final_string = %s' % str(final_string), __name__, log_utils.LOGDEBUG)
		reg_pattern = re.compile(final_string)
		if split:
			return release_title.split(re.search(reg_pattern, release_title).group(), 1)[1]
		else:
			return bool(re.search(reg_pattern, release_title))
	except:
		log_utils.error()
		return None


def episode_extras_filter():
	return ['extra', 'extras', 'deleted', 'unused', 'footage', 'inside', 'blooper', 'bloopers', 'making of', 'feature', 'sample']


def supported_video_extensions():
	import xbmc
	supported_video_extensions = xbmc.getSupportedMedia('video').split('|')
	return [i for i in supported_video_extensions if i != '' and i != '.zip']


def getFileType(url):
	try:
		type = ''
		fmt = url_strip(url)
		# log_utils.log('fmt = %s' % fmt, log_utils.LOGDEBUG)
		if fmt is None:
			return type
		if any(value in fmt for value in ['blu.ray', 'bluray', '.bd.']):
			type += ' BLURAY /'
		if any(value in fmt for value in ['bd.r', 'bdr', 'bd.rip', 'bdrip', 'br.rip', 'brrip']):
			type += ' BR-RIP /'
		if 'remux' in fmt:
			type += ' REMUX /'
		if any(i in fmt for i in ['dvd.rip', 'dvdrip']):
			type += ' DVD /'
		if any(value in fmt for value in ['web.dl', 'webdl', 'web.rip', 'webrip']):
			type += ' WEB /'
		if 'hdtv' in fmt:
			type += ' HDTV /'
		if 'sdtv' in fmt:
			type += ' SDTV /'
		if any(value in fmt for value in ['hd.rip', 'hdrip']):
			type += ' HDRIP /'
		if 'hdr.' in fmt:
			type += ' HDR /'
		if any(value in fmt for value in ['dd.5.1.', 'dd.5.1ch.', 'dd5.1.', 'dolby.digital', 'dolbydigital']):
			type += ' DOLBYDIGITAL /'
		if any(value in fmt for value in ['.dd.ex.', 'ddex', 'dolby.ex.', 'dolby.digital.ex.', 'dolbydigital.ex.']):
			type += ' DD-EX /'
		if any(value in fmt for value in ['dolby.digital.plus', 'dolbydigital.plus', 'dolbydigitalplus', 'dd.plus.', 'ddplus']):
			type += ' DD+ /'
		if any(value in fmt for value in ['dd.7.1ch', 'dd.true.hd.', 'dd.truehd', 'ddtruehd']):
			type += ' DOLBY-TRUEHD /'
		if 'atmos' in fmt:
			type += ' ATMOS /'
		if '.dts.' in fmt:
			type += ' DTS /'
		if any(value in fmt for value in ['dts.hd.', 'dtshd']):
			type += ' DTS-HD /'
		if any(value in fmt for value in ['dts.hd.ma.', 'dtshd.ma.', 'dtshdma', '.hd.ma.', 'hdma']):
			type += ' DTS-HD MA/'
		if any(value in fmt for value in ['dts.x.', 'dtsx']):
			type += ' DTS-X /'
		if any(value in fmt for value in AUDIO_8CH):
			type += ' 8CH /'
		if any(value in fmt for value in AUDIO_7CH):
			type += ' 7CH /'
		if any(value in fmt for value in AUDIO_6CH):
			type += ' 6CH /'
		if any(value in fmt for value in AUDIO_2CH):
			type += ' 2CH /'
		if any(value in fmt for value in CODEC_XVID):
			type += ' XVID /'
		if any(value in fmt for value in CODEC_DIVX):
			type += ' DIVX /'
		if any(value in fmt for value in CODEC_MPEG):
			type += ' MPEG /'
		if '.avi' in fmt:
			type += ' AVI /'
		if any(value in fmt for value in ['.ac3', '.ac.3.']):
			type += ' AC3 /'
		if any(value in fmt for value in CODEC_H264):
			type += ' X264 /'
		if any(value in fmt for value in CODEC_H265):
			type += ' X265 /'
		if any(value in fmt for value in CODEC_MKV):
			type += ' MKV /'
		if any(value in fmt for value in HDCAM):
			type += ' HDCAM /'
		if any(value in fmt for value in MULTI_LANG):
			type += ' MULTI-LANG /'
		if any(value in fmt for value in ADDS):
			type += ' ADDS /'
		if any(value in fmt for value in SUBS):
			if type != '':
				type += ' WITH SUBS'
			else:
				type = 'SUBS'
		type = type.rstrip('/')
		return type
	except:
		log_utils.error()
		return ''


def url_strip(url):
	try:
		url = unquote_plus(url)
		if 'magnet' in url:
			url = url.split('&dn=')[1]
		url = url.lower().replace("'", "").lstrip('.').rstrip('.')
		fmt = re.sub('[^a-z0-9]+', '.', url)
		fmt = '.%s.' % fmt
		fmt = re.sub(r'(.+)((?:19|20)[0-9]{2}|season.\d+|s[0-3]{1}[0-9]{1}|e\d+|complete)(.complete\.|.episode\.\d+\.|.episodes\.\d+\.\d+\.|.series|.extras|.ep\.\d+\.|.\d{1,2}\.|-|\.|\s)', '', fmt) # new for pack files
		if '.http' in fmt:
			fmt = None
		if fmt == '':
			return None
		else:
			return '.%s' % fmt
	except:
		log_utils.error()
		return None
