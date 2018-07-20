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


class createEXTNetwork(VCDBaseActions):
    def run(self, vcloud="default", data=None):
        self.set_connection(vcloud)
        self.get_sessionid()

        post = {}
        all_vsphere = self.get_vsphere()
        contenttype = "application/vnd.vmware.admin.vmwexternalnet+xml; "\
                      "charset=ISO-8859-1"
        for vsphere in data:
            endpoint = 'admin/extension/externalnets'
            for network in data[vsphere]:
                if network not in all_vsphere[vsphere]['vsnetworks'].keys():
                    post[vsphere + ' - ' + network] = "Network not available"
                    continue
                else:
                    if "name" in data[vsphere][network].keys():
                        name = data[vsphere][network]['name']
                    else:
                        name = "%s|%s" % (network, vsphere)
                    extnet = Element('vmext:VMWExternalNetwork')
                    extnet.set('xmlns:vmext', 'http://www.vmware.com/'
                                              'vcloud/extension/v1.5')
                    extnet.set('xmlns:vcloud', 'http://www.vmware.'
                                               'com/vcloud/v1.5')
                    extnet.set('name', name)
                    extnet.set('type', 'application/vnd.vmware'
                                       '.admin.vmwexternalnet+xml')

                    if "description" in data[vsphere][network].keys():
                        description = SubElement(extnet, 'vcloud:Description')
                        description.text = data[vsphere][network][
                            'description']
                        extnet.extend(description)

                    configuration = SubElement(extnet, 'vcloud:Configuration')
                    extnet.extend(configuration)

                    ipscopes = SubElement(configuration, 'vcloud:IpScopes')
                    configuration.extend(ipscopes)

                    ipscope = SubElement(ipscopes, 'vcloud:IpScope')
                    ipscopes.extend(ipscope)

                    isinherited = SubElement(ipscope, 'vcloud:IsInherited')
                    isinherited.text = "false"

                    gateway = SubElement(ipscope, 'vcloud:Gateway')
                    if self.check_ip(data[vsphere][network]['gateway']):
                        gateway.text = data[vsphere][network]['gateway']
                    else:
                        post[vsphere + ' - ' + network] =\
                            "Invalid Gateway Address"
                        continue
                    ipscope.extend(gateway)

                    netmask = SubElement(ipscope, 'vcloud:Netmask')
                    if self.check_ip(data[vsphere][network]['netmask']):
                        netmask.text = data[vsphere][network]['netmask']
                    else:
                        post[vsphere + ' - ' + network] =\
                            "Invalid Subnet Address"
                        continue
                    ipscope.extend(netmask)

                    dns1 = SubElement(ipscope, 'vcloud:Dns1')
                    if self.check_ip(data[vsphere][network]['dns1']):
                        dns1.text = data[vsphere][network]['dns1']
                    else:
                        post[vsphere + ' - ' + network] =\
                            "Invalid Primary DNS Address"
                        continue
                    ipscope.extend(dns1)

                    dns2 = SubElement(ipscope, 'vcloud:Dns2')
                    if self.check_ip(data[vsphere][network]['dns2']):
                        dns2.text = data[vsphere][network]['dns2']
                    else:
                        post[vsphere + ' - ' + network] =\
                            "Invalid Secondary DNS Address"
                        continue
                    ipscope.extend(dns2)

                    dnssuffix = SubElement(ipscope, 'vcloud:DnsSuffix')
                    if data[vsphere][network]['dnssuffix']:
                        dnssuffix.text = data[vsphere][network]['dnssuffix']
                    ipscope.extend(dnssuffix)

                    ipranges = SubElement(ipscope, 'vcloud:IpRanges')

                    for item in data[vsphere][network]['ip_pools']:
                        startip = item.split('-',)[0]
                        endip = item.split('-', 1)[-1]
                        iprange = SubElement(ipranges, 'vcloud:IpRange')

                        startaddress = SubElement(iprange,
                                                  'vcloud:StartAddress')
                        startaddress.text = startip
                        endaddress = SubElement(iprange, 'vcloud:EndAddress')
                        endaddress.text = endip

                    fencemode = SubElement(configuration,
                                           'vcloud:FenceMode')
                    fencemode.text = "isolated"
                    ipranges.extend(fencemode)

                    vimportgroupref = SubElement(extnet,
                                                 'vmext:VimPortGroupRef')
                    extnet.extend(vimportgroupref)

                    vimserverref = SubElement(vimportgroupref,
                                              'vmext:VimServerRef')
                    vimserverref.set("href", all_vsphere[vsphere]['href'])

                    moref = SubElement(vimportgroupref, 'vmext:MoRef')
                    moref.text = all_vsphere[vsphere]['vsnetworks'][
                        network]['moref']

                    vimobjecttype = SubElement(vimportgroupref,
                                               'vmext:VimObjectType')
                    vimobjecttype.text = all_vsphere[vsphere]['vsnetworks'][
                        network]['type']

                    post[vsphere + ' - ' + network] = self.vcd_post(endpoint,
                                                                    extnet,
                                                                    contenttype
                                                                    )

                    # print tostring(extnet)

        return post
