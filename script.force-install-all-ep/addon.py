#!/usr/bin/env python

import xbmc
import xbmcgui
import xbmcaddon
import os
import xml.etree.ElementTree as et   # Module used to access xml files
from resources.lib import commontasks
#from resources.lib.SetDownloadPaths import SetDownloadPaths

# PRB Install Everything EP (Entertainment Pack)
# A quick way to modify download paths for the following addons
# Dreamcatcher, Exodus, Genesis, MP3Streams and Phoenix

# Date: 01 March 2016
# Written By: Phantom Raspberry Blower

# Get addon details
__addon_id__ = 'script.force-install-all-ep'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'
__url__ = sys.argv[0]

try:
    __handle__ = int(sys.argv[1])
    main = 2
except:
	main = 1

# Defines local variables
__resources__ = xbmc.translatePath(os.path.join('special://home/addons/' +
                                                __addon_id__,
                                                'resources'))
__userdata_path__ = xbmc.translatePath(os.path.join('special://home', 'userdata'))
__addons_download_paths_list__ = os.path.join(__resources__, 'addons_download_paths.list')

# Get settings
__download_dir__ = __addon__.getSetting('set_media_source')

__folders__ = ['Addons', 'Backups', 'Movies', 'Music', 'Pictures', 'Screen Shots', 'TV Shows']

def _set_media_source_paths():
    # Set the download locations for each media type
    settings = ['addons_path',
                'backups_path',
                'movies_download_path',
                'music_download_path',
                'pictures_download_path',
                'screenshots_path',
                'tv_shows_download_path']
    count = 0
    msg = ''
    for index in range(len(settings)):
        if __addon__.getSetting(settings[index]) == '':
            if __download_dir__ != '':
                __addon__.setSetting(settings[index], '%s%s/' % (__download_dir__, __folders__[index]))
                msg += '[COLOR orange]%s[/COLOR], ' % __folders__[index]
                count += 1
    if count > 0:
        msg = 'Set the following download paths: %s\n' % msg
    else:
        msg = '[COLOR green]Download paths already set[/COLOR] :)\n'
    return msg

def set_media_source():
    # Set the root location of media files
    global __download_dir__
    msg = ''
    dialog = xbmcgui.Dialog()
    download_dir = dialog.browse(3, 'Media Source', 'files', '')
    __download_dir__ = download_dir
    if download_dir != '':
        __addon__.setSetting('set_media_source', download_dir)
        msg += _create_folders(stealth=True)
        msg += _set_media_source_paths()
        msg += _set_download_paths()
        msg = msg.replace(', \n', '.\n')
        commontasks.message(msg, 'Summary')

def _set_download_paths():
    # Set download paths for addons that allow downloading
    addon_types = ['plugin', '.video.', '.audio.', '.program.']
    msg = 'Set download paths for the following addons: '
    if os.path.isfile(__addons_download_paths_list__):
        # Fetch list of addons
        al = commontasks.read_from_file(__addons_download_paths_list__)
        addons_list = al.split('\n')
        # Iterate through the list of addons
        for list in addons_list:
            if list != '':
                split_list = list.split('<>')
                setting_value = split_list[3]
                addon_data_dir = xbmc.translatePath(os.path.join('special://profile/addon_data',
                	                                             split_list[1]))
                if os.path.isdir(addon_data_dir):
                    # Check the settings xml file exists
                    if not os.path.isfile(os.path.join(addon_data_dir, 'settings.xml')):
                        # Create a new settings xml file
                        _create_settings_xml(split_list[1])
                    settings_file = os.path.join(addon_data_dir, 'settings.xml')
                    tree = et.parse(settings_file)
                    root = tree.getroot()
                    # Iterate though all settings
                    for setting in root.iter('setting'):
                        value = ''
                        if setting.get('id') == split_list[2]:
                            try:
                                # Set new value
                                if setting_value.lower() == 'true' or setting_value.lower() == 'false':
                                    value = setting_value.lower()
                                else:
                                    if __addon__.getSetting(setting_value) == '':
                                        value = '%s%s/' % (__download_dir__, split_list[4].replace('\r', ''))
                                        __addon__.setSetting(setting_value, value)
                                    else:
                                        value = __addon__.getSetting(setting_value)
                                setting.set('value', value)
                            except:
                                pass
                    try:
                        # Save settings file
                        tree.write(settings_file)
                        temp2 = '[COLOR orange]%s[/COLOR], ' % split_list[0]
                        msg += temp2
                        msg = msg.replace(temp2 + temp2, temp2)
                    except:
                        pass
        for item in addon_types:
            msg = msg.replace(item, '') + '\n'
    return msg.replace(', \n', '.')

def _create_settings_xml(addon=None):
    # Copy the default settings xml file to userdata folder
    resources = xbmc.translatePath(os.path.join('special://home/addons/' +
                                                addon,
                                                'resources'))	
    if os.path.isfile(os.path.join(resources, 'settings.xml')):
        settings_file = os.path.join(resources, 'settings.xml')
        tree = et.parse(settings_file)
        root = tree.getroot()
        msg = ''
        new_root = et.Element('settings')
        for setting in root.iter('setting'):
            if setting.get('id') != None:
                if setting.get('default') != None:
                    et.SubElement(new_root, "setting", value=setting.get('default'), id=setting.get('id'))
                else:
                    et.SubElement(new_root, "setting", value="", id=setting.get('id'))
                msg += '%s=%s\n' % (setting.get('id'), setting.get('default'))
        new_tree = et.ElementTree(new_root)
        addon_data_dir = xbmc.translatePath(os.path.join('special://profile/addon_data', addon))
        new_tree.write(os.path.join(addon_data_dir, 'settings.xml'))
        commontasks.message(msg, "Create Settings XML")

def _create_folders(stealth=False):
    # Create download folders on hard drive if not already there
    msg = ''
    if os.path.isdir(__download_dir__):
        for folder in __folders__:
            if os.path.isdir(__download_dir__ + folder) != True:
                msg += '[COLOR orange]%s[/COLOR], ' % folder
                os.mkdir(__download_dir__ + folder)
    if len(msg) > 0:
        msg = 'Created the following folders: %s\n' + msg
        if stealth == False:
            commontasks.message(msg, 'Folders Created')
    else:
        msg = '[COLOR green]Folders already exist[/COLOR] :)\n'
        if stealth == False:
            commontasks.message(msg, "Folders Present")
    return msg

def get_params():
    """
    Get the current parameters
    :return: param[]
    """
    param = []
    paramstring = sys.argv[main]
    if len(paramstring[1:]) >= 1:
        params = paramstring[1:]
        pairsofparams = params.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

def send_web_form(recursive=True):
    # Send the system info results to web form
    systeminfo_path = xbmc.translatePath(os.path.join('special://home/addons/'
                                                    'script.system-info/',
                                                    'resources/lib'))
    sendinfo = xbmc.translatePath(os.path.join(systeminfo_path, 'sendinfo.py'))
    if os.path.isfile(sendinfo):
        xbmc.executebuiltin('XBMC.RunPlugin(plugin://script.system-info/?action=send)')
        commontasks.message('Form is being sent to PRB.', 'Send Form')
    else:
        if recursive == True:
            commontasks.install_addon('script.system-info')
            send_web_form(False)


if __name__ == '__main__':
    # Remove waiting dialog (like hourglass)
    xbmc.executebuiltin("Dialog.Close(busydialog)")
    if main == 2:
        __addon__.openSettings()
    else:
        handle_id = __addon__.getSetting('handle_id')
        params=get_params()
        # Check the parameters passed to the addon
        if params:
            if params['action'] == 'set_media_source':
                set_media_source()
            if params['action'] == 'run_prb_clean':
                commontasks.install_addon('service.prb-clean')
            if params['action'] == 'send_web_form':
                send_web_form()
