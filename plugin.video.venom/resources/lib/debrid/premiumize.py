# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

import re
import requests
import sys

try:
	from urllib import quote_plus, urlencode, unquote
except:
	from urllib.parse import quote_plus, urlencode, unquote

from resources.lib.modules import cache
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules.source_utils import supported_video_extensions

CLIENT_ID = '522962560' # used to auth
BaseUrl = 'https://www.premiumize.me/api'
folder_list_url = '%s/folder/list' % BaseUrl
folder_rename_url = '%s/folder/rename' % BaseUrl
folder_delete_url = '%s/folder/delete' % BaseUrl
item_details_url = '%s/item/details' % BaseUrl
item_delete_url = '%s/item/delete' % BaseUrl
item_rename_url = '%s/item/rename' % BaseUrl
transfer_create_url = '%s/transfer/create' % BaseUrl
transfer_directdl_url = '%s/transfer/directdl' % BaseUrl
transfer_list_url = '%s/transfer/list' % BaseUrl
transfer_clearfinished_url = '%s/transfer/clearfinished' % BaseUrl
transfer_delete_url = '%s/transfer/delete' % BaseUrl
account_info_url = '%s/account/info' % BaseUrl
cache_check_url = '%s/cache/check' % BaseUrl
list_services_path_url = '%s/services/list' % BaseUrl
pm_icon = control.joinPath(control.artPath(), 'premiumize.png')
addonFanart = control.addonFanart()
store_to_cloud = control.setting('premiumize.saveToCloud') == 'true'


class Premiumize:
	name = "Premiumize.me"

	def __init__(self):
		self.hosts = []
		self.patterns = []
		self.token = control.setting('premiumize.token')
		self.headers = {'User-Agent': 'Venom for Kodi', 'Authorization': 'Bearer %s' % self.token}
		self.server_notifications = False


	def _get(self, url):
		try:
			response = requests.get(url, headers=self.headers, timeout=15).json()
			if 'status' in response:
				if response.get('status') == 'success':
					return response
				if response.get('status') == 'error' and self.server_notifications:
					control.notification(message=response.get('message'))
		except:
			log_utils.error()
			pass
		return response


	def _post(self, url, data={}):
		try:
			response = requests.post(url, data, headers=self.headers, timeout=15).json()
			if 'status' in response:
				if response.get('status') == 'success':
					return response
				if response.get('status') == 'error' and self.server_notifications:
					control.notification(message=response.get('message'))
		except:
			log_utils.error()
			pass
		return response


	def auth(self):
		data = {'client_id': CLIENT_ID, 'response_type': 'device_code'}
		token = requests.post('https://www.premiumize.me/token', data=data, timeout=15).json()
		expiry = float(token['expires_in'])
		token_ttl = token['expires_in']
		poll_again = True
		success = False
		progressDialog = control.progressDialog
		progressDialog.create(control.lang(40054),
								line1=control.lang(32513) % token['verification_uri'],
								line2=control.lang(32514) % token['user_code'])
		progressDialog.update(0)
		while poll_again and not token_ttl <= 0 and not progressDialog.iscanceled():
			poll_again, success = self.poll_token(token['device_code'])
			progress_percent = 100 - int((float((expiry - token_ttl) / expiry) * 100))
			progressDialog.update(progress_percent)
			control.sleep(token['interval'] * 1000)
			token_ttl -= int(token['interval'])
		progressDialog.close()
		if success:
			control.notification(message=40052, icon=pm_icon)


	def poll_token(self, device_code):
		data = {'client_id': CLIENT_ID, 'code': device_code, 'grant_type': 'device_code'}
		token = requests.post('https://www.premiumize.me/token', data=data, timeout=15).json()
		if 'error' in token:
			if token['error'] == "access_denied":
				control.okDialog(title='default', message=control.lang(40020))
				return False, False
			return True, False
		self.token = token['access_token']
		self.headers = {'User-Agent': 'Venom for Kodi', 'Authorization': 'Bearer %s' % self.token}
		control.sleep(500)
		account_info = self.get_account_info()
		control.setSetting('premiumize.token', token['access_token'])
		control.setSetting('premiumize.username', str(account_info['customer_id']))
		return False, True


	def add_headers_to_url(self, url):
		return url + '|' + urlencode(self.headers)


	def get_account_info(self):
		try:
			accountInfo = self._get(account_info_url)
			return accountInfo
		except:
			log_utils.error()
			pass
		return None


	def account_info_to_dialog(self):
		from datetime import datetime
		import math
		try:
			accountInfo = self.get_account_info()
			expires = datetime.fromtimestamp(accountInfo['premium_until'])
			days_remaining = (expires - datetime.today()).days
			expires = expires.strftime("%A, %B %d, %Y")
			points_used = int(math.floor(float(accountInfo['space_used']) / 1073741824.0))
			space_used = float(int(accountInfo['space_used']))/1073741824
			percentage_used = str(round(float(accountInfo['limit_used']) * 100.0, 1))
			items = []
			items += [control.lang(40040) % accountInfo['customer_id']]
			items += [control.lang(40041) % expires]
			items += [control.lang(40042) % days_remaining]
			items += [control.lang(40043) % points_used]
			items += [control.lang(40044) % space_used]
			items += [control.lang(40045) % percentage_used]
			return control.selectDialog(items, 'Premiumize')
		except:
			log_utils.error()
			pass
		return


	def valid_url(self, host):
		try:
			self.hosts = self.get_hosts()
			if not self.hosts['Premiumize.me']: return False
			if any(host in item for item in self.hosts['Premiumize.me']):
				return True
			return False
		except:
			log_utils.error()


	def get_hosts(self):
		hosts_dict = {'Premiumize.me': []}
		hosts = []
		try:
			result = cache.get(self._get, 168, list_services_path_url)
			for x in result['directdl']:
				for alias in result['aliases'][x]:
					hosts.append(alias)
			hosts_dict['Premiumize.me'] = list(set(hosts))
		except:
			log_utils.error()
			pass
		return hosts_dict


# # from resolveURL
	# def get_all_hosters(self):
		# try:
			# response = self._get(list_services_path_url)
			# if not response:
				# return None
			# aliases = response.get('aliases', {})
			# patterns = response.get('regexpatterns', {})

			# tldlist = []
			# for tlds in aliases.values():
				# for tld in tlds:
					# tldlist.append(tld)
			# if self.get_setting('torrents') == 'true':
				# tldlist.extend([u'torrent', u'magnet'])
			# regex_list = []
			# for regexes in patterns.values():
				# for regex in regexes:
					# try:
						# regex_list.append(re.compile(regex))
					# except:
						# log_utils.log('Throwing out bad Premiumize regex: %s' % regex, __name__, log_utils.LOGDEBUG)
			# log_utils.log('Premiumize.me patterns: %s regex: (%d) hosts: %s' % (patterns, len(regex_list), tldlist), __name__, log_utils.LOGDEBUG)
			# return tldlist, regex_list
		# except Exception as e:
			# log_utils.log('Error getting Premiumize hosts: %s' % e, __name__, log_utils.LOGDEBUG)
		# return [], []


# # from resolveURL
	# def valid_url(self, url, host):
		# if url and self.get_setting('torrents') == 'true':
			# url_lc = url.lower()
			# if url_lc.endswith('.torrent') or url_lc.startswith('magnet:'):
				# return True
		# if not self.patterns or not self.hosts:
			# self.hosts, self.patterns = self.get_all_hosters()
		# if url:
			# if not url.endswith('/'):
				# url += '/'
			# for pattern in self.patterns:
				# if pattern.findall(url):
					# return True
		# elif host:
			# if host.startswith('www.'):
				# host = host.replace('www.', '')
			# if any(host in item for item in self.hosts):
				# return True
		# return False


	def unrestrict_link(self, link):
		try:
			data = {'src': link}
			response = self._post(transfer_directdl_url, data)
			try: return self.add_headers_to_url(response['content'][0]['link'])
			except: return None
		except:
			log_utils.error()
			return None


	def resolve_magnet(self, magnet_url, info_hash, season, episode, ep_title):
		from resources.lib.modules.source_utils import seas_ep_filter, episode_extras_filter
		try:
			file_url = None
			correct_files = []
			extensions = supported_video_extensions()
			extras_filtering_list = episode_extras_filter()
			data = {'src': magnet_url}
			response = self._post(transfer_directdl_url, data)
			if not 'status' in response or response['status'] != 'success':
				return None
			valid_results = [i for i in response.get('content') if any(i.get('path').lower().endswith(x) for x in extensions) and not i.get('link', '') == '']
			if len(valid_results) == 0:
				return
			if season:
				episode_title = re.sub('[^A-Za-z0-9-]+', '.', ep_title.replace('\'', '')).lower()
				for item in valid_results:
					if seas_ep_filter(season, episode, item['path'].split('/')[-1]):
						correct_files.append(item)
					if len(correct_files) == 0:
						continue
					for i in correct_files:
						compare_link = seas_ep_filter(season, episode, i['path'], split=True)
						compare_link = re.sub(episode_title, '', compare_link)
						if not any(x in compare_link for x in extras_filtering_list):
							file_url = i['link']
							break
			else:
				file_url = max(valid_results, key=lambda x: x.get('size')).get('link', None)
			if file_url:
				if store_to_cloud: self.create_transfer(magnet_url)
				return self.add_headers_to_url(file_url)
		except Exception as e:
			log_utils.log('Error resolve_magnet_pack: %s' % str(e), __name__, log_utils.LOGDEBUG)
			return None


	def display_magnet_pack(self, magnet_url, info_hash):
		try:
			end_results = []
			extensions = supported_video_extensions()
			data = {'src': magnet_url}
			result = self._post(transfer_directdl_url, data=data)
			if not 'status' in result or result['status'] != 'success':
				return None
			for item in result.get('content'):
				if any(item.get('path').lower().endswith(x) for x in extensions) and not item.get('link', '') == '':
					try:
						path = item['path'].split('/')[-1]
					except:
						path = item['path']
					end_results.append({'link': item['link'], 'filename': path, 'size': float(item['size'])/1073741824})
			return end_results
		except Exception as e:
			log_utils.log('Error display_magnet_pack: %s' % str(e), __name__, log_utils.LOGDEBUG)
			return None


	def add_uncached_torrent(self, magnet_url, pack=False):
		def _transfer_info(transfer_id):
			info = self.list_transfer()
			if 'status' in info and info['status'] == 'success':
				for item in info['transfers']:
					if item['id'] == transfer_id:
						return item
			return {}
		def _return_failed(message=control.lang(33586)):
			try:
				control.progressDialog.close()
			except:
				pass
			control.hide()
			control.sleep(500)
			control.okDialog(title=control.lang(40018), message=message)
			return False
		control.busy()
		extensions = supported_video_extensions()
		transfer_id = self.create_transfer(magnet_url)
		if not transfer_id:
			control.hide()
			return
		if not transfer_id['status'] == 'success':
			return _return_failed()
		transfer_id = transfer_id['id']
		transfer_info = _transfer_info(transfer_id)
		if not transfer_info:
			return _return_failed()
		if pack:
			# self.clear_cache()
			control.hide()
			control.okDialog(title='default', message=control.lang(40017) % control.lang(40057))
			return True
		interval = 5
		line1 = '%s...' % (control.lang(40017) % control.lang(40057))
		line2 = transfer_info['name']
		line3 = transfer_info['message']
		control.progressDialog.create(control.lang(40018), line1, line2, line3)
		while not transfer_info['status'] == 'seeding':
			control.sleep(1000 * interval)
			transfer_info = _transfer_info(transfer_id)
			line3 = transfer_info['message']
			control.progressDialog.update(int(float(transfer_info['progress']) * 100), line3=line3)
			if control.monitor.abortRequested():
				return sys.exit()
			try:
				if control.progressDialog.iscanceled():
					return _return_failed(control.lang(40014))
			except:
				pass
			if transfer_info.get('status') == 'stalled':
				return _return_failed()
		control.sleep(1000 * interval)
		try:
			control.progressDialog.close()
		except:
			log_utils.error()
			pass
		control.hide()
		return True


	def check_cache_item(self, media_id):
		try:
			media_id = media_id.encode('ascii', errors='ignore').decode('ascii', errors='ignore')
			media_id = media_id.replace(' ', '')
			url = '%s?items[]=%s' % (cache_check_url, media_id)
			result = requests.get(url, headers=self.headers).json()
			if 'status' in result:
				if result.get('status') == 'success':
					response = result.get('response', False)
					if isinstance(response, list):
						return response[0]
				if result.get('status') == 'error':
					control.notification(message=result.get('message'))
		except:
			log_utils.error()
			pass
		return False


	def check_cache_list(self, hashList):
		try:
			postData = {'items[]': hashList}
			response = requests.post(cache_check_url, data=postData, headers=self.headers, timeout=10).json()
			if 'status' in response:
				if response.get('status') == 'success':
					response = response.get('response', False)
					if isinstance(response, list):
						return response
		except:
			log_utils.error()
			pass
		return False


	def list_transfer(self):
		return self._get(transfer_list_url)


	def create_transfer(self, src,  folder_id=0):
		try:
			data = {'src': src, 'folder_id': folder_id}
			return self._post(transfer_create_url, data)
		except:
			log_utils.error()


	def clear_finished_transfers(self):
		try:
			response = self._post(transfer_clearfinished_url)
			if not response:
				return
			if 'status' in response:
				if response.get('status') == 'success':
					log_utils.log('Finished transfers successfully cleared from the Premiumize.me cloud', __name__, log_utils.LOGDEBUG)
					control.refresh()
					return
		except:
			log_utils.error()
			pass
		return


	def delete_transfer(self, media_id, folder_name=None):
		try:
			if not control.yesnoDialog(control.lang(40050) % folder_name, '', ''): return
			data = {'id': media_id}
			response = self._post(transfer_delete_url, data)
			if not response:
				return
			if 'status' in response:
				if response.get('status') == 'success':
					log_utils.log('Transfer successfully deleted from the Premiumize.me cloud', __name__, log_utils.LOGDEBUG)
					control.refresh()
					return
		except:
			log_utils.error()
			pass
		return


	def my_files(self, folder_id=None):
		try:
			if folder_id:
				url = folder_list_url + '?id=%s' % folder_id
			else:
				url = folder_list_url
			response = self._get(url)
			if response:
				return response.get('content')
		except:
			log_utils.error()
			pass
		return None


	def my_files_to_listItem(self, folder_id=None, folder_name=None):
		try:
			sysaddon = sys.argv[0]
			syshandle = int(sys.argv[1])
			extensions = supported_video_extensions()
			cloud_files = self.my_files(folder_id)
			if not cloud_files:
				control.notification(message='Request Failure-Empty Content')
				return
			cloud_files = [i for i in cloud_files if ('link' in i and i['link'].lower().endswith(tuple(extensions))) or i['type'] == 'folder']
			cloud_files = sorted(cloud_files, key=lambda k: k['name'])
			cloud_files = sorted(cloud_files, key=lambda k: k['type'], reverse=True)
		except:
			log_utils.error()
			return
		folder_str, file_str, downloadMenu, renameMenu, deleteMenu = control.lang(40046).upper(), control.lang(40047).upper(), control.lang(40048), control.lang(40049), control.lang(40050)
		for count, item in enumerate(cloud_files, 1):
			try:
				cm = []
				type = item['type']
				name = item['name']
				# name = control.strip_non_ascii_and_unprintable(item['name']) #keep an eye out if this is needed
				if type == 'folder':
					isFolder = True
					size = 0
					label = '%02d | [B]%s[/B] | [I]%s [/I]' % (count, folder_str, name)
					url = '%s?action=pm_MyFiles&id=%s&name=%s' % (sysaddon, item['id'], quote_plus(name))
				else:
					isFolder = False
					url_link = item['link']
					if url_link.startswith('/'):
						url_link = 'https' + url_link
					size = item['size']
					display_size = float(int(size))/1073741824
					label = '%02d | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, file_str, display_size, name)
					url = '%s?action=playURL&url=%s' % (sysaddon, url_link)
					cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=premiumize)' %
								(sysaddon, quote_plus(name), quote_plus(pm_icon), url_link)))
				cm.append((renameMenu % type.capitalize(), 'RunPlugin(%s?action=pm_Rename&type=%s&id=%s&name=%s)' %
								(sysaddon, type, item['id'], quote_plus(name))))
				cm.append((deleteMenu % type.capitalize(), 'RunPlugin(%s?action=pm_Delete&type=%s&id=%s&name=%s)' %
								(sysaddon, type, item['id'], quote_plus(name))))

				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': pm_icon, 'poster': pm_icon, 'thumb': pm_icon, 'fanart': addonFanart, 'banner': pm_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def user_transfers(self):
		try:
			response = self._get(transfer_list_url)
			if response:
				return response.get('transfers')
		except:
			log_utils.error()
			pass
		return None


	def user_transfers_to_listItem(self):
		try:
			sysaddon = sys.argv[0]
			syshandle = int(sys.argv[1])
			extensions = supported_video_extensions()
			transfer_files = self.user_transfers()
			if not transfer_files:
				control.notification(message='Request Failure-Empty Content')
				return
		except:
			log_utils.error()
			return
		folder_str, file_str, downloadMenu, renameMenu, deleteMenu, clearFinishedMenu = control.lang(40046).upper(),\
			control.lang(40047).upper(), control.lang(40048), control.lang(40049), control.lang(40050), control.lang(40051)
		for count, item in enumerate(transfer_files, 1):
			try:
				cm = []
				type = 'folder' if item['file_id'] is None else 'file'
				name = item['name']
				# name = control.strip_non_ascii_and_unprintable(item['name']) #keep an eye out if this is needed
				status = item['status']
				progress = item['progress']
				if status == 'finished':
					progress = 100
				else:
					try:
						progress = re.findall(r'(?:\d{0,1}\.{0,1})(\d+)', str(progress))[0][:2]
					except:
						progress = 'UNKNOWN'
				if type == 'folder':
					isFolder = True if status == 'finished' else False
					status_str = '[COLOR %s]%s[/COLOR]' % (control.getColor(control.setting('highlight.color')), status.capitalize())
					label = '%02d | [B]%s[/B] - %s | [B]%s[/B] | [I]%s [/I]' % (count, status_str, str(progress) + '%', folder_str, name)
					url = '%s?action=pm_MyFiles&id=%s&name=%s' % (sysaddon, item['folder_id'], quote_plus(name))

					# Till PM addresses issue with item also being removed from public acess if item not accessed for 60 days this option is disabled.
					# cm.append((clearFinishedMenu, 'RunPlugin(%s?action=pm_ClearFinishedTransfers)' % sysaddon))
				else:
					isFolder = False
					details = self.item_details(item['file_id'])
					if not details:
						control.notification(message='Request Failure-Empty Content')
						return
					url_link = details['link']
					if url_link.startswith('/'):
						url_link = 'https' + url_link
					size = details['size']
					display_size = float(int(size))/1073741824
					label = '%02d | %s%% | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, str(progress), file_str, display_size, name)
					url = '%s?action=playURL&url=%s' % (sysaddon, url_link)
					cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=premiumize)' %
								(sysaddon, quote_plus(name), quote_plus(pm_icon), url_link)))

				cm.append((deleteMenu % 'Transfer', 'RunPlugin(%s?action=pm_DeleteTransfer&id=%s&name=%s)' %
							(sysaddon, item['id'], quote_plus(name))))
				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': pm_icon, 'poster': pm_icon, 'thumb': pm_icon, 'fanart': addonFanart, 'banner': pm_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def item_details(self, item_id):
		try:
			data = {'id': item_id}
			itemDetails = self._post(item_details_url, data)
			return itemDetails
		except:
			log_utils.error()
			pass
		return None


	def rename(self, type, folder_id=None, folder_name=None):
		try:
			if type == 'folder':
				url = folder_rename_url
				t = control.lang(40049) % type
			else:
				if not control.yesnoDialog(control.lang(40049) % folder_name + ': [B](YOU MUST ENTER MATCHING FILE EXT.)[/B]', '', ''): return
				url = item_rename_url
				t = control.lang(40049) % type + ': [B](YOU MUST ENTER MATCHING FILE EXT.)[/B]'
			k = control.keyboard('', t)
			k.doModal()
			q = k.getText() if k.isConfirmed() else None
			if not q:
				return
			data = {'id': folder_id, 'name': q}
			response = self._post(url, data=data)
			if not response:
				return
			if 'status' in response:
				if response.get('status') == 'success':
					control.refresh()
		except:
			log_utils.error()
			pass


	def delete(self, type, folder_id=None, folder_name=None):
		try:
			if type == 'folder':
				url = folder_delete_url
			else:
				url = item_delete_url
			if not control.yesnoDialog(control.lang(40050) % folder_name, '', ''): return
			data = {'id': folder_id}
			response = self._post(url, data=data)
			if not response:
				return
			if 'status' in response:
				if response.get('status') == 'success':
					control.refresh()
		except:
			log_utils.error()
			pass