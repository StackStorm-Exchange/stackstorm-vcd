# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from lib.vcd import VCDBaseActions
from xml.etree.ElementTree import Element, SubElement


class deployVAPPTemplate(VCDBaseActions):
    def run(self, vcloud="default", data=None):
        contenttype = "application/vnd.vmware.vcloud.composeVAppParams+xml"
        self.set_connection(vcloud)
        self.get_sessionid()

        post = {}
        all_orgs = self.get_orgs()
        for org in data:
            for vdc in data[org]['vdcs']:
                if org not in all_orgs.keys():
                    post["%s" % (org.lower())] = "Org does not exist"
                    continue

                org_details = self.get_org(all_orgs[org]['id'])
                # Check VDC exists
                if vdc not in org_details['vdcs'].keys():
                    post["%s (%s)" % (vdc.lower(), org.lower())] =\
                        "VDC does not exist"
                    continue

                # Check VAPP defined in input data
                if "vapps" not in data[org]['vdcs'][vdc].keys():
                    post["%s (%s)" % (vdc.lower(), org.lower())] =\
                        "No VAPPS defined"
                    continue

                vdcid = org_details['vdcs'][vdc]['id']
                endpoint = "vdc/%s/action/composeVApp" % vdcid

                cpureq = 0
                memreq = 0
                storagereq = {}
                storagestats = {}

                # CHECK RESOURCES AVAILABLE
                for svapp in data[org]['vdcs'][vdc]['vapps']:
                    for svm in data[org]['vdcs'][vdc]['vapps'][
                            svapp]['vms']:
                        svmdata = data[org]['vdcs'][vdc]['vapps'][
                            svapp]['vms'][svm]
                        cpureq += svmdata['cpu']
                        memreq += svmdata['memory']
                        if svmdata['Storage_Profile'] in storagereq.keys():
                            storagereq[svmdata['Storage_Profile']] += \
                                svmdata['hdd']
                        else:
                            storagereq[svmdata['Storage_Profile']] = 0
                            storagereq[svmdata['Storage_Profile']] += \
                                svmdata['hdd']

                compute = org_details['vdcs'][vdc]['computecapacity']
                if compute['Cpu']['Units'] == "MHz":
                    cpuused = int(compute['Cpu']['Used']) / 1000
                    cpulimit = int(compute['Cpu']['Limit']) / 1000
                if compute['Memory']['Units'] == "MB":
                    memused = int(compute['Memory']['Used']) / 1024
                    memlimit = int(compute['Memory']['Limit']) / 1024
                for sp in org_details['vdcs'][vdc]['storageprofiles']:
                    spdetails = org_details['vdcs'][vdc]['storageprofiles'][sp]
                    if sp not in storagestats.keys():
                        storagestats[sp] = {}
                    if spdetails['unit'] == 'MB':
                        storagestats[sp]['used'] = \
                            int(spdetails['used']) / 1024
                        storagestats[sp]['limit'] = \
                            int(spdetails['limit']) / 1024
                    else:
                        storagestats[sp]['used'] = int(spdetails['used'])
                        storagestats[sp]['limit'] = int(spdetails['limit'])

                notenough = False
                if (cpureq + cpuused) > cpulimit:
                    post["%s - %s - CPU" % (org.lower(), vdc.lower())] = \
                        "Insufficant Allocation"
                    notenough = True

                if (memreq + memused) > memlimit:
                    post["%s - Memory" % (vdc.lower())] = \
                        "Insufficant Allocation"
                    notenough = True

                for profile in storagereq:
                    if (storagereq[profile] + storagestats[profile]['used'])\
                            > storagestats[profile]['limit']:
                        post["%s - %s" % (vdc.lower(), profile.lower())] = \
                            "Insufficant Storage"
                        notenough = True
                if notenough:
                    continue

                for vapp in data[org]['vdcs'][vdc]['vapps']:
                    # Skip if VAPP already exists
                    if vapp in org_details['vdcs'][vdc]['vapps'].keys():
                        post["%s - %s" % (vdc.lower(), vapp.lower())] = \
                            "VAPP Already exists"
                        continue
                    vappdata = data[org]['vdcs'][vdc]['vapps'][vapp]
                    composevapp = Element('ComposeVAppParams')
                    composevapp.set('name', vapp)
                    composevapp.set('xmlns',
                                    'http://www.vmware.com/vcloud/v1.5')
                    composevapp.set('xmlns:ovf',
                                    'http://schemas.dmtf.org/ovf/envelope/1')

                    vappdescription = SubElement(composevapp, 'Description')
                    vappdescription.text = vappdata['Description']
                    composevapp.extend(vappdescription)

                    vappinstantiate = SubElement(composevapp,
                                                 'InstantiationParams')

                    vappnetconfsec = SubElement(vappinstantiate,
                                                'NetworkConfigSection')
                    ovfinfo = SubElement(vappnetconfsec, 'ovf:Info')
                    ovfinfo.text = "Configuration parameters for "\
                                   "logical networks"

                    # Check Network exists
                    if "availablenetworks" in org_details['vdcs'][vdc].keys():
                        vappnetcon = SubElement(vappnetconfsec,
                                                'NetworkConfig')
                        vappnetcon.set('networkName', vappdata['Network'])
                        networkhref = org_details['vdcs'][vdc][
                            'availablenetworks'][vappdata['Network']]['href']

                        configuration = SubElement(vappnetcon,
                                                   'Configuration')
                        parentnetwork = SubElement(configuration,
                                                   'ParentNetwork')
                        parentnetwork.set('href', networkhref)
                        fencemode = SubElement(configuration, 'FenceMode')
                        fencemode.text = 'bridged'
                        isdeployed = SubElement(vappnetcon, 'IsDeployed')
                        isdeployed.text = "True"
                    else:
                        post["%s - %s" % (vdc.lower(), vapp.lower())] =\
                            "No Network Found"

                    for vm in data[org]['vdcs'][vdc]['vapps'][vapp]['vms']:
                        # Map vm data to easier variable
                        vmdata = data[org]['vdcs'][vdc][
                            'vapps'][vapp]['vms'][vm]

                        # check template catalog for this Organisation
                        if vmdata['Catalog'] not in  \
                                org_details['catalogs'].keys():
                            post["%s - %s" % (vmdata['Catalog'].lower(),
                                              vm.lower())] =\
                                              "Catalog does not exist"
                            continue

                        # Check vapp template exists for this Organisation
                        if vmdata['Template'] not in org_details['catalogs'][
                                vmdata['Catalog']]['templates'].keys():
                            post["%s - %s" % (vmdata['Template'].lower(),
                                              vm.lower())] = \
                                              "Template does not exist"
                            continue

                        # Check VM template exist for Organisation
                        if vmdata['Templatevm'] in org_details['catalogs'][
                                vmdata['Catalog']]['templates'][
                                vmdata['Template']]['vms'].keys():
                            vmref = org_details['catalogs'][vmdata['Catalog']][
                                'templates'][vmdata['Template']]['vms'][
                                vmdata['Templatevm']]['href']
                        else:
                            post["%s - %s" % (vmdata['Templatevm'].lower(),
                                              vm.lower())] = \
                                              "VM does not exist"
                            continue

                        vmsourceditem = SubElement(composevapp, 'SourcedItem')
                        vmsource = SubElement(vmsourceditem, 'Source')
                        vmsource.set('href', vmref)

                        vmgeneralparams = SubElement(vmsourceditem,
                                                     'VmGeneralParams')
                        vmsourceditem.extend(vmgeneralparams)

                        vmname = SubElement(vmgeneralparams, 'Name')
                        vmname.text = vm

                        vmdescription = SubElement(vmgeneralparams,
                                                   'Description')
                        vmdescription.text = vmdata['Description']

                        vmneedcust = SubElement(vmgeneralparams,
                                                'NeedsCustomization')
                        vmneedcust.text = "true"

                        vminstantiateparams = SubElement(vmsourceditem,
                                                         'InstantiationParams')

                        # GUEST OS CUSTOMIZATION
                        vmguestcust = SubElement(vminstantiateparams,
                                                 'GuestCustomizationSection')
                        vmguestcust.set('xmlns',
                                        'http://www.vmware.'
                                        'com/vcloud/v1.5')
                        vmguestcust.set('xmlns:ovf',
                                        'http://schemas.dmtf.org/'
                                        'ovf/envelope/1')
                        vmguestcust.set('ovf:required', 'false')

                        vmguestcustinfo = SubElement(vmguestcust, 'ovf:Info')
                        vmguestcustinfo.text = "Guest OS Customization"

                        vmguestcustenable = SubElement(vmguestcust, 'Enabled')
                        vmguestcustenable.text = "True"

                        vmguestcustsid = SubElement(vmguestcust, 'ChangeSid')
                        vmguestcustsid.text = "True"

                        vmcompname = SubElement(vmguestcust, 'ComputerName')
                        vmcompname.text = vmdata['Hostname']

                        # NETWORK ADAPTER CUSTOMIZATION
                        vmnetconsec = SubElement(vminstantiateparams,
                                                 'NetworkConnectionSection')
                        vmnetconsec.set('xmlns',
                                        'http://www.vmware.com/vcloud/v1.5')
                        vmnetconsec.set('xmlns:ovf',
                                        'http://schemas.dmtf.org/'
                                        'ovf/envelope/1')
                        vmnetconsec.set('type',
                                        'application/vnd.vmware.vcloud.'
                                        'networkConnectionSection+xml')
                        vmnetconsec.set('href',
                                        vmref + '/networkConnectionSection/')
                        vmnetconsec.set('ovf:required', 'false')

                        # vmnetconsecinfo = SubElement(vmnetconsec, 'ovf:Info')

                        vmnetconindex = SubElement(vmnetconsec,
                                                   'PrimaryNetworkConn'
                                                   'ectionIndex')
                        vmnetconindex.text = str(0)

                        vmnetcon = SubElement(vmnetconsec,
                                              'NetworkConnection')
                        vmnetcon.set('network', vmdata['Network']['Name'])

                        vmnetindx = SubElement(vmnetcon,
                                               'NetworkConnectionIndex')
                        vmnetindx.text = str(0)

                        # SET IP if provided otherwise set to DHCP
                        if "IP" in vmdata['Network'].keys():
                            vmnetip = SubElement(vmnetcon, 'IpAddress')
                            vmnetip.text = vmdata['Network']['IP']

                            vmnetisconnected = SubElement(vmnetcon,
                                                          'IsConnected')
                            vmnetisconnected.text = "True"

                            vmnetipmode = SubElement(vmnetcon,
                                                     'IpAddressAllocationMode')
                            vmnetipmode.text = "MANUAL"
                        else:
                            vmnetisconnected = SubElement(vmnetcon,
                                                          'IsConnected')
                            vmnetisconnected.text = "True"

                            vmnetipmode = SubElement(vmnetcon,
                                                     'IpAddressAllocationMode')
                            vmnetipmode.text = "DHCP"

                        # Setup Hardware customisation section
                        vmhardwaresection = SubElement(vminstantiateparams,
                                                       'ovf:VirtualHardware'
                                                       'Section')
                        vmhardwaresection.set('xmlns:ovf',
                                              'http://schemas.dmtf.org/'
                                              'ovf/envelope/1')
                        vmhardwaresection.set('xmlns:rasd',
                                              'http://schemas.dmtf.org/wbem/w'
                                              'scim/1/cim-schema/2/CIM_Resourc'
                                              'eAllocationSettingData')
                        vmhardwaresection.set('xmlns:vmw',
                                              'http://www.vmware.'
                                              'com/schema/ovf')
                        vmhardwaresection.set('xmlns:vcloud',
                                              'http://www.vmware.'
                                              'com/vcloud/v1.5')
                        vmhardwaresection.set('vcloud:href',
                                              vmref +
                                              '/virtualHardwareSection/')
                        vmhardwaresection.set('vcloud:type',
                                              'application/vnd.vmware.vcloud.'
                                              'virtualHardwareSection+xml')

                        vmhwinfo = SubElement(vmhardwaresection,
                                              'ovf:Info')
                        vmhwinfo.text = "Hardware Requirements"

                        # Build CPU customisation
                        setcpu = SubElement(vmhardwaresection,
                                            'ovf:Item')
                        cpuallocationunits = SubElement(setcpu,
                                                        'rasd:AllocationUnits')
                        cpuallocationunits.text = "hertz * 10^6"

                        cpudescription = SubElement(setcpu,
                                                    'rasd:Description')
                        cpudescription.text = "Number of Virtual CPUs"

                        cpuelementname = SubElement(setcpu,
                                                    'rasd:ElementName')
                        cpuelementname.text = "1 Virtual CPU(s)"

                        cpuinstanceid = SubElement(setcpu,
                                                   'rasd:InstanceID')
                        cpuinstanceid.text = str(40)

                        cpureservation = SubElement(setcpu,
                                                    'rasd:Reservation')
                        cpureservation.text = str(0)

                        cpuresourcetype = SubElement(setcpu,
                                                     'rasd:ResourceType')
                        cpuresourcetype.text = str(3)

                        cpuvirtualquantity = SubElement(setcpu,
                                                        'rasd:VirtualQuantity')
                        cpuvirtualquantity.text = str(vmdata['cpu'])

                        cpuweight = SubElement(setcpu, 'rasd:Weight')
                        cpuweight.text = str(0)

                        # Build Memory customisation
                        setmemory = SubElement(vmhardwaresection,
                                               'ovf:Item')
                        memallocationUnits = SubElement(setmemory,
                                                        'rasd:AllocationUnits')
                        memallocationUnits.text = "byte * 2^20"

                        memdescription = SubElement(setmemory,
                                                    'rasd:Description')
                        memdescription.text = "Memory Size"

                        memelementname = SubElement(setmemory,
                                                    'rasd:ElementName')
                        memelementname.text = "1024 MB of memory"

                        meminstanceid = SubElement(setmemory,
                                                   'rasd:InstanceID')
                        meminstanceid.text = str(50)

                        memreservation = SubElement(setmemory,
                                                    'rasd:Reservation')
                        memreservation.text = str(0)

                        memresourcetype = SubElement(setmemory,
                                                     'rasd:ResourceType')
                        memresourcetype.text = str(4)

                        memvirtualquantity = SubElement(setmemory,
                                                        'rasd:VirtualQuantity')
                        memvirtualquantity.text = str(vmdata['memory'] * 1024)

                        memweight = SubElement(setmemory, 'rasd:Weight')
                        memweight.text = str(0)

                    # post to API endpoint
                    post["%s (%s)" % (vm.lower(), vapp.lower())] =\
                        self.vcd_post(endpoint,
                                      composevapp,
                                      contenttype)
        return post
