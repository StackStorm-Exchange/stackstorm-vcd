# VCloud Director

## Description

Basic actions to integrate with VCloud Director.


## Connection Configuration

Copy the sample configuration file [vcd.yaml.example](./vcd.yaml.example) to `/opt/stackstorm/configs/vcd.yaml`
and edit as required. Required fields for connecting to vcloud are address, user and password.

Run `sudo st2ctl reload --register-configs` to get StackStorm to load the updated configuration.


## Actions

* `vcloud_director.get_org` - Retrieve a single organisation details
* `vcloud_director.get_orgs` - Retrieve a list of available organisations
* `vcloud_director.get_pvdcs` - Retrieve details about the Provider VDCs

