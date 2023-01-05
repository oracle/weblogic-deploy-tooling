---
title: "Create Domain Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 1
description: "Creates a domain and populates the domain with all the resources and applications specified in the model."
---


The Create Domain Tool uses a model and WLST offline to create a domain.  To use the tool, at a minimum, the model must specify the domain's administrative password in the `domainInfo` section of the model, as shown below.

```yaml
domainInfo:
    AdminPassword: welcome1
```

Using the model above, simply run the `createDomain` tool, specifying the type of domain to create and where to create it.

    $ weblogic-deploy\bin\createDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_parent d:\demo\domains -model_file MinimalDemoDomain.yaml

Clearly, creating an empty domain with only the template-defined servers is not very interesting, but this example just reinforces how sparse the model can be.  When running the Create Domain Tool, the model must be provided either inside the archive file or as a standalone file.  If both the archive and model files are provided, the model file outside the archive will take precedence over any that might be inside the archive.  If the archive file is not provided, the Create Domain Tool will create the `topology` section only (using the `domainInfo` section) of the model in the domain.  This is because the `resources` and `appDeployments` sections of the model can reference files from the archive so to create the domain with the model-defined resources and applications, an archive file must be provided--even if the model does not reference anything in the archive.  At some point in the future, this restriction may be relaxed to require the archive only if it is actually needed.

The Create Domain Tool understands three domain types: `WLS`, `RestrictedJRF`, and `JRF`.  When specifying the domain type, the Oracle Home must match the requirements for the domain type.  Both `RestrictedJRF` and `JRF` require an Oracle Home with the FMW Infrastucture (also known as JRF) installed.  When creating a JRF domain, the RCU database information must be provided as arguments to the `createDomain` script.  Note that the tool will prompt for any passwords required.  Optionally, they can be piped to standard input (for example, `stdin`) of the script, to make the script run without user input.  For example, the command to create a JRF domain looks like the one below.  Note that this requires the user to have run RCU prior to running the command.

    $ weblogic-deploy\bin\createDomain.cmd -oracle_home c:\jrf12213 -domain_type JRF -domain_parent d:\demo\domains -model_file DemoDomain.yaml -rcu_db mydb.example.com:1539/PDBORCL -rcu_prefix DEMO [-rcu_db_user SYS]

To have the Create Domain Tool run RCU, simply add the `-run_rcu` argument to the previous command line and the RCU schemas will be automatically created.  Be aware that when the tool runs RCU, it will automatically drop any conflicting schemas that already exist with the same RCU prefix prior to creating the new schemas!

It is also possible to specify the connection information in the model instead of using the command-line arguments.  This is especially easier for databases that require complex database connection string and extra parameters, such as RAC or Oracle Autonomous Transaction Processing Cloud Service database.  For information on how to use it, refer to [Specifying RCU connection information in the model]({{< relref "/content/rcuinfo.md" >}}).

To create more complex domains, it may be necessary to create a custom domain type. This is useful for cases where the domain has custom templates, or templates for other Oracle products. For more information, refer to [Domain type definitions]({{< relref "/userguide/tools-config/domain_def.md" >}}).

### Using an encrypted model

If the model or variables file contains passwords encrypted with the WDT Encryption tool, decrypt the passwords during create with the `-use_encryption` flag on the command line to tell the Create Domain Tool that encryption is being used and to prompt for the encryption passphrase.  As with the database passwords, the tool can also read the passphrase from standard input (for example, `stdin`) to allow the tool to run without any user input. You can bypass the stdin prompt with two other options. You can bypass the stdin prompt with two other options: store the passphrase in an environment variable, and use the environment variable name with the command-line
option `-passphrase_env` or create a file with the single value of the passphrase. Provide the name of the file with the command-line option `-passphrase_file`. The passphrase will be read by the tool from the file.

### Using multiple models

The Create Domain Tool supports the use of multiple models, as described in [Using multiple models]({{< relref "/concepts/model#using-multiple-models" >}}).

### Development domain and `boot.properties`

When creating a development domain, WDT provides the convenience of making a `boot.properties` file for each of the servers in the domain. The `boot.properties` file will contain encrypted values of the Administration Server user name and password. When the Administration Server or Managed Server is started, WebLogic Server will bypass the prompt for credentials, and instead use the credentials from the `boot.properties` file.

A domain is in production mode if the `ServerStartMode` option is set to `prod` or the domain `ProductionModeEnabled` is set to `true`. The default value for both of these attributes is development mode.

The `boot.properties` file is stored in the domain home on the machine where WDT runs. It is stored for each server as `<domain_home>/servers/<server_name>/security/boot.properties`.

The following is a model example with both attributes explicitly set to development mode.

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome1
    ServerStartMode: dev
topology:
    Name: my-domain
    AdminServerName: admin-server
    ProductionModeEnabled: false
```

### Parameter table for `createDomain`
| Parameter | Definition | Default |
| --- | --- | --- |
| `-archive_file` | The path to the archive file to use.  If the `-model_file` argument is not specified, the model file in this archive will be used.  This can also be specified as a comma-separated list of archive files.  The overlapping contents in each archive take precedence over previous archives in the list. |    |
| `-domain_home` | Required if `-domain_parent` is not used. The full directory and name where the domain should be created.
| `-domain_parent` | Required if `-domain_home` is not used. The parent directory where the domain should be created. The name is the domain name in the model. |    |
| `-domain_type` | The type of domain (for example, `WLS`, `JRF`). | `WLS` |
| `-java_home` | The Java home to use for the new domain. If not specified, it defaults to the value of the `JAVA_HOME` environment variable. |    |
| `-model_file` | The location of the model file.  This can also be specified as a comma-separated list of model locations, where each successive model layers on top of the previous ones. |    |
| `-oracle_home` | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set.|    |
| `-opss_wallet_passphrase_env` | An alternative to entering the OPSS wallet passphrase at a prompt. The value is an environment variable name that WDT will use to retrieve the passphrase. |    |
| `-opss_wallet_passphrase_file` | An alternative to entering the OPSS wallet passphrase at a prompt. The value is the name of a file with a string value which WDT will read to retrieve the passphrase.
| `-passphrase_env` | An alternative to entering the encryption passphrase at a prompt. The value is an environment variable name that WDT will use to retrieve the passphrase. |    |
| `-passphrase_file` | An alternative to entering the encryption passphrase at a prompt. The value is the name of a file with a string value which WDT will read to retrieve the passphrase. |    |
| `-rcu_database` | The RCU database connect string.  |    |
| `-rcu_prefix` | The RCU prefix to use. |    |
| `-rcu_db_user` | The RCU `dbUser` to use. | `sys` |
| `-run_rcu` | Run RCU to create the database schemas specified by the domain type using the specified RCU prefix. Running RCU will drop any existing schemas with the same RCU prefix if they exist prior to trying to create them. |    |
| `-use_encryption` | One or more of the passwords in the model or variables file(s) are encrypted and must be decrypted. Java 8 or later required for this feature. |    |
| `-variable_file` | The location of the property file containing the values for variables used in the model. This can also be specified as a comma-separated list of property files, where each successive set of properties layers on top of the previous ones. |    |
