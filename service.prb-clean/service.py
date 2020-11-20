import os
import xbmc
import xbmcaddon
import xbmcgui
import glob
from subprocess import Popen, PIPE

from resources.lib import commontasks

g_addons_removed_lst = []

# Get addon details
__addon_id__ = 'service.prb-clean'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addon_name__ = 'PRB Clean'

# Define local variables
__resources__ = xbmc.translatePath(os.path.join('special://home/addons/'
                                            'service.prb-clean',
                                            'resources'))
__addons_to_remove_list__ = os.path.join(__resources__, 'addons_to_remove.list')
__addons_to_clean_list__ = os.path.join (__resources__, 'addons_to_clean.list')
__music_addons_to_clean_list__ = os.path.join(__resources__, 'music_addons_to_clean.list')
__userdata_path__ = xbmc.translatePath(os.path.join('special://home', 'userdata'))


def cpu_serial():
    # Get CPU Serial Number
    return _get_cpu_item('Serial', '0000000000000000')

# Get CPU items
def _get_cpu_item(item, ini_value):
    temp = ini_value
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:len(item)] == item:
                item_value = line[len(item)+3:]
        f.close()
    except:
        item_value = 'Unable to get %s! :(' % item
    return item_value.strip()


def clean_addons():
    # Clean addons fetches the list of addons 
    if os.path.isfile(__addons_to_clean_list__):
        al = commontasks.read_from_file(__addons_to_clean_list__)
        addons_list = al.split('\n')
        for list in addons_list:
            if list != '':
                split_list = list.split('<>')
                clean_addon(split_list[0], split_list[1])


def clean_addon(addon_id, addon_name):
    # Clean addon removes the colours from addon names
    # to allow addons to be listed alphabetically
    addon_dir = xbmc.translatePath(os.path.join('special://home/addons', addon_id))
    if os.path.isdir(addon_dir):
        old_xml_doc = commontasks.read_from_file('%s/addon.xml' % addon_dir)
        rep_string = commontasks.regex_from_to(old_xml_doc, 'name="', '"')
        new_xml_doc = old_xml_doc.replace(rep_string, addon_name)
        commontasks.write_to_file('%s/addon.xml' % addon_dir, str(new_xml_doc), False)
        xbmc.sleep(100)


def remove_addons_and_dependancies():
    # Remove addons and dependancies for depricated addons
    if os.path.isfile(__addons_to_remove_list__):
        al = commontasks.read_from_file(__addons_to_remove_list__)
        addons_list = al.split('\n')
        for list in addons_list:
            if list != '':
                split_list = list.split('<>')
                remove_dependancies(split_list[0], split_list[1])
                remove_addon(split_list[0], split_list[1])

        remove_dependancies(__addon_id__, __addon_name__)
        remove_addon(__addon_id__, __addon_name__)

        if len(g_addons_removed_lst) > 0:
            text = ''
            for item in g_addons_removed_lst:
                if len(g_addons_removed_lst) == 1:
                    text = '%s' % item
                else:
                    if text == '':
                        text = '%s' % item
                    else:
                        text += ', %s' % item
            text += '\n'
            text = "The following addons are now obsolete and have been removed.\n[COLOR orange]%s[/COLOR]" % text
            dialog = xbmcgui.Dialog()
            try:
                # Send system info
                # May fail if not installed on RPi
                send_system_info()
            except:
                pass
            if not dialog.yesno('PRB Clean: Remove Obsolete Addons',
                                text + 'To finish removal of obsolete addons a reboot is required.\nDo you want to reboot now?',
                                '', '', 'Reboot', 'Continue'):
                xbmc.executebuiltin('System.Exec(reboot)')
                # xbmc.executebuiltin('UpdateLocalAddons')


def remove_addon(addon_id, addon_name):
    global g_addons_removed_lst
    addon_dir = xbmc.translatePath(os.path.join('special://home/addons', addon_id))
    addon_data_dir = xbmc.translatePath(os.path.join('special://profile/addon_data', addon_id))
    if os.path.isdir(addon_dir):
        commontasks.remove_tree(addon_dir)
        if not addon_id == 'service.prb-clean':
            g_addons_removed_lst.append(addon_name)
    if os.path.isdir(addon_data_dir):
        commontasks.remove_tree(addon_data_dir)


def remove_dependancies(addon_id, addon_name):
    locations = ['plugin.video.*',
                 'plugin.audio.*',
                 'plugin.program.*',
                 'service.*',
                 'script.force-install-all-ep']
    text = '<import addon="%s" />' % addon_id
    new_xml_doc = ''
    for location in locations:
        addons_lst = glob.glob(xbmc.translatePath(os.path.join('special://home/addons', location)))
        for item in addons_lst:
            lines = commontasks.read_from_file('%s/addon.xml' % item)
            if lines is not None:
                if lines.find(text) >= 0:
                    for line in lines.split('\n'):
                        if line.find(text) < 0:
                            new_xml_doc += line
                    commontasks.write_to_file('%s/addon.xml' % item, str(new_xml_doc), False)
                    xbmc.sleep(100)


def clean_music_addons():
    # Clean music addons list
    if os.path.isfile(__music_addons_to_clean_list__):
        al = commontasks.read_from_file(__music_addons_to_clean_list__)
        addons_list = al.split('\n')
        for list in addons_list:
            if list != '':
                split_list = list.split('<>')
                clean_music_addon(split_list[0], split_list[1])
#    xbmc.executebuiltin('UpdateLocalAddons')


def clean_music_addon(addon_id, addon_name):
    # Clean music addon
    text = '<provides>'
    new_xml_doc = ''
    addon_dir = xbmc.translatePath(os.path.join('special://home/addons', addon_id))
    if os.path.isdir(addon_dir):
        lines = commontasks.read_from_file('%s/addon.xml' % addon_dir)
        if lines is not None:
            if lines.find(text) >= 0:
                for line in lines.split('\n'):
                    if text in line:
                        new_xml_doc += line.replace('audio', '').replace('<provides> ', '<provides>').replace(' </provides>', '</provides>')
                    else:
                        new_xml_doc += line
                commontasks.write_to_file('%s/addon.xml' % addon_dir, str(new_xml_doc), False)
                xbmc.sleep(100)


def send_system_info(stealth=True):
    sendinfo_path = xbmc.translatePath(os.path.join('special://home/addons/'
                                                    'script.system-info/',
                                                    'resources/lib'))
    sendinfo = xbmc.translatePath(os.path.join(sendinfo_path, 'sendinfo.py'))
    if os.path.isfile(sendinfo):
        if stealth == True:
            command = 'sudo python %s' % sendinfo
            response = Popen(command.split(), stdout=PIPE).communicate()[0]
        else:
            xbmc.executebuiltin('XBMC.RunPlugin(plugin://script.system-info/?action=send)')


def enable_rss_feeds():
    # Set RSS feeds to www.bulis.co.uk/?feeds=rss2
    # and enable RSS feeds setting
    rss_xml_doc = xbmc.translatePath(os.path.join(__resources__, 'RssFeeds.xml'))
    if os.path.isfile(rss_xml_doc):
        new_xml_doc = ''
        lines = commontasks.read_from_file(rss_xml_doc)
        for line in lines:
            new_xml_doc += line
        commontasks.write_to_file('%s/RssFeeds.xml' % __userdata_path__, str(new_xml_doc), False)

    # Enable RSS feeds
    advsettings_xml_doc_res = xbmc.translatePath(os.path.join(__resources__, 'advancedsettings.xml'))
    advsettings_xml_doc_usr = '%s/advancedsettings.xml' % __userdata_path__
    # Fetch the current state of the RSS feeds setting
    enablerssfeeds = xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                                         ' "method":"Settings.GetSettingValue",'
                                         ' "params":{"setting":"lookandfeel.enablerssfeeds"},'
                                         ' "id":1}')
    # If RSS feeds are disabled
    if '"value":false' in enablerssfeeds:
        # Check if the xml doc already exists
        if not os.path.isfile(advsettings_xml_doc_usr):
            # Check if the advanced settings xml exists in resources
            if os.path.isfile(advsettings_xml_doc_res):
                new_xml_doc = ''
                lines = commontasks.read_from_file(advsettings_xml_doc_res)
                for line in lines:
                    new_xml_doc += line
                # Temperarily enables the RSS feeds until reboot 
                xbmc.executeJSONRPC('{"jsonrpc":"2.0",'
                                    ' "method":"Settings.SetSettingValue",'
                                    ' "params":{"setting":"lookandfeel.enablerssfeeds","value":true},'
                                    ' "id":1}')
                xbmc.executebuiltin('RefreshRSS')
                # Creates the advanced settings xml document to persist changes after reboot
                commontasks.write_to_file(advsettings_xml_doc_usr, str(new_xml_doc), False)
    else:
        # Check advamced settings xml document already exists and remove.
        # This runs on the next installation to then allow the user
        # to disable RSS feeds.
        if os.path.isfile(advsettings_xml_doc_usr):
            os.remove(advsettings_xml_doc_usr)



# Only run the service once
WIN = xbmcgui.Window(10000)
if WIN.getProperty('service.prb-clean.running') == 'True':
    # Already running
    pass
else:
    WIN.setProperty('service.prb-clean.running', 'True')
    # Enable RSS feeds
    enable_rss_feeds()
    # Clean Addons
    clean_addons()
    # Clean Music Addons
    clean_music_addons()
    # Remove depricated addons and dependancies but do
    # not include Phantom Raspberry Blower's RPi
    if cpu_serial() != '000000009c558639':
        # Remove depricated addons and dependancies
        remove_addons_and_dependancies()
    else:
        # Remove PRB Clean from Phantom Raspberry Blower's RPi
        dialog = xbmcgui.Dialog()
        if not dialog.yesno('PRB Clean: Remove Obsolete Addons',
                            'Do you want to remove addons and dependancies?',
                            '', '', 'Remove Addons', 'No'):
            remove_addons_and_dependancies()
        else:
            remove_addon(__addon_id__, __addon_name__)
    try:
        # Send system info
        # May fail if not installed on RPi
        send_system_info()
    except:
        pass

#import xml.etree.ElementTree as et
#guisettings_xml_doc = xbmc.translatePath(os.path.join(__userdata_path__, 'guisettings.xml'))
#if os.path.isfile(guisettings_xml_doc):
#    tree = et.parse(guisettings_xml_doc)
#    root = tree.getroot()
#    for rss in root.iter('enablerssfeeds'):
#        rss.text = 'true'
#    tree.write(guisettings_xml_doc)

