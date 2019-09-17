#!/bin/python

import xbmc
import xbmcgui
import xbmcaddon

import os
import platform
from subprocess import Popen, PIPE

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 01-10-2018
# Description: Addon for displaying system information
#              about software, CPU, hardware, memory,
#              storage, networks and addons installed.
#              Tested on Raspberry Pi.

# Get addon details
__addon_id__ = 'script.system-info'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

# Get localized language text
__language__ = __addon__.getLocalizedString
_software = __language__(30102)
_cpu = __language__(30114)
_memory = __language__(30121)
_storage = __language__(30142)
_network = __language__(30125)
_previous_networks = __language__(30144)
_network_devices = __language__(30143)
_addons_installed = __language__(30145)
_form_sent = __language__(30146)
_system_information = __language__(30147)
_does_not_work_with_ms_windows = __language__(30148)

_addon_resources_lib_path_ = xbmc.translatePath(os.path.join('special://home/addons/',
                                                __addon_id__ + '/resources/lib/'))

def showText(heading, text):
    id = 10147
    xbmc.executebuiltin('ActivateWindow(%d)' % id)
#    xbmc.sleep(500)
    win = xbmcgui.Window(id)
    retry = 50
    while (retry > 0):
        try:
            xbmc.sleep(10)
            retry -= 1
            win.getControl(1).setLabel(heading)
            win.getControl(5).setText(text)
            quit()
            return
        except: pass


def get_params():
    """
    Get the current parameters
    :return: param[]
    """
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring[1:])>=1:
        params=paramstring[1:]
        pairsofparams=params.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param


def notification(message, title, icon, duration):
    # Show message notification
    dialog = xbmcgui.Dialog()
    dialog.notification(title, message, icon, duration)


def shell_cmd_output(command):
    output = Popen(command.split(), stdout=PIPE).communicate()[0]
    return output

if __name__ == '__main__':
    os_friendly_name = platform.system()
    if os_friendly_name != 'Windows':
        params=get_params()
        # Check the parameters passed to the addon
        if params:
            if params['action'] == 'send':
                # Submit information
                cmdCommand = 'sudo python %ssendinfo.py' % _addon_resources_lib_path_
                response = shell_cmd_output(cmdCommand)
                notification(response, "[COLOR orange]%s[/COLOR]" % _form_sent, __icon__, 5000)
        else:
            # Display information
            cmdCommand = 'sudo python %ssysteminfo.py' % _addon_resources_lib_path_
            response = shell_cmd_output(cmdCommand).replace('\t', '').replace(':', ': ')
            # Change heading colour
            headings_dict = {'Software': _software,
                             'CPU': _cpu,
                             'Memory': _memory,
                             'Storage': _storage,
                             'Network': _network,
                             'Previous Networks': _previous_networks,
                             'Network Devices': _network_devices,
                             'Addons Installed': _addons_installed}
            for key, value in headings_dict.iteritems():
                response = response.replace('\n%s' % key, '[COLOR orange]\n%s:[/COLOR]' % value) 

            showText(_system_information, response)
    else:
        response = "System Info does not work with MS Windows"
        notification(response, "[COLOR orange]%s[/COLOR]" % _does_not_work_with_ms_windows, __icon__, 5000)
