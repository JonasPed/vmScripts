#!/usr/bin/env python3

import sys
import argparse
from xml.dom import minidom
from collections import namedtuple
from subprocess import call
from subprocess import check_output

def GetDisks(domain):
    Disk = namedtuple('Disk', 'device, file')

    d = []

    raw_xml = check_output(["virsh", "dumpxml " + domain])
    xml = minidom.parseString(raw_xml)

    disks = xml.getElementsByTagName('disk')
    for disk in disks:
        if disk.getAttribute("type") == "file":
            target = disk.getElementsByTagName("target")[0]
            device = target.getAttribute('dev')
            
            source = disk.getElementsByTagName("source")[0]
            file = source.getAttribute("file")
            
            d.append(Disk(device = device, file = file))
        
    print(d)
    return d

def __SnapShotDomain(domain, name):
#     xml = "<domainsnapshot><name>" + name + "</name><description>backup</description></domainsnapshot>"
    __ExecuteCommand("virsh snapshot-create-as " + domain + " " + name + " \"backup\" --disk-only --atomic")
#     domainPtr.snapshotCreateXML(xml, libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_DISK_ONLY + libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC)
    
def CreateTempSnapshot(domainPtr):
    __SnapShotDomain(domain, "backup_snapshot")

def DoBlockCommit(domainPtr, disk, domain):
    __ExecuteCommand("virsh blockcommit " + domain + " " + disk.device + " --active --pivot --shallow --verbose")
    
#     domainPtr.blockCommit(disk.device, Null, Null, 0, libvirt.VIR_DOMAIN_BLOCK_COMMIT_SHALLOW + 
#                                                         libvirt.VIR_DOMAIN_BLOCK_COMMIT_ACTIVE + 
#                                                         libvirt.VIR_DOMAIN_BLOCK_COMMIT_DELETE )
 
def DeleteSnapshot(domain):
    __ExecuteCommand("virsh snapshot-delete --domain " + domain + " backup_snapshot --metadata")

def DeleteSnapshotFiles(disk):
    __ExecuteCommand("virsh vol-delete --pool Default --vol " + disk.file)

def PoolRefresh():
    __ExecuteCommand("virsh pool-refresh Default")

def __ExecuteCommand(command):
    call(command, shell = True)


def BackupDomain(domain):
    domain = "test"

    CreateTempSnapshot(domain)

    disks = GetDisks(domain)

    for d in disks:
        DoBlockCommit(domain, d, domain)
        
    DeleteSnapshot(domain)
    
    PoolRefresh()
    
    for d in disks:
        DeleteSnapshotFiles(d)

def BackupAllDomains():
    raise Exception("Not yet implemented")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backup virtual machine.')
    parser.add_argument("--all", dest="allDomains", action="store_true", help = "Backup all running domains.")
    parser.add_argument('--domain', dest='domains', action='append', help='Domain to backup. Use multiple --domain arguments to backup multiple domains in one call.')

    args = parser.parse_args()
    if(args.allDomains == False and args.domains == None):
        print("Use either --all or --domain argument.")
        sys.exit(1)

    if(args.allDomains and args.domains != None):
        print("Arguments --all and --domain are mutually exclusive.")
        sys.exit(1)

    if(args.allDomains):
        BackupAllDomains()
    else:
        for domain in args.domains:
            BackupDomain(domain)    
    
    sys.exit(0)
