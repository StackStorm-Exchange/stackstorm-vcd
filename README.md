# VCloud Director

## Description

Basic actions to integrate with VCloud Director.


## Connection Configuration

Copy the sample configuration file [vcd.yaml.example](./vcd.yaml.example) to `/opt/stackstorm/configs/vcd.yaml`
and edit as required. Required fields for connecting to vcloud are address, user and password.

Run `sudo st2ctl reload --register-configs` to get StackStorm to load the updated configuration.


## Actions
### Get Actions
* 'vcd.get_extnet' - Retrieve external networks  
* 'vcd.get_org' - Retrieve details for an Organisations 
* 'vcd.get_orgs' - Retrieve list of Organisations 
* 'vcd.get_pvdcs' - Retrieve list of Provider VDCs 
* 'vcd.get_vapp' - Retrieve details for a vApp 
* 'vcd.get_vdc' - Retrieve details for a VDC  
* 'vcd.get_vsnetworks' - Retrieve VSphere networks  
* 'vcd.get_vsphere' - Retrieve VSphere servers  

### Create Actions
#### Org Actions
* 'vcd.create_org' - Create an Organisation  
* 'vcd.create_org_admin' - Create an Organisation Admin Account 
* 'vcd.create_vdc' - Create an VDC  
These actions are designed to work from the same input structure. it will use/ignore elements based on the actions function.

Sample Imput:
```
{"TEST":{
	"Description":"Something to explain here",
	"FullName":"Test Inc",
	"vdcs":{
		"test1":{
			"Storage_Profile": "storage-premium",
			"Description": "Test VDC 1",
			"AllocationModel": "ReservationPool",
			"PVDC": "PVDC-One",
			"ComputeCapacity":{
				"Cpu":{
					"Units":"GHz"
					},
				"Memory":{
					"Units":"MB"
					}
				}
			}
		},
	"IsEnabled":true,
	"org_admin":{
		"admin1":{
			"FullName": "Admin account 1",
			"Password": "Password1",
			"IsEnabled": true
			}
		}
	}
}
```

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
