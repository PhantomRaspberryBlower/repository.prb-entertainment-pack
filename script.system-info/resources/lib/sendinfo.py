#!/bin/python

import os
import re
import requests
import platform
from subprocess import Popen, PIPE

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 01-10-2018
# Description: Script for submitting system information
#              about software, CPU, memory, storage,
#              networks and insatlled addons to a web form.
#              Tested on Raspberry Pi's.

def regex_from_to(text, from_string, to_string, excluding=True):
    if excluding:
        r = re.search("(?i)" + from_string +
                      "([\S\s]+?)" +
                      to_string, text).group(1)
    else:
        r = re.search("(?i)(" +
                      from_string +
                      "[\S\s]+?" +
                      to_string +
                      ")", text).group(1)
    return r


response = ''
curr_path = os.path.realpath(__file__).replace('sendinfo.py', '')
os_friendly_name = platform.system()
if os_friendly_name != 'Windows':
    command = 'sudo python %ssysteminfo.py' % curr_path
    response = Popen(command.split(), stdout=PIPE).communicate()[0]
    response = response.replace('\t', '').replace(':', ': ')
    url = 'http://www.bulis.co.uk/index.php?rest_route=/contact-form-7/v1/contact-forms/1191/feedback'
    payload = {'username': regex_from_to(response, 'Username: ', '\n'),
               'hostname': regex_from_to(response, 'Hostname: ', '\n'),
               'platform': regex_from_to(response, 'Platform: ', '\n'),
               'distribution': regex_from_to(response, 'Distribution: ', '\n'),
               'dist-version': regex_from_to(response, 'Dist. Version: ', '\n'),
               'system': regex_from_to(response, 'System: ', '\n'),
               'node': regex_from_to(response, 'Node: ', '\n'),
               'release': regex_from_to(response, 'Release: ', '\n'),
               'version': regex_from_to(response, '  Version: ', '\n'),
               'machine': regex_from_to(response, 'Machine: ', '\n'),
               'processor': regex_from_to(response, 'Processor: ', '\n'),
               'model': regex_from_to(response, 'Model: ', '\n'),
               'cores': regex_from_to(response, 'Cores: ', '\n'),
               'temperature': regex_from_to(response, 'Temp:', '\n'),
               'hardware': regex_from_to(response, 'Hardware: ', '\n'),
               'revision': regex_from_to(response, 'Revision: ', '\n'),
               'serial-number': regex_from_to(response, 'Serial number: ', '\n'),
               'total-memory': regex_from_to(response, 'Total: ', '\n'),
               'used-memory': regex_from_to(response, 'Used: ', '\n'),
               'free-memory': regex_from_to(response, 'Free: ', '\n'),
               'storage': regex_from_to(response, 'Storage:', 'Network:'),
               'lan-ip-addr-eth0': regex_from_to(response, 'eth0: ', '\n'),
               'lan-ip-addr-wlan0': regex_from_to(response, 'wlan0: ', '\n'),
               'gateway-ip-addr': regex_from_to(response, 'Gateway IP Address: ', '\n'),
               'wan-ip-addr': regex_from_to(response, 'WAN IP Address: ', '\n'),
               'whois-netname': regex_from_to(response, 'netname: ', '\n'),
               'whois-role': regex_from_to(response, 'role: ', '\n'),
               'whois-desc': regex_from_to(response, 'descr: ', '\n'),
               'whois-country': regex_from_to(response, 'country: ', '\n'),
               'previous-networks': regex_from_to(response, 'Previous Networks:', 'Network Devices:'),
               'network-devices': regex_from_to(response, 'Network Devices:', '\n\n').replace(': ', ':'),
               'addons-installed': regex_from_to(response, 'Addons Installed:', '\n\n')}
    r = requests.post(url, data=payload)
    print regex_from_to(r.text, '"message":"', '"}')
else:
    print 'Unable to send - System Info does not work with MS Windows operating system. :('
