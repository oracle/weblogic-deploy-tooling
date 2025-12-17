---
title: "SSH support"
date: 2023-12-22T09:36:00-05:00
draft: false
weight: 2
description: "Describes WDT tooling SSH support."
---

WDT 4.0 introduces the ability to perform online operations remotely using SSH to provide access to the remote
server's file system.  SSH support is provided by the SSHJ Java library and is integrated in a way intended to support
a both user/password-based and private/public key-based authentication, a wide variety of key encryption formats, and
a reasonable set of defaults to minimize the number of inputs required for typical usage scenarios.  

### SSH prerequisites 
WDT does not attempt to configure SSH between the machines.  As such, you must ensure that SSH is working between
the machines in question and have made an initial SSH connection outside WDT as the user that WDT will use.  This
ensures that any necessary SSH configuration files (for example, the `known_hosts` file on the client and the `authorized_keys`
file on the server) are properly initialized to allow the SSH connection between the machines to be established.

### SSH verification
The Verify SSH Tool will allow the user to verify that SSH is working properly for use by WDT.  For example, to verify
that SSH is working for the current OS user with public/private key authentication using the standard RSA keys, simply
run the command shown here.

```shell
% verifySSH.sh -oracle_home $MW_HOME -ssh_host windows-host.mytenancy.oraclevcn.com
...
Issue Log for verifySSH version 4.0.0 running WebLogic version 14.1.1.0.0.231012 in offline mode:

Total:   SEVERE :    0  WARNING :    0

verifySSH.sh completed successfully (exit code = 0)
```

See the [Verify SSH Tool]({{% relref "/userguide/tools/verify_ssh.md" %}}) documentation for more information.
