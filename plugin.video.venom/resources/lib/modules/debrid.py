# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

from resources.lib.modules import control
from resources.lib.modules import log_utils

from resources.lib.debrid import alldebrid
from resources.lib.debrid import premiumize
from resources.lib.debrid import realdebrid


def debrid_resolvers(order_matters=True):
	try:
		ad_enabled = control.setting('alldebrid.token') != ''
		pm_enabled = control.setting('premiumize.token') != ''
		rd_enabled = control.setting('realdebrid.token') != ''

		premium_resolvers = []
		if ad_enabled: premium_resolvers.append(alldebrid.AllDebrid())
		if pm_enabled: premium_resolvers.append(premiumize.Premiumize())
		if rd_enabled: premium_resolvers.append(realdebrid.RealDebrid())

		if order_matters:
			premium_resolvers.sort(key=lambda x: get_priority(x))
			# log_utils.log('premium_resolvers sorted = %s' % str(premium_resolvers), __name__, log_utils.LOGNOTICE)
		return premium_resolvers
	except:
		log_utils.error()
		pass


def status():
	return debrid_resolvers() != []


def get_priority(cls):
	# log_utils.log('cls __name__ priority = %s' % str(cls.__class__.__name__ + '.priority').lower(), __name__, log_utils.LOGNOTICE)
	# log_utils.log('cls __name__ priority setting = %s' % str(control.setting((cls.__class__.__name__ + '.priority').lower())), __name__, log_utils.LOGNOTICE)
	try:
		return int(control.setting((cls.__class__.__name__ + '.priority').lower()))
	except:
		log_utils.error()
		return 10


# def resolver(url, debrid):
	# try:
		# debrid_resolver = [resolver for resolver in debrid_resolvers if resolver.name == debrid][0]
		# debrid_resolver.login()
		# _host, _media_id = debrid_resolver.get_host_and_id(url)
		# stream_url = debrid_resolver.get_media_url(_host, _media_id)
		# return stream_url
	# except Exception as e:
		# log_utils.log('%s Resolve Failure: %s' % (debrid, e), log_utils.LOGWARNING)
		# return None