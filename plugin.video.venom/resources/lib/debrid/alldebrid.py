# -*- coding: utf-8 -*-


import json
import re
import requests
import sys

try:
	from urllib import quote_plus
except:
	from urllib.parse import quote_plus

from resources.lib.modules import cache
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules.source_utils import supported_video_extensions

base_url = 'https://api.alldebrid.com/v4/'
# user_agent = 'Venom for Kodi'
user_agent = 'Venom%20for%20Kodi'
ad_icon = control.joinPath(control.artPath(), 'alldebrid.png')
addonFanart = control.addonFanart()
store_to_cloud = control.setting('alldebrid.saveToCloud') == 'true'


class AllDebrid:
	name = "AllDebrid"

	def __init__(self):
		self.token = control.setting('alldebrid.token')
		self.timeout = 15.0
		self.server_notifications = True


	def _get(self, url, url_append=''):
		response = None
		try:
			if self.token == '': return None
			url = base_url + url + '?agent=%s&apikey=%s' % (user_agent, self.token) + url_append
			response = requests.get(url, timeout=self.timeout).json()
			# log_utils.log('response = %s' % response, __name__, log_utils.LOGDEBUG)
			if 'status' in response:
				if response.get('status') == 'success':
					if 'data' in response:
						response = response['data']
				elif response.get('status') == 'error' and self.server_notifications:
					control.notification(message=response.get('error').get('message'))
					return None
		except requests.exceptions.ConnectionError:
			control.notification(message='Failed to connect to All Debrid', icon=ad_icon)
		except BaseException:
			log_utils.error()
			pass
		return response


	def _post(self, url, data={}):
		response = None
		try:
			if self.token == '': return None
			url = base_url + url + '?agent=%s&apikey=%s' % (user_agent, self.token)
			response = requests.post(url, data=data, timeout=self.timeout).json()
			if 'status' in response:
				if response.get('status') == 'success':
					if 'data' in response:
						response = response['data']
				elif response.get('status') == 'error' and self.server_notifications:
					control.notification(message=response.get('error').get('message'))
					return None
		except requests.exceptions.ConnectionError:
			control.notification(message='Failed to connect to All Debrid', icon=ad_icon)
		except BaseException:
			log_utils.error()
			pass
		return response


	def auth_loop(self):
		control.sleep(5000)
		response = requests.get(self.check_url, timeout=self.timeout).json()
		response = response['data']
		if 'error' in response:
			self.token = 'failed'
			return control.notification(message=40021)
		if response['activated']:
			try:
				control.progressDialog.close()
				self.token = str(response['apikey'])
				control.setSetting('alldebrid.token', self.token)
			except:
				self.token = 'failed'
				return control.notification(message=40021)
		return


	def auth(self):
		self.token = ''
		url = base_url + 'pin/get?agent=%s' % user_agent
		response = requests.get(url, timeout=self.timeout).json()
		response = response['data']
		control.progressDialog.create(control.lang(40056))
		control.progressDialog.update(-1,
				control.lang(32513) % 'https://alldebrid.com/pin/',
				control.lang(32514) % response['pin'])
		self.check_url = response.get('check_url')
		control.sleep(2000)
		while not self.token:
			if control.progressDialog.iscanceled():
				control.progressDialog.close()
				break
			self.auth_loop()
		if self.token in (None, '', 'failed'):
			return
		control.sleep(2000)
		account_info = self._get('user')
		control.notification(message=40010, icon=pm_icon)


	def account_info(self):
		response = self._get('user')
		return response


	def account_info_to_dialog(self):
		from datetime import datetime
		try:
			account_info = self.account_info()['user']
			username = account_info['username']
			email = account_info['email']
			status = 'Premium' if account_info['isPremium'] else 'Not Active'
			expires = datetime.fromtimestamp(account_info['premiumUntil'])
			days_remaining = (expires - datetime.today()).days
			heading = control.lang(40059).upper()
			items = []
			items += [control.lang(40036) % username]
			items += [control.lang(40035) % email]
			items += [control.lang(40037) % status]
			items += [control.lang(40041) % expires]
			items += [control.lang(40042) % days_remaining]
			return control.selectDialog(items, 'All Debrid')
		except:
			log_utils.error()
			pass
		return


	def check_cache(self, hashes):
		try:
			data = {'magnets[]': hashes}
			response = self._post('magnet/instant', data)
			try: return response
			except: return None
		except:
			log_utils.error()
			return None


	def check_single_magnet(self, hash_string):
		try:
			cache_info = self.check_cache(hash_string)['magnets'][0]
			try: return cache_info['instant']
			except: return None
		except:
			log_utils.error()
			return None


	def unrestrict_link(self, link):
		try:
			url = 'link/unlock'
			url_append = '&link=%s' % link
			response = self._get(url, url_append)
			try: return response['link']
			except: return None
		except:
			log_utils.error()
			return None


	def create_transfer(self, magnet):
		try:
			url = 'magnet/upload'
			url_append = '&magnet=%s' % magnet
			result = self._get(url, url_append)
			result = result['magnets'][0]
			log_utils.log('All Debrid: Sending MAGNET URL %s to the All Debrid cloud' % magnet, __name__, log_utils.LOGDEBUG)
			try: return result.get('id', "")
			except: return None
		except:
			log_utils.error()
		return None


	def list_transfer(self, transfer_id):
		try:
			url = 'magnet/status'
			url_append = '&id=%s' % transfer_id
			result = self._get(url, url_append)
			try: return result['magnets']
			except: return None
		except:
			log_utils.error()
			return None


	def delete_transfer(self, transfer_id, folder_name=None, silent=True):
		try:
			if not silent:
				if not control.yesnoDialog(control.lang(40050) % folder_name, '', ''): return
			url = 'magnet/delete'
			url_append = '&id=%s' % transfer_id
			response = self._get(url, url_append)
			if silent:
				return
			else:
				if response and 'message' in response:
					control.notification(message=response.get('message'))
					log_utils.log('%s successfully deleted from the All Debrid cloud' % folder_name, __name__, log_utils.LOGDEBUG)
					control.refresh()
					return
		except:
			log_utils.error()
			pass


	def restart_transfer(self, transfer_id, folder_name=None, silent=True):
		try:
			if not silent:
				if not control.yesnoDialog(control.lang(40007) % folder_name, '', ''): return
			url = 'magnet/restart'
			url_append = '&id=%s' % transfer_id
			response = self._get(url, url_append)
			if silent:
				return
			else:
				if response and 'message' in response:
					control.notification(message=response.get('message'))
					control.refresh()
					return
		except:
			log_utils.error()
			pass


	def user_cloud(self):
		url = 'magnet/status'
		return self._get(url)


	def user_transfers_to_listItem(self):
		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		transfer_files = self.user_cloud()['magnets']
		if not transfer_files:
			control.notification(message='Request Failure-Empty Content')
			return
		folder_str, deleteMenu, restartMenu = control.lang(40046).upper(), control.lang(40050), control.lang(40008)
		for count, item in enumerate(transfer_files, 1):
			# log_utils.log('item = %s' % str(item), __name__, log_utils.LOGDEBUG)
			try:
				status_code = item['statusCode'] 
				if status_code in (0,1, 2, 3):
					active = True
					downloaded = item['downloaded']
					size = item['size']
					try: percent = str(round(float(downloaded) / size * 100, 1))
					except: percent = '0'
				else:
					active = False
				folder_name = item['filename']
				# normalized_folder_name = normalize(folder_name)
				id = item['id']
				status_str = '[COLOR %s]%s[/COLOR]' % (control.getColor(control.setting('highlight.color')), item['status'].capitalize())
				if active:
					label = '%02d | [B]%s[/B] - %s | [B]%s[/B]' % (count, status_str, str(percent) + '%', folder_name)
				else:
					label = '%02d | [B]%s[/B] | [B]%s[/B] | [I]%s [/I]' % (count, status_str, folder_str, folder_name)
				if status_code == 4:
					url = '%s?action=ad_BrowseUserCloud&source=%s' % (sysaddon, json.dumps(item))
					isFolder = True
				else:
					url = ''
					isFolder = False
				cm = []
				cm.append((deleteMenu % 'Transfer', 'RunPlugin(%s?action=ad_DeleteTransfer&id=%s&name=%s)' %
					(sysaddon, id, folder_name)))
				if status_code in (6, 7, 9, 10):
					cm.append((restartMenu, 'RunPlugin(%s?action=ad_RestartTransfer&id=%s&name=%s)' %
						(sysaddon, id, folder_name)))
				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': ad_icon, 'poster': ad_icon, 'thumb': ad_icon, 'fanart': addonFanart, 'banner': ad_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def user_cloud_to_listItem(self, folder_id=None):
		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		folder_str, deleteMenu = control.lang(40046).upper(), control.lang(40050)
		cloud_dict = self.user_cloud()['magnets']
		cloud_dict = [i for i in cloud_dict if i['statusCode'] == 4]
		for count, item in enumerate(cloud_dict, 1):
			try:
				cm = []
				folder_name = item['filename']
				# normalized_folder_name = normalize(folder_name)
				id = item['id']
				status_str = '[COLOR %s]%s[/COLOR]' % (control.getColor(control.setting('highlight.color')), item['status'].capitalize())
				label = '%02d | [B]%s[/B] | [B]%s[/B] | [I]%s [/I]' % (count, status_str, folder_str, folder_name)
				url = '%s?action=ad_BrowseUserCloud&source=%s' % (sysaddon, json.dumps(item))
				cm.append((deleteMenu % 'Transfer', 'RunPlugin(%s?action=ad_DeleteTransfer&id=%s&name=%s)' %
					(sysaddon, id, folder_name)))
				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': ad_icon, 'poster': ad_icon, 'thumb': ad_icon, 'fanart': addonFanart, 'banner': ad_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def browse_user_cloud(self, folder):
		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		extensions = supported_video_extensions()
		torrent_folder = json.loads(folder)
		links = torrent_folder['links']
		links = [i for i in links if i['filename'].lower().endswith(tuple(extensions))]
		status_code = torrent_folder['statusCode'] 
		file_str, downloadMenu, deleteMenu = control.lang(40047).upper(), control.lang(40048), control.lang(40050)

		for count, item in enumerate(links, 1):
			try:
				cm = []
				url_link = item['link']
				# name = clean_file_name(item['filename']).upper()
				name = item['filename']
				size = item['size']
				display_size = float(int(size))/1073741824
				label = '%02d | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, file_str, display_size, name)
				if status_code == 4:
					url = '%s?action=playURL&url=%s&caller=alldebrid&type=unrestrict' % (sysaddon, url_link)
				else:
					url = ''
				cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=alldebrid)' %
								(sysaddon, quote_plus(name), quote_plus(ad_icon), url_link)))
				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': ad_icon, 'poster': ad_icon, 'thumb': ad_icon, 'fanart': addonFanart, 'banner': ad_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def resolve_magnet(self, magnet_url, info_hash, season, episode, ep_title):
		from resources.lib.modules.source_utils import seas_ep_filter, episode_extras_filter
		try:
			file_url = None
			correct_files = []
			extensions = supported_video_extensions()
			extras_filtering_list = episode_extras_filter()
			transfer_id = self.create_transfer(magnet_url)
			transfer_info = self.list_transfer(transfer_id)
			if season:
				valid_results = [i for i in transfer_info.get('links') if any(i.get('filename').lower().endswith(x) for x in extensions) and not i.get('link', '') == '']
				if len(valid_results) == 0:
					return
				for item in valid_results:
					if seas_ep_filter(season, episode, item['filename']):
						correct_files.append(item)
					if len(correct_files) == 0:
						continue
					episode_title = re.sub('[^A-Za-z0-9-]+', '.', ep_title.replace('\'', '')).lower()
					for i in correct_files:
						compare_link = seas_ep_filter(season, episode, i['filename'], split=True)
						compare_link = re.sub(episode_title, '', compare_link)
						if not any(x in compare_link for x in extras_filtering_list):
							media_id = i['link']
							break
			else:
				sources = [(link.get('size'), link.get('link'))
						for link in transfer_info.get('links')
						if any(link.get('filename').lower().endswith(x) for x in extensions)]
				media_id = max(sources)[1]
			if not store_to_cloud:
				self.delete_transfer(transfer_id)
			file_url = self.unrestrict_link(media_id)
			return file_url
		except:
			log_utils.error()
			if transfer_id:
				self.delete_transfer(transfer_id)
			return None


	def display_magnet_pack(self, magnet_url, info_hash):
		try:
			extensions = supported_video_extensions()
			transfer_id = self.create_transfer(magnet_url)
			transfer_info = self.list_transfer(transfer_id)
			end_results = []
			for item in transfer_info.get('links'):
				if any(item.get('filename').lower().endswith(x) for x in extensions) and not item.get('link', '') == '':
					end_results.append({'link': item['link'], 'filename': item['filename'], 'size': item['size']})
			self.delete_transfer(transfer_id)
			return end_results
		except:
			log_utils.error()
			if transfer_id:
				self.delete_transfer(transfer_id)
			return None


	def add_uncached_torrent(self, magnet_url, pack=False):
		def _return_failed(message=control.lang(33586)):
			try:
				control.progressDialog.close()
			except:
				pass
			self.delete_transfer(transfer_id)
			control.hide()
			control.sleep(500)
			control.okDialog(title=control.lang(40018), message=message)
			return False
		control.busy()
		transfer_id = self.create_transfer(magnet_url)
		if not transfer_id:
			return _return_failed()
		transfer_info = self.list_transfer(transfer_id)
		if not transfer_info:
			return _return_failed()
		if pack:
			# self.clear_cache()
			control.hide()
			control.okDialog(title='default', message=control.lang(40017) % control.lang(40059))
			return True
		interval = 5
		line1 = '%s...' % (control.lang(40017) % control.lang(40059))
		line2 = transfer_info['filename']
		line3 = transfer_info['status']
		control.progressDialog.create(control.lang(40018), line1, line2, line3)
		while not transfer_info['statusCode'] == 4:
			control.sleep(1000 * interval)
			transfer_info = self.list_transfer(transfer_id)
			file_size = transfer_info['size']
			line2 = transfer_info['filename']
			if transfer_info['statusCode'] == 1:
				download_speed = round(float(transfer_info['downloadSpeed']) / (1000**2), 2)
				progress = int(float(transfer_info['downloaded']) / file_size * 100) if file_size > 0 else 0
				line3 = control.lang(40016) % (download_speed, transfer_info['seeders'], progress, round(float(file_size) / (1000 ** 3), 2))
			elif transfer_info['statusCode'] == 3:
				upload_speed = round(float(transfer_info['uploadSpeed']) / (1000 ** 2), 2)
				progress = int(float(transfer_info['uploaded']) / file_size * 100) if file_size > 0 else 0
				line3 = control.lang(40015) % (upload_speed, progress, round(float(file_size) / (1000 ** 3), 2))
			else:
				line3 = transfer_info['status']
				progress = 0
			control.progressDialog.update(progress, line2=line2, line3=line3)
			if control.monitor.abortRequested():
				return sys.exit()
			try:
				if control.progressDialog.iscanceled():
					return _return_failed(control.lang(40014))
			except:
				pass
			if 5 <= transfer_info['statusCode'] <= 10:
				return _return_failed()
		control.sleep(1000 * interval)
		try:
			control.progressDialog.close()
		except:
			pass
		control.hide()
		return True


	def valid_url(self, host):
		try:
			self.hosts = self.get_hosts()
			if not self.hosts['AllDebrid']: return False
			if any(host in item for item in self.hosts['AllDebrid']):
				return True
			return False
		except:
			log_utils.error()


	def get_hosts(self):
		url = 'hosts'
		hosts_dict = {'AllDebrid': []}
		hosts = []
		try:
			result = cache.get(self._get, 168, url)
			result = result['hosts']
			for k, v in result.items():
				try: hosts.extend(v['domains'])
				except: pass
			hosts_dict['AllDebrid'] = list(set(hosts))
		except:
			log_utils.error()
			pass
		return hosts_dict



# # from resolveURL
	# def get_all_hosters(self):
		# hosters = []
		# url = '{0}/user/hosts?agent={1}&apikey={2}'.format(api_url, urllib_parse.quote_plus(AGENT), self.get_setting('token'))
		# try:
			# result = self.net.http_GET(url, headers=self.headers).content
			# js_data = json.loads(result)
			# if js_data.get('status', False) == "success":
				# js_data = js_data.get('data')
				# regexes = [value.get('regexp') for _, value in js_data.get('hosts', {}).items()
						   # if value.get('status', False)]
				# hosters = [re.compile(regex) for regex in regexes]
				# logger.log_debug('AllDebrid hosters : {0}'.format(len(hosters)))
				# regexes = [value.get('regexp') for _, value in js_data.get('streams', {}).items()]
				# streamers = []
				# for regex in regexes:
					# try:
						# streamers.append(re.compile(regex))
					# except:
						# pass
				# logger.log_debug('AllDebrid Streamers : {0}'.format(len(streamers)))
				# hosters.extend(streamers)
				# logger.log_debug('AllDebrid Total hosters : {0}'.format(len(hosters)))
			# else:
				# logger.log_error('Error getting AD Hosters')
		# except Exception as e:
			# logger.log_error('Error getting AD Hosters: {0}'.format(e))
		# return hosters


# # from resolveURL
	# def get_hosts(self):
		# hosts = []
		# url = '{0}/hosts/domains?agent={1}&apikey={2}'.format(api_url, urllib_parse.quote_plus(AGENT), self.get_setting('token'))
		# try:
			# js_result = self.net.http_GET(url, headers=self.headers).content
			# js_data = json.loads(js_result)
			# if js_data.get('status', False) == "success":
				# # hosts = [host.replace('www.', '') for host in js_data.get('hosts', [])]
				# hosts = js_data.get('data').get('hosts')
				# hosts.extend(js_data.get('data').get('streams'))
				# if self.get_setting('torrents') == 'true':
					# hosts.extend(['torrent', 'magnet'])
				# logger.log_debug('AllDebrid hosts : {0}'.format(hosts))
			# else:
				# logger.log_error('Error getting AD Hosts')
		# except Exception as e:
			# logger.log_error('Error getting AD Hosts: {0}'.format(e))
		# return hosts


# # from resolveURL
	# def valid_url(self, url, host):
		# logger.log_debug('in valid_url {0} : {1}'.format(url, host))
		# if url:
			# if url.lower().startswith('magnet:') and self.get_setting('torrents') == 'true':
				# return True
			# if self.hosters is None:
				# self.hosters = self.get_all_hosters()
			# for regexp in self.hosters:
				# if re.search(regexp, url):
					# logger.log_debug('AllDebrid Match found')
					# return True
		# elif host:
			# if self.hosts is None:
				# self.hosts = self.get_hosts()
			# if any(host in item for item in self.hosts):
				# return True
		# return False



	def revoke_auth(self):
		control.setSetting('alldebrid.token', '')
		control.setSetting('alldebrid.username', '')
		control.okDialog(title=40059, message=40009)