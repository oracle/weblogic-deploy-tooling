---
title: "Validate Model Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 6
description: "Provides both standalone validation of a model as well as model usage information to help users write or edit their models."
---


When working with a metadata model that drives tooling, it is critical to make it easy both to validate that the model and its related artifacts are well-formed and to provide help on the valid attributes and subfolders for a particular model location.  The Validate Model Tool provides both validation and help for model authors as a standalone tool.  In addition, the tool is integrated with the `createDomain` and `deployApps` tools to catch validation errors early, before any actions are performed on the domain.

To use the Validate Model Tool, simply run the `validateModel` shell script with the correct arguments.  To see the list of valid arguments for any tool in the WebLogic Deploy Tooling installation, simply run the shell script with the `-help` option (or with no arguments) to see the shell script usage information.

For example, starting with the following model shown below, where the `AdminServer` attribute `Machine` is misspelled as `Machines`:

```yaml
topology:
    Name: DemoDomain
    AdminServerName: AdminServer
    Cluster:
        mycluster:
    Server:
        AdminServer:
            ListenAddress: 192.168.1.50
            ListenPort: 7001
            Machines: machine1
            SSL:
                Enabled: true
                ListenPort: 7002
            ServerStart:
                ClassPath: c:\foo\bar
        m1:
            ListenAddress: 192.168.1.50
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine1
            ServerStart:
                ClassPath: c:\foo\bar
        m2:
            ListenAddress: 192.168.1.51
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine2
            ServerStart:
                ClassPath: c:\foo\bar
    Machine:
        machine1:
            NodeManager:
                ListenAddress: 192.168.1.50
                ListenPort: 5556
        machine2:
            NodeManager:
                ListenAddress: 192.168.1.51
                ListenPort: 5556
```

To validate the standalone model file, run the tool as follows:

    $ weblogic-deploy\bin\validateModel.cmd -oracle_home c:\wls12213 -model_file InvalidDemoDomain.yaml

The output of the tool will look something like this:

    -----------------------------------------------
    Validation Area: topology Section
    -----------------------------------------------

      Errors: 1
        Message: Machines is not one of the folder, folder instance or attribute names allowed in model location topology:/Server/AdminServer

Use the [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}) to determine the valid list of attributes and folders at this model location.

If the model contains variable definitions and the variable file or files is specified, the Validate Model Tool will validate that all variable references in the model are defined in the variable files.  For example, invoking the tool as shown here:

    $ weblogic-deploy\bin\validateModel.cmd -oracle_home c:\wls12213 -model_file InvalidDemoDomain.yaml -variable_file InvalidDemoDomain.properties

Results in output similar to that shown below, if the `db.password` variable is not defined in the variable file.

    -----------------------------------------------
    Validation Area: Variable Substitutions
    -----------------------------------------------

      Errors: 2
        Message: Model location resource:/JDBCSystemResource/Generic1/JdbcResource/JDBCDriverParams/PasswordEncrypted references variable db.password that is not defined in D:/demo/InvalidDemoDomain.properties
        Message: Model location resource:/JDBCSystemResource/Generic2/JdbcResource/JDBCDriverParams/PasswordEncrypted references variable db.password that is not defined in D:/demo/InvalidDemoDomain.properties

If the model references binaries that should be present in the archive, the Validate Model Tool will validate that all binary references in the model that point to archive file locations are present in the archive file.  For example, invoking the tool as shown here:

    $ weblogic-deploy\bin\validateModel.cmd -oracle_home c:\wls12213 -model_file InvalidDemoDomain.yaml -archive_file InvalidDemoDomain.zip

Results in output similar to that shown below, if the `simpleear.ear` file is not in the model-specified location inside the archive file.

    -----------------------------------------------
    Validation Area: Archive Entries
    -----------------------------------------------

      Errors: 1
        Message: Model location appDeployments:/Application/simpleear/SourcePath references file wlsdeploy/applications/simpleear.ear that is not found in the archive file D:/demo/InvalidDemoDomain.zip

### Using multiple models

The Validate Model Tool supports the use of multiple models, as described in [Using multiple models]({{< relref "/concepts/model#using-multiple-models" >}}).

### Parameter table for `validateModel`
| Parameter | Definition | Default |
| ---- | ---- | ---- |
| `-archive_file` | The path to the archive file to use.  If the archive file is not provided, validation will only validate the artifacts provided.  This can also be specified as a comma-separated list of archive files.  The overlapping contents in each archive take precedence over previous archives in the list. |    |
| `-domain_type` | The type of domain.  (for example, `WLS`, `JRF`) | `WLS` |
| `-model_file` | The location of the model file to use.  This can also be specified as a comma-separated list of model locations, where each successive model layers on top of the previous ones. If not specified, the tool will look for the model in the archive. If the model is not found, validation will only validate the artifacts provided. |    |
| `-oracle_home` | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set. |    |
| `-target_mode` | The target WLST mode that the tool should use to validate the model content.  The only valid values are `online` or `offline`. | `offline` |
| `-target_version` | The target version of WebLogic Server the tool should use to validate the model content.  This version number can be different than the version being used to run the tool.  | Oracle home version   |
| `-variable_file` | The location of the property file containing the variable values for all variables used in the model. If the variable file is not provided, validation will only validate the artifacts provided. |    |
