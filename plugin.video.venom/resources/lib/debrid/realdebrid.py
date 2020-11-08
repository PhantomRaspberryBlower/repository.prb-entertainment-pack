# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

import json
import re
import requests
import sys

try:
	from urllib import quote_plus, unquote
except:
	from urllib.parse import quote_plus, unquote

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import workers
from resources.lib.modules.source_utils import supported_video_extensions


FormatDateTime = "%Y-%m-%dT%H:%M:%S.%fZ"
rest_base_url = 'https://api.real-debrid.com/rest/1.0/'
oauth_base_url = 'https://api.real-debrid.com/oauth/v2/'
unrestrict_link_url = 'unrestrict/link'
device_code_url = 'device/code?%s'
credentials_url = 'device/credentials?%s'
downloads_delete_url = 'downloads/delete'
add_magnet_url = 'torrents/addMagnet'
torrents_info_url = 'torrents/info'
select_files_url = 'torrents/selectFiles'
torrents_delete_url = 'torrents/delete'
check_cache_url = 'torrents/instantAvailability'
torrents_active_url = "torrents/activeCount"
hosts_domains_url = 'hosts/domains'
# hosts_status_url = 'hosts/status'
hosts_regex_url = 'hosts/regex'
rd_icon = control.joinPath(control.artPath(), 'realdebrid.png')
addonFanart = control.addonFanart()
store_to_cloud = control.setting('realdebrid.saveToCloud') == 'true'


class RealDebrid:
	name = "Real-Debrid"

	def __init__(self):
		self.hosters = None
		self.hosts = None
		self.cache_check_results = {}
		self.token = control.setting('realdebrid.token')
		self.client_ID = control.setting('realdebrid.client_id')
		if self.client_ID == '':
			self.client_ID = 'X245A4XAIBGVM'
		self.secret = control.setting('realdebrid.secret')
		self.device_code = ''
		self.auth_timeout = 0
		self.auth_step = 0


	def _get(self, url, fail_check=False, token_ck=False):
		try:
			original_url = url
			url = rest_base_url + url
			if self.token == '':
				log_utils.log('No Real Debrid Token Found', __name__, log_utils.LOGDEBUG)
				return None
			# if not fail_check: # with fail_check=True new token does not get added
			if '?' not in url:
				url += "?auth_token=%s" % self.token
			else:
				url += "&auth_token=%s" % self.token
			response = requests.get(url, timeout=15).json()
			if 'bad_token' in str(response) or 'Bad Request' in str(response):
				if not fail_check:
					if self.refresh_token() and token_ck:
						return
					response = self._get(original_url, fail_check=True)
			return response
		except:
			log_utils.error()
			pass
		return None


	def _post(self, url, data):
		original_url = url
		url = rest_base_url + url
		if self.token == '':
			log_utils.log('No Real Debrid Token Found', __name__, log_utils.LOGDEBUG)
			return None
		if '?' not in url:
			url += "?auth_token=%s" % self.token
		else:
			url += "&auth_token=%s" % self.token
		response = requests.post(url, data=data, timeout=15).text
		if 'bad_token' in response or 'Bad Request' in response:
			self.refresh_token()
			response = self._post(original_url, data)
		elif 'error' in response:
			response = json.loads(response)
			control.notification(message=response.get('error'))
			return None
		try:
			return json.loads(response)
		except:
			return response


	def auth_loop(self):
		control.sleep(self.auth_step*1000)
		url = 'client_id=%s&code=%s' % (self.client_ID, self.device_code)
		url = oauth_base_url + credentials_url % url
		response = json.loads(requests.get(url).text)
		if 'error' in response:
			return control.okDialog(title='default', message=40019)
		else:
			try:
				control.progressDialog.close()
				self.client_ID = response['client_id']
				self.secret = response['client_secret']
			except:
				log_utils.error()
				control.okDialog(title='default', message=40019)
			return


	def auth(self):
		self.secret = ''
		self.client_ID = 'X245A4XAIBGVM'
		url = 'client_id=%s&new_credentials=yes' % self.client_ID
		url = oauth_base_url + device_code_url % url
		response = json.loads(requests.get(url).text)
		control.progressDialog.create(control.lang(40055))
		control.progressDialog.update(-1,
				control.lang(32513) % 'https://real-debrid.com/device',
				control.lang(32514) % response['user_code'])

		self.auth_timeout = int(response['expires_in'])
		self.auth_step = int(response['interval'])
		self.device_code = response['device_code']

		while self.secret == '':
			if control.progressDialog.iscanceled():
				control.progressDialog.close()
				break
			self.auth_loop()
		if self.secret:
			self.get_token()


	def account_info(self):
		return self._get('user')


	def account_info_to_dialog(self):
		from datetime import datetime
		import time
		try:
			userInfo = self.account_info()
			try: expires = datetime.strptime(userInfo['expiration'], FormatDateTime)
			except: expires = datetime(*(time.strptime(userInfo['expiration'], FormatDateTime)[0:6]))
			days_remaining = (expires - datetime.today()).days
			expires = expires.strftime("%A, %B %d, %Y")
			items = []
			items += [control.lang(40035) % userInfo['email']]
			items += [control.lang(40036) % userInfo['username']]
			items += [control.lang(40037) % userInfo['type'].capitalize()]
			items += [control.lang(40041) % expires]
			items += [control.lang(40042) % days_remaining]
			items += [control.lang(40038) % userInfo['points']]
			return control.selectDialog(items, 'Real-Debrid')
		except:
			log_utils.error()
			pass
		return


	def user_torrents(self):
		try:
			url = 'torrents'
			return self._get(url)
		except:
			log_utils.error()
			pass


	def user_torrents_to_listItem(self):
		try:
			sysaddon = sys.argv[0]
			syshandle = int(sys.argv[1])
			torrent_files = self.user_torrents()
			if not torrent_files: return
			# torrent_files = [i for i in torrent_files if i['status'] == 'downloaded']
			folder_str, deleteMenu = control.lang(40046).upper(), control.lang(40050)

			for count, item in enumerate(torrent_files, 1):
				try:
					cm = []
					isFolder = True if item['status'] == 'downloaded' else False

					status = '[COLOR %s]%s[/COLOR]' % (control.getColor(control.setting('highlight.color')), item['status'].capitalize())
					folder_name = cleantitle.normalize(item['filename'])
					label = '%02d | [B]%s[/B] - %s | [B]%s[/B] | [I]%s [/I]' % (count, status, str(item['progress']) + '%', folder_str, folder_name)

					url = '%s?action=rd_BrowseUserTorrents&id=%s' % (sysaddon, item['id']) if isFolder else None

					cm.append((deleteMenu % 'Torrent', 'RunPlugin(%s?action=rd_DeleteUserTorrent&id=%s&name=%s)' %
							(sysaddon, item['id'], quote_plus(folder_name))))
					item = control.item(label=label)
					item.addContextMenuItems(cm)
					item.setArt({'icon': rd_icon, 'poster': rd_icon, 'thumb': rd_icon, 'fanart': addonFanart, 'banner': rd_icon})
					item.setInfo(type='video', infoLabels='')
					control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
				except:
					log_utils.error()
					pass
			control.content(syshandle, 'files')
			control.directory(syshandle, cacheToDisc=True)
		except:
			log_utils.error()
			pass


	def browse_user_torrents(self, folder_id):
		try:
			sysaddon = sys.argv[0]
			syshandle = int(sys.argv[1])
			torrent_files = self.torrent_info(folder_id)
		except:
			return
		extensions = supported_video_extensions()
		try:
			file_info = [i for i in torrent_files['files'] if i['path'].lower().endswith(tuple(extensions))]
			file_urls = torrent_files['links']
			for c, i in enumerate(file_info):
				try: i.update({'url_link': file_urls[c]})
				except: pass
			pack_info = sorted(file_info, key=lambda k: k['path'])
		except:
			return control.notification(message=33586)

		file_str, downloadMenu, renameMenu, deleteMenu, clearFinishedMenu = \
				control.lang(40047).upper(), control.lang(40048), control.lang(40049), control.lang(40050), control.lang(40051)

		for count, item in enumerate(pack_info, 1):
			try:
				cm = []
				name = item['path']
				if name.startswith('/'):
					name = name.split('/')[-1]

				url_link = item['url_link']
				if url_link.startswith('/'):
					url_link = 'http' + url_link

				size = float(int(item['bytes']))/1073741824
				label = '%02d | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, file_str, size, name)

				url = '%s?action=playURL&url=%s&caller=realdebrid&type=unrestrict' % (sysaddon, url_link)

				cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=realdebrid&type=unrestrict)' %
							(sysaddon, quote_plus(name), quote_plus(rd_icon), url_link)))
				cm.append((deleteMenu % 'Torrent', 'RunPlugin(%s?action=rd_DeleteUserTorrent&id=%s&name=%s)' %
							(sysaddon, item['id'], quote_plus(name))))

				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': rd_icon, 'poster': rd_icon, 'thumb': rd_icon, 'fanart': addonFanart, 'banner': rd_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def delete_user_torrent(self, media_id, name):
		try:
			if not control.yesnoDialog(control.lang(40050) % name, '', ''): return
			url = torrents_delete_url + "/%s&auth_token=%s" % (media_id, self.token)
			response = requests.delete(rest_base_url + url).text
			if not 'error' in response:
				log_utils.log('Real-Debrid: %s was removed from your active Torrents' % name, __name__, log_utils.LOGDEBUG)
				control.refresh()
				return
		except Exception as e:
			log_utils.log('Real-Debrid Error: DELETE TORRENT %s | %s' % (name, e), __name__, log_utils.LOGDEBUG)
			raise


	def downloads(self, page):
		import math
		try:
			# Need to check token, and refresh if needed
			ck_token = self._get('user', token_ck=True)
			url = 'downloads?page=%s&auth_token=%s' % (page, self.token)
			response = requests.get(rest_base_url + url)
			total_count = float(response.headers['X-Total-Count'])
			pages = int(math.ceil(total_count / 50.0))
			return json.loads(response.text), pages
		except:
			log_utils.error()
			pass


	def my_downloads_to_listItem(self, page):
		try:
			from datetime import datetime
			sysaddon = sys.argv[0]
			syshandle = int(sys.argv[1])
			my_downloads, pages = self.downloads(page)
		except:
			my_downloads = None

		if not my_downloads:
			return
		extensions = supported_video_extensions()
		my_downloads = [i for i in my_downloads if i['download'].lower().endswith(tuple(extensions))]
		downloadMenu, deleteMenu = control.lang(40048), control.lang(40050)

		for count, item in enumerate(my_downloads, 1):
			if page > 1:
				count += (page-1)*50
			try:
				cm = []
				generated = datetime.strptime(item['generated'], FormatDateTime)
				generated = generated.strftime('%Y-%m-%d')
				name = control.strip_non_ascii_and_unprintable(item['filename'])

				size = float(int(item['filesize']))/1073741824
				label = '%02d | %.2f GB | %s  | [I]%s [/I]' % (count, size, generated, name)

				url_link = item['download']
				url = '%s?action=playURL&url=%s' % (sysaddon, url_link)
				cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=realdebrid)' %
								(sysaddon, quote_plus(name), quote_plus(rd_icon), url_link)))

				cm.append((deleteMenu % 'File', 'RunPlugin(%s?action=rd_DeleteDownload&id=%s&name=%s)' %
								(sysaddon, item['id'], name)))

				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': rd_icon, 'poster': rd_icon, 'thumb': rd_icon, 'fanart': addonFanart, 'banner': rd_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
			except:
				log_utils.error()
				pass

		if page < pages:
			page += 1
			next = True
		else:
			next = False
		if next:
			try:
				nextMenu = control.lang(32053)
				url = '%s?action=rd_MyDownloads&query=%s' % (sysaddon, page)
				page = '  [I](%s)[/I]' % page
				nextMenu = '[COLOR skyblue]' + nextMenu + page + '[/COLOR]'
				item = control.item(label=nextMenu)
				icon = control.addonNext()
				item.setArt({'icon': rd_icon, 'poster': rd_icon, 'thumb': rd_icon, 'fanart': addonFanart, 'banner': rd_icon})
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def delete_download(self, media_id, name):
		try:
			if not control.yesnoDialog(control.lang(40050) % name, '', ''): return
			# Need to check token, and refresh if needed
			ck_token = self._get('user', token_ck=True)
			url = downloads_delete_url + "/%s&auth_token=%s" % (media_id, self.token)
			response = requests.delete(rest_base_url + url).text
			if not 'error' in response:
				log_utils.log('Real-Debrid: %s was removed from your MyDownloads' % name, __name__, log_utils.LOGDEBUG)
				control.refresh()
				return
		except Exception as e:
			log_utils.log('Real-Debrid Error: DELETE DOWNLOAD %s | %s' % (name, e), __name__, log_utils.LOGDEBUG)


	def check_cache_list(self, hashList):
		if isinstance(hashList, list):
			hashList = [hashList[x:x+100] for x in range(0, len(hashList), 100)]
			# Need to check token, and refresh if needed, before blasting threads at it
			ck_token = self._get('user', token_ck=True)
			threads = []
			for section in hashList:
				threads.append(workers.Thread(self.check_hash_thread, section))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.cache_check_results
		else:
			hashString = "/" + hashList
			return self._get("torrents/instantAvailability" + hashString)


	def check_hash_thread(self, hashes):
		try:
			hashString = '/' + '/'.join(hashes)
			response = self._get("torrents/instantAvailability" + hashString)
			if not response: return
			self.cache_check_results.update(response)
		except:
			log_utils.error()
			pass


	def resolve_magnet(self, magnet_url, info_hash, season, episode, ep_title):
		from resources.lib.modules.source_utils import seas_ep_filter, episode_extras_filter
		try:
			torrent_id = None
			rd_url = None
			match = False
			extensions = supported_video_extensions()
			extras_filtering_list = episode_extras_filter()
			info_hash = info_hash.lower()
			torrent_files = self._get(check_cache_url + '/' + info_hash)
			if not info_hash in torrent_files:
				return None
			torrent_id = self.add_magnet(magnet_url)
			torrent_info = self.torrent_info(torrent_id)
			torrent_files = torrent_files[info_hash]['rd']
			for item in torrent_files:
				try:
					video_only = self.video_only(item, extensions)
					if not video_only: continue
					if season:
						correct_file_check = False
						item_values = [i['filename'] for i in item.values()]
						for value in item_values:
							correct_file_check = seas_ep_filter(season, episode, value)
							if correct_file_check: break
						if not correct_file_check: continue
					torrent_keys = item.keys()
					if len(torrent_keys) == 0: continue
					torrent_keys = ','.join(torrent_keys)
					self.add_torrent_select(torrent_id, torrent_keys)
					torrent_info = self.torrent_info(torrent_id)
					status = torrent_info.get('status')
					if 'error' in torrent_info: continue
					selected_files = [(idx, i) for idx, i in enumerate([i for i in torrent_info['files'] if i['selected'] == 1])]
					if season:
						correct_files = []
						correct_file_check = False
						for value in selected_files:
							correct_file_check = seas_ep_filter(season, episode, value[1]['path'])
							if correct_file_check:
								correct_files.append(value[1])
								break
						if len(correct_files) == 0: continue
						episode_title = re.sub('[^A-Za-z0-9-]+', '.', ep_title.replace("\'", '')).lower()
						for i in correct_files:
							compare_link = seas_ep_filter(season, episode, i['path'], split=True)
							compare_link = re.sub(episode_title, '', compare_link)
							if any(x in compare_link for x in extras_filtering_list):
								continue
							else:
								match = True
								break
						if match:
							index = [i[0] for i in selected_files if i[1]['path'] == correct_files[0]['path']][0]
							break
					else:
						match, index = True, 0
				except:
					log_utils.error()
					pass
			if match:
				rd_link = torrent_info['links'][index]
				rd_url = self.unrestrict_link(rd_link)
				if rd_url.endswith('rar'): rd_url = None
				if not store_to_cloud: self.delete_torrent(torrent_id)
				return rd_url
			self.delete_torrent(torrent_id)
		except Exception as e:
			if torrent_id: self.delete_torrent(torrent_id)
			log_utils.log('Real-Debrid Error: RESOLVE MAGNET | %s' % e, __name__, log_utils.LOGDEBUG)
			return None


	def display_magnet_pack(self, magnet_url, info_hash):
		try:
			torrent_id = None
			rd_url = None
			match = False
			video_only_items = []
			list_file_items = []
			info_hash = info_hash.lower()
			extensions = supported_video_extensions()
			torrent_files = self._get(check_cache_url + '/' + info_hash)
			if not info_hash in torrent_files:
				return None
			torrent_id = self.add_magnet(magnet_url)
			if not torrent_id:
				return None
			torrent_files = torrent_files[info_hash]['rd']
			for item in torrent_files:
				video_only = self.video_only(item, extensions)
				if not video_only: continue
				torrent_keys = item.keys()
				if len(torrent_keys) == 0: continue
				video_only_items.append(torrent_keys)
			video_only_items = max(video_only_items, key=len)
			torrent_keys = ','.join(video_only_items)
			self.add_torrent_select(torrent_id, torrent_keys)
			torrent_info = self.torrent_info(torrent_id)
			list_file_items = [dict(i, **{'link':torrent_info['links'][idx]})  for idx, i in enumerate([i for i in torrent_info['files'] if i['selected'] == 1])]
			list_file_items = [{'link': i['link'], 'filename': i['path'].replace('/', ''), 'size': float(i['bytes'])/1073741824} for i in list_file_items]
			self.delete_torrent(torrent_id)
			return list_file_items
		except Exception as e:
			if torrent_id:
				self.delete_torrent(torrent_id)
			log_utils.log('Real-Debrid Error: DISPLAY MAGNET PACK | %s' % str(e), __name__, log_utils.LOGDEBUG)
			raise


	def torrents_activeCount(self):
		return self._get(torrents_active_url)


	def add_uncached_torrent(self, magnet_url, pack=False):
		def _return_failed(message=control.lang(33586)):
			try:
				control.progressDialog.close()
			except:
				pass
			self.delete_torrent(torrent_id)
			control.hide()
			control.sleep(500)
			control.okDialog(title=control.lang(40018), message=message)
			return False
		control.busy()
		try:
			active_count = self.torrents_activeCount()
			if active_count['nb'] >= active_count['limit']:
				return _return_failed()
		except:
			pass
		interval = 5
		stalled = ['magnet_error', 'error', 'virus', 'dead']
		extensions = supported_video_extensions()
		torrent_id = self.add_magnet(magnet_url)
		if not torrent_id:
			return _return_failed()
		torrent_info = self.torrent_info(torrent_id)
		if 'error_code' in torrent_info:
			return _return_failed()
		status = torrent_info['status']
		if status == 'magnet_conversion':
			line1 = control.lang(40013)
			line2 = torrent_info['filename']
			line3 = control.lang(40012) % str(torrent_info['seeders'])
			timeout = 100
			control.progressDialog.create(control.lang(40018), line1, line2, line3)
			while status == 'magnet_conversion' and timeout > 0:
				control.progressDialog.update(timeout, line3=line3)
				if control.monitor.abortRequested():
					return sys.exit()
				try:
					if control.progressDialog.iscanceled():
						return _return_failed(control.lang(40014))
				except:
					pass
				if any(x in status for x in stalled):
					return _return_failed()
				timeout -= interval
				control.sleep(1000 * interval)
				torrent_info = self.torrent_info(torrent_id)
				status = torrent_info['status']
				line3 = control.lang(40012) % str(torrent_info['seeders'])
			try:
				control.progressDialog.close()
			except:
				pass
		if status == 'magnet_conversion':
			return _return_failed()
		if status == 'waiting_files_selection':
			video_files = []
			all_files = torrent_info['files']
			for item in all_files:
				if any(item['path'].lower().endswith(x) for x in extensions):
					video_files.append(item)
			if pack:
				try:
					if len(video_files) == 0: return _return_failed()
					video_files = sorted(video_files, key=lambda x: x['path'])
					torrent_keys = [str(i['id']) for i in video_files]
					if not torrent_keys: return _return_failed(control.lang(40014))
					torrent_keys = ','.join(torrent_keys)
					self.add_torrent_select(torrent_id, torrent_keys)
					control.okDialog(title='default', message=control.lang(40017) % control.lang(40058))
					# self.clear_cache()
					control.hide()
					return True
				except:
					return _return_failed()
			else:
				try:
					video = max(video_files, key=lambda x: x['bytes'])
					file_id = video['id']
				except ValueError:
					return _return_failed()
				self.add_torrent_select(torrent_id,str(file_id))
			control.sleep(2000)
			torrent_info = self.torrent_info(torrent_id)
			status = torrent_info['status']
			if status == 'downloaded':
				return True
			file_size = round(float(video['bytes']) / (1000 ** 3), 2)
			line1 = '%s...' % (control.lang(40017) % control.lang(40058))
			line2 = torrent_info['filename']
			line3 = status
			control.progressDialog.create(ls(40018), line1, line2, line3)
			while not status == 'downloaded':
				control.sleep(1000 * interval)
				torrent_info = self.torrent_info(torrent_id)
				status = torrent_info['status']
				if status == 'downloading':
					line3 = control.lang(40011) % (file_size, round(float(torrent_info['speed']) / (1000**2), 2), torrent_info['seeders'], torrent_info['progress'])
				else:
					line3 = status
				control.progressDialog.update(int(float(torrent_info['progress'])), line3=line3)
				if control.monitor.abortRequested():
					return sys.exit()
				try:
					if control.progressDialog.iscanceled():
						return _return_failed(control.lang(40011))
				except:
					pass
				if any(x in status for x in stalled):
					return _return_failed()
			try:
				control.progressDialog.close()
			except Exception:
				pass
			control.hide()
			return True
		control.hide()
		return False


	def torrent_info(self, torrent_id):
		try:
			url = torrents_info_url + "/%s" % torrent_id
			return self._get(url)
		except Exception as e:
			log_utils.log('Real-Debrid Error: TORRENT INFO | %s' % e, __name__, log_utils.LOGDEBUG)


	def add_magnet(self, magnet):
		try:
			data = {'magnet': magnet}
			response = self._post(add_magnet_url, data)
			return response.get('id', "")
		except Exception as e:
			log_utils.log('Real-Debrid Error: ADD MAGNET | %s' % e, __name__, log_utils.LOGDEBUG)
			return None


	def add_torrent_select(self, torrent_id, file_ids):
		try:
			url = '%s/%s' % (select_files_url, torrent_id)
			data = {'files': file_ids}
			return self._post(url, data)
		except Exception as e:
			log_utils.log('Real-Debrid Error: ADD SELECT FIELES | %s' % e, __name__, log_utils.LOGDEBUG)
			return None


	def unrestrict_link(self, link):
		post_data = {'link': link}
		response = self._post(unrestrict_link_url, post_data)
		try: return response['download']
		except: return None


	def delete_torrent(self, torrent_id):
		try:
			# Need to check token, and refresh if needed
			ck_token = self._get('user', token_ck=True)
			url = torrents_delete_url + "/%s&auth_token=%s" % (torrent_id, self.token)
			response = requests.delete(rest_base_url + url)
			log_utils.log('Real-Debrid: Torrent ID %s was removed from your active torrents' % torrent_id, __name__, log_utils.LOGDEBUG)
			return True
		except Exception as e:
			log_utils.log('Real-Debrid Error: DELETE TORRENT | %s' % e, __name__, log_utils.LOGDEBUG)
			raise


	def get_link(self, link):
		if 'download' in link:
			if 'quality' in link:
				label = '[%s] %s' % (link['quality'], link['download'])
			else:
				label = link['download']
			return label, link['download']


	def video_only(self, storage_variant, extensions):
		return False if len([i for i in storage_variant.values() if not i['filename'].lower().endswith(tuple(extensions))]) > 0 else True


	def valid_url(self, host):
		try:
			self.hosts = self.get_hosts()
			if not self.hosts['Real-Debrid']: return False
			# log_utils.log('self.hosts = %s' % self.hosts, __name__, log_utils.LOGDEBUG)
			if any(host in item for item in self.hosts['Real-Debrid']):
				return True
			return False
		except:
			log_utils.error()


	def get_hosts(self):
		hosts_dict = {'Real-Debrid': []}
		try:
			result = cache.get(self._get, 168, hosts_domains_url)
			hosts_dict['Real-Debrid'] = result
		except:
			log_utils.error()
			pass
		return hosts_dict


	def get_hosts_regex(self):
		hosts_regexDict = {'Real-Debrid': []}
		try:
			result = cache.get(self._get, 168, hosts_regex_url)
			hosts_regexDict['Real-Debrid'] = result
		except:
			log_utils.error()
			pass
		return hosts_regexDict


# from resolveURL
	# def get_all_hosters(self):
		# hosters = []
		# try:
			# url = '%s/%s' % (rest_base_url, hosts_regexes_path)
			# js_result = json.loads(self.net.http_GET(url, headers=self.headers).content)
			# regexes = [regex[1:-1].replace(r'\/', '/').rstrip('\\') for regex in js_result]
			# logger.log_debug('RealDebrid hosters : %s' % regexes)
			# hosters = [re.compile(regex, re.I) for regex in regexes]
		# except Exception as e:
			# logger.log_error('Error getting RD regexes: %s' % e)
		# return hosters


# from resolveURL
	# def valid_url(self, url, host):
		# # logger.log_debug('in valid_url %s : %s' % (url, host))
		# if url:
			# if url.lower().startswith('magnet:') and self.get_setting('torrents') == 'true':
				# return True
			# if self.hosters is None:
				# self.hosters = self.get_all_hosters()

			# for host in self.hosters:
				# # logger.log_debug('RealDebrid checking host : %s' %str(host))
				# if re.search(host, url):
					# logger.log_debug('RealDebrid Match found')
					# return True
		# elif host:
			# if self.hosts is None:
				# self.hosts = self.get_hosts()

			# if host.startswith('www.'):
				# host = host.replace('www.', '')
			# if any(host in item for item in self.hosts):
				# return True
		# return False


	def refresh_token(self):
		try:
			self.client_ID = control.setting('realdebrid.client_id')
			self.secret = control.setting('realdebrid.secret')
			self.device_code = control.setting('realdebrid.refresh')
			log_utils.log('Refreshing Expired Real Debrid Token: |%s|%s|' % (self.client_ID, self.device_code), __name__, log_utils.LOGDEBUG)
			if not self.get_token():
				# empty all auth settings to force a re-auth on next use
				self.reset_authorization()
				log_utils.log('Unable to Refresh Real Debrid Token', __name__, log_utils.LOGDEBUG)
			else:
				log_utils.log('Real Debrid Token Successfully Refreshed', __name__, log_utils.LOGDEBUG)
				return True
		except:
			log_utils.error()
			return False


	def get_token(self):
		try:
			url = oauth_base_url + 'token'
			postData = {'client_id': self.client_ID, 'client_secret': self.secret, 'code': self.device_code, 'grant_type': 'http://oauth.net/grant_type/device/1.0'}
			response = requests.post(url, data=postData).json()
			# log_utils.log('Authorizing Real Debrid Result: |%s|' % response, __name__, log_utils.LOGDEBUG)
			self.token = response['access_token']
			control.sleep(1500)
			account_info = self.account_info()
			username = account_info['username']
			control.setSetting('realdebrid.username', username)
			control.setSetting('realdebrid.client_id', self.client_ID)
			control.setSetting('realdebrid.secret', self.secret,)
			control.setSetting('realdebrid.token', self.token)
			control.addon('script.module.myaccounts').setSetting('realdebrid.token', self.token)
			control.setSetting('realdebrid.refresh', response['refresh_token'])
			return True
		except Exception as e:
			log_utils.log('Real Debrid Authorization Failed: %s' % e, __name__, log_utils.LOGDEBUG)
			return False


	def reset_authorization(self):
		try:
			control.setSetting('realdebrid.client_id', '')
			control.setSetting('realdebrid.secret', '')
			control.setSetting('realdebrid.token', '')
			control.setSetting('realdebrid.refresh', '')
			control.setSetting('realdebrid.username', '')
		except:
			log_utils.error()
			pass