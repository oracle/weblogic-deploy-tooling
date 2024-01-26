---
title: "Deploy Applications Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 3
description: "Adds resources and applications to an existing domain, either in offline or online mode."
---

{{% notice note %}}
The Deploy Applications Tool is deprecated in WDT 4.0.0. For comparable functionality and more, use the [Update Domain Tool]({{< relref "/userguide/tools/update.md" >}}).
{{% /notice %}}

The Deploy Applications Tool uses a model, the archive, and WLST to deploy applications and resources into an existing WebLogic Server domain in either WLST online or offline mode.  When deploying applications and resources from a model, the Deploy Applications Tool focuses primarily on the `resources` and `appDeployments` sections of the model.  There are exceptions for the `domainInfo` and `topology` sections, where those configuration elements are deemed to be "application-related."  For example, the servers' `ServerStart` folder has an `Arguments` and a `ClassPath` attribute that change the server environment (when started by the Node Manager) that applications may rely on to function properly.  Likewise, the `domainInfo` section contains a list of JAR files that are to be placed in `<DOMAIN_HOME>/lib` which are relevant to applications for a similar reason.

The Deploy Applications Tool will only add or update elements in the specified model. It will not attempt to remove any missing elements that were present in a previous model.

In WLST online mode, the tool tries to minimize the need to redeploy the applications and shared libraries, and the need to restart the server.  It does this in a few ways:

- If the model references an application or shared library that is already deployed, the tool compares the binaries to determine whether redeployment is required.  Redeployment of shared libraries is particularly expensive since all applications using the shared library must be redeployed--even if the application has not changed.
- It looks at the knowledge base to determine which attributes require restart when they are changed.  If an attribute requires restart, the tool compares the current and model values to make sure that they are different before trying to apply a change.

The goal is to make the tool both able to support iterative deployment and able to minimize service disruption while doing its work when working against a running domain.

Running the Deploy Applications Tool in WLST offline mode is very similar to running the Create Domain Tool; simply provide the domain location and archive file, and separate model and variable files, if needed.  For example:

    $ weblogic-deploy\bin\deployApps.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties

You can use online mode either on the admin server or from a remote machine.  If you are running from the admin server, you can specify domain home directory `-domain_home` location.

If you are running from a remote machine with `-remote` option, then you do not need to specify the domain home directory `-domain_home` option.

To run the tool in online mode, add the `-admin_url` and `-admin_user` arguments with the necessary values to connect to the WebLogic Server Administration Server. For example:

    $ weblogic-deploy\bin\deployApps.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties -admin_url t3://127.0.0.1:7001 -admin_user weblogic

or if running from a remote machine

    $ weblogic-deploy\bin\deployApps.cmd -oracle_home c:\wls12213 -remote -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties -admin_url t3://127.0.0.1:7001 -admin_user weblogic

If you are running from a remote machine, then you do not need to specify the domain home directory `-domain_home` option,  but there are limitations:

- Any attribute in the model that referenced a path into the archive file unless the path begins with `wlsdeploy/applications` or `wlsdeploy/sharedLibraries` will result in an error, as the tool cannot remotely
  create such directory or file.  For example, if you specify a `domainBin: [ wlsdeploy/domainBin/setUserOverrides.sh]` which references a file entry in the archive file `wlsdeploy/domainBin/setUserOverrides.sh`,
  the tool will fail with an error.
- Exploded format application specified in the archive is not supported
-
As usual, the tool will prompt for the password (it can also be supplied by piping it to standard input of the tool). To bypass the prompt, you can use one of two options. Store the password in an environment variable, and use the variable name with command-line option `-admin_pass_env`. Store the password in a file. Provide the file name with command-line option `-admin_pass_file`.

When running the tool in WLST online mode, the deploy operation may require server restarts or a domain restart to pick up the changes.  The deploy operation can also encounter situations where it cannot complete its operation until the domain is restarted.  To communicate these conditions to scripts that may be calling the Deploy Applications Tool, the shell scripts have three special, non-zero exit codes to communicate these states:

- `103` - The entire domain needs to be restarted.
- `104` - The domain changes have been canceled because the changes in the model requires a domain restart and `-cancel_changes_if_restart_required` is specified.


### Using output files

If the `-output_dir` command-line argument is specified, the tool will generate output files that provide information about servers and resources that need to be restarted. These files are only applicable for online deployments.

For more information about these files, see [Using output files]({{< relref "/userguide/tools/update#using-output-files" >}}) for the Update Domain Tool.


### Using an encrypted model

If the model or variables file contains passwords encrypted with the WDT Encryption tool, decrypt the passwords during create with the `-use_encryption` flag on the command line to tell the Deploy Applications Tool that encryption is being used and to prompt for the encryption passphrase.  As with the database passwords, the tool can also read the passphrase from standard input (for example, `stdin`) to allow the tool to run without any user input. You can bypass the stdin prompt with two other options. Store the passphrase in an environment variable, and use the environment variable name with command-line option `-passphrase_env`. Another option is to create a file containing the passphrase value. Pass this filename using the command-line option `-passphrase_file`.


### Using multiple models

The Deploy Applications Tool supports the use of multiple models, as described in [Using multiple models]({{< relref "/concepts/model#using-multiple-models" >}}).

### Parameter table for `deployApps`
| Parameter                             | Definition                                                                                                                                                                                                                                                                              | Default                                    |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `-admin_pass_env`                     | An alternative to entering the admin password at a prompt. The value is an environment variable name that WDT will use to retrieve the password.                                                                                                                                        |                                            |
| `-admin_pass_file`                    | An alternative to entering the admin password at a prompt. The value is the name of a file that contains a password string that the tool will read to retrieve the password.                                                                                                            |                                            |
| `-admin_url`                          | The admin server URL used for online deploy.                                                                                                                                                                                                                                            |                                            |
| `-admin_user`                         | The admin user name used for online deploy.                                                                                                                                                                                                                                             |                                            |
| `-archive_file`                       | The path to the archive file. If the `-model_file` argument is not used, the model file in this file will be used. This can also be specified as a comma-separated list of archive files.  The overlapping contents in each archive take precedence over previous archives in the list. |                                            |
| `-cancel_changes_if_restart_required` | Cancel the changes if the update requires a domain restart.                                                                                                                                                                                                                             |                                            |
| `-discard_current_edit`               | Discard all current domain edits before starting the update.                                                                                                                                                                                                                            |                                            |
| `-domain_home`                        | (Required for offline mode). The location of the existing domain home.                                                                                                                                                                                                                  | For online mode, the server's value.       |
| `-domain_type`                        | The type of domain.  (for example, `WLS`, `JRF`)                                                                                                                                                                                                                                        | `WLS`                                      |
| `-model_file`                         | The location of the model file. This can also be specified as a comma-separated list of model locations, where each successive model layers on top of the previous ones.                                                                                                                |                                            |
| `-oracle_home`                        | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set.                                                                                                                                                                      |                                            |
| `-output_dir`                         | If specified, files containing restart information are written to this directory, including `restart.file`, `non_dynamic_changes.file`, and `results.json`.                                                                                                                             |                                            |
| `-passphrase_env`                     | An alternative to entering the encryption passphrase at a prompt. The value is an environment variable name that WDT will use to retrieve the passphrase.                                                                                                                               |                                            |
| `-passphrase_file`                    | An alternative to entering the encryption passphrase at a prompt. The value is the name of a file with a string value which WDT will read to retrieve the passphrase.                                                                                                                   |                                            |
| `-use_encryption`                     | One or more of the passwords in the model or variables file(s) are encrypted and must be decrypted. Java 8 or later is required for this feature.                                                                                                                                       |                                            |
| `-variable_file`                      | The location of the property file containing the values for variables used in the model. This can also be specified as a comma-separated list of property files, where each successive set of properties layers on top of the previous ones.                                            |                                            |
| `-wait_for_edit_lock`                 | Skip checks for active edit sessions and pending changes before trying to acquire the WLST online edit lock to modify domain configuration.                                                                                                                                             |                                            |
| `-remote`                             | Deploy main from a remote machine.                                                                                                                                                                                                                                                      |                                            |
| `-ssh_host`                           | The DNS name or IP address of the remote host.                                                                                                                                                                                                                                          |                                            |
| `-ssh_port`                           | The TCP port on the remote host where the sshd daemon is listening for connection requests.                                                                                                                                                                                             | `22`                                       |
| `-ssh_user`                           | The user name on the remote host to use for authentication purposes.                                                                                                                                                                                                                    | Same as the local user running the tool.   |
| `-ssh_pass_env`                       | The environment variable name to use to retrieve the remote user's password when authenticating with user name and password.                                                                                                                                                            |                                            |
| `-ssh_pass_file`                      | The file name of a file that contains the password string for the remote user's password when authenticating with user name and password.                                                                                                                                               |                                            |
| `-ssh_pass_prompt`                    | A flag to force the tool to prompt the user to provide the remote user's password through standard input when authenticating with user name and password.                                                                                                                               | Do not prompt or read from standard input. |
| `-ssh_private_key`                    | The local file name of the user's private key file to use when authenticating with a public/private key pair.                                                                                                                                                                           | `$HOME/.ssh/id_rsa`                        |                                                                                       
| `-ssh_private_key_pass_env`           | The environment variable name to use to retrieve user's private key passphrase when authenticating with a public/private key pair.                                                                                                                                                      |                                            |
| `-ssh_private_key_pass_file`          | The file name of a file that contains the user's private key passphrase string when authenticating with a public/private key pair.                                                                                                                                                      |                                            |
| `-ssh_private_key_pass_prompt`        | A flag to force the tool to prompt the user to provide their private key passphrase through standard input when authenticating with a public/private key pair.                                                                                                                          | Do not prompt or read from standard input. |
