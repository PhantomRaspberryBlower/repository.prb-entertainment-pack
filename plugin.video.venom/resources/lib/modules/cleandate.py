# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

import datetime
import time
# Import _strptime to workaround python 2 bug with threads
import _strptime


def iso_2_utc(iso_ts):
	if not iso_ts: return 0
	delim = -1

	if not iso_ts.endswith('Z'):
		delim = iso_ts.rfind('+')
		if delim == -1:
			delim = iso_ts.rfind('-')

	if delim > -1:
		ts = iso_ts[:delim]
		sign = iso_ts[delim]
		tz = iso_ts[delim + 1:]
	else:
		ts = iso_ts
		tz = None

	if ts.find('.') > -1: ts = ts[:ts.find('.')]
	try: d = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S')
	except TypeError: d = datetime.datetime(*(time.strptime(ts, '%Y-%m-%dT%H:%M:%S')[0:6]))

	dif = datetime.timedelta()
	if tz:
		hours, minutes = tz.split(':')
		hours = int(hours)
		minutes = int(minutes)
		if sign == '-':
			hours = -hours
			minutes = -minutes
		dif = datetime.timedelta(minutes=minutes, hours=hours)

	utc_dt = d - dif
	epoch = datetime.datetime.utcfromtimestamp(0)
	delta = utc_dt - epoch

	try: seconds = delta.total_seconds()  # works only on 2.7
	except: seconds = delta.seconds + delta.days * 24 * 3600  # close enough
	return seconds