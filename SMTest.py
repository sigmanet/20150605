__author__ = 'TMagill'
import csv
import sys
import re


class baseClass():
    pass


flag = 0
lastswitch = ''
directorconfig = ''
maclist = []

def config_hostname(oldconfig, newhostname):
    """
    This changes the hostname for all iterations of the config
    """

    newconfigfinal = ''

    for line in oldconfig.split('\n'):
        m = re.search(r'(hostname) (\w+)', line)
        if m:
            newline = '\nhostname ' + newhostname + '\n'
        else:
            newline = line + '\n'
        newconfigfinal += newline
    return newconfigfinal


def copy_like(newconfig, newmodnum):
    """
    This converts original switch configs for equal port numbered switches
    or copies a 24 port switch config to the first 24 ports

    :param newconfig: active config being manipulated
    :param newmodnum: active switch module number of stack
    :return:
    """

    newconfigfinal = ''
    intnum = 0
    for line in newconfig.split('\n'):
        change = 0
        m = re.search(r'(FastEthernet0)/(\d+)', line)
        if m:
            change = 1
            intnum = m.group(2)
            newline = '\ninterface GigabitEthernet' + \
                      newmodnum + '/0/' + intnum + '\n'
        m = re.search(r'(GigabitEthernet0)/(\d+)', line)
        if m:
            change = 1
            intnum = m.group(2)
            newline = '\ninterface TenGigabitEthernet' + \
                      newmodnum + '/1/' + intnum + '\n'
        if change == 0:
            newline = line + '\n'
        newconfigfinal += newline
    return newconfigfinal


def copy_24top(newconfig, newmodnum):
    """
    This copies a 24 port switch config to the last 24 ports of a
    48 port switch

    :param newconfig: active config being manipulated
    :param newmodnum: active switch module number of stack
    :return:
    """

    newconfigfinal = ''
    intnum = 0
    for line in newconfig.split('\n'):
        change = 0
        m = re.search(r'(FastEthernet0)/(\d+)', line)
        if m:
            change = 1
            intnum = str(int(m.group(2)) + 24)
            newline = '\ninterface GigabitEthernet' + \
                      newmodnum + '/0/' + intnum + '\n'
        m = re.search(r'(GigabitEthernet0)/(\d+)', line)
        if m:
            change = 1
            intnum = str(int(m.group(2)) + 2)
            newline = '\ninterface TenGigabitEthernet' + \
                      newmodnum + '/1/' + intnum + '\n'
        if change == 0:
            newline = line + '\n'
        newconfigfinal += newline
    # print newconfigfinal
    return newconfigfinal


def config_interfaces(newconfig, newmodnum, oldnumports, newnumports):
    """
    This looks at old and new port numbers and determines which
    mapping function is required

    :param newconfig: active config being manipulated
    :param newmodnum: module number of new stack member
    :param oldnumports: old switch number of ports
    :param newnumports: new switch number of ports
    :return:
    """

    global flag
    print '->config_interfaces', newmodnum, oldnumports, newnumports, flag
    if newnumports == oldnumports:
        # copy normal and fix module numbers
        newconfig = copy_like(newconfig, newmodnum)

    elif newnumports == '48' and oldnumports == '24' and flag == 0:
        # copy to bottom ports, set flag to 1
        newconfig = copy_like(newconfig, newmodnum)
        flag = 1

    elif newswitch.numports == '48' and oldswitch.numports == '24' and flag == 1:
        # copy to bottom ports (+24), set flag to 0
        newconfig = copy_24top(newconfig, newmodnum)
        flag = 0
    else:
        print "Error: config_interfaces - No match"
    return newconfig


def config_postconfig(newhostname):
    """
    Create post-config script to perform cleanup
    """
    postconfig = 'copy run start\n' \
                 'copy startup-config tftp://1.1.1.2/QA/' + \
                 newhostname + '.txt\n' \
                 'conf t\n' \
                 'no interface vlan 1\n' \
                 'end\n'
    return postconfig

def scrub_config(oldconfig):
    """
    This cleans up original config by removing anything before the version
    and deleting anything start with the end line

    :param oldconfig: the original config passed in
    :return:
    """
    write = 0
    newconfigfinal = ''
    for line in oldconfig.split('\n'):
        m = re.search(r'^version (\w+)', line)
        if m:
            print 'write = 1'
            write = 1
        m = re.search(r'^end', line)
        if m:
            write = 0

        if write == 1:
            print 'write = 1'
            newconfigfinal += line + '\n'
    print newconfigfinal
    return newconfigfinal

def director_config(macset):
    vsconfig = 'config t\n!\n'
    for mac in macset:
        vsconfig += 'vstack config tftp://1.1.1.2/' + mac + '.txt\n'
        vsconfig += 'vstack image tftp://1.1.1.2/cat3k_caa-universalk9.SPA.03.03.05.SE.150-1.EZ5.bin\n'
        vsconfig += 'vstack script tftp://1.1.1.2/' + mac + '-postconfig.txt\n!\n'
    vstackconfigout = open(
    'C:/Users/tmagill/Documents/Projects/'
    'Santa_Monica/Scripts/configs/vstackconfig.txt', 'w')
    vstackconfigout.write(vsconfig)
    vstackconfigout.close()

#
# Initialize files
#
# basename = sys.argv[1]
basename = "C:/Users/tmagill/Documents/Projects/" \
           "Santa_Monica/Scripts/configs/switchtable.csv"
csvfile = open(basename, 'r')
reader = csv.DictReader(csvfile)

with open(basename, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    global maclist
    for row in reader:
        oldswitch = baseClass()

        oldswitch.hostname = row['Old Hostname']
        oldswitch.numports = row['Old Ports']
        oldswitch.config = open('C:/Users/tmagill/Documents/Projects/'
                                'Santa_Monica/Scripts/configs/' + row['Config'],
                                'r').read()

        oldswitch.config = scrub_config(oldswitch.config)

        newmac = row['Master MAC']
        # check if new switch
        if newmac <> lastswitch:
            flag = 0
            newswitch = baseClass()

            print '\n\nNEW SWITCH ON THIS LINE:', newmac
        else:
            print '\n\nDUP SWITCH ON THIS LINE:', newmac
            flag = 1

        newswitch.mac = row['Master MAC']
        newswitch.hostname = row['New Hostname']
        newswitch.numports = row['New Ports']
        newswitch.modnum = row['Module']

        if flag == 0:
            newswitch.config = oldswitch.config
            newswitch.config = config_interfaces(newswitch.config,
                                                 newswitch.modnum,
                                                 oldswitch.numports,
                                                 newswitch.numports)
        else:
            newswitch.config = newswitch.config + \
                               config_interfaces(oldswitch.config,
                                                 newswitch.modnum,
                                                 oldswitch.numports,
                                                 newswitch.numports)

        # Update hostname for stack
        newswitch.config = config_hostname(newswitch.config, newswitch.hostname)
        print '*******\n', newswitch.config

        # Write config for stack
        configout = open('C:/Users/tmagill/Documents/Projects/'
                         'Santa_Monica/Scripts/configs/' \
                         + newswitch.mac + '.txt', 'w')
        configout.write(newswitch.config)
        configout.close()
        # creat post-config script
        newswitch.postconfig = config_postconfig(newswitch.hostname)

        # Write post-config script for stack
        postconfigout = open(
            'C:/Users/tmagill/Documents/Projects/'
            'Santa_Monica/Scripts/configs/' \
            + newswitch.mac + '-postconfig.txt', 'w')
        postconfigout.write(newswitch.postconfig)
        postconfigout.close()

        # Create CLI script to configure vstack
        maclist.append(newswitch.mac)
        macset = set(maclist)
        director_config(macset)
        lastswitch = newswitch.mac



