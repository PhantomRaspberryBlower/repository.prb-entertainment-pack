#!/bin/python
 
from urllib2 import urlopen
from collections import namedtuple
from subprocess import check_call, Popen, PIPE
import socket
import fcntl
import struct
import platform
import getpass
import os

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 01-10-2018
# Description: Script for displaying system information
#              about software, CPU, hardware, memory,
#              storage, networks and addons installed.
#              Tested on Raspberry Pi.

class SystemInfo():

    # ## Software Information ## #

    @property
    def username(self):
        # Get username
        return getpass.getuser()

    @property
    def hostname(self):
        # Get hostname
        return socket.gethostname()

    @property
    def is_user_root(self):
        # Is current user root
        if os.geteuid() == 0:
            return True
        else:
            return False

    @property
    def os_platform(self):
        return platform.platform()    

    @property
    def platform_system(self):
        return platform.system()

    @property
    def platform_node(self):
        return platform.node()

    @property
    def platform_release(self):
        return platform.release()

    @property
    def platform_version(self):
        return platform.version()

    @property
    def platform_machine(self):
        return platform.machine()

    @property
    def platform_processor(self):
        return platform.processor()

    @property
    def platform_architecture(self):
        return platform.architecture()
    
    @property
    def platform_python_build(self):
        return platform.python_build()

    @property
    def platform_python_compiler(self):
        return platform.python_compiler()
    
    @property
    def platform_python_branch(self):
        return platform.python_branch()
    
    @property
    def platform_python_implementation(self):
        return platform.python_implementation()
    
    @property
    def platform_python_revision(self):
        return platform.python_revision()
    
    @property
    def platform_python_version(self):
        return platform.python_version()
    
    @property
    def platform_python_version_tuple(self):
        return platform.python_version_tuple()
    
    @property
    def platform_win32_ver(self):
        # Windows platforms
        return platform.win32_ver()
    
    @property
    def platform_mac_ver(self):
        return platform.mac_ver()   

    @property
    def platform_linux_distribution(self):
        # Unix platforms
        return platform.linux_distribution()

    # ## CPU Information ## #

    @property
    def cpu_model(self):
        # Get Model Name
        return self._get_cpu_item('model name', '')

    @property
    def cpu_hardware(self):
        # Get Hardware
        return self._get_cpu_item('Hardware', '')

    @property
    def cpu_revision(self):
        # Get Revision
        return self._get_cpu_item('Revision', '')

    @property
    def cpu_serial(self):
        # Get CPU Serial Number
        return self._get_cpu_item('Serial', '0000000000000000')

    @property
    def cpu_cores(self):
        # Get number of cpu cores
        # Linux, Unix and MacOS:
        if hasattr(os, "sysconf"):
            if "SC_NPROCESSORS_ONLN" in os.sysconf_names:
                # Linux and Unix:
                ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
                if isinstance(ncpus, int) and ncpus > 0:
                    return ncpus
            else: # OSX:
                return int(os.popen2("sysctl -n hw.ncpu")[1].read())

    @property
    def cpu_temp(self):
        # Return CPU temperature as a character string
        try:
            output = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE).communicate()[0]
            return str(output[5:len(output)-3])
        except:
            return 'Unable to get CPU temperature! :('

    # ## Memory Informtion ## #

    # Get memory info
    @property
    def ram_info(self):
        _ntuple_RAMinfo = namedtuple('RAM', 'total used free')
        output = Popen(['free'], stdout=PIPE).communicate()[0]
        for line in output.split('\n'):
            if 'Mem:' in line:
                total = line.split()[1]
                used = line.split()[2]
                free = int(total) - int(used)
        return _ntuple_RAMinfo(total, used, free)

    # ## Storage Informtion ## #

    # Get hard drive(s) info
    @property
    def disk_info(self):
        devices = []
        devices.append(self.disk_usage("/root/"))
        for device in self.get_devices("/media/"):
            devices.append(self.disk_usage("/media/" + device + "/"))
        return devices

    # ## Network Informtion ## #

    @property
    def wan_ip_addr(self):
        # Get the WAN IP address
        try:
            return urlopen('http://ip.42.pl/raw').read()
        except:
            return 'Unable to get WAN IP Address! :('

    @property
    def default_gateway(self):
        # Get default gateway
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) and 2:
                    continue
                return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

    @property
    def arp_info(self):
        # Discover other devices on the network
        import re
        devices = []
        s = Popen(["arp"], stdout=PIPE).communicate()[0]
        for item in s.split('\n'):
            devices.append("%s" % item.strip())
        return devices

    ## # Functions # ##

    # ## Software Information ## #

    def get_platform_info(self):
        distname, dist_version, id = platform.linux_distribution()
        system, node, release, version, machine, processor = platform.uname()
        return (self.os_platform,
                distname,
                dist_version,
                id,
                system,
                node,
                release,
                version,
                machine,
                processor)

    def get_installed_addons(self, dir=None):
        if not dir == None:
            output = [dI for dI in os.listdir(dir) if os.path.isdir(os.path.join(dir, dI))]
            output.sort()
            return output


    # ## CPU Information ## #

    # Get CPU items
    def _get_cpu_item(self, item, ini_value):
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

    # ## Hard Disk Informtion ## #

    # Get Hard Drive Devices
    def get_devices(self, path):
        return next(os.walk(path))[1]

    # Get hard drive usage
    def disk_usage(self, path):
        _ntuple_diskusage = namedtuple('usage', 'path total used free')
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return _ntuple_diskusage(path, total, used, free)

    # ## Network Informtion ## #

    # Get list of network settings
    def get_network_settings(self):
        _ntuple_LANinfo = namedtuple('LAN', 'ssid psk proto')
        ssid = ''
        psk = ''
        proto = ''
        settings = []
        if os.path.exists('/var/lib/connman'):
            for network in next(os.walk('/var/lib/connman'))[1]:
                try:
                    settings.append((network, ''))
                    file = open('/var/lib/connman/%s/settings' % network, 'r')
                    for line in file:
                        settings.append((line[:line.find('=')],
                                         line[line.find('=')+1:].replace('\n',
                                         '')))
                    file.close()
                    settings.append(('', ''))
                except:
                    pass
        elif os.path.exists('/etc/wpa_supplicant/wpa_supplicant.conf'):
            file = open('/etc/wpa_supplicant/wpa_supplicant.conf', 'r')
            for line in file:
                settings.append((line[:line.find('=')].strip(),
                                 line[line.find('=')+1:].replace('\n',
                                 '')))
            file.close()
        else:
            return 'Unable to get Network Settings! :('
        return settings

    # Get list of networks
    def get_networks_info(self):
        try:
            lst = []
            tabs = ''
            for name, value in self.get_network_settings():
                if name != value:
                    if value != '':
                        if len(name) < 10:
                            tabs = "\t\t\t"
                        elif len(name) < 18:
                            tabs = "\t\t"
                        elif len(name) < 24:
                            tabs = "\t"
                        else:
                            tabs = "\t\t"
                        lst.append(' %s:%s%s\n' % (name, tabs, value))
                else:
                    lst.append('%s\n' % name)
            return lst
        except:
            return 'Unable to get Networks! :('

    # Get LAN IP address for either etho or wlan
    def get_lan_ip_addr(self, ifname):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                                    s.fileno(),
                                    0x8915, # SIOCGIFADDR
                                    struct.pack('256s', ifname[:15])
                                    )[20:24])
        except:
            return 'Unable to get LAN IP address! :('

    # Get whois response
    def get_whois(self, ip):
        results = []
        if self.is_tool_installed('whois') is False:
            if self.is_user_root:
                self.install_tool('whois')
            else:
                return results
        desc = ['netname:', 'descr:', 'country:', 'role:']
        command = 'whois ' + ip
        output = Popen(command.split(), stdout=PIPE).communicate()[0]
        for line in output.split('\n'):
            for item in desc:
                if line[0:len(item)] == item:
                    results.append(line[len(item):].strip())
        return results

    # Check tool is installed
    def is_tool_installed(self, name):
        try:
            devnull = open(os.devnull)
            Popen([name],
                  stdout=devnull,
                  stderr=devnull).communicate()
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                return False
        return True

    # Install Whois
    def install_tool(self, name):
        # Install tool and suppress output
        devnull = open(os.devnull, 'w')
        check_call(["sudo",
                    "apt-get",
                    "install",
                    "-y",
                    "-qq",
                    name], stdout=devnull, stderr=devnull)

    # Get complete system information
    def get_system_info(self):
        try:
            arp_info = self.arp_info
            disk_info = self.disk_info
            ram_info = self.ram_info
            networks_info = self.get_networks_info()
            whois_info = self.get_whois(self.wan_ip_addr)
            disk_info_txt = '\nStorage:'
            networks_info_txt = ''
            arp_info_txt = '\nNetwork Devices:\n'
            if self.is_user_root:
                networks_info_txt = '\nPrevious Networks:\n'
                for network in networks_info:
                    networks_info_txt = networks_info_txt + '\
                    %s' % (network)

            addons_info = self.get_installed_addons('/home/osmc/.kodi/addons')
            addons_info_txt = '\nAddons Installed:'
            for addon in addons_info:
                if (not addon == 'packages' and not addon == 'temp' 
                    and not 'resource.language.' in addon):
                    addons_info_txt = addons_info_txt + '\n \
                    %s' % (addon)

            addons_info_txt += '\n'
            (os_platform,
             distname,
             dist_version,
             id,
             system,
             node,
             release,
             version,
             machine,
             processor) = self.get_platform_info()
            for item in disk_info:
                disk_info_txt = disk_info_txt + u'\n \
                    Path:\t\t\t%s\n \
                    Total:\t\t\t%sGB\n \
                    Used:\t\t\t%sGB\n \
                    Free:\t\t\t%sGB\n' % (
                    item.path,
                    item.total / (1024**3),
                    item.used / (1024**3),
                    item.free / (1024**3))

            for device in arp_info:
                arp_info_txt = arp_info_txt + '\t\t%s\n' % device

            return u'\nSoftware:\n \
                    Username:\t\t\t%s\n \
                    Hostname:\t\t\t%s\n \
                    Platform:\t\t\t%s\n \
                    Distribution:\t\t%s\n \
                    Dist. Version:\t\t%s\n \
                    System:\t\t\t%s\n \
                    Node:\t\t\t%s\n \
                    Release:\t\t\t%s\n \
                    Version:\t\t\t%s\n \
                    Machine:\t\t\t%s\n \
                    Processor:\t\t\t%s\n \
                    \nCPU:\n \
                    Model:\t\t\t%s\n \
                    Cores:\t\t\t%s\n \
                    Temp:\t\t\t%s\n \
                    Hardware:\t\t\t%s\n \
                    Revision:\t\t\t%s\n \
                    Serial number:\t\t%s\n \
                    \nMemory:\n \
                    Total:\t\t\t%sMB\n \
                    Used:\t\t\t%sMB\n \
                    Free:\t\t\t%sMB\n \
                    %s \
                    \nNetwork:\n \
                    LAN IP Address:\n \
                    \teth0:\t\t\t%s\n \
                    \twlan0:\t\t\t%s\n \
                    Gateway IP Address:\t%s\n \
                    WAN IP Address:\t\t%s\n \
                    Whois:\n \
                    \tnetname:\t\t%s\n \
                    \trole:\t\t\t%s\n \
                    \tdescr:\t\t\t%s\n \
                    \tcountry:\t\t%s\n \
                    %s \
                    %s \
                    %s' % (self.username,
                           self.hostname,
                           self.os_platform,
                           distname,
                           dist_version,
                           system,
                           node,
                           release,
                           version,
                           machine,
                           processor,
                           self.cpu_model,
                           self.cpu_cores,
                           self.cpu_temp,
                           self.cpu_hardware,
                           self.cpu_revision,
                           self.cpu_serial,
                           int(ram_info.total) / 1024,
                           int(ram_info.used) / 1024,
                           int(ram_info.free) / 1024,
                           disk_info_txt,
                           self.get_lan_ip_addr('eth0'),
                           self.get_lan_ip_addr('wlan0'),
                           self.default_gateway,
                           self.wan_ip_addr,
                           whois_info[0],
                           whois_info[3],
                           whois_info[1],
                           whois_info[2],
                           networks_info_txt,
                           arp_info_txt,
                           addons_info_txt)
        except: 
            return 'Error! Unable to get system informtaion! :('

# Check if running stand-alone or imported
if __name__ == u'__main__':
    if platform.system() != u'Windows':
        import systeminfo
        si = SystemInfo()
        info = si.get_system_info()
        print(info)
    else:
        print(u'This script does not work with a Windows operating system. :( - Yet!')
