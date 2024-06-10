---
title: "Discover Domain Tool"
date: 2024-05-07T13:30:00-05:00
draft: false
weight: 4
description: "Introspects an existing domain and creates a model file describing the domain and an archive file of the binaries deployed to the domain."
---

The Discover Domain Tool provides a bootstrapping mechanism to creating a model and archive file by inspecting an
existing domain and gathering configuration and binaries from it.  

By default, the model file produced by the tool is not directly usable by the Create Domain, Update Domain or the 
Deploy Applications Tools because the Discover Domain Tool does not discover the passwords from the existing domain.
Instead, it puts a `--FIX ME--` placeholder for passwords it finds.  Security provider data is also not discovered by
default.  Therefore, the tool injects the same placeholder value in the `AdminUserName` and `AdminPassword` fields in
the `domainInfo` section of the model. The idea of this tool is simply to provide a starting point where the user can
edit the generated model and archive file to suit their needs for running one of the other tools.

In WDT 4.2.0, several optional features have been added to change the default behavior that make it possible
to discover passwords and the security providers data that give the Discover Domain Tool the ability to produce a fully
populated model that is usable by the other tools without editing the model file.  Please see the
[Discovering security information]({{< relref "#discovering-security-information" >}}) section for
more information.

The Discover Domain tool can be run in either offline or online mode, and each mode has some options that control its
behavior.

- offline mode - Offline mode uses WLST offline to read the domain configuration from the domain home directory.  This
  means that the tool must run on the same host as the domain's Administration Server and that the user running the
  tool needs full read access to the domain home directory structure.  By default, the tool will gather files referenced
  by the domain configuration (for example, applications, domain libraries) and store those files in a zip file known as
  the archive file.  To prevent the collection of these files, simply add the `-skip_archive` argument to the
  command-line use to invoke the tool.
- online mode - Online mode uses WLST online to read the domain configuration using the Administration Server's MBeans.
  The user running the tool needs to provide the administrative credentials and URL to connect to the Administration
  Server.  There are four options when running the tool:
  - Normal mode (default) - In this mode, the tool must run on the same host as the domain's Administration Server
    and the user running the tool must have full read access to the domain home directory structure and any other 
    locations where domain-specific files are stored.
  - `-skip_archive` mode - In this mode, the tool can be run from anywhere since the archive file is not being created.
  - `-remote` mode - This mode is similar to `-skip_archive` mode except that the tool will generate a list of `TODO`
     messages that inform the user which artifacts needs to be gathered and added to an archive file in order to create
     a complete model of the domain.
  - SSH mode - In this mode, the tool can be run from any host for which you have set up SSH connectivity between the
    host where WDT is running and the host where the Administration Server is running.  The `-ssh_user` (which, by
    default, is the same user running the tool) must have full read access to the domain home directory structure and
    any other locations where domain-specific files are stored on the server.  See the
    [SSH support]({{< relref "/userguide/tools/shared/ssh.md" >}}) and
    [Verify SSH Tool]({{< relref "/userguide/tools/verify_ssh.md" >}}) pages for more information about running in SSH
    mode.

You can customize what is generated in the model for credential-related attributes (that is, user names and passwords)
by using the `-variable_file` argument on the command line with variable file location. This file is a Java properties
file which will contain a key=value pair for each credential-related attribute found in the model. The key is a unique
token name for the specific attribute, and the value is the replacement value; by default, user name attributes are
populated with the discovered value and password attributes are populated with an empty string. The attribute in the
model is injected with the token name and property field notation. For example, `@@PROP:AdminUserName@@` or 
`@@PROP:JDBCSystemResource.<Name>.JdbcResource.JDBCDriverParams.PasswordEncrypted@@`.

If [variable injection]({{< relref "/userguide/tools-config/variable_injectors.md" >}}) is configured, but the
`-variable_file` argument is not used, the variable file is created with the same name as the model file,
with the file extension `.properties`. As with the archive and model file, each run of the Discover Domain Tool will
overwrite the contents of an existing variable file with the values from the current run.

Before the model is persisted to the model file, any variable injectors or model filters are run, in that order. The
final step is validation, which validates the contents of the model, archive and variable file. If the validation is
successful, the model is persisted. For more information on these three topics, see:

- [Variable injection]({{< relref "/userguide/tools-config/variable_injectors.md" >}})
- [Model filters]({{< relref "/userguide/tools-config/model_filters.md" >}})
- [Validate Model Tool]({{< relref "/userguide/tools/validate.md" >}})

The resulting model can also be modified for compatibility with specific target environments, such as Oracle WebLogic
Server Kubernetes Operator. For more information, see [Target environments]({{< relref "/userguide/target_env.md" >}}).

Any problems (or success) will be listed in the Discover Domain Tool summary. The summary will print the version of the
tool and Oracle home, and the WLST mode with which the tool was run (online or offline). A recap of all important
messages will be listed, along with a total for each type.

Here is an example of a summary with a single SEVERE message:

```
Issue Log for discoverDomain version 4.2.0 running WebLogic version 12.1.3.0.0 in online mode against server using WebLogic version 12.1.3.0.0:

SEVERE Messages:

        1. WLSDPLY-20008: discoverDomain argument processing failed: discoverDomain invoked with ambiguous configuration: -passphrase argument was specified without one of the associated arguments: -discover_passwords or -discover_security_provider_data.

Total:   SEVERE :    1  WARNING :    0

discoverDomain.sh failed due to a parameter validation error
```

#### Running the tool in offline mode

To run the Discover Domain Tool in offline mode, simply provide the Oracle home and domain location. Provide a location
and file name for the model file and archive file where the discovered domain information will be written. The model
can be generated in either YAML or JSON format. Simply label the file name with the correct suffix.

Example of basic discoverDomain:

    $ weblogic-deploy\bin\discoverDomain.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DiscoveredDemoDomain.zip -model_file DiscoveredDemoDomain.yaml

When creating the archive, the tool will try to gather all binaries, scripts, and required directories referenced by
the domain configuration.

{{% notice note %}}
Any binaries referenced from the `ORACLE_HOME` will not be gathered, as they are assumed to exist in any target
domain to which model-driven operations will be applied.  Doing this is key to allowing the model to be WebLogic
Server version independent.
{{% /notice %}}

#### Running the tool in online mode

To run the Discover Domain Tool in online mode, you have several options as described earlier.  In normal mode, WDT
must be run on the same host as the Administration Server by a user that has read access to the necessary directories
(for example, the domain home directory) to collect the files to populate the archive file. Simply include the admin
user name and admin URL on the command line. The tool will prompt for a password to be entered into STDIN. To bypass the
prompt, you can use one of three options:

- Store the password in an environment variable, and use the variable name with command-line option `-admin_pass_env`.
- Store the password value in a file. Provide the file name with command-line option `-admin_pass_file`.
- Pipe the value on STDIN to the shell script. 

An example of running in online WLST mode from the admin server:

    $ weblogic-deploy/bin/discoverDomain.sh -oracle_home /u01/oracle -domain_home /u01/oracle/domains/DemoDomain -archive_file ./DiscoveredDemoDomain.zip -model_file ./DiscoveredDemoDomain.yaml -admin_user weblogic -admin_url t3://localhost:7001

To run the tool against a remote Administration Server, you can use one of the other modes: `-skip_archive`, `-remote`
or SSH mode.  

With `-remote`, file collection will be skipped and the tool will generate `TODO` messages for any files that are
needed for the domain but could not be gathered.  You can manually gather the necessary files and use the [Archive
Helper Tool]({{< relref "/userguide/tools/archive_helper.md" >}}) to create an archive file to complete the model.

An example of running in online WLST mode from a remote host:

    $ weblogic-deploy/bin/discoverDomain.sh -oracle_home /u01/oracle -remote -model_file ./DiscoveredDemoDomain.yaml -admin_user weblogic -admin_url t3://my.remote.host:7001

With SSH mode, the tool will gather the files from the remote machine using SSH and SCP.  Please see the
[SSH Support]({{< relref "/userguide/tools/shared/ssh.md" >}}) and
[Verify SSH Tool]({{< relref "/userguide/tools/verify_ssh.md" >}}) pages for more information on setting up and
using SSH-based access to remote domains.

#### Domain types

By default, the Discover Domain Tool, like all other WDT tools, assumes that the domain is a pure WebLogic Server domain.
What it means to be a WebLogic Server domain is defined by the `WLS` typedef file, located at 
`weblogic-deploy/lib/typedefs/WLS.json`.  Other domain types are known simply by having the corresponding typedef file
installed at `weblogic-deploy/lib/typedefs/<type-name>.json`.  For example, the `JRF` domain type is defined by the
`weblogic-deploy/lib/typedefs/JRF.json` typedef file.

When discovering a domain of another type, simply add the `-domain_type <type-name>` command-line argument; for example,
for a JRF domain, add `-domain_type JRF` to the command-line arguments.  Domain typedefs play an important role for the
Discover Domain Tool because they apply a set of filters defined in the matching typedef file's `discover-filters`
section that cause configuration elements to be excluded from the discovered model.  The rationale for this is that
these domain template-defined resources that are automatically created when creating a new domain of the same type so
there is typically no need to clutter the model with these boilerplate resource definitions that users do not typically
modify.  For more information, refer to [Domain type definitions]({{< relref "/userguide/tools-config/domain_def.md" >}})
page.

An example of using the domain type argument:

    $ weblogic-deploy\bin\discoverDomain.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DiscoveredDemoDomain.zip -model_file DiscoveredDemoDomain.yaml -domain_type JRF

### Discovering security information
WDT has introduced features that allow you to more fully discover a domain by discovering passwords stored in the domain
configuration files and by discovering data from the default security providers.  This section discusses those options.

#### Discovering passwords

Starting in 4.1.0, the Discover Domain Tool supports discovering passwords from the domain configuration files
(for example, config.xml and any JDBCSystemResource XML file) by adding the `-discover_passwords` flag to the
command-line.  This feature works in both offline and online modes provided that WDT has access to the domain home
directory (that is, it does not work with the online `-remote` argument).  By default, WDT will try to use 
WDT encryption to encrypt the passwords in the model using the WDT passphrase passed to the tool, which requires using
one of the following command-line arguments: `-passphrase_env`, `-passphrase_file`, or `passphrase_prompt`.
This allows the user to discover the passwords from a domain and securely store them in the model using technology
that is not tied to the source domain.

{{% notice warning %}}WDT provides a configuration setting in `tool.properties` that allows the passwords to be stored
in the model without being encrypted.  Oracle strongly recommends that you do not use this feature since not only will
it result in passwords being stored in clear text in the model but also may result in passwords in the WDT log files.
{{% /notice %}}

#### Discovering default security provider data

By default, WebLogic Server domains come configured with four default security provider types that store domain-specific
information in them:

- `DefaultAuthenticator` - stores users and groups.
- `XACMLAuthenticator` - stores authorization policies.
- `XACMLRoleMapper` - stores role definitions and the rule for mapping those to users and groups.
- `DefaultCredentialMapper` - stores credentials for remote endpoints so that an authorized local user can authenticate 
  to the remote endpoint.

The WDT model file already has model sections for each of these providers' data, as follows:

- `topology:/Security/User` - is used to create users stored in the `DefaultAuthenticator`.
- `topology:/Security/Group` - is used to create groups stored in the `DefaultAuthenticator`.
- `domainInfo:/WLSPolicies` - is used to create authorization policies stored in the `XACMLAuthorizer`.
- `domainInfo:/WLSRoles` - is used to create WebLogic roles stored in the `XACMLRoleMapper`.
- `domainInfo:/WLSUserPasswordCredentialMappings` - is used to create credential mappings stored in the `DefaultCredentialMapper`.

Starting in 4.2.0, the Discover Domain Tool supports the `-discover_security_provider_data <scope>` command-line argument.
The scope can be one of the following values or a list of some of these value:

- `ALL` - discovers all 4 provider types
- `DefaultAuthenticator` - discovers users and groups.
- `XACMLAuthorizer` - discovers authorization policies.
- `XACMLRoleMapper` - discovers role definitions.
- `DefaultCredentialMapper` - discovers credential mappings.

The `ALL` scope is exactly the same as a scope value that lists each of the four provider types (for example,
`DefaultAuthenticator,XACMLAuthorizer,XACMLRoleMapper,DefaultCredentialMapper`)

{{% notice note %}}Discovery filters out all security data that matches the defaults for the WLS version being used
except for users, because WDT needs to discover the users' passwords to use when creating a new domain from the
discovered model.
{{% /notice %}}

When discovering the `DefaultAuthenticator` or the `DefaultCredentialMapper`, any discovered passwords will be stored
in the model using WDT encryption; therefore, the WDT encryption passphrase must be provided using one of the
following command-line arguments: `-passphrase_env`, `-passphrase_file`, or `passphrase_prompt`.  Failure to do so will
result in the model password values being set to `-- FIX ME --`.

{{% notice warning %}}WDT provides a configuration setting in `tool.properties` that allows the passwords to be stored
in the model without being encrypted.  Oracle strongly recommends that you do not use this feature since not only will
it result in passwords being stored in clear text in the model but also may result in passwords in the WDT log files.
{{% /notice %}}

When discovering the `XACMLAuthorizer` or the `XACMLRoleMapper`, WDT analyzes the XACML documents to try to determine
the policy or expression from which the XACML was generated.  If this succeeds, the model will contain that policy or
role.  If not, the XACML document will be added to the archive file and a reference to that document will be added to
the model instead.

#### Discovering the default administrator user name and password

A WDT model used to create a domain require that the default administrator user name and password be provided in the
`domainInfo` section's `AdminUserName` and `AdminPassword` attributes.  These values are used to populate the
domain's administrative credentials prior to writing the domain to disk.  By default, the Discover Domain Tool sets the
value of these model attributes to `--FIX ME--`, or to empty strings if the variables file is being used.  When
using the `-discover_security_provider_data` feature, these fields will be populated with the actual administrative user
name and password.  Since it is not possible to determine the default administrative user name or the password, the
tool uses the values passed to the tool on the command-line.  If desired, this feature can be disabled using the
`store.discover.admin_credentials` property in the WDT tool.property file

{{% notice note %}}
If the domain being discovered has multiple administrators, the administrative credentials provided to the Discover
Domain Tool will be the ones added to the model.  If the resulting model is used to create another domain, that user
will become the default administrator for the new domain.  Therefore, it is important to choose the credentials used
to invoke the Discover Domain Tool with this in mind.
{{% /notice %}}

### Environment variables
The following environment variables may be set.

-  `JAVA_HOME`             The location of the JDK. This must be a valid Java 7 or later JDK.
-  `WLSDEPLOY_PROPERTIES`  System properties that will be passed to WLST.

{{% notice warning %}}
When running the Discover Domain Tool (and any other tool that use WLST), the actual JDK used to run the tool
will be the JDK used to install WebLogic Server in the Oracle Home and not the one defined by the `JAVA_HOME`
environment variable.  The best practice is to set `JAVA_HOME` to point to the same JDK installation that was used to
install WebLogic Server.
{{% /notice %}}


### Opening an issue against the Discover Domain Tool

Please provide the full console output of the tool (that is, what is printed to stdout and stderr) and the log file,
`discoverDomain.log`, which is typically found in the `<install home>/weblogic-deploy/logs` directory.  If possible,
please provide the model, variable and archive files, and any other information that helps to understand the
environment, what you are doing, and what is happening.

### Parameter table for `discoverDomain`
 Parameter                      | Definition                                                                                                                                                                                       | Default                                    |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `-archive_file`                | The path to the archive file.                                                                                                                                                                    |                                            |
| `-admin_pass_env`              | An alternative to entering the admin password at a prompt. The value is an environment variable name that WDT will use to retrieve the password.                                                 |                                            |
| `-admin_pass_file`             | An alternative to entering the admin password at a prompt. The value is a the name of a file that contains a password string that the tool will read to retrieve the password.                   |                                            |
| `-admin_url`                   | The admin server URL used for online discovery.                                                                                                                                                  |                                            |
| `-admin_user`                  | The admin user used for online discovery.                                                                                                                                                        |                                            |
| `-discover_passwords`          | Whether to discover passwords from the target domain.                                                                                                                                            |                                            |
| `-domain_home`                 | Used only for offline operation.  The location of the existing domain home.                                                                                                                      | For online mode, the server's value.       |
| `-domain_type`                 | The type of domain (for example, `WLS`, `JRF`).                                                                                                                                                  | `WLS`                                      |
| `-java_home`                   | Overrides the `JAVA_HOME`  value when discovering domain values to be replaced with the Java home global token.                                                                                  |                                            |
| `-model_file`                  | The path to the model file.                                                                                                                                                                      |                                            |
| `-oracle_home`                 | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set.                                                                               |                                            |
| `-output_dir`                  | Output directory required for `-target`.                                                                                                                                                         |                                            |
| `-passphrase_env`              | An alternative to entering the encryption passphrase at a prompt when discovering passwords. The value is an environment variable name that WDT will use to retrieve the passphrase.             |                                            |
| `-passphrase_file`             | An alternative to entering the encryption passphrase at a prompt when discovering passwords. The value is the name of a file with a string value which WDT will read to retrieve the passphrase. |                                            |
| `-passphrase_prompt`           | Allow WDT to prompt for the encryption passphrase or read it from stdin.                                                                                                                         |                                            |
| `-skip_archive`                | Do not generate an archive file. The `-archive_file` option will be ignored.                                                                                                                     |                                            |
| `-target`                      | The target output type. The default is `wko`. For more information about target types, see [Target Environments]({{< relref "userguide/target_env" >}}).                                         |                                            |
| `-remote`                      | Update the domain from a remote machine.                                                                                                                                                         |                                            |
| `-ssh_host`                    | The DNS name or IP address of the remote host.                                                                                                                                                   |                                            |
| `-ssh_port`                    | The TCP port on the remote host where the SSH daemon is listening for connection requests.                                                                                                       | `22`                                       |
| `-ssh_user`                    | The user name on the remote host to use for authentication purposes.                                                                                                                             | Same as the local user running the tool.   |
| `-ssh_pass_env`                | The environment variable name to use to retrieve the remote user's password when authenticating with user name and password.                                                                     |                                            |
| `-ssh_pass_file`               | The file name of a file that contains the password string for the remote user's password when authenticating with user name and password.                                                        |                                            |
| `-ssh_pass_prompt`             | A flag to force the tool to prompt the user to provide the remote user's password through standard input when authenticating with user name and password.                                        | Do not prompt or read from standard input. |
| `-ssh_private_key`             | The local file name of the user's private key file to use when authenticating with a public/private key pair.                                                                                    | `$HOME/.ssh/id_rsa`                        |                                                                                       
| `-ssh_private_key_pass_env`    | The environment variable name to use to retrieve user's private key passphrase when authenticating with a public/private key pair.                                                               |                                            |
| `-ssh_private_key_pass_file`   | The file name of a file that contains the user's private key passphrase string when authenticating with a public/private key pair.                                                               |                                            |
| `-ssh_private_key_pass_prompt` | A flag to force the tool to prompt the user to provide their private key passphrase through standard input when authenticating with a public/private key pair.                                   | Do not prompt or read from standard input. |
| `-variable_file`               | The path to the variable property file.                                                                                                                                                          |                                            |
