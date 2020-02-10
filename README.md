# VCloud Director

## Description

Basic actions to integrate with VCloud Director.

## Connection Configuration

Copy the sample configuration file [vcd.yaml.example](./vcd.yaml.example) to `/opt/stackstorm/configs/vcd.yaml`
and edit as required. Required fields for connecting to vcloud are address, user and password.

> Do not use `st2 pack config vcd` as this pack uses complex nested configuration

Run `sudo st2ctl reload --register-configs` to get StackStorm to load the updated configuration.

## Actions
### Get Actions
* `vcd.get_extnet` - Retrieve external networks  
* `vcd.get_org` - Retrieve details for an Organisations 
* `vcd.get_orgs` - Retrieve list of Organisations 
* `vcd.get_pvdcs` - Retrieve list of Provider VDCs 
* `vcd.get_vapp` - Retrieve details for a vApp 
* `vcd.get_vdc` - Retrieve details for a VDC  
* `vcd.get_vsnetworks` - Retrieve VSphere networks  
* `vcd.get_vsphere` - Retrieve VSphere servers  

### Create Actions
#### Org Actions
* `vcd.create_org` - Create an Organisation  
* `vcd.create_org_admin` - Create an Organisation Admin Account 
* `vcd.create_vdc` - Create an VDC  
* `vcd.create_vdc_network` - Create an VDC network. currently only bridge type is supported.
* `vcd.deploy_vapp_template` - Deploy a VAPP and listed VMs from Catalogs
These actions are designed to work from the same input structure. it will use/ignore elements based on the actions function.

Sample Imput:
```
{"TEST":{
    "Description":"Do Robots dream of electric Vcloud Orgs",
    "FullName":"Test Organisation",
    "vdcs":{
        "TEST1":{
            "Storage":{
                "Storage_Profile":"teststorageprofile",
                "Limit":10000
            },
            "ComputeCapacity": {
                "Cpu": {
                    "Limit": 4000
                },
                "Memory": {
                    "Limit": 6000
                }
            },            
            "Description":"Test VDC 1",
            "AllocationModel":"ReservationPool",
            "PVDC":"testpvdc"
        },
        "TEST2":{
            "Storage":{
                "Storage_Profile":"teststorageprofile",
                "Limit":10000,
                "Unit":"MB"
            },
            "ComputeCapacity": {
                "Cpu": {
                    "Allocatedpercent": 40,
                    "Limit": 3000
                }
            },
            "Description":"Test VDC 2",
            "AllocationModel":"AllocationPool",
            "PVDC":"testpvdc",
            "vapps": {
                "vapp1": {
                    "Description": "Test2 - vapp1",
                    "Network": "autonetworkone",
                    "vms": {
                        "vm1":{
                            "powerOn": false,
                            "Hostname": "testmachine1",
                            "Description": "VM Description",
                            "Catalog": "testcatalog",
                            "Template": "CentOS7",
                            "Templatevm": "CentOS7",
                            "Network": {
                                "Name": "autonetworkone",
                                "IP": "127.0.0.20"
                                },
                            "cpu": 2,
                            "memory": 8,
                            "hdd": 60,
                            "Storage_Profile": "teststorageprofile",
                            "Password": "Pa55w0rd?"                            
                        },
                        "vm2":{
                            "powerOn": false,
                            "Hostname": "testmachine2",
                            "Description": "VM Description",
                            "Catalog": "testcatalog",
                            "Template": "Win2016",
                            "Templatevm": "Win2016",
                            "Network": {
                                "Name": "autonetworkone",
                                "IP": "127.0.0.21"
                                },
                            "cpu": 3,
                            "memory": 8,
                            "hdd": 40,
                            "Storage_Profile": "teststorageprofile",
                            "Password": "Pa55w0rd?"                            
                        }
                    }
                }
            },
            "org_network": {
                "autonetworkone": {
                    "type": "bridged",
                    "parent": "vspherenetwork1"
                }
            }
        }
    },
    "IsEnabled":true,
    "org_admin":{
        "TEST.admin1":{
            "FullName":"Admin account 1",
            "Password":"Password1",
            "IsEnabled":true
        },
        "TEST.admin2":{
            "FullName":"Admin account 2",
            "Password":"Password1",
            "IsEnabled":true
        }
    }
}
}
```

The input to the action is pared with the defaults that can be set in the config file. So not all of these options are required on the input.

* 'vcd.create_ext_network' - Create an External Network from VSphere portgroups 
Sample input:
```
{"vsphere1":{
  "vsphere-network1":{
    "name": "new-vsphere-network",
    "description":"test network",
    "dns2":"2.2.2.2",
    "dns1":"1.1.1.1",
    "netmask":"255.255.255.0",
    "ip_pools":["192.168.0.2-192.168.0.5"],
    "dnssuffix":"something.com",
    "gateway":"192.168.0.1"
    }
  }
}
```
Name and description are optional fields. If no Name is provided it will generate name using the "vsphere network name" + "the "vsphere name"
for example: "new-vsphere-network|vsphere1"

## Todo
* Expand `create_vdc_network` to include other network types, not just `bridged`.
* Review `get_orgs` to cope with large number of orgs without timing out. 
* Create deploy Template actions.
** Identify why Windows OS customisation during deploy action doesn't apply although CentOS does.
** Identify why Hardware customisation doesn't apply when deploying different VM templates.
* With the latest ST2 migrate to the Python 3 and the VCloud python module
