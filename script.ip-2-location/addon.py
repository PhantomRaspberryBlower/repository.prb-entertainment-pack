#!/bin/python

import xbmcgui
import xbmcaddon

from resources.lib.ipinfo import IPInfo

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-09-2018
# Description: Addon for displaying a location for a given IP address

# Get addon details
__addon_id__ = 'script.ip-2-location'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__author__ = 'Phantom Raspberry Blower'


def  ip2location(ipaddr):
    """
    Show ip info including location
    """
    ip_info = IPInfo(ipaddr)
    if ip_info == 'Error getting IP address info!':
        notification(ip_info, 'IP 2 Location', __icon__, 5000)
    else:
        window = xbmcgui.WindowXMLDialog('script-ip-2-location.xml',
                                         __addon__.getAddonInfo('path'))
        win = xbmcgui.Window(10147)
        win.setProperty('HeadingLabel', '[COLOR blue]Location for IP Address:[/COLOR] ' + ip_info.ip_addr)
        win.setProperty('MapImage', ip_info.mapimage)
        win.setProperty('Region', ip_info.region)
        win.setProperty('City', ip_info.city)
        win.setProperty('PostCode', ip_info.postcode)
        win.setProperty('Coordinates', ip_info.coordinates)
        win.setProperty('Country', ip_info.country)
        win.setProperty('Hostname', ip_info.hostname)
        win.setProperty('AddressType', ip_info.addrtype)
        win.setProperty('ASN', ip_info.asn)
        win.setProperty('Organization', ip_info.organization)
        win.setProperty('Route', ip_info.route)
        win.setProperty('Description', ip_info.description)
        window.doModal()
        del window

def notification(message, title, icon, duration):
    # Show message notification
    dialog = xbmcgui.Dialog()
    dialog.notification(title, message, icon, duration)


if __name__ == '__main__':
    dialog = xbmcgui.Dialog()
    ip_addr = dialog.input('Enter IP Address', type=xbmcgui.INPUT_IPADDRESS)
    ip2location(ip_addr)
else:
    print 'Needs to run as main!'
