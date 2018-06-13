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
import copy


class createORG(VCDBaseActions):
    def run(self, vcloud="default", data=None):
        # Define setting section attribute order
        OrgGeneralSettings = ['CanPublishCatalogs',
                              'CanPublishExternally',
                              'CanSubscribe',
                              'DeployedVMQuota',
                              'StoredVmQuota',
                              'UseServerBootSequence',
                              'DelayAfterPowerOnSeconds',
                              'VdcQuota']
        VAppLeaseSettings = ['DeleteOnStorageLeaseExpiration',
                             'DeploymentLeaseSeconds',
                             'StorageLeaseSeconds']
        VAppTemplateLeaseSettings = ['DeleteOnStorageLeaseExpiration',
                                     'StorageLeaseSeconds']
        OrgPasswordPolicySettings = ['AccountLockoutEnabled',
                                     'InvalidLoginsBeforeLockout',
                                     'AccountLockoutIntervalMinutes']
        OrgOperationLimitsSettings = ['ConsolesPerVmLimit',
                                      'OperationsPerUser',
                                      'OperationsPerOrg']

        self.set_connection(vcloud)
        self.get_sessionid()

        post = {}
        contenttype = "application/vnd.vmware.admin.organization+xml; "\
                      "charset=ISO-8859-1"
        endpoint = 'admin/orgs'
        all_orgs = self.get_orgs()
        for org in data:
            settings = {}
            adminorg = Element('AdminOrg')
            adminorg.set('xmlns', 'http://www.vmware.com/vcloud/v1.5')
            adminorg.set('type',
                         'application/vnd.vmware.admin.organization+xml')
            adminorg.set('name', org)

            description = SubElement(adminorg, 'Description')
            description.text = data[org]['Description']
            adminorg.extend(description)

            fullname = SubElement(adminorg, 'FullName')
            fullname.text = data[org]['FullName']
            adminorg.extend(fullname)

            isenabled = SubElement(adminorg, 'IsEnabled')
            isenabled.text = str(data[org]['IsEnabled'])
            adminorg.extend(isenabled)

            settingsxml = SubElement(adminorg, 'Settings')
            adminorg.extend(settingsxml)

            if "org" in self.config['defaults'].keys():
                settings = copy.deepcopy(self.config['defaults']['org'][
                                                     'Settings'])

            if "Settings" in data[org].keys():
                settings = self.merge_dict(settings, data[org]['Settings'])

            if "OrgGeneralSettings" in settings.keys():
                orggeneral = SubElement(settingsxml, 'OrgGeneralSettings')
                settingsxml.extend(orggeneral)
                for item in OrgGeneralSettings:
                    if item in settings['OrgGeneralSettings'].keys():
                        jdata = {item: settings['OrgGeneralSettings'][item]}
                        self.convertjson(orggeneral, jdata)

            if "VAppLeaseSettings" in settings.keys():
                orgvapplease = SubElement(settingsxml, 'VAppLeaseSettings')
                settingsxml.extend(orgvapplease)
                for item in VAppLeaseSettings:
                    if item in settings['VAppLeaseSettings'].keys():
                        jdata = {item: settings['VAppLeaseSettings'][item]}
                        self.convertjson(orgvapplease, jdata)

            if "VAppTemplateLeaseSettings" in settings.keys():
                orgvapptemplatelease = SubElement(settingsxml,
                                                  'VAppTemplateLeaseSettings')
                settingsxml.extend(orgvapptemplatelease)
                for item in VAppTemplateLeaseSettings:
                    if item in settings['VAppTemplateLeaseSettings'].keys():
                        jdata = {item: settings['VAppTemplateLeaseSettings'][
                                                item]}
                        self.convertjson(orgvapptemplatelease, jdata)

            if "OrgPasswordPolicySettings" in settings.keys():
                orgpasswordpolicy = SubElement(settingsxml,
                                               'OrgPasswordPolicySettings')
                settingsxml.extend(orgpasswordpolicy)
                for item in OrgPasswordPolicySettings:
                    if item in settings['OrgPasswordPolicySettings'].keys():
                        jdata = {item: settings['OrgPasswordPolicySettings'][
                                                item]}
                        self.convertjson(orgpasswordpolicy, jdata)

            if "OrgOperationLimitsSettings" in settings.keys():
                orgoperationlimits = SubElement(settingsxml,
                                                'OrgOperationLimitsSettings')
                settingsxml.extend(orgoperationlimits)
                for item in OrgOperationLimitsSettings:
                    if item in settings['OrgOperationLimitsSettings'].keys():
                        jdata = {item: settings['OrgOperationLimitsSettings'][
                                                item]}
                        self.convertjson(orgoperationlimits, jdata)

            if org not in all_orgs.keys():
                post['org-' + org] = self.vcd_post(endpoint, adminorg,
                                                   contenttype)
            else:
                post['org-' + org] = "Org Already Exists"

        return post
