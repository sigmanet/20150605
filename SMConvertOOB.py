__author__ = 'TMagill'
import csv
import sys
import re

tftpserver = '1.1.1.2'
ios = 'cat3k_caa-universalk9.SPA.03.03.05.SE.150-1.EZ5.bin'
tftproot = 'c:/TFTP-Root/SM2/'
# basename = sys.argv[1]
basename = "C:/Users/tmagill/Documents/Projects/" \
           "Santa_Monica/Scripts/configs/switchtable.csv"
basetemplate = "C:/Users/tmagill/Documents/Projects/" \
           "Santa_Monica/Scripts/configs/base.txt"

lastswitch = ''
directorconfig = ''
maclist = []

class switchClass():
    def __init__(self):
        self.config = ''
        self.flag = 0
        self.mac = ''
        self.hostname = ''
        self.numports = ''
        self.modnum = ''

    def scrub_config(self):
        """
        This cleans up original config by removing anything before the version
        and deleting anything start with the end line

        :param oldconfig: the original config passed in
        :return:
        """
        write = 0
        oldconfig = self.config
        self.config = ''
        for line in oldconfig.split('\n'):
            m = re.search(r'^version (\w+)', line)
            if m:
                write = 1
            m = re.search(r'^end', line)
            if m:
                write = 0

            if write == 1:
                self.config += line + '\n'

    def identify(self):
        for line in self.config.split('\n'):
            m = re.search(r'interface FastEthernet0/24', line)
            if m:
                self.model = 'f24'
                self.numports = '24'
                self.portype = 'FastEthernet0'
            m = re.search(r'interface FastEthernet0/48', line)
            if m:
                self.model = 'f48'
                self.numports = '48'
                self.portype = 'FastEthernet0'
            m = re.search(r'interface GigabitEthernet0/24', line)
            if m:
                self.model = 'g24'
                self.numports = '24'
                self.portype = 'GigabitEthernet0'
            m = re.search(r'interface GigabitEthernet0/48', line)
            if m:
                self.model = 'g48'
                self.numports = '48'
                self.portype = 'GigabitEthernet0'

        print 'Identify: ' + self.model


    def config_hostname(self, newhostname):
        """
        This changes the hostname for all iterations of the config
        """

        newconfigfinal = ''

        for line in self.config.split('\n'):
            m = re.search(r'(hostname) (\w+)', line)
            if m:
                newline = '\nhostname ' + newhostname + '\n'
            else:
                newline = line + '\n'
            newconfigfinal += newline
        self.config = newconfigfinal

    def convertf(self, oldconfig):
        """
        This converts original switch configs for equal port numbered switches
        or copies a 24 port switch config to the first 24 ports

        :param newconfig: active config being manipulated
        :param newmodnum: active switch module number of stack
        :return:
        """

        newconfigfinal = ''
        intnum = 0
        if self.flag == 1:
            adddown = 24
            addup = 2
        else:
            adddown = 0
            addup = 0
        for line in oldconfig.split('\n'):
            change = 0
            m = re.search(r'(^interface FastEthernet0)/(\d+)', line)
            if m:
                change = 1
                intnum = str(int(m.group(2)) + adddown)
                newline = '\ninterface GigabitEthernet' + \
                          self.modnum + '/0/' + intnum + '\n'
            m = re.search(r'(^interface GigabitEthernet0)/(\d+)', line)
            if m:
                change = 1
                intnum = str(int(m.group(2)) + addup)
                newline = '\ninterface TenGigabitEthernet' + \
                          self.modnum + '/1/' + intnum + '\n'
            if change == 0:
                newline = line + '\n'
            newconfigfinal += newline
        # print newconfigfinal
        self.config += newconfigfinal

    def convertg(self, oldconfig):
        """
        This converts original switch configs for equal port numbered switches
        or copies a 24 port switch config to the first 24 ports

        :param newconfig: active config being manipulated
        :param newmodnum: active switch module number of stack
        :return:
        """

        global oldswitch
        newconfigfinal = ''
        intnum = 0
        if self.flag == 1:
            adddown = 24
            addup = 2
        else:
            adddown = 0
            addup = 0
        for line in oldswitch.config.split('\n'):
            change = 0
            newint = 'GigabitEthernet'
            submod = '/0/'
            m = re.search(r'(^interface GigabitEthernet0)/(\d+)', line)
            if m:
                change = 1
                intnum = int(m.group(2)) + adddown
                if oldswitch.model == 'g24' and intnum >= 25:
                    intnum -= 24
                    newint = 'TenGigabitEthernet'
                    submod = '/1/'
                elif oldswitch.model == 'g48' and intnum >= 49:
                    intnum -= 48
                    newint = 'TenGigabitEthernet'
                    submod = '/1/'
                newline = '\ninterface ' + newint + \
                          self.modnum + submod + str(intnum) + '\n'
        # print newconfigfinal
            if change == 0:
                newline = line + '\n'
            newconfigfinal += newline
        self.config += newconfigfinal

    def config_interfaces(self, oldconfig, oldnumports, oldmodel):
        """
        This looks at old and new port numbers and determines which
        mapping function is required

        :param newconfig: active config being manipulated
        :param newmodnum: module number of new stack member
        :param oldnumports: old switch number of ports
        :param newnumports: new switch number of ports
        :return:
        """
        global oldswitch
        print '->config_interfaces', self.modnum, oldnumports, self.numports, self.flag, oldmodel
        if self.numports == oldnumports:
            # copy normal and fix module numbers
            print 'equal',
            if oldswitch.model[:1] == 'f':
                self.flag = 0
                self.convertf(oldconfig)
            elif oldswitch.model[:1] == 'g':
                self.flag = 0
                self.convertg(oldconfig)
            else:
                print 'Unknown Model'

        elif self.numports == '48' and oldnumports == '24' and self.flag == 0:
            # copy to bottom ports, set flag to 1
            print 'unequal, flag 0'
            if oldswitch.model[:1] == 'f':
                self.flag = 0
                self.convertf(oldconfig)
            elif oldswitch.model[:1] == 'g':
                self.flag = 0
                self.convertg(oldconfig)
            else:
                print 'Unknown Model'
            self.flag = 1

        elif self.numports == '48' and oldswitch.numports == '24' and self.flag == 1:
            # copy to bottom ports (+24), set flag to 0
            print 'unequal, flag 1'
            if oldswitch.model[:1] == 'f':
                self.flag = 0
                self.convertf(oldconfig)
            elif oldswitch.model[:1] == 'g':
                self.flag = 0
                self.convertg(oldconfig)
            else:
                print 'Unknown Model'
            self.flag = 0
            print 'DEBUG: ',self.flag
        else:
            print "Error: config_interfaces - No match"

    def addtemplate(self, template):
        tmp = open(basetemplate, 'r')
        self.append = tmp.read()
        tmp.close()
        self.config += self.append

def config_postconfig(newhostname):
    """
    Create post-config script to perform cleanup
    """
    global tftpserver
    postconfig = '"copy run start"\n' \
                 '"copy running-config tftp://' + tftpserver + 'QA/' + \
                 newhostname + '.txt"\n' \
                 '"do copy running-config tftp://' + tftpserver + 'QA/' + \
                 newhostname + '.txt"\n' \
                 '"interface vlan 1" "no ip address" "shutdown\n' \
                 '"copy run start"\n' \
                 '"interface g1/0/1" "desc vstack postconfig test"\n'

    return postconfig



def director_config(macset, ios):
    global tftpserver
    vsconfig = 'config t\n!\n'
    for mac in macset:
        vsconfig += 'vstack group custom ' + mac + ' mac\n'
        vsconfig += ' match mac ' + mac + '\n'
        vsconfig += ' config tftp://' + tftpserver + '/' + mac + '.txt\n'
        vsconfig += ' image tftp://' + tftpserver + '/' + ios + '\n'
        vsconfig += ' script tftp://' + tftpserver + '/' + mac + '-postconfig.txt\n'
        vsconfig += '!\n'
    vstackconfigout = open(
    tftproot + 'vstackconfig.txt', 'w')
    vstackconfigout.write(vsconfig)
    vstackconfigout.close()

#
# Initialize files
#

csvfile = open(basename, 'r')
reader = csv.DictReader(csvfile)

with open(basename, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    global maclist
    for row in reader:
        oldswitch = switchClass()

        oldswitch.hostname = row['Old Hostname']
        oldswitch.numports = row['Old Ports']
        oldswitch.config = open('C:/Users/tmagill/Documents/Projects/'
                                'Santa_Monica/Scripts/configs/' + row['Config'],
                                'r').read()

        oldswitch.scrub_config()
        oldswitch.identify()

        # check if new switch
        newmac = row['Master MAC']
        if newmac <> lastswitch:
            newswitch = switchClass()
            print '\n\nNEW SWITCH ON THIS LINE:', newmac
        else:
            print '\n\nDUP SWITCH ON THIS LINE:', newmac
            newswitch.flag = 1

        newswitch.mac = row['Master MAC']
        newswitch.hostname = row['New Hostname']
        newswitch.numports = row['New Ports']
        newswitch.modnum = row['Module']


        newswitch.config_interfaces(oldswitch.config, oldswitch.numports, oldswitch.model)

        # Update hostname for stack
        newswitch.config_hostname(newswitch.hostname)
        newswitch.addtemplate(basetemplate)
        # print '*******\n', newswitch.config

        # Write config for stack
        configout = open(tftproot + newswitch.mac + '.txt', 'w')
        configout.write(newswitch.config)
        configout.close()
        # create post-config script
        newswitch.postconfig = config_postconfig(newswitch.hostname)

        # Write post-config script for stack
        postconfigout = open(
            tftproot + newswitch.mac + '-postconfig.txt', 'w')
        postconfigout.write(newswitch.postconfig)
        postconfigout.close()

        # Create CLI script to configure vstack
        maclist.append(newswitch.mac)
        macset = set(maclist)
        director_config(macset, ios)
        lastswitch = newswitch.mac



