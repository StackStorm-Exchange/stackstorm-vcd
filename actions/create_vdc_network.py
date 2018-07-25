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


class createVDCNetwork(VCDBaseActions):
    def run(self, vcloud="default", data=None):
        contenttype = "application/vnd.vmware.vcloud.orgVdcNetwork+xml"
        self.set_connection(vcloud)
        self.get_sessionid()

        post = {}
        all_orgs = self.get_orgs()
        all_pvdcs = self.get_pvdcs("false")
        for org in data:
            for vdc in data[org]['vdcs']:
                if org not in all_orgs.keys():
                    post["%s" % (org.lower())] = "Org does not exist"
                    continue

                org_details = self.get_org(all_orgs[org]['id'])
                if vdc not in org_details['vdcs'].keys():
                    post["%s (%s)" % (vdc.lower(), org.lower())] =\
                        "VDC does not exist"
                    continue

                endpoint = "admin/vdc/%s/networks" % org_details['vdcs'][
                    vdc]['id']
                pvdc = data[org]['vdcs'][vdc]['PVDC']
                pvdc_details = self.get_pvdc_details(all_pvdcs[pvdc]['id'])

                if 'org_network' not in data[org]['vdcs'][vdc]:
                    post["%s (%s)" % (vdc.lower(), org.lower())] =\
                        "No networks defined"
                    continue

                for network in data[org]['vdcs'][vdc]['org_network']:
                    if network in org_details['vdcs'][vdc][
                            'availablenetworks'].keys():
                        post["%s (%s)" % (network.lower(), vdc.lower())] =\
                            "Network Already Exists"
                        continue

                    netdets = data[org]['vdcs'][vdc]['org_network'][network]
                    orgvdcnetwork = Element('OrgVdcNetwork')
                    orgvdcnetwork.set('xmlns',
                                      'http://www.vmware.com/vcloud/v1.5')
                    orgvdcnetwork.set('name', network)

                    configuration = SubElement(orgvdcnetwork, 'Configuration')
                    orgvdcnetwork.extend(configuration)

                    if netdets['type'] == "bridged":
                        parent = netdets['parent']
                        if parent not in pvdc_details[
                                'external_networks'].keys():
                            post["%s (%s)" % (network.lower(), vdc.lower())] =\
                                "Parent Network Not Found"
                            continue

                        networkref = pvdc_details['external_networks'][
                            parent]['href']
                        networkref = networkref.replace(
                            "extension/externalnet", "network")

                        parentnetwork = SubElement(configuration,
                                                   'ParentNetwork')
                        parentnetwork.set('href', networkref)

                        fencemode = SubElement(configuration, 'FenceMode')
                        fencemode.text = netdets['type']
                    else:
                        post["%s (%s)" % (network.lower(), vdc.lower())] =\
                            "Unsupported Network Type"

                    post["%s (%s)" % (network.lower(), vdc.lower())] =\
                        self.vcd_post(endpoint,
                                      orgvdcnetwork,
                                      contenttype)
        return post
