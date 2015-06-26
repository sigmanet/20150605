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
        """
        Initialize switch object
        :return:
        """

        self.config = ''
        self.mac = ''
        self.hostname = ''
        self.numports = ''
        self.modnum = ''
        self.model = ''
        self.porttype = ''
        self.secondhalf = 0
        self.postconfig = ''
        self.finalconfig = ''

    def scrub_config(self):
        """
        This cleans up original config by removing anything before the version
        and deleting anything start with the end line

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
        """
        This determines what type of switch the original config comes from.

        :return:
        """

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


    def config_hostname(self):
        """
        This changes the hostname for all iterations of the config
        """

        newconfigfinal = ''

        for line in self.config.split('\n'):
            m = re.search(r'(hostname) (\w+)', line)
            if m:
                newline = '\nhostname ' + self.hostname + '\n'
            else:
                newline = line + '\n'
            newconfigfinal += newline
        self.config = newconfigfinal

    def convertf(self, oldswitch):
        """
        Used for FastEthernet Switches
        This converts original switch configs for equal port numbered switches
        or copies a 24 port switch config to the first 24 ports
        """

        print 'convertf'
        newconfigfinal = ''
        intnum = 0
        if self.secondhalf == 1:
            adddown = 24
            addup = 2
        else:
            adddown = 0
            addup = 0
        for line in oldswitch.config.split('\n'):
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

    def convertg(self, oldswitch):
        """
        Used for GigabitEthernet Switches
        This converts original switch configs for equal port numbered switches
        or copies a 24 port switch config to the first 24 ports

        """

        newconfigfinal = ''
        intnum = 0
        if self.secondhalf == 1:
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

                if oldswitch.model == 'g24' and intnum >= 25 and self.secondhalf == 0:
                    intnum -= 24
                    newint = 'TenGigabitEthernet'
                    submod = '/1/'
                elif oldswitch.model == 'g24' and intnum >= 49 and self.secondhalf == 1:
                    intnum -= 46
                    newint = 'TenGigabitEthernet'
                    submod = '/1/'
                elif oldswitch.model == 'g48' and intnum >= 49:
                    intnum -= 48
                    newint = 'TenGigabitEthernet'
                    submod = '/1/'
                newline = '\ninterface ' + newint + \
                          self.modnum + submod + str(intnum) + '\n'
            if change == 0:
                newline = line + '\n'
            newconfigfinal += newline
        self.config += newconfigfinal


    def get_first_port(self):
        """
        This extracts teh gconfig for G1/0/1 in the new config to be used in the post install script
        """
        write = 0
        self.g101 = ''
        for line in self.config.split('\n'):
            m = re.search(r'^interface GigabitEthernet1/0/1$', line)
            if m:
                write = 1
            m = re.search(r'\!', line)
            if m:
                write = 0

            if write == 1:
               self.g101  += line + '\n'

    def config_interfaces(self, oldswitch):
        """
        This looks at old and new port numbers and determines which
        mapping function is required

        :param oldswitch: object containing all info for origin switch
        """
        print '->config_interfaces', self.modnum, oldswitch.numports, self.numports, self.secondhalf, oldswitch.model
        if self.numports == oldswitch.numports:
            # copy normal and fix module numbers
            print 'equal',
            if oldswitch.model[:1] == 'f':
                self.convertf(oldswitch)
            elif oldswitch.model[:1] == 'g':
                self.convertg(oldswitch)
            else:
                print 'Unknown Model'
            self.secondhalf = 0

        elif self.numports == '48' and oldswitch.numports == '24' and self.secondhalf == 0:
            # copy to bottom ports, set flag to 1
            print 'unequal, is not second half'
            if oldswitch.model[:1] == 'f':
                self.convertf(oldswitch)
            elif oldswitch.model[:1] == 'g':
                self.convertg(oldswitch)
            else:
                print 'Unknown Model'
            self.secondhalf = 1

        elif self.numports == '48' and oldswitch.numports == '24' and self.secondhalf == 1:
            # copy to bottom ports (+24), set flag to 0
            print 'unequal, is second half'
            if oldswitch.model[:1] == 'f':
                self.convertf(oldswitch)
            elif oldswitch.model[:1] == 'g':
                self.convertg(oldswitch)
            else:
                print 'Unknown Model'
            self.secondhalf = 0
        else:
            print "Error: config_interfaces - No match"

    def addtemplate(self, template):
        """
        Append base.txt file to new switch config for customization
        """

        tmp = open(basetemplate, 'r')
        self.append = tmp.read()
        tmp.close()
        self.config += self.append

    def config_postconfig(self, tftpserver):
        """
        Create post-config script to perform cleanup
        """

        self.postconfig = '"copy run start"\n' \
                     '"copy running-config tftp://' + tftpserver + 'QA/' + \
                     self.hostname + '.txt"\n' \
                     '"do copy running-config tftp://' + tftpserver + 'QA/' + \
                     self.hostname + '.txt"\n' \
                     '"interface vlan 1" "no ip address" "shutdown\n' \
                     '"copy run start"\n' \
                     '"interface g1/0/1" "desc vstack postconfig test"\n' \
                    + self.g101




def director_config(macset, ios, tftpserver):
    """
    Generate config script to be applied to director
    :param macset:
    :param ios:
    :return:
    """

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
newswitch = switchClass()

#  Open master CSV file and process lines
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
        if row['Master MAC'] <> newswitch.mac:
            print '\n\nNEW SWITCH ON THIS LINE:', row['Master MAC']

            # Update hostname for stack
            newswitch.config_hostname()

            # Add additional customization
            newswitch.addtemplate(basetemplate)

            # Write config for stack
            configout = open(tftproot + newswitch.mac + '.txt', 'w')
            configout.write(newswitch.config)
            configout.close()
            # create post-config script
            # newswitch.postconfig = config_postconfig(newswitch.hostname)

            configwritten = 1


            newswitch = switchClass()

        else:
            print '\n\nDUP SWITCH ON THIS LINE:', row['Master MAC']
            # newswitch.flag = 1

            configwritten = 0

        # Assign attributes to active newswitch instance
        newswitch.mac = row['Master MAC']
        newswitch.hostname = row['New Hostname']
        newswitch.numports = row['New Ports']
        newswitch.modnum = row['Module']

        # Process interfaces
        newswitch.config_interfaces(oldswitch)

        # Get information for g1/0/1 to be used in postconfig script
        newswitch.get_first_port()


        # print '*******\n', newswitch.config



        # Write post-config script for stack
        newswitch.config_postconfig(tftpserver)
        postconfigout = open(
            tftproot + newswitch.mac + '-postconfig.txt', 'w')
        postconfigout.write(newswitch.postconfig)
        postconfigout.close()

        # Create CLI script to configure vstack
        maclist.append(newswitch.mac)
        macset = set(maclist)
        director_config(macset, ios, tftpserver)
        lastswitch = newswitch.mac



        newswitch.finalconfig += newswitch.config

    if configwritten == 0:
        # Update hostname for stack
        newswitch.config_hostname()

        # Add additional customization
        newswitch.addtemplate(basetemplate)

        # Write config for stack
        configout = open(tftproot + newswitch.mac + '.txt', 'w')
        configout.write(newswitch.config)
        configout.close()

