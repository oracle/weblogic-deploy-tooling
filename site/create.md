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

The Create Domain Tool has an extensible domain type system, it is defined using python dictionary called typedefs.  See - [TypeDefs Definition](developer_guide.md#typedefs-definition) for details.  

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

One last note is that if the model or variables file contains encrypted passwords, add the `-use_encryption` flag to the command line to tell the Create Domain Tool that encryption is being used and to prompt for the encryption passphrase.  As with the database passwords, the tool can also read the passphrase from standard input (for example, `stdin`) to allow the tool to run without any user input.

