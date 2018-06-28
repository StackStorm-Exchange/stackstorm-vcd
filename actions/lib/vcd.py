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

import requests
import xmltodict

import collections
import re
from st2actions.runners.pythonrunner import Action
from xml.etree.ElementTree import SubElement, tostring


class VCDBaseActions(Action):

    def __init__(self, config):
        super(VCDBaseActions, self).__init__(config)
        if config is None:
            raise ValueError("No Configuration details found")

        if "vcloud" in config:
            if config['vcloud'] is None:
                raise ValueError("'vcloud' config defined by empty")
            else:
                pass
        else:
            raise ValueError("No Connection configuration details found")

    def set_connection(self, vcloud=None):
        if vcloud is None:
            vcloud = "default"

        self.vcd_host = self.config['vcloud'][vcloud]['host']
        self.vcd_user = self.config['vcloud'][vcloud]['user']
        self.vcd_pass = self.config['vcloud'][vcloud]['passwd']
        if "ssl_verify" in self.config['vcloud'][vcloud].keys():
            self.vcd_ssl = self.config['vcloud'][vcloud]['ssl_verify']
        else:
            self.vcd_ssl = True

    def get_sessionid(self):
        url = 'https://%s/api/sessions' % self.vcd_host
        headers = {'Accept': 'application/*+xml;version=5.1'}
        p = requests.post(url, headers=headers, auth=(self.vcd_user +
                          "@SYSTEM", self.vcd_pass), verify=self.vcd_ssl)
        self.vcd_auth = p.headers['x-vcloud-authorization']

        return self.vcd_auth

    def get_pvdc_details(self, pvdc_ref):
        pvdc_data = {}
        pvdc_data['external_networks'] = {}
        pvdc_data['compute_capacity'] = {}
        pvdc_data['compute_capacity']['cpu'] = {}
        pvdc_data['compute_capacity']['memory'] = {}
        pvdc_data['network_pools'] = {}
        pvdc_data['storage_profiles'] = {}
        pvdc_data['vcenter'] = {}
        pvdc_data['hosts'] = {}

        endpoint = 'admin/extension/providervdc/%s' % (pvdc_ref)
        jdata = self.vcd_get(endpoint)

        pvdc_data['id'] = jdata['vmext:VMWProviderVdc']['@id'].split(
                                'providervdc:', 1)[-1]
        pvdc_data['enabled'] = jdata['vmext:VMWProviderVdc'][
                                     'vcloud:IsEnabled']
        pvdc_data['href'] = jdata['vmext:VMWProviderVdc']['@href']

        try:
            networks = []
            if isinstance(jdata['vmext:VMWProviderVdc'][
                    'vcloud:AvailableNetworks'][
                    'vcloud:Network'], list):
                networks = jdata['vmext:VMWProviderVdc'][
                    'vcloud:AvailableNetworks'][
                    'vcloud:Network']
            else:
                networks.append(jdata['vmext:VMWProviderVdc'][
                    'vcloud:AvailableNetworks'][
                    'vcloud:Network'])
            for item in networks:
                pvdc_data['external_networks'][item['@name']] = {}
                pvdc_data['external_networks'][item['@name']][
                    'href'] = item['@href']
                pvdc_data['external_networks'][item['@name']]['id'] = \
                    item['@href'].split('externalnet/', 1)[-1]
        except Exception:
            pass

        try:
            for item in jdata['vmext:VMWProviderVdc'][
                    'vcloud:ComputeCapacity'][
                    'vcloud:Cpu']:
                pvdc_data['compute_capacity']['cpu'][str(item).split(
                    'vcloud:', 1)[-1]] = jdata['vmext:VMWProviderVdc'][
                    'vcloud:ComputeCapacity']['vcloud:Cpu'][item]
        except Exception:
            pass

        try:
            for item in jdata['vmext:VMWProviderVdc'][
                    'vcloud:ComputeCapacity'][
                    'vcloud:Memory']:
                pvdc_data['compute_capacity']['memory'][str(item).split(
                    'vcloud:', 1)[-1]] = jdata['vmext:VMWProviderVdc'][
                    'vcloud:ComputeCapacity']['vcloud:Memory'][item]
        except Exception:
            pass

        try:
            storageprofiles = []
            if isinstance(jdata['vmext:VMWProviderVdc'][
                    'vcloud:StorageProfiles'][
                    'vcloud:ProviderVdcStorageProfile'], list):
                storageprofiles = jdata['vmext:VMWProviderVdc'][
                    'vcloud:StorageProfiles'][
                    'vcloud:ProviderVdcStorageProfile']
            else:
                storageprofiles.append(jdata['vmext:VMWProviderVdc'][
                    'vcloud:StorageProfiles'][
                    'vcloud:ProviderVdcStorageProfile'])
            for item in storageprofiles:
                pvdc_data['storage_profiles'][item['@name']] = {}
                pvdc_data['storage_profiles'][item['@name']][
                    'href'] = item['@href']
                pvdc_data['storage_profiles'][item['@name']]['id'] = \
                    item['@href'].split('pvdcStorageProfile/', 1)[-1]
        except Exception:
            pass

        try:
            for item in jdata['vmext:VMWProviderVdc']['vmext:HostReferences'][
                    'vmext:HostReference']:
                pvdc_data['hosts'][item['@name']] = {}
                pvdc_data['hosts'][item['@name']]['id'] = \
                    item['@href'].split('host/', 1)[-1]
        except Exception:
            pass

        if jdata['vmext:VMWProviderVdc']['vcloud:NetworkPoolReferences']\
                is not None:
            if isinstance(jdata['vmext:VMWProviderVdc'][
                    'vcloud:NetworkPoolReferences'][
                    'vcloud:NetworkPoolReference'], list):
                for item in jdata['vmext:VMWProviderVdc'][
                        'vcloud:NetworkPoolReferences'][
                        'vcloud:NetworkPoolReference']:
                    pvdc_data['network_pools'][item['@name']] = {}
                    pvdc_data['network_pools'][item['@name']][
                        'href'] = item['@href']
                    pvdc_data['network_pools'][item['@name']]['id'] = \
                        item['@href'].split('networkPool/', 1)[-1]
            else:
                name = jdata['vmext:VMWProviderVdc'][
                    'vcloud:NetworkPoolReferences'][
                    'vcloud:NetworkPoolReference']['@name']
                nid = jdata['vmext:VMWProviderVdc'][
                    'vcloud:NetworkPoolReferences'][
                    'vcloud:NetworkPoolReference'][
                    '@href'].split('networkPool/', 1)[-1]
                href = jdata['vmext:VMWProviderVdc'][
                    'vcloud:NetworkPoolReferences'][
                    'vcloud:NetworkPoolReference'][
                    '@href']
                pvdc_data['network_pools'][name] = {}
                pvdc_data['network_pools'][name]['href'] = href
                pvdc_data['network_pools'][name]['id'] = nid

        vname = jdata['vmext:VMWProviderVdc'][
            'vmext:VimServer']['@name']
        vhref = jdata['vmext:VMWProviderVdc'][
            'vmext:VimServer']['@href']
        vid = vhref.split('vimServer/', 1)[-1]

        pvdc_data['vcenter'][vname] = {}
        pvdc_data['vcenter'][vname]['href'] = vhref
        pvdc_data['vcenter'][vname]['id'] = vid
        pvdc_data['vcenter'][vname]['vsnetworks'] = self.get_vsnetworks(vid)

        return pvdc_data

    def get_pvdcs(self):
        endpoint = 'admin/extension/providerVdcReferences'
        self.pvdcs = {}
        jdata = self.vcd_get(endpoint)
        jpvdcs = {}
        if isinstance(jdata['vmext:VMWProviderVdcReferences'][
                            'vmext:ProviderVdcReference'], list):
            for pvdc in jdata['vmext:VMWProviderVdcReferences'][
                    'vmext:ProviderVdcReference']:
                jpvdcs[pvdc['@name']] = self.get_pvdc_details(
                    pvdc['@href'].split('providervdc/', 1)[-1])
            self.pvdcs = jpvdcs
        else:
            name = jdata['vmext:VMWProviderVdcReferences'][
                    'vmext:ProviderVdcReference']['@name']
            ref = jdata['vmext:VMWProviderVdcReferences'][
                    'vmext:ProviderVdcReference']['@href'].split(
                    'providervdc/', 1)[-1]
            self.pvdcs[name] = self.get_pvdc_details(ref)

        return self.pvdcs

    def get_storage_profiles(self, pvdc):
        storage_profiles = {}
        endpoint = 'query?type=providerVdcStorageProfile&format=references&'\
                   'filter=providerVdc==https://%s/api/admin/providervdc/%s'\
                   % (self.vcd_host, self.pvdcs[pvdc]['id'])
        jdata = self.vcd_get(endpoint)

        for storage_profile in jdata['ProviderVdcStorageProfileReferences'][
                'ProviderVdcStorageProfileReference']:
            storage_profiles[storage_profile['@name']] = {}
            storage_profiles[storage_profile['@name']]['id'] =\
                storage_profile['@id']
            storage_profiles[storage_profile['@name']]['href'] =\
                storage_profile['@href']

        return storage_profiles

    def get_network_pools(self):
        network_pools = {}
        endpoint = "admin/extension/networkPoolReferences"
        jdata = self.vcd_get(endpoint)

        for network in jdata['vmext:VMWNetworkPoolReferences'][
                             'vmext:NetworkPoolReference']:
            network_pools[network['@name']] = {}
            network_pools[network['@name']]['href'] = network['@href']

        return network_pools

    def get_orgs(self):
        orgs = {}
        endpoint = "org"
        jdata = self.vcd_get(endpoint)
        for item in jdata['OrgList']['Org']:
            orgs[item['@name']] = {}
            orgs[item['@name']]['id'] = item['@href'].split('org/', 1)[-1]
        return orgs

    def get_org(self, org_ref=None):
        org = {}
        org['vdcs'] = {}
        org['users'] = {}
        endpoint = "admin/org/%s" % org_ref
        jdata = self.vcd_get(endpoint)
        org['desc'] = jdata['AdminOrg']['Description']
        org['fullname'] = jdata['AdminOrg']['FullName']
        org['id'] = jdata['AdminOrg']['@id'].split('org:', 1)[-1]

        if jdata['AdminOrg']['Vdcs']:
            for item in jdata['AdminOrg']['Vdcs']['Vdc']:
                if isinstance(item, dict):
                    if "@name" in item.keys():
                        vdcid = item['@href'].split('vdc/', 1)[-1]
                        org['vdcs'][item['@name']] = self.get_vdc(vdcid)

        if "Users" in jdata['AdminOrg'].keys():
            if jdata['AdminOrg']['Users'] is not None:
                if isinstance(jdata['AdminOrg']['Users'][
                        'UserReference'], list):
                    for item in jdata['AdminOrg']['Users']['UserReference']:
                        org['users'][item['@name']] = {}
                        org['users'][item['@name']]['id'] =\
                            item['@href'].split('user/', 1)[-1]
                else:
                    name = jdata['AdminOrg']['Users']['UserReference']['@name']
                    nameid = jdata['AdminOrg']['Users']['UserReference'][
                                   '@href'].split('user/', 1)[-1]
                    org['users'][name] = {}
                    org['users'][name]['id'] = nameid

        return org

    def get_vdc(self, vdc_ref=None):
        vdc = {}
        endpoint = 'admin/vdc/%s' % vdc_ref
        jdata = self.vcd_get(endpoint)
        vdc['name'] = jdata['AdminVdc']['@name']
        vdc['href'] = jdata['AdminVdc']['@href']
        vdc['id'] = jdata['AdminVdc']['@href'].split('vdc/', 1)[-1]
        vdc['AllocationModel'] = jdata['AdminVdc']['AllocationModel']
        vdc['VmQuota'] = jdata['AdminVdc']['VmQuota']

        vdc['vapps'] = {}
        vdc['media'] = {}
        vdc['templates'] = {}

        try:
            if isinstance(jdata['AdminVdc']['ResourceEntities'][
                    'ResourceEntity'], list):
                vdcres = jdata['AdminVdc']['ResourceEntities'][
                               'ResourceEntity']
            else:
                vdcres = []
                vdcres.append(jdata['AdminVdc']['ResourceEntities'][
                    'ResourceEntity'])
            for item in vdcres:
                if "api/media/" in item['@href']:
                    vdc['media'][item['@name']] = {}
                    vdc['media'][item['@name']]['id'] = item[
                        '@href'].split('media/', 1)[-1]
                    vdc['media'][item['@name']]['href'] = item['@href']
                elif "api/vApp/" in item['@href']:
                    vdc['vapps'][item['@name']] = self.get_vapp(
                        item['@href'].split('vapp-', 1)[-1])
                elif "api/vAppTemplate/" in item['@href']:
                    vdc['templates'][item['@name']] = {}
                    vdc['templates'][item['@name']]['id'] = item[
                        '@href'].split('vappTemplate-', 1)[-1]
                    vdc['templates'][item['@name']]['href'] = item['@href']
        except Exception:
            pass

        return vdc

    def get_vapp(self, vapp_id):
        vapp = {}
        endpoint = 'vApp/vapp-%s' % vapp_id
        jdata = self.vcd_get(endpoint)

        vapp['name'] = jdata['VApp']['@name']
        vapp['description'] = jdata['VApp']['Description']
        vapp['href'] = jdata['VApp']['@href']
        vapp['id'] = jdata['VApp']['@id']

        vms = []
        vapp['vms'] = {}
        hwitems = ['rasd:Description',
                   'rasd:ResourceSubType',
                   'rasd:VirtualQuantity',
                   'rasd:VirtualQuantityUnits',
                   'rasd:ResourceType']
        if isinstance(jdata['VApp']['Children']['Vm'], list):
            vms = jdata['VApp']['Children']['Vm']
        else:
            vms.append(jdata['VApp']['Children']['Vm'])
        for item in vms:
            vapp['vms'][item['@name']] = {}
            vapp['vms'][item['@name']]['id'] = item['@id'].split(
                'vcloud:vm:', 1)[-1]
            vapp['vms'][item['@name']]['href'] = item['@href']
            vapp['vms'][item['@name']]['spec'] = {}

            for hw in item['ovf:VirtualHardwareSection']['ovf:Item']:
                if "rasd:ElementName" in hw.keys():
                    vapp['vms'][item['@name']]['spec'][hw[
                        'rasd:ElementName']] = {}
                    for hwitem in hwitems:
                        if hwitem in hw.keys():
                            vapp['vms'][item['@name']]['spec'][hw[
                                 'rasd:ElementName']][hwitem.split(
                                     'rasd:', 1)[-1]] = hw[hwitem]
                            if "rasd:Connection" in hw.keys():
                                if "@vcloud:ipAddress" in hw[
                                        'rasd:Connection'].keys():
                                    vapp['vms'][item['@name']]['spec'][hw[
                                        'rasd:ElementName']]['ip'] = hw[
                                        'rasd:Connection'][
                                        '@vcloud:ipAddress']

        return vapp

    def get_users(self):
        users = {}
        endpoint = "admin/users/query"
        jdata = self.vcd_get(endpoint)
        for item in jdata['QueryResultRecords']['UserRecord']:
            users[item['@name']] = {}
            users[item['@name']]['id'] = item['@href'].split('org/', 1)[-1]
        return users

    def get_extnet(self):
        extnet = {}
        networks = []
        endpoint = "admin/extension/externalNetworkReferences"
        jdata = self.vcd_get(endpoint)
        if isinstance(jdata['vmext:VMWExternalNetworkReferences'][
                            'vmext:ExternalNetworkReference'], list):
            networks = jdata['vmext:VMWExternalNetworkReferences'][
                             'vmext:ExternalNetworkReference']
        else:
            networks.append(jdata['vmext:VMWExternalNetworkReferences'][
                                  'vmext:ExternalNetworkReference'])

        for item in networks:
            enhref = item['@href']
            enid = enhref.split('externalnet/', 1)[-1]
            extnet[item['@name']] = self.get_extnet_details(enid)

        return extnet

    def get_extnet_details(self, netid):
        network = {}
        endpoint = 'admin/extension/externalnet/%s' % netid
        jdata = self.vcd_get(endpoint)
        data = jdata['vmext:VMWExternalNetwork']
        network['description'] = data['vcloud:Description']
        network['id'] = data['@id']
        network['href'] = data['@href']
        config = data['vcloud:Configuration']
        network['configuration'] = {}
        network['configuration']['IPRanges'] = []

        config_items = ['IsInherited',
                        'Gateway',
                        'Netmask',
                        'Dns1',
                        'Dns2',
                        'IsEnabled']
        config_set = config['vcloud:IpScopes']['vcloud:IpScope']
        for item in config_items:
            network['configuration'][item] = config_set['vcloud:' + item]

        ipranges = []
        if isinstance(config_set['vcloud:IpRanges']['vcloud:IpRange'], list):
            ipranges = config_set['vcloud:IpRanges']['vcloud:IpRange']
        else:
            ipranges.extend(config_set['vcloud:IpRanges']['vcloud:IpRange'])
        for iprange in ipranges:
            ip = str(iprange['vcloud:StartAddress'] + '-' + iprange[
                'vcloud:EndAddress'])
            network['configuration']['IPRanges'].append(ip)

        return network

    def get_vsphere(self):
        vsphere = {}
        servers = []
        endpoint = 'admin/extension/vimServerReferences'
        jdata = self.vcd_get(endpoint)
        if isinstance(jdata['vmext:VMWVimServerReferences'][
                'vmext:VimServerReference'], list):
            servers = jdata['vmext:VMWVimServerReferences'][
                            'vmext:VimServerReference']
        else:
            servers.append(jdata['vmext:VMWVimServerReferences'][
                                 'vmext:VimServerReference'])
        for server in servers:
            vsphere[server['@name']] = {}
            vsphere[server['@name']]['href'] = server['@href']
            vsphere[server['@name']]['id'] = server['@href'].split(
                'vimServer/', 1)[-1]
            vsphere[server['@name']]['vsnetworks'] = self.get_vsnetworks(
                vsphere[server['@name']]['id'])
        return vsphere

    def get_vsnetworks(self, vsid):
        networks = {}
        endpoint = 'admin/extension/vimServer/%s/networks' % vsid
        jdata = self.vcd_get(endpoint)
        for dvgroup in jdata['vmext:VimObjectRefList'][
                             'vmext:VimObjectRefs'][
                             'vmext:VimObjectRef']:
            if dvgroup['vmext:VimObjectType'] == "DV_PORTGROUP":
                portgroups = self.get_dvportgroup(dvgroup['vmext:MoRef'], vsid)
                for network in portgroups:
                    networks[network] = {}
                    networks[network] = portgroups[network]
        return networks

    def get_dvportgroup(self, moref, vsid):
        portgroup = {}
        data = []
        endpoint = 'query?type=portgroup&format=records&filter=(moref==%s)'\
            % (moref)
        jdata = self.vcd_get(endpoint)
        results = jdata['QueryResultRecords']['PortgroupRecord']
        if isinstance(results, list):
            data = results
        else:
            data.append(results)
        for result in data:
            if result['@vc'].endswith(vsid):
                portgroup[result['@name']] = {}
                portgroup[result['@name']]['moref'] = result['@moref']
                portgroup[result['@name']]['type'] = result['@portgroupType']

        return portgroup

    def get_roleid(self, role):
        endpoint = 'admin/roles/query'
        roleid = ""
        jdata = self.vcd_get(endpoint)
        jdata = jdata['QueryResultRecords']['RoleRecord']
        for item in jdata:
            for element in item:
                if item[element] == role:
                    roleid = item['@href'].split('role/', 1)[-1]

        return roleid

    def merge_dict(self, d1, d2):
        for k, v2 in d2.items():
            v1 = d1.get(k)
            if (isinstance(v1, collections.Mapping) and
                    isinstance(v2, collections.Mapping)):
                self.merge_dict(v1, v2)
            else:
                d1[k] = v2
        return d1

    def vcd_get(self, endpoint):
        url = 'https://%s/api/%s' % (self.vcd_host, endpoint)
        headers = {'Accept': 'application/*+xml;version=5.1',
                   'x-vcloud-authorization': self.vcd_auth}
        p = requests.get(url, headers=headers, verify=self.vcd_ssl)
        return xmltodict.parse(p.text)

    def vcd_post(self, endpoint, xml, contenttype):
        url = 'https://%s/api/%s' % (self.vcd_host, endpoint)
        headers = {'Accept': 'application/*+xml;version=20.0',
                   'x-vcloud-authorization': self.vcd_auth,
                   'Content-Type': contenttype,
                   # 'Content-Length': str(len(xml))}
                   'Content-Length': str(len(tostring(xml)))}
        payload = tostring(xml)
        # payload = xml
        payload = '<?xml version="1.0" encoding="UTF-8"?>' + payload
        payload = payload.replace(">True<", ">true<")
        payload = payload.replace(">False<", ">false<")
        try:
            p = requests.post(url, headers=headers,
                              data=payload, verify=self.vcd_ssl)
        except requests.exceptions.HTTPError as e:
            raise Exception("Error: %s" % e)

        return xmltodict.parse(p.text)

    def convertjson(self, parent, jdata):
        for item in jdata:
            xmlitem = SubElement(parent, item)
            if isinstance(jdata[item], dict):
                self.convertjson(xmlitem, jdata[item])
            else:
                xmlitem.text = str(jdata[item])
                parent.extend(xmlitem)
        return parent

    def check_ip(self, address):
        result = False
        ipreg = re.compile('^((25[0-5]|2[0-4][0-9]|[01]?[0-9]'
                           '[0-9]?)\.){3}(25[0-5]|2[0-4][0-9]'
                           '|[01]?[0-9][0-9]?)$')
        if ipreg.match(address):
            result = True
        return result
