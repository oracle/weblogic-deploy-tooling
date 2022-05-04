---
title: "Targeting server groups"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 10
description: "Targeting server groups to managed servers and dynamic server groups to dynamic clusters."
---



To create more complex domains with clusters of different types, it is necessary to control the targeting of server groups to managed servers.
By default, all server groups in the domain type definition are targeted to all managed servers.
To create a SOA domain with SOA and OSB clusters, simply add the OSB template and server group to the SOA domain definition, as shown below.

```json
{
    "name": "SOA",
    "description": "SOA type domain definitions",
    "versions": {
        "12.2.1.3": "SOA_12213"
    },
    "definitions": {
        "SOA_12213": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [
                "Oracle SOA Suite",
                "Oracle Service Bus"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR",  "SOA-MGD-SVRS",  "OSB-MGD-SVRS-COMBINED" ],
            "dynamicClusterServerGroupsToTarget": [ "SOA-DYN-CLUSTER" ],
            "rcuSchemas": [ "STB", "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS", "UCSUMS", "SOAINFRA" ]
        }
    }
}
```

Then, use the `ServerGroupTargetingLimits` map in the `domainInfo` section to limit the targeting of the Web Services Manager, SOA, and OSB server groups to the `soa_cluster` or `osb_cluster`, as appropriate.  In the example below, notice that the `JRF-MAN-SVR` server group is not listed; therefore, it will use the default targeting and be targeted to all managed servers.  The value of each element in this section is a logical list of server and/or cluster names.  As shown in the example, the value for each server group can be specified as a list, a comma-separated string, or a single-valued string.  There is no semantic difference between listing a cluster's member server names versus using the cluster name; the example uses these simply to show what is possible.

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome1
    ServerStartMode: prod
    ServerGroupTargetingLimits:
        'WSMPM-MAN-SVR': soa_cluster
        'SOA-MGD-SVRS': soa_server1,soa_server2
        'OSB-MGD-SVRS-COMBINED': [ osb_server1, osb_server2 ]

topology:
    Name: soa_domain
    AdminServerName: AdminServer
    Cluster:
        soa_cluster:
        osb_cluster:
    Server:
        AdminServer:
            ListenAddress: myadmin.example.com
            ListenPort: 7001
            Machine: machine1
            SSL:
                Enabled: true
                ListenPort: 7002
        soa_server1:
            ListenAddress: managed1.example.com
            ListenPort: 8001
            Cluster: soa_cluster
            Machine: machine2
            SSL:
                Enabled: true
                ListenPort: 8002
        soa_server2:
            ListenAddress: managed2.example.com
            ListenPort: 8001
            Cluster: soa_cluster
            Machine: machine3
            SSL:
                Enabled: true
                ListenPort: 8002
        osb_server1:
            ListenAddress: managed1.example.com
            ListenPort: 9001
            Cluster: osb_cluster
            Machine: machine2
            SSL:
                Enabled: true
                ListenPort: 9002
        osb_server2:
            ListenAddress: managed2.example.com
            ListenPort: 9001
            Cluster: osb_cluster
            Machine: machine3
            SSL:
                Enabled: true
                ListenPort: 9002
    UnixMachine:
        machine1:
            NodeManager:
                ListenAddress: myadmin.example.com
                ListenPort: 5556
        machine2:
            NodeManager:
                ListenAddress: managed1.example.com
                ListenPort: 5556
        machine3:
            NodeManager:
                ListenAddress: managed2.example.com
                ListenPort: 5556
    SecurityConfiguration:
        NodeManagerUsername: weblogic
        NodeManagerPasswordEncrypted: welcome1
```

#### Targeting dynamic cluster server groups
Dynamic Cluster Server Groups are server groups that can be targeted to dynamic clusters. Dynamic clusters were added in WebLogic Server version 12.1.2.
In WebLogic Server version 12.2.1.1, the ability to target a single dynamic server group to a dynamic cluster was added. In WebLogic Server Version 12.2.1.4,
you now have the ability to target multiple dynamic server groups to a dynamic cluster.

To enable targeting of dynamic server groups to dynamic clusters, add the `dynamicClusterServerGroupsToTarget` entry with any dynamic server groups you wish to be targeted to the dynamic clusters in your model or domain. This list must only contain one dynamic server group if you are running a version of WebLogic Server earlier than 12.2.1.4.
```json
{
  "definitions": {
    "dynamicClusterServerGroupsToTarget" : [ "WSMPM-DYN-CLUSTER", "WSM-CACHE-DYN-CLUSTER" ]
  }
}
```
If you wish to specify which dynamic server group to target to a dynamic server, add `DynamicClusterServerGroupTargetingLimits` to the `domainInfo` of your model. This entry can coexist with managed servers defined in `ServerGroupTargetingLimits`.
```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome1
    ServerStartMode: prod
    DynamicClusterServerGroupTargetingLimits:
        SOA-DYN-CLUSTER: soa_dynamic_cluster
```
