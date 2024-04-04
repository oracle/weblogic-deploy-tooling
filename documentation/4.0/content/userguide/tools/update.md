---
title: "Update Domain Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
description: "Updates an existing domain and populates the domain with all the resources and applications specified in the model, either in offline or online mode."
---


The Update Domain Tool uses a model, the archive, and WLST to update the configuration of an existing WebLogic Server domain, and to deploy applications and resources into the domain in either WLST online or offline mode.  The Update Domain Tool will add or re-configure elements from the `topology` section of the model, and deploy applications and resources from the `resources` and `appDeployments` sections, as described in the Deploy Applications Tool.

The Update Domain Tool will only add or update elements in the specified model. It will not attempt to remove any missing elements that were present in a previous model.

Running the Update Domain Tool in WLST offline mode is very similar to running the Create Domain Tool; simply provide the domain location and archive file, and separate model and variable files, if needed.  For example:

    $ weblogic-deploy\bin\updateDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties

You can use online mode either on the admin server or from a remote machine.  If you are running from the admin server, you can specify domain home directory `-domain_home` location.

If you are running from a remote machine, then you do not need to specify the domain home directory `-domain_home` option,  but there is are limitations:

- Any attribute in the model that referenced a path into the archive file unless the path begins with `wlsdeploy/applications` or `wlsdeploy/sharedLibraries` will result in an error, as the tool cannot remotely
  create such directory or file.  For example, if you specify a `domainBin: [ wlsdeploy/domainBin/setUserOverrides.sh]` which references a file entry in the archive file `wlsdeploy/domainBin/setUserOverrides.sh`,
  the tool will fail with an error.
- Exploded format application specified in the archive is not supported

In WLST online mode, simply add the information on how to connect to the WebLogic Server Administration Server, for example:

    $ weblogic-deploy\bin\updateDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties -admin_url t3://127.0.0.1:7001 -admin_user weblogic

or from a remote machine

    $ weblogic-deploy\bin\updateDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -remote -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties -admin_url t3://127.0.0.1:7001 -admin_user weblogic

As usual, the tool will prompt for the password (it can also be supplied by piping it to standard input of the tool). To bypass the prompt, you can use one of two options. Store the password in an environment variable, and use the variable name with command-line option `-admin_pass_env`. Store the password in a file. Provide the file name with command-line option `-admin_pass_file`.

Unlike the Create Domain Tool, the full domain home directory is specified, rather than the domain's parent directory, because the domain has already been established.

The Update Domain Tool will not attempt to recreate or add schemas for the RCU database, for domain types that use RCU.

When running the tool in WLST online mode, the update operation may require server restarts or a domain restart to pick up the changes.  The update operation can also encounter situations where it cannot complete its operation until the domain is restarted.  To communicate these conditions to scripts that may be calling the Update Domain Tool, the shell scripts have two special, non-zero exit codes to communicate these states:

- `103` - The entire domain needs to be restarted.
- `104` - The domain changes have been canceled because the changes in the model requires a domain restart and `-cancel_changes_if_restart_required` is specified.

### Online update for shared libraries

- When updating shared library online, it is recommended to deploy a new version of the library by updating the 
  version(s) in the MANIFEST.MF file and update the deployment descriptor of any application that wants to upgrade to 
  use the new library, this avoids complicated issues like in-place update of shared 
  library.

- In-place update of shared library online is not supported - if you only 
  update the library contents without updating the version(s) of the library in the MANIFEST.MF file.  You will get an error 
  from WebLogic Server indicating the library is referenced by applications and cannot be undeployed. You must undeploy 
  all applications referencing the shared library first before proceeding; this is the same behavior when using the 
  WebLogic Server console. Also, a shared library can potentially be referenced by another 
  shared library module which in turns used by other applications, currently there is no capability within 
  WebLogic Server to handle automating undeploy and deploy of an application that uses shared library when the library is 
  updated in-place.  

### Using output files

If the `-output_dir` command-line argument is specified, the tool will generate output files that provide information about servers and resources that need to be restarted. These files are only applicable for online deployments.

The file `restart.file` contains a list of servers and resources that need to be restarted. Here is an example:
```text
:AdminServer:Generic1:JDBCSystemResource
:AdminServer::
```

The file `non_dynamic_changes.file` contains text describing the attributes that will require a restart in order for new values to be applied. Here is an example:
```text
Server re-start is REQUIRED for the set of changes in progress.

The following non-dynamic attribute(s) have been changed on MBeans 
that require server re-start:
MBean Changed : com.bea:Name=AdminServer,Type=Log,Server=AdminServer
Attributes changed : RedirectStderrToServerLogEnabled, RedirectStdoutToServerLogEnabled

MBean Changed : com.bea:Name=MailSession-0,Type=MailSession
Attributes changed : SessionPasswordEncrypted
```

The file `results.json` contains information about servers and resources need to be restarted, and attribute values that require a restart in order for new values to be applied.
```json
{
    "nonDynamicChanges" : {
        "com.bea:Name=MailSession-0,Type=MailSession" : [
            "SessionPasswordEncrypted"
        ],
        "com.bea:Name=AdminServer,Type=Log,Server=AdminServer" : [
            "RedirectStderrToServerLogEnabled",
            "RedirectStdoutToServerLogEnabled"
        ]
    },
    "nonDynamicChangesText" : [
        "",
        "Server re-start is REQUIRED for the set of changes in progress.",
        "",
        "The following non-dynamic attribute(s) have been changed on MBeans",
        "that require server re-start:",
        "MBean Changed : com.bea:Name=AdminServer,Type=Log,Server=AdminServer",
        "Attributes changed : RedirectStderrToServerLogEnabled, RedirectStdoutToServerLogEnabled",
        "",
        "MBean Changed : com.bea:Name=MailSession-0,Type=MailSession",
        "Attributes changed : SessionPasswordEncrypted",
        ""
    ],
    "restarts" : [
        {
            "server" : "AdminServer",
            "resourceName" : "Generic1",
            "resourceType" : "JDBCSystemResource"
        },
        {
            "server" : "AdminServer"
        }
    ]
}
```

### Using an encrypted model

If the model or variables file contains passwords encrypted with the WDT Encryption tool, decrypt the passwords during create with the `-use_encryption` flag on the command line to tell the Update Domain Tool that encryption is being used and to prompt for the encryption passphrase.  As with the database passwords, the tool can also read the passphrase from standard input (for example, `stdin`) to allow the tool to run without any user input. You can bypass the stdin prompt with two other options. Store the passphrase in an environment variable, and use the environment variable name with command-line option `-passphrase_env`. Another option is to create a file containing the passphrase value. Pass this filename with the command-line option `-passphrase_file`.

### Using multiple models

The Update Domain Tool supports the use of multiple models, as described in [Using multiple models]({{< relref "/concepts/model#using-multiple-models" >}}).

### Parameter table for `updateDomain`
| Parameter                             | Definition                                                                                                                                                                                                                                                                                            | Default                                    |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `-admin_pass_env`                     | An alternative to entering the admin password at a prompt. The value is an environment variable name that WDT will use to retrieve the password.                                                                                                                                                      |                                            |
| `-admin_pass_file`                    | An alternative to entering the admin password at a prompt. The value is a the name of a file that contains a password string that the tool will read to retrieve the password.                                                                                                                        |                                            |
| `-admin_url`                          | The admin server URL for online update.                                                                                                                                                                                                                                                               |                                            |
| `-admin_user`                         | The admin user name for online update.                                                                                                                                                                                                                                                                |                                            |
| `-archive_file`                       | The path to the archive file to use. If the `-model_file` argument is not specified, the model file in this archive will be used. This can also be specified as a comma-separated list of archive files. The overlapping contents in each archive take precedence over previous archives in the list. |                                            |
| `-cancel_changes_if_restart_required` | Cancel the changes if the update requires domain restart.                                                                                                                                                                                                                                             |                                            |
| `-discard_current_edit`               | Discard all existing domain edits before the update.                                                                                                                                                                                                                                                  |                                            |
| `-domain_home`                        | (Required for offline mode) The location of the existing local domain home.                                                                                                                                                                                                                           | For online mode, the server's value.       |
| `-domain_type`                        | The type of domain.  (for example, `WLS`, `JRF`)                                                                                                                                                                                                                                                      | `WLS`                                      |
| `-model_file`                         | The location of the model file. This can also be specified as a comma-separated list of model locations, where each successive model layers on top of the previous ones.                                                                                                                              |                                            |
| `-oracle_home`                        | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set.                                                                                                                                                                                    |                                            |
| `-passphrase_env`                     | An alternative to entering the encryption passphrase at a prompt. The value is an environment variable name that WDT will use to retrieve the passphrase.                                                                                                                                             |                                            |
| `-passphrase_file`                    | An alternative to entering the encryption passphrase at a prompt. The value is a the name of a file with a string value which WDT will read to retrieve the passphrase.                                                                                                                               |                                            |
| `-update_dir`                         | If specified, files containing restart information are written to this directory, including `restart.file`, `non_dynamic_changes.file`, and `results.json`.                                                                                                                                           |                                            |
| `-use_encryption`                     | One or more of the passwords in the model or variables file(s) are encrypted and must be decrypted. Java 8 or later required for this feature.                                                                                                                                                        |                                            |
| `-variable_home`                      | The location of the property file containing the values for variables used in the model. This can also be specified as a comma-separated list of property files, where each successive set of properties layers on top of the previous ones.                                                          |                                            |
| `-wait_for_edit_lock`                 | Skip checks for active edit sessions and pending changes before trying to acquire the WLST online edit lock to modify domain configuration.                                                                                                                                                           |                                            |
| `-remote`                             | Update the domain from a remote machine.                                                                                                                                                                                                                                                              |                                            |
| `-ssh_host`                           | The DNS name or IP address of the remote host.                                                                                                                                                                                                                                                        |                                            |
| `-ssh_port`                           | The TCP port on the remote host where the sshd daemon is listening for connection requests.                                                                                                                                                                                                           | `22`                                       |
| `-ssh_user`                           | The user name on the remote host to use for authentication purposes.                                                                                                                                                                                                                                  | Same as the local user running the tool.   |
| `-ssh_pass_env`                       | The environment variable name to use to retrieve the remote user's password when authenticating with user name and password.                                                                                                                                                                          |                                            |
| `-ssh_pass_file`                      | The file name of a file that contains the password string for the remote user's password when authenticating with user name and password.                                                                                                                                                             |                                            |
| `-ssh_pass_prompt`                    | A flag to force the tool to prompt the user to provide the remote user's password through standard input when authenticating with user name and password.                                                                                                                                             | Do not prompt or read from standard input. |
| `-ssh_private_key`                    | The local file name of the user's private key file to use when authenticating with a public/private key pair.                                                                                                                                                                                         | `$HOME/.ssh/id_rsa`                        |                                                                                       
| `-ssh_private_key_pass_env`           | The environment variable name to use to retrieve user's private key passphrase when authenticating with a public/private key pair.                                                                                                                                                                    |                                            |
| `-ssh_private_key_pass_file`          | The file name of a file that contains the user's private key passphrase string when authenticating with a public/private key pair.                                                                                                                                                                    |                                            |
| `-ssh_private_key_pass_prompt`        | A flag to force the tool to prompt the user to provide their private key passphrase through standard input when authenticating with a public/private key pair.                                                                                                                                        | Do not prompt or read from standard input. |
