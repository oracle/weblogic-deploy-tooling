---
title: "Verify SSH Tool"
date: 2024-01-02T09:19:24-05:00
draft: false
weight: 13
description: "Verifies the SSH configuration and arguments."
---

With the Verify SSH Tool, you can verify that an SSH connection can be successfully established by WDT and optionally,
if files can be transferred between the machines using the provided arguments.  Before running the Verify SSH Tool, you
must ensure you have performed the [SSH Prerequisites]({{< relref "/userguide/tools/shared/ssh#ssh-prerequisites" >}}).

### Public/private key authentication

To verify SSH connectivity using a user's public/private key for authentication, simply provide the user name on the
remote machine and the user's private key file, as needed.  The Verify SSH Tool (and other WDT tools that support SSH)
have a reasonable set of defaults for every SSH-related command-line parameter except the remote SSH host.  For example,
if the local and remote user name is the same, the user's private key is in `$HOME/.ssh/id_rsa`, and the user's private
key has no passphrase, simply run the Verify SSH Tool as shown.

```shell
./weblogic-deplog/bin/verifySSH.sh -oracle_home $MW_HOME -ssh_host remote-machine.mycorp.io
...
Issue Log for verifySSH version 4.0.0 running WebLogic version 12.2.1.4.0.210930 in offline mode:

Total:   SEVERE :    0  WARNING :    0

verifySSH.sh completed successfully (exit code = 0) 
```

If the user's private key has a passphrase assigned, simply provide the private key passphrase using one of the
supported parameters.  For example, to pipe the passphrase to standard input, use the `-ssh_private_key_prompt`
parameter as shown.

```shell
echo 'Welcome1' | ./weblogic-deplog/bin/verifySSH.sh -oracle_home $MW_HOME -ssh_host remote-machine.mycorp.io -ssh_private_key_pass_prompt
```

If the remote user name is different than the local user name, simply use the `-ssh_user` parameter to specify the
remote user name as shown.

```shell
./weblogic-deplog/bin/verifySSH.sh -oracle_home $MW_HOME -ssh_host remote-machine.mycorp.io -ssh_user robertpatrick
```

### User name and password authentication
To verify SSH connectivity using a user name and password for authentication, simply provide the user name on the
remote machine and the user's password using one of the supported parameters.  For example, to read password from a file,
use the `-ssh_pass_file` parameter as shown.

```shell
./weblogic-deplog/bin/verifySSH.sh -oracle_home $MW_HOME -ssh_host remote-machine.mycorp.io -ssh_user robertpatrick -ssh_pass_file /path/to/password/file.txt
```

### Testing file upload and download

An SSH connection typically is sufficient to download a remote file or upload a local file to the remote system provided
that the local and remote users have the necessary file system permissions.  The Verify SSH tool allows you to optionally
test uploading or downloading a file.  For example, to test file upload, run `verifySSH` as shown.

```shell
./weblogic-deplog/bin/verifySSH.sh -oracle_home $MW_HOME -ssh_host remote-machine.mycorp.io -local_test_file /path/to/local/file.txt -remote_output_dir /tmp
```

To test file download, run `verifySSH` as shown.

```shell
./weblogic-deplog/bin/verifySSH.sh -oracle_home $MW_HOME -ssh_host remote-machine.mycorp.io -remote_test_file /path/to/remote/file.txt -local_output_dir /tmp
```

### Parameter table for `verifySSH`
| Parameter                      | Definition                                                                                                                                                     | Default                                    |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `-oracle_home`                 | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set.                                             |                                            |
| `-ssh_host`                    | The DNS name or IP address of the remote host.                                                                                                                 |                                            |
| `-ssh_port`                    | The TCP port on the remote host where the sshd daemon is listening for connection requests.                                                                    | `22`                                       |
| `-ssh_user`                    | The user name on the remote host to use for authentication purposes.                                                                                           | Same as the local user running the tool.   |
| `-ssh_pass_env`                | The environment variable name to use to retrieve the remote user's password when authenticating with user name and password.                                   |                                            |
| `-ssh_pass_file`               | The file name of a file that contains the password string for the remote user's password when authenticating with user name and password.                      |                                            |
| `-ssh_pass_prompt`             | A flag to force the tool to prompt the user to provide the remote user's password through standard input when authenticating with user name and password.      | Do not prompt or read from standard input. |
| `-ssh_private_key`             | The local file name of the user's private key file to use when authenticating with a public/private key pair.                                                  | `$HOME/.ssh/id_rsa`                        |                                                                                       
| `-ssh_private_key_pass_env`    | The environment variable name to use to retrieve user's private key passphrase when authenticating with a public/private key pair.                             |                                            |
| `-ssh_private_key_pass_file`   | The file name of a file that contains the user's private key passphrase string when authenticating with a public/private key pair.                             |                                            |
| `-ssh_private_key_pass_prompt` | A flag to force the tool to prompt the user to provide their private key passphrase through standard input when authenticating with a public/private key pair. | Do not prompt or read from standard input. |
| `-remote_test_file`            | The file name of a remote file to download to the local output directory during the verification process.                                                      |                                            | 
| `-local_output_dir`            | The local directory name to use to write the remote test file being downloaded during the verification process.                                                |                                            | 
| `-local_test_file`             | The file name of a local file to upload to the remote output directory during the verification process.                                                        |                                            | 
| `-remote_output_dir`           | The remote directory name to use to write the local test file being uploaded during the verification process.                                                  |                                            | 
