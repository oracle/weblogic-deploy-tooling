---
title: "Deploy Applications Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 3
description: "Adds resources and applications to an existing domain, either in offline or online mode."
---

{{% notice note %}}
The Deploy Applications Tool is deprecated in WDT 4.0.0. For comparable functionality and more, use the
[Update Domain Tool]({{< relref "/userguide/tools/update.md" >}}).
{{% /notice %}}

The Deploy Applications Tool uses a model, the archive, and WLST to deploy applications and resources into an existing
WebLogic Server domain in either WLST online or offline mode.  When deploying applications and resources from a model,
the Deploy Applications Tool focuses primarily on the `resources` and `appDeployments` sections of the model.
There are exceptions for the `domainInfo` and `topology` sections, where those configuration elements are deemed to be
"application-related."  For example, the servers' `ServerStart` folder has an `Arguments` and a `ClassPath` attribute
that change the server environment (when started by the Node Manager) that applications may rely on to function properly.
Likewise, the `domainInfo` section contains a list of JAR files that are to be placed in `<DOMAIN_HOME>/lib` which are
relevant to applications for a similar reason.

Like the Update Domain Tool, the Deploy Applications Tool can be run in either offline or online mode, and online mode has
some options that control its behavior.

- offline mode - Offline mode uses WLST offline to read and update the domain configuration from the domain home
  directory.  This means that the tool must run on the same host as the domain's Administration Server and that the user
  running the tool needs full read and write access to the domain home directory structure.
- online mode - Online mode uses WLST online to read and update the domain configuration using the Administration
  Server's MBeans. The user running the tool needs to provide the administrative credentials and URL to connect to the
  Administration Server.  There are three options when running the tool:
  - Normal mode (default) - In this mode, the tool must run on the same host as the domain's Administration Server
    and the user running the tool must have full read and write access to the domain home directory structure, and
    full read access to any other locations where domain-specific files are stored.
  - `-remote` mode - This mode allows the tool to be run from a host other than the host where the domain's
    Administration Server is located.  Since the tool has no direct access to the file system of the host where the
    Administration Server is running, there are limitations:
    - Any attribute in the model that referenced a path into the archive file unless the path begins with
      `wlsdeploy/applications` or `wlsdeploy/sharedLibraries` will result in an error, as the tool cannot remotely
      create such directory or file.  For example, if you specify a `domainBin: [ wlsdeploy/domainBin/setUserOverrides.sh ]`
      which references a file entry in the archive file `wlsdeploy/domainBin/setUserOverrides.sh`, the tool will fail
      with an error.
    - Exploded format applications and shared libraries in the archive are not supported.  This is due to a limitation
      in the WebLogic Deploy subsystem where it only supports uploading a file, not a directory.
  - SSH mode - In this mode, the tool can be run from any host for which you have set up SSH connectivity between the
    host where WDT is running and the host where the Administration Server is running.  The `-ssh_user` (which, by
    default, is the same user running the tool) must have full read and write access to the domain home directory
    structure, and full read access to any other locations where domain-specific files are stored.  See the
    [SSH support]({{< relref "/userguide/tools/shared/ssh.md" >}}) and
    [Verify SSH Tool]({{< relref "/userguide/tools/verify_ssh.md" >}}) pages for more information about running in SSH
    mode.

The Deploy Applications Tool will only add or update elements in the specified model. It will not attempt to remove any
missing elements that are already present in the domain.  The Update Domain Tool will not attempt to recreate or add
schemas for the RCU database, for domain types that use RCU.

In WLST online mode, the tool tries to minimize the need to redeploy the applications and shared libraries, and the need
to restart the server.  It does this in a few ways:

- If the model references an application or shared library that is already deployed, the tool compares the binaries to
  determine whether redeployment is required.  Redeployment of shared libraries is particularly expensive since all
  applications using the shared library must be redeployed--even if the application has not changed.
- It looks at the knowledge base to determine which attributes require restart when they are changed.  If an attribute
  requires restart, the tool compares the current domain and model values to make sure that they are different before
  trying to apply a change.

The goal is to make the tool both able to support iterative deployment and able to minimize service disruption while
doing its work when working against a running domain.

#### Online update for shared libraries

When updating shared library online, it is recommended to deploy a new version of the library by updating the version(s)
in the MANIFEST.MF file and update the deployment descriptor of any application that wants to upgrade to use the new
library, this avoids complicated issues like in-place update of shared library.

In-place update of shared library online is not supported.  If you only update the library contents without updating the
version(s) of the library in the MANIFEST.MF file.  You will get an error from WebLogic Server indicating the library is
referenced by applications and cannot be undeployed. You must undeploy all applications referencing the shared library
first before proceeding; this is the same behavior when using the WebLogic Server console. Also, a shared library can
potentially be referenced by another shared library module which in turns used by other applications, currently there
is no capability within WebLogic Server to handle automating undeploy and deploy of an application that uses shared
library when the library is updated in-place.

#### Using output files

If the `-output_dir` command-line argument is specified, the tool will generate output files that provide information
about servers and resources that need to be restarted. These files are only applicable for online deployments.

For more information about these files, see [Using output files]({{< relref "/userguide/tools/update#using-output-files" >}})
for the Update Domain Tool.

#### Running the tool in offline mode

Running the Deploy Applications Tool in WLST offline mode is very similar to running the Update Domain Tool; simply
provide the domain location and archive file, and separate model and variable files, if needed.  For example:

    $ weblogic-deploy\bin\deployApps.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -model_file DemoDomain.yaml -variable_file DemoDomain.properties -archive_file DemoDomain.zip

#### Running the tool in online mode

In WLST online mode, simply remove the `-domain_home` argument and add the information on how to connect to the WebLogic
Server Administration Server.  Here is an example of running in online WLST mode from the admin server:

    $ weblogic-deploy\bin\deployApps.cmd -admin_url t3://127.0.0.1:7001 -admin_user weblogic -oracle_home c:\wls12213≈ -model_file DemoDomain.yaml -variable_file DemoDomain.properties -archive_file DemoDomain.zip

Here is an example of running the tool in `-remote` mode:

    $ weblogic-deploy\bin\deployApps.cmd -remote -admin_url t3://my.remote.machine:7001 -admin_user weblogic -oracle_home c:\wls12213 -model_file DemoDomain.yaml -variable_file DemoDomain.properties -archive_file DemoDomain.zip

Running in SSH mode looks very similar.  This example assumes that you have already set up and verified SSH connectivity
from the host where WDT is running to the host where the domain's Administration Server is running.  It also assumes that
the default values for the other SSH-related arguments are sufficient for your configuration.

    $ weblogic-deploy\bin\deployApps.cmd -ssh_host my.remote.machine -admin_url t3://my.remote.machine:7001 -admin_user weblogic -oracle_home c:\wls12213 -model_file DemoDomain.yaml -variable_file DemoDomain.properties -archive_file DemoDomain.zip

As usual, the tool will prompt for the password (it can also be supplied by piping it to standard input of the tool).
To bypass the prompt, you can use one of two options:
- Store the password in an environment variable, and use the variable name with command-line option `-admin_pass_env`.
- Store the password in a file. Provide the file name with command-line option `-admin_pass_file`.

When running the tool in WLST online mode, the deploy operation may require server restarts or a domain restart to pick
up the changes.  The deploy operation can also encounter situations where it cannot complete its operation until the
domain is restarted.  To communicate these conditions to scripts that may be calling the Deploy Applications Tool, the
shell scripts have two special, non-zero exit codes to communicate these states:

- `103` - The entire domain needs to be restarted.
- `104` - The domain changes have been canceled because the changes in the model requires a domain restart and `-cancel_changes_if_restart_required` is specified.

### Using an encrypted model

If the model or variables file contains passwords encrypted with the WDT Encrypt Model Tool, you must provide the
WDT encryption passphrase used to encrypt the model so that the Create Domain Tool can decrypt them.  To do this,
provide one of the following command-line arguments:

- `-passphrase_env <ENV_VAR>` - read the passphrase from the specified environment variable,
- `-passphrase_file <file-name>` - read the passphrase from a file that contains the passphrase, or
- `-passphrase_prompt` - have the tool read the passphrase from `stdin`, either by prompting or piping the value to
  the shell script's standard input.

### Using multiple models

The Deploy Applications Tool supports the use of multiple models, as described in
[Using multiple models]({{< relref "/concepts/model#using-multiple-models" >}}).

### Environment variables
The following environment variables may be set.

-  `JAVA_HOME`             The location of the JDK. This must be a valid Java 7 or later JDK.
-  `WLSDEPLOY_PROPERTIES`  System properties that will be passed to WLST.

{{% notice warning %}}
When running the Deploy Applications Tool (and any other tool that use WLST), the actual JDK used to run the tool
will be the JDK used to install WebLogic Server in the Oracle Home and not the one defined by the `JAVA_HOME`
environment variable.  The best practice is to set `JAVA_HOME` to point to the same JDK installation that was used to
install WebLogic Server.
{{% /notice %}}

### Opening an issue against the Deploy Applications Tool

Please provide the full console output of the tool (that is, what is printed to stdout and stderr) and the log file,
`deployApps.log`, which is typically found in the `<install home>/weblogic-deploy/logs` directory.  If possible,
please provide the model, variable and archive files, and any other information that helps to understand the
environment, what you are doing, and what is happening.  For example, when running in online mode and encountering an
error deploying an application, the domain's Administration Server log file will often be the key to understanding
the cause of the error.


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
| `-passphrase_prompt`                  | Allow WDT to prompt for the encryption passphrase or read it from stdin.                                                                                                                                                                                                                                 |    |
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
| `-use_encryption`                     | (deprecated) Replaced by the `-passphrase_prompt` argument.                                                                                                                                           |                                            |
| `-variable_file`                      | The location of the property file containing the values for variables used in the model. This can also be specified as a comma-separated list of property files, where each successive set of properties layers on top of the previous ones.                                            |                                            |
| `-wait_for_edit_lock`                 | Skip checks for active edit sessions and pending changes before trying to acquire the WLST online edit lock to modify domain configuration.                                                                                                                                             |                                            |
