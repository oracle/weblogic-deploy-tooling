+++
title = "Release 4.2.1"
date = 2024-01-09T18:27:38-05:00
weight = 69
pre = "<b> </b>"
+++


### Changes in Release 4.2.1
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1717, #1728 - Extended the API integration between WebLogic Kubernetes Toolkit UI and WDT to pass back the encrypted
  passwords when running the Prepare Model Tool from the WebLogic Kubernetes Toolkit UI.
- #1722 - Added logic to detect a situation where the user specified in `domainInfo:/AdminUserName` is also listed in
  the `topology:/Security/User` list of users and update the `topology:/Security/User` user's `Password` field to be
  the same as that specified in `domainInfo:/AdminPassword`.
- #1723 - Added support for the WebLogic Server 12.2.1.4 and 14.1.1 July 2024 PSUs.

#### Bug Fixes
- #1713 - Added logic at startup to detect when WDT logging is not properly configured.
- #1715 - Fixed a bug where the `domainInfo:/OPSSWalletPassphrase` field was not properly handled when using the
  Prepare Model Tool or when using the Discover Domain Tool with the `-target` argument.
- #1716 - Fixed the Discover Domain Tool documentation to add missing command-line arguments.
- #1718 - Fixed an issue with the `NativeVersionEnabled` attribute of `NMProperties` not working correctly when running
  the Update Domain Tool.
- #1720 - Fixed an issue with RCU pre-check error handling that was causing an unhandled Jython error.
- #1721 - Fixed a bug in the SSH directory listing command for a remote Unix machine.
- #1724 - Fixed an off-by-one error when using the Archive Helper Tool's `remove custom` command with a name that starts
  with `wlsdeploy/custom/` or `config/wlsdeploy/custom/` that was causing the specified location to not be removed.
- #1727, #1729 - Fixed an issue with Create Domain Tool's RCU pre-check functionality that was causing a Jython 
  AttributeException for `set` when the STB DataSource was defined in the `resources:/JDBCSystemResource` section of the
  model and specifying one or more JDBC driver properties.
- #1730 - Fixed an issue where an application or library deployment plan was not being collected when the `SourcePath`
  contained an excluded location like `@@ORACLE_HOME@@`.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```

- SSH support for the Update Domain Tool and Deploy Apps Tool does not work when using an archive file and the remote 
  WebLogic Server is running on Windows using the optional, Windows-provided, OpenSSH component.  This is due to an
  issue with the SSHJ library WDT is using.  See https://github.com/hierynomus/sshj/issues/929 for more information.

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
