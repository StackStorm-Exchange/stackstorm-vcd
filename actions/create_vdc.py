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
from xml.etree.ElementTree import Element, SubElement, tostring
import copy


class createVDC(VCDBaseActions):
    def run(self, vcloud="default", data=None):
        self.set_connection(vcloud)
        self.get_sessionid()
        compute = ['Cpu',
                   'Memory']
        computeorder = ['Units',
                        'Allocated',
                        'Limit',
                        'Reserved',
                        'Users',
                        'Overhead']

        cpu_order = []
        mem_order = []
        post = {}
        endpoint = 'admin/orgs'
        all_orgs = self.get_orgs()
        all_pvdcs = self.get_pvdcs()
        for org in data:
            for vdc in data[org]['vdcs']:
                if org not in all_orgs.keys():
                    post["%s-%s" % (org, vdc)] = "Org Does not exist"
                    continue
                endpoint = "admin/org/%s/vdcsparams" % all_orgs[org]['id']
                createvdcparams = Element('CreateVdcParams')
                createvdcparams.set('xmlns', 'http://www.vmware.'
                                             'com/vcloud/v1.5')
                createvdcparams.set('name', vdc)

                description = SubElement(createvdcparams, 'Description')
                description.text = data[org]['vdcs'][vdc]['Description']
                createvdcparams.extend(description)

                computecapacity = SubElement(createvdcparams,
                                             'ComputeCapacity')
                createvdcparams.extend(computecapacity)

                cpucapacity = SubElement(computecapacity, 'Cpu')
                computecapacity.extend(cpucapacity)

                memorycapacity = SubElement(computecapacity, 'Memory')
                computecapacity.extend(memorycapacity)

                vdcsettings = copy.deepcopy(self.config['defaults']['vdc'])
                vdcsettings = self.merge_dict(vdcsettings, data[org][
                                                                'vdcs'][vdc])

                if vdcsettings['AllocationModel'] not in ("AllocationPool",
                                                          "ReservationPool"):
                    post["%s-%s" % (org, vdc)] = "Invalid Allocation Model"
                    continue
                else:
                    if vdcsettings['AllocationModel'] == "ReservationPool":
                        vdcsettings['ComputeCapacity']['Cpu'][
                                    'Allocatedpercent'] = 100
                        vdcsettings['ComputeCapacity']['Memory'][
                                    'Allocatedpercent'] = 100

                # ComputeCapacity
                if "ComputeCapacity" in vdcsettings.keys():
                    cpulimit = vdcsettings['ComputeCapacity'][
                                           'Cpu']['Limit']
                    cpupercent = vdcsettings['ComputeCapacity'][
                                             'Cpu']['Allocatedpercent']
                    cpuallocated = int(round(float(
                                       cpulimit) / 100 * cpupercent))
                    vdcsettings['ComputeCapacity']['Cpu'][
                                'Allocated'] = cpuallocated

                    memlimit = vdcsettings['ComputeCapacity'][
                                           'Memory']['Limit']
                    mempercent = vdcsettings['ComputeCapacity'][
                                             'Memory']['Allocatedpercent']
                    memallocated = int(round(float(
                                       memlimit) / 100 * mempercent))
                    vdcsettings['ComputeCapacity']['Memory'][
                                'Allocated'] = memallocated

                del vdcsettings['ComputeCapacity']['Cpu'][
                                'Allocatedpercent']
                del vdcsettings['ComputeCapacity']['Memory'][
                                'Allocatedpercent']

                if vdcsettings['ComputeCapacity']['Cpu']:
                    for item in computeorder:
                        if item in vdcsettings['ComputeCapacity'][
                                               'Cpu'].keys():
                            jdata = {item: vdcsettings['ComputeCapacity'][
                                                       'Cpu'][item]}
                            self.convertjson(cpucapacity, jdata)

                if vdcsettings['ComputeCapacity']['Memory']:
                    for item in computeorder:
                        if item in vdcsettings['ComputeCapacity'][
                                               'Memory'].keys():
                            jdata = {item: vdcsettings['ComputeCapacity'][
                                                       'Memory'][item]}
                            self.convertjson(memorycapacity, jdata)

                # post['org-' + org] = self.vcd_post(endpoint, createvdcparams)

                if vdcsettings['NetworkQuota']:
                    networkquota = SubElement(createvdcparams, 'NetworkQuota')
                    networkquota.text = str(vdcsettings['NetworkQuota'])
                    createvdcparams.extend(networkquota)

                # Storage Profile code here

                # set IS Thin Provision option
                if "IsThinProvision" in vdcsettings.keys():
                    thinprovision = SubElement(createvdcparams,
                                               'IsThinProvision')
                    thinprovision.text = str(vdcsettings['IsThinProvision'])
                    createvdcparams.extend(thinprovision)
                else:
                    thinprovision = SubElement(createvdcparams,
                                               'IsThinProvision')
                    thinprovision.text = "true"
                    createvdcparams.extend(thinprovision)

                # Provider VDC Reference
                pvdchref = all_pvdcs[data[org]['vdcs'][
                                     vdc]['PVDC']]['href']

                providervdc = SubElement(createvdcparams,
                                         'ProviderVdcReference')
                providervdc.set("href", pvdchref)
                createvdcparams.extend(providervdc)

                # set Fast Provisioning
                if "UsesFastProvisioning" in vdcsettings.keys():
                    fastprovision = SubElement(createvdcparams,
                                               'UsesFastProvisioning')
                    fastprovision.text = str(vdcsettings[
                                             'UsesFastProvisioning'])
                    createvdcparams.extend(fastprovision)
                else:
                    fastprovision = SubElement(createvdcparams,
                                               'UsesFastProvisioning')
                    fastprovision.text = "false"
                    createvdcparams.extend(fastprovision)

                post[org + '-' + vdc] = "Will create VDC"

                print tostring(createvdcparams)
        return post
