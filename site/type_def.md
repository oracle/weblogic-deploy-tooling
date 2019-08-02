## Domain Type Definitions

WebLogic Server Deploy Tooling has an extensible domain type system.  The three built-in domain types (`WLS`, `RestrictedJRF`, and `JRF`) are defined in JSON files of the same name in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, the `JRF` domain type is defined in the `WLSDEPLOY_HOME/lib/typedefs/JRF.json` file with similar content, as shown below.

```json
{
    "copyright": "Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.",
    "license": "The Universal Permissive License (UPL), Version 1.0",
    "name": "JRF",
    "description": "JRF type domain definitions",
    "versions": {
        "12.1.2": "JRF_1212",
        "12.1.3": "JRF_1213",
        "12.2.1": "JRF_12CR2",
        "12.2.1.3": "JRF_12213"
    },
    "definitions": {
        "JRF_1212" : {
            "baseTemplate": "@@WL_HOME@@/common/templates/wls/wls.jar",
            "extensionTemplates": [
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf_template_12.1.2.jar",
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf.ws.async_template_12.1.2.jar",
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.wsmpm_template_12.1.2.jar",
                "@@ORACLE_HOME@@/em/common/templates/wls/oracle.em_wls_template_12.1.2.jar"
            ],
            "serverGroupsToTarget" : [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        },
        "JRF_1213" : {
            "baseTemplate": "@@WL_HOME@@/common/templates/wls/wls.jar",
            "extensionTemplates": [
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf_template_12.1.3.jar",
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf.ws.async_template_12.1.3.jar",
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.wsmpm_template_12.1.3.jar",
                "@@ORACLE_HOME@@/em/common/templates/wls/oracle.em_wls_template_12.1.3.jar"
            ],
            "serverGroupsToTarget" : [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        },
        "JRF_12CR2": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [
                "Oracle JRF WebServices Asynchronous services",
                "Oracle WSM Policy Manager",
                "Oracle Enterprise Manager"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        },
        "JRF_12213": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [
                "Oracle JRF WebServices Asynchronous services",
                "Oracle WSM Policy Manager",
                "Oracle Enterprise Manager"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        }
    }
}
```

This file tells the Create Domain Tool which templates to use to create the domain, which server groups to target, and even which RCU schemas to create, all based on the installed version of WebLogic Server.  New domain types can be defined by creating a new JSON file with the same structure in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, to define a `SOA` domain type for 12.2.1.3, add the `WLSDEPLOY_HOME/lib/typedefs/SOA.json` file with with similar content, as shown below.

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
                "Oracle SOA Suite"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR",  "SOA-MGD-SVRS" ],
            "rcuSchemas": [ "STB", "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS", "UCSUMS", "SOAINFRA" ]
        }
    }
}
```

After the new domain `typedef` file exists, simply specify the new domain type name to the `createDomain` script, being sure to reference an Oracle Home with the required components installed.  For pre-12.2.1 versions, the `-wlst_path` argument must be used to point to the product home where the appropriate WLST shell script exists; for example, for SOA 12.1.3, add `-wlst_path <ORACLE_HOME>/soa` so that the tool uses the WLST shell script with the proper environment for SOA domains.  In 12.2.1 and later, this is no longer necessary because the WLST shell script in the standard `<ORACLE_HOME>oracle_common/common/bin` directory will automatically load all components in the Oracle Home.  Using the new domain type, simply run the following command to run RCU and create the SOA domain with all of its resources and applications deployed.

    weblogic-deploy\bin\createDomain.cmd -oracle_home d:\SOA12213 -domain_type SOA -domain_parent d:\demo\domains -model_file DemoDomain.yaml -archive_file DemoDomain.zip -variable_file DemoDomain.properties -run_rcu -rcu_db mydb.example.com:1539/PDBORCL -rcu_prefix DEMO

### Server Group Targeting

To create more complex domains with clusters of different types, it is necessary to control the targeting of server groups to managed servers.  By default, all server groups in the domain type definition are targeted to all managed servers.  To create a SOA domain with SOA and OSB clusters, simply add the OSB template and server group to the SOA domain definition, as shown below.

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
        'SOA-MGD-SVRS': 'soa_server1,soa_server2'
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

### Custom Extension Templates

The `customExtensionTemplates` attribute can be used to specify custom extension templates to be applied to the domain. These should be specified as absolute file paths, and can use tokens.  

```json
{
    "name": "MyCustom",
    "description": "My custom type domain definitions",
    "versions": {
        "12.2.1.3": "My_12213"
    },
    "definitions": {
        "My_12213": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [ ],
            "customExtensionTemplates": [
                "/user/me/templates/my-template.jar",
                "@@ORACLE_HOME@@/user_templates/other-template.jar"
            ],
            "serverGroupsToTarget": [ "MY-MAN-SVR" ],
            "rcuSchemas": [ ]
        }
    }
}
```

If there are any server groups in the custom template that should be targeted to managed servers, they should be specified in the `serverGroupsToTarget` attribute, similar to `MY_MAN_SVR` in the example above.

### Targeting in Earlier WebLogic Server Versions

Templates in WebLogic Server versions prior to 12.2.1 may require the use of the `applyJRF` WLST command to correctly target resources to the correct clusters and servers. The default behavior for WebLogic Deploy Tooling is to invoke `applyJRF` only when the `extensionTemplates` list includes JRF templates.

A custom type definition file can require `applyJRF` to be invoked after the templates are added. This is done by setting the `targeting` attribute to `APPLY_JRF`, as in this example:

```json
{
    "name": "MyCustom",
    "description": "My custom type domain definitions",
    "versions": {
        "10.3.6": "My_11G"
    },
    "definitions": {
        "My_11G": {
            "baseTemplate": "@@WL_HOME@@/common/templates/wls/wls.jar",
            "extensionTemplates": [
                "/user/me/templates/my-template.jar"
             ],
            "targeting": "APPLY_JRF",
            "serverGroupsToTarget": [ "MY-MAN-SVR" ],
            "rcuSchemas": [ ]
        }
    }
}
```

The `targeting` attribute is not valid for WebLogic Server versions 12.2.1 and up.
