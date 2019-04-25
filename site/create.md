## The Create Domain Tool

The Create Domain Tool uses a model and WLST offline to create a domain.  To use the tool, at a minimum, the model must specify the domain's administrative password in the `domainInfo` section of the model, as shown below.

```yaml
domainInfo:
    AdminPassword: welcome1
```

Using the model above, simply run the `createDomain` tool, specifying the type of domain to create and where to create it.

    weblogic-deploy\bin\createDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_parent d:\demo\domains -model_file MinimalDemoDomain.yaml

Clearly, creating an empty domain with only the template-defined servers is not very interesting, but this example just reinforces how sparse the model can be.  When running the Create Domain Tool, the model must be provided either inside the archive file or as a standalone file.  If both the archive and model files are provided, the model file outside the archive will take precedence over any that might be inside the archive.  If the archive file is not provided, the Create Domain Tool will create the `topology` section only (using the `domainInfo` section) of the model in the domain.  This is because the `resources` and `appDeployments` sections of the model can reference files from the archive so to create the domain with the model-defined resources and applications, an archive file must be provided--even if the model does not reference anything in the archive.  At some point in the future, this restriction may be relaxed to require the archive only if it is actually needed.

The Create Domain Tool understands three domain types: `WLS`, `RestrictedJRF`, and `JRF`.  When specifying the domain type, the Oracle Home must match the requirements for the domain type.  Both `RestrictedJRF` and `JRF` require an Oracle Home with the FMW Infrastucture (also known as JRF) installed.  When creating a JRF domain, the RCU database information must be provided as arguments to the `createDomain` script.  Note that the tool will prompt for any passwords required.  Optionally, they can be piped to standard input (for example, `stdin`) of the script, to make the script run without user input.  For example, the command to create a JRF domain looks like the one below.  Note that this requires the user to have run RCU prior to running the command.

    weblogic-deploy\bin\createDomain.cmd -oracle_home c:\jrf12213 -domain_type JRF -domain_parent d:\demo\domains -model_file DemoDomain.yaml -rcu_db mydb.example.com:1539/PDBORCL -rcu_prefix DEMO

To have the Create Domain Tool run RCU, simply add the `-run_rcu` argument to the previous command line and the RCU schemas will be automatically created.  Be aware that when the tool runs RCU, it will automatically drop any conflicting schemas that already exist with the same RCU prefix prior to creating the new schemas!

It is also possible to specify the connection information in the model instead of using the command-line arguments.  This is especially easier for databases that require complex database connection string and extra parameters, such as RAC or Oracle Autonomous Transaction Processing Cloud Service database.  For information on how to use it, refer to [Specifying RCU connection information in the model](rcuinfo.md)

The Create Domain Tool has an extensible domain type system.  The three built-in domain types (`WLS`, `RestrictedJRF`, and `JRF`) are defined in JSON files of the same name in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, the `JRF` domain type is defined in the `WLSDEPLOY_HOME/lib/typedefs/JRF.json` file whose contents look like those shown below.

```json
{
    "copyright": "Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.",
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

This file tells the Create Domain Tool which templates to use to create the domain, which server groups to target, and even which RCU schemas to create, all based on the version of WebLogic Server installed.  New domain types can be defined by creating a new JSON file with the same structure in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, to define a `SOA` domain type for 12.2.1.3, add the `WLSDEPLOY_HOME/lib/typedefs/SOA.json` file with contents like those shown below.

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

One last note is that if the model or variables file contains encrypted passwords, add the `-use_encryption` flag to the command line to tell the Create Domain Tool that encryption is being used and to prompt for the encryption passphrase.  As with the database passwords, the tool can also read the passphrase from standard input (for example, `stdin`) to allow the tool to run without any user input.

