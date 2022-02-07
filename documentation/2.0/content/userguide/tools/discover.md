---
title: "Discover Domain Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 4
description: "Introspects an existing domain and creates a model file describing the domain and an archive file of the binaries deployed to the domain."
---


The Discover Domain Tool provides a bootstrapping mechanism to creating a model and archive file by inspecting an existing domain and gathering configuration and binaries from it.  Note that the model file produced by the tool is not directly usable by the Create Domain Tool or the Deploy Applications Tool because the Discover Domain Tool does not discover the passwords from the existing domain.  Instead, it puts a `--FIX ME--` placeholder for passwords it finds.  Domain users are also not discoverable so the tool injects the same placeholder value in the `AdminUserName` and `AdminPassword` fields in the `domainInfo` section. The idea of this tool is simply to provide a starting point where the user can edit the generated model and archive file to suit their needs for running one of the other tools.

To run the Discover Domain Tool, simply provide the Oracle home and domain location. Provide a location and file name for the model file and archive file where the discovered domain information will be written. The model can be generated in either YAML or JSON format. Simply label the file name with the correct suffix. Both a sh and cmd script are provided.

Example of basic discoverDomain:

    $ weblogic-deploy\bin\discoverDomain.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DiscoveredDemoDomain.zip -model_file DiscoveredDemoDomain.yaml

When creating the archive, the tool will try to gather all binaries, scripts, and required directories referenced by the domain configuration with the following caveats.

1. Any binaries referenced from the `ORACLE_HOME` will not be gathered, as they are assumed to exist in any target domain to which model-driven operations will be applied.  Doing this is key to allowing the model to be WebLogic Server version independent.
2. In its current form, the Discover Domain Tool will only gather binaries and scripts that are accessible from the local machine.  Warnings will be generated for any binaries or scripts that cannot be found but the configuration for those binaries will still be collected, where possible.  It is the user's responsibility to add those missing files to the archive in the appropriate locations and edit the the model, as needed, to point to those files inside the archive using the relative path inside the archive (for example, `wlsdeploy/applications/myapp.ear`).
3. You can you run the Discover Domain Tool without generating an archive file if you wish to inspect the model file. A create or update domain requires a valid archive file for any binaries, scripts or directories that will be installed into the domain.

You can customize what is generated in the model for password attributes by providing a variable file location and name. This file is a text properties file which will contain a key=value for each password found in the model. The key is a unique token name for a password attribute, and the value is the replacement value; in this case, an empty string. The attribute in the model is injected with the token name and property field notation. For example, `@@PROP:AdminUserName@@` or `@@PROP:JDBCSystemResource.<Name>.JdbcResource.JDBCDriverParams.PasswordEncrypted@@`.

A command-line example containing the variable file name:

    $ weblogic-deploy\bin\discoverDomain.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DiscoveredDemoDomain.zip -model_file DiscoveredDemoDomain.json -variable_file DiscoverDemoDomain.properties

To discover the domain using online WLST, simply include the admin user name and admin URL on the command line. The tool will prompt for a password to be entered into STDIN. To bypass the prompt, you can use one of two options. Store the password in an environment variable, and use the variable name with command-line option `-admin_pass_env`. Store the password value in a file. Provide the file name with command-line option `-admin_pass_file`.

An example of running in online WLST mode:

    $ weblogic-deploy/bin/discoverDomain.sh -oracle_home /u01/oracle -domain_home /u01/oracle/domains/DemoDomain -archive_file ./DiscoveredDemoDomain.zip -model_file ./DiscoveredDemoDomain.yaml -admin_user weblogic -admin_url t3://localhost:7001

Note that the command must run on the same system where the domain binaries are located in order to successfully gather the corresponding binaries into the archive file.

When a domain is created using custom or product templates, the templates will install resources into the domain that do not need to be discovered for the model or collected into the archive. The domain type argument, which corresponds to a domain typedef file, must describe the type of domain in order for these resources and files to be ignored. By default, discover runs using domain type WLS, which assumes only the WebLogic Server template was applied to the domain. The tool has canned typedefs for two other domain types, RestrictedJRF and JRF. You may use these domain types, or another custom typedef. For more information, refer to [Domain type definitions]({{< relref "/userguide/tools-config/domain_def.md" >}}).

An example of using the domain type argument:

    $ weblogic-deploy\bin\discoverDomain.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DiscoveredDemoDomain.zip -model_file DiscoveredDemoDomain.yaml -domain_type RestrictedJRF

Before the model is persisted to the model file, any variable injectors or model filters are run, in that order. The final step is validation, which validates the contents of the model, archive and variable file. If the validation is successful, the model is persisted. For more information on these three topics, see:

 - [Variable injection]({{< relref "/userguide/tools/variable_injection.md" >}})
 - [Model filters]({{< relref "/userguide/tools-config/model_filters.md" >}})
 - [Validate Model Tool]({{< relref "/userguide/tools/validate.md" >}})


The resulting model can also be modified for compatibility with specific target environments, such as Oracle WebLogic Server Kubernetes Operator. For more information, see [Target environments]({{< relref "/userguide/target_env.md" >}}).

Any problems (or success) will be listed in the Discover Domain Tool summary. The summary will print the version of the tool and Oracle home, and the WLST mode with which the tool was run (online or offline). A recap of all Warning and Severe messages will be listed, along with a total.


An example of a summary with a WARNING message:

```
Issue Log for discoverDomain version 1.5.2-SNAPSHOT running WebLogic version 10.3.6.0 offline mode:

WARNING Messages:

        1. WLSDPLY-06200: Unable to get the Security Realm Provider name in version 10.3.6.0 with offline wlst. The SecurityConfiguration will not be added to the model. The work-around is to manually add the Security Configuration to the model or to discover the domain in online mode : Invalid Security Provider name "Provider" found for provider type at location /SecurityConfiguration/Realm/Adjudicator.

Total:       WARNING :     1    SEVERE :     0
```

### Environmental variables
The following environment variables may be set.

-  `JAVA_HOME`             The location of the JDK. This must be a valid Java 7 or later JDK.
-  `WLSDEPLOY_HOME`        The location of the WebLogic Deploy Tooling installation. By default, the location is calculated
                         from the location of the `discoverDomain` script.
-  `WLSDEPLOY_PROPERTIES`  System properties that will be passed to WLST.

### Opening an issue against Discover Domain

Please provide the `STDOUT` and `STDERR` log streams in the GitHub Issue. If the summary is not listed (unhandled exception stack trace occurs), be sure and include the Oracle and WDT installation versions and whether the tool was run in online or offline WLST mode. If possible, provide the model, variable and archive files, and the log file, `discoverDomain.log`, from location `<install home>\weblogic-deploy\log`.

### Parameter table for `discoverDomain`
| Parameter | Definition | Default |
| ---- | ---- | ---- |
| `-archive_file` | The path to the archive file. |    |
| `-admin_pass_env` | An alternative to entering the admin password at a prompt. The value is an environment variable name that WDT will use to retrieve the password. |    |
| `-admin_pass_file` | An alternative to entering the admin password at a prompt. The value is a the name of a file that contains a password string that the tool will read to retrieve the password. |    |
| `-admin_url` | The admin server URL used for online discovery. |    |
| `-admin_user` | The admin user used for online discovery. |    |
| `-domain_home` | (Required). The location of the existing domain home. |    |
| `-domain_type` | The type of domain.  (for example, `WLS`, `JRF`) | `WLS` |
| `-java_home` | Overrides the `JAVA_HOME`  value when discovering domain values to be replaced with the Java home global token. |    |
| `-model_file` | The path to the model file. If not present, model file will be stored in archive file. |    |
| `-oracle_home` | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set. |    |
| `-output_dir` | Output directory required for `-target`. |    |
| `-skip_archive` | Do not generate an archive file. The `-archive_file` option will be ignored. |    |
| `-target` | Targeting platform - `k8s`, `wko`, `vz`. |    |
| `-variable_file` | The location to write properties for attributes that have been replaced with tokens by the variable injector. If this is included, all credentials will automatically be replaced by tokens and the property written to this file. |    |
