---
title: "Create Domain Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
description: "Creates a domain and populates the domain with all the resources and applications specified in the model."
---


The Create Domain Tool uses a model and WLST offline to create a domain.  To use the tool, at a minimum, the model must
specify the domain's administrative password in the `domainInfo` section of the model, as shown below.

```yaml
domainInfo:
    AdminPassword: welcome1
```

Using the model above, simply run the `createDomain` tool, specifying where to create the WebLogic Server domain.

    $ weblogic-deploy\bin\createDomain.cmd -oracle_home c:\wls12213 -domain_parent d:\demo\domains -model_file MinimalDemoDomain.yaml

Clearly, creating an empty domain with only the template-defined servers is not very interesting, but this example just
reinforces how sparse the model can be.  When running the Create Domain Tool, the model file must be provided.  Any
references to external files must either already exist or be included in the archive file.  If the model references
one or more paths into the archive file (for example, `wlsdeploy/applications/myapp.war`), the Create Domain Tool will
generate errors if the `-archive_file <archive-file-name>` is not supplied or the archive file supplied does not include
the path specified.

For more information about the archive file and its structure, please refer to the [Archive File]
({{% relref "/concepts/archive.md" %}}) page.

You can customize the model to externalize configuration values that change across environments by using model tokens
that reference properties defined in a variable file.  These model tokens are of the form `@@PROP:<name>@@`, where 
`<name>` maps to a property name in the variable file supplied with the `-variable_file <variable-file-name>`
command-line argument.  Let's look at an example.

The following model section uses model tokens for a JDBC DataSource URL, user name, and password.
```yaml
resources:
    JDBCSystemResource:
        MyDatabase:
            Target: mycluster
            JdbcResource:
                DatasourceType: GENERIC
                JDBCConnectionPoolParams:
                    ConnectionReserveTimeoutSeconds: 10
                    InitialCapacity: 0
                    MaxCapacity: 5
                    MinCapacity: 0
                    TestConnectionsOnReserve: true
                    TestTableName: SQL ISVALID
                JDBCDriverParams:
                    DriverName: oracle.jdbc.OracleDriver
                    PasswordEncrypted: '@@PROP:JDBCSystemResource.MyDatabase.JdbcResource.JDBCDriverParams.PasswordEncrypted@@'
                    URL: '@@PROP:JDBCSystemResource.MyDatabase.JdbcResource.JDBCDriverParams.URL@@'
                    Properties:
                        user:
                            Value: '@@PROP:JDBCSystemResource.MyDatabase.JdbcResource.JDBCDriverParams.Properties.user.Value@@'
```

The following variable file specifies the values that will be substituted for each token.

```properties
JDBCSystemResource.MyDatabase.JdbcResource.JDBCDriverParams.URL=jdbc:oracle:thin:@//mydb.example.com:1539/PDBORCL
JDBCSystemResource.MyDatabase.JdbcResource.JDBCDriverParams.Properties.user.Value=scott
JDBCSystemResource.MyDatabase.JdbcResource.JDBCDriverParams.PasswordEncrypted=tiger
```
The following command-line supplies the variable file to enable token resolution while creating the domain.

    $ weblogic-deploy\bin\createDomain.cmd -model_file mymodel.yaml -variable_file myvariables.properties -oracle_home c:\wls12213 -domain_parent d:\demo\domains

#### Domain types

By default, the Create Domain Tool, like all other WDT tools, assumes that the domain being created is a pure WebLogic
Server domain.  What it means to be a WebLogic Server domain is defined by the `WLS` typedef file, located at
`weblogic-deploy/lib/typedefs/WLS.json`.  Other domain types are known simply by having the corresponding typedef file
installed at `weblogic-deploy/lib/typedefs/<type-name>.json`.  For example, the `JRF` domain type is defined by the
`weblogic-deploy/lib/typedefs/JRF.json` typedef file.

When creating a domain of another type, simply add the `-domain_type <type-name>` command-line argument; for example,
for a JRF domain, add `-domain_type JRF` to the command-line arguments.  Domain typedefs play an important role for the
Create Domain Tool because they tell the tool what domain templates to apply, how to handle targeting of resources
defined by the domain templates, and information about any RCU schemas that are needed.  For more information, refer to
[Domain type definitions]({{% relref "/userguide/tools-config/domain_def.md" %}}) page.

An example of using the domain type argument:

    $ weblogic-deploy\bin\createDomain.cmd -domain_type JRF -model_file model.yaml -oracle_home c:\wls12213 -domain_parent d:\demo\domains 

{{% notice note %}}
When specifying a domain type, it is critical that the Oracle Home being referenced has the necessary products installed.
For example, to create a `JRF` domain, the Oracle Home needs to have the FMW Infrastructure installed.
{{% /notice %}}

When creating domains whose type relies on RCU schemas, you must create the RCU schemas in the database.  This can be
accomplished by either running the `rcu` utility installed in the Oracle Home (for example,
`$ORACLE_HOME/oracle_common/bin/rcu`) directly or having the Create Domain Tool run RCU for you.  With either approach,
the `domainInfo:/RCUDbInfo` section is important to provide the information needed to configure the template-defined
RCU data sources.  The following example shows the minimal set of attributes required when the `rcu` utility has already
been used to create the schemas.

```yaml
domainInfo:
    RCUDbInfo:
        rcu_db_conn_string: mydb.example.com:1539/PDBORCL
        rcu_prefix: DEMO
        rcu_schema_password: my-demo-password
```

When using the Create Domain Tool to create the RCU schemas, the `rcu_admin_password` attribute must also be specified.
If the database administrative user is not `sys as sysdba`, then the `rcu_admin_user` attribute is used to specify the
database administrative user name that should be used instead.

```yaml
domainInfo:
    RCUDbInfo:
        rcu_db_conn_string: mydb.example.com:1539/PDBORCL
        rcu_prefix: DEMO
        rcu_admin_user: admin
        rcu_admin_password: my-admin-password
        rcu_schema_password: my-demo-password
```

The RCUDbInfo section has other fields that may be important in more advanced scenarios.  Please see the
[Connect to a database]({{% relref "/userguide/database/connect-db.md" %}}) page for more information.

Once the model is properly configured for running RCU, simply add the `-run_rcu` argument to the Create Domain Tool
command line.

    $ weblogic-deploy\bin\createDomain.cmd -run_rcu -domain_type JRF -run_rcu -model_file jrf-model.yaml -oracle_home c:\wls12213 -domain_parent d:\demo\domains 

{{% notice warning %}}
When using the `-run_rcu` to create the RCU schemas, note that the default behavior of the Create Domain Tool is to
first try to drop the schemas prior to creating them.  This behavior can be disabled using the `disable.rcu.drop.schema`
property in the `tool.properties` file.  See the [Tool property file]
({{% relref "/userguide/tools-config/tool_prop.md" %}}) page for more information.
{{% /notice %}}

To create more complex domains, it may be necessary to create a custom domain type. This is useful for cases where the
domain has custom templates, or templates for other Oracle products. For more information, refer to
[Domain type definitions]({{% relref "/userguide/tools-config/domain_def.md" %}}).

### User password validation

By default, WLST offline requires the administrator password to have a minimum of 8 characters and a minimum of 1
numeric or special character.  The Create Domain tool will validate both the `domainInfo` section's `AdminPassword`
attribute value and any `Password` fields for users added in the `topology` section's `Security/User` section against
the default rules.

Prior to 3.5.0, validation errors for the administrator password resulted in a WLST error that aborted domain creation
while validation errors for other users resulted in warnings from WDT even though the domain and user was created.
However, due to a bug, any of these users with an invalid password were created with an unusable password.

Starting in 3.5.0, this validation has been unified and enhanced.  Now, password validation:

- Happens upfront during model validation;
- Logs errors for all users' password validation errors and aborts the domain creation process;
- Takes into account any model settings for the WebLogic Server System Password Validator to ensure passwords
  follow its settings.  For example, if model contains the snippet shown below, the minimum length of the passwords
  will be 12 instead of the default value of 8.  Any attributes not present in the model will use their default values
  during password validation.

```yaml
topology:
    SecurityConfiguration:
        Realm:
            myrealm:
                PasswordValidator:
                    SystemPasswordValidator:
                        SystemPasswordValidator:
                            MinPasswordLength: 12
```

**WARNING:** The `MinPasswordLength` attribute, whose default value is 8, and the `MinNumericOrSpecialCharacters`
             attribute, whose default value is 1, have special behavior.  WLST offline does not consider these
             values when validating the administrator password.  Instead, it always uses the default values so even if
             Create Domain allowed a lower value, WLST offline would fail to create the domain due to the password
             not meeting these default values.  For this new password validation purposes only, Create Domain will
             use the larger value between the one specified in the model and the default value.  Create Domain will
             still create the `SystemPasswordValidator` security provider with the exact settings in the model.

This new validation behavior can be disabled by setting the `enable.create.domain.password.validation` property to
`false` in `$WLSDEPLOY_HOME/lib/tool.properties` or by adding
`-Dwdt.config.enable.create.domain.password.validation=false` to the `WLSDEPLOY_PROPERTIES` environment variable prior
to invoking the Create Domain tool.  Note that disabling this validation will disable all validation of passwords
except for the WLST offline validation of the domain's administrative password.

### Using an encrypted model

If the model or variables file contains passwords encrypted with the WDT Encrypt Model Tool, you must provide the 
WDT encryption passphrase used to encrypt the model so that the Create Domain Tool can decrypt them.  To do this,
provide one of the following command-line arguments: 

- `-passphrase_env <ENV_VAR>` - read the passphrase from the specified environment variable,
- `-passphrase_file <file-name>` - read the passphrase from a file that contains the passphrase, or
- `-passphrase_prompt` - have the tool read the passphrase from `stdin`, either by prompting or piping the value to
  the shell script's standard input.

### Using multiple models

The Create Domain Tool supports the use of multiple models, as described in
[Using multiple models]({{% relref "/concepts/model#using-multiple-models" %}}).

### Development domain and `boot.properties`

When creating a development domain, WDT provides the convenience of making a `boot.properties` file for each of the
servers in the domain. The `boot.properties` file will contain encrypted values of the Administration Server user name
and password. When the Administration Server or Managed Server is started, WebLogic Server will bypass the prompt for
credentials, and instead use the credentials from the `boot.properties` file.

A domain is in production mode if the `ServerStartMode` option is set to either `prod` or `secure`, or if the domain
MBean's `ProductionModeEnabled` attribute is set to `true`.  It is an anti-pattern to use both attributes in the same
model.

The `boot.properties` file is stored in the domain home on the machine where WDT runs. It is stored for each server
as `<domain_home>/servers/<server_name>/security/boot.properties`.

The following is a model example using `ServerStartMode` to specify the domain should be created in development mode.
Note that this example is for illustrative purposes only since the default for a domain is development mode so that
`ServerStartMode` line below has no effect.

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome1
    ServerStartMode: dev
topology:
    Name: my-domain
```

### Environment variables
The following environment variables may be set.

-  `JAVA_HOME`             The location of the JDK. This must be a valid Java 7 or later JDK.
-  `WLSDEPLOY_PROPERTIES`  System properties that will be passed to WLST.

{{% notice warning %}}
When running the Create Domain Tool (and any other tool that use WLST), the actual JDK used to run the tool
will be the JDK used to install WebLogic Server in the Oracle Home and not the one defined by the `JAVA_HOME`
environment variable.  The best practice is to set `JAVA_HOME` to point to the same JDK installation that was used to
install WebLogic Server.
{{% /notice %}}


### Opening an issue against the Create Domain Tool

Please provide the full console output of the tool (that is, what is printed to stdout and stderr) and the log file,
`createDomain.log`, which is typically found in the `<install home>/weblogic-deploy/logs` directory.  If possible,
please provide the model, variable and archive files, and any other information that helps to understand the
environment, what you are doing, and what is happening.

### Parameter table for `createDomain`
| Parameter                       | Definition                                                                                                                                                                                                                                                                                               | Default |
|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| --- |
| `-archive_file`                 | The path to the archive file to use.  If the `-model_file` argument is not specified, the model file in this archive will be used.  This can also be specified as a comma-separated list of archive files.  The overlapping contents in each archive take precedence over previous archives in the list. |    |
| `-domain_home`                  | Required if `-domain_parent` is not used. The full directory and name where the domain should be created.                                                                                                                                                                                                
| `-domain_parent`                | Required if `-domain_home` is not used. The parent directory where the domain should be created. The name is the domain name in the model.                                                                                                                                                               |    |
| `-domain_type`                  | The type of domain (for example, `WLS`, `JRF`).                                                                                                                                                                                                                                                          | `WLS` |
| `-java_home`                    | The Java home to use for the new domain. If not specified, it defaults to the value of the `JAVA_HOME` environment variable.                                                                                                                                                                             |    |
| `-model_file`                   | The location of the model file.  This can also be specified as a comma-separated list of model locations, where each successive model layers on top of the previous ones.                                                                                                                                |    |
| `-oracle_home`                  | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set.                                                                                                                                                                                       |    |
| `-opss_wallet`                  | The location of the Oracle wallet containing the domain's encryption key required to reconnect to an existing set of RCU schemas.                                                                                                                                                                        |    |
| `-opss_wallet_passphrase_env`   | An alternative to entering the OPSS wallet passphrase at a prompt. The value is an environment variable name that WDT will use to retrieve the passphrase.                                                                                                                                               |    |
| `-opss_wallet_passphrase_file`  | An alternative to entering the OPSS wallet passphrase at a prompt. The value is the name of a file with a string value which WDT will read to retrieve the passphrase.                                                                                                                                   
| `-passphrase_env`               | An alternative to entering the encryption passphrase at a prompt. The value is an environment variable name that WDT will use to retrieve the passphrase.                                                                                                                                                |    |
| `-passphrase_file`              | An alternative to entering the encryption passphrase at a prompt. The value is the name of a file with a string value which WDT will read to retrieve the passphrase.                                                                                                                                    |    |
| `-passphrase_prompt`            | Allow WDT to prompt for the encryption passphrase or read it from stdin.                                                                                                                                                                                                                                 |    |
| `-run_rcu`                      | Run RCU to create the database schemas specified by the domain type using the specified RCU prefix. Running RCU will drop any existing schemas with the same RCU prefix if they exist prior to trying to create them.                                                                                    |    |
| `-use_encryption`               | (deprecated) Replaced by the `-passphrase_prompt` argument.                                                                                                                                                                                                                                              |    |
| `-variable_file`                | The location of the property file containing the values for variables used in the model. This can also be specified as a comma-separated list of property files, where each successive set of properties layers on top of the previous ones.                                                             |    |
