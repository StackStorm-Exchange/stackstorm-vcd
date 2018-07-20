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


class createORGADMIN(VCDBaseActions):
    def run(self, vcloud="default", data=None):
        self.set_connection(vcloud)
        self.get_sessionid()

        post = {}
        # Added for future use.
        # elementorder = ['FullName', 'EmailAddress', 'Telephone', 'IsEnabled',
        #                 'IsLocked', 'IM', 'NameInSource', 'IsAlertEnabled',
        #                 'AlertEmailPrefix', 'AlertEmail', 'IsExternal',
        #                 'ProviderType', 'IsDefaultCached', 'IsGroupRole',
        #                 'StoredVmQuota', 'DeployedVmQuota', 'Password']
        all_orgs = self.get_orgs()
        roleid = self.get_roleid('Organization Administrator')
        contenttype = "application/vnd.vmware.admin.user+xml; "\
                      "charset=ISO-8859-1"
        for org in data:
            orgid = all_orgs[org]['id']
            endpoint = 'admin/org/%s/users' % orgid
            org_details = self.get_org(orgid)
            for user in data[org]['org_admin']:
                if org in all_orgs.keys():
                    endpoint = "admin/org/%s/users" % all_orgs[org]['id']
                    orgadmin = Element('User')
                    orgadmin.set('xmlns', 'http://www.vmware.com/vcloud/v1.5')
                    orgadmin.set('name', user)

                    fullname = SubElement(orgadmin, 'FullName')
                    fullname.text = data[org]['org_admin'][user]['FullName']
                    orgadmin.extend(fullname)

                    isenabled = SubElement(orgadmin, 'IsEnabled')
                    isenabled.text = "true"
                    orgadmin.extend(isenabled)

                    role = SubElement(orgadmin, 'Role')
                    role.set('href', "https://%s/api/admin/role/%s" % (
                             self.vcd_host, roleid))

                    password = SubElement(orgadmin, 'Password')
                    password.text = str(data[org]['org_admin'][
                        user]['Password'])
                    orgadmin.extend(password)

                    groupreferences = SubElement(orgadmin, 'GroupReferences')
                    orgadmin.extend(groupreferences)

                    if user in org_details['users'].keys():
                        post[org + ' - ' + user] = "User exists"
                    else:
                        post[org + ' - ' + user] = self.vcd_post(endpoint,
                                                                 orgadmin,
                                                                 contenttype)
                else:
                    post['%s-%s' % (org, user)] = "Org does not exist"

        return post
