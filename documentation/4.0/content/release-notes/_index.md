+++
title = "Release Notes"
date = 2024-01-09T18:27:38-05:00
weight = 76
pre = "<b> </b>"
+++


### Changes in Release 4.0.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
- #1481 - Added new Verify SSH Tool to support testing an environment for using the new SSH support.
- #1516 - Added SSH support for Discover Domain, Update Domain, and Deploy Apps Tools that will allow
          these tools to work against a WebLogic domain running on a remote machine.
- #1548, #1553, #1556 - Revamped the Model Help Tool to improve the semantics and behavior of interactive mode.
                 Added online mode support.  Fixed CRDs to work consistently with alias folders and attributes.
- #1550 - Refactored the archive file and moved content extraction into `$DOMAIN_HOME/config/wlsdeploy` for some types
          to take advantage of existing Pack/Unpack behavior and admin server to managed server replications capabilities.
- #1584 - Added support for creating WebLogic authorization policies during domain creation (GitHub issue #1496). 

#### Other Changes
- #1544 - Consolidated multiple internal WLST helper methods to get an MBean.
- #1552 - Added typedef support for `discoverExcludedBinariesList` to allow OIG to add a custom application in the
          Oracle Home to the archive file.
- #1564 - Added Discover Domain Tool support for discovering the WebLogic Remote Console domain extension.
- #1568 - Added the ability to remove MBean assignments in the model by setting them to null or empty (GitHub issue #1483).
- #1569 - Improved version handling for online operations to always use the server's WebLogic Server version.
- #1572 - Enhanced the `wlsdeploy.debugToStdout` system property to also include exception stacktraces when set to `true`.
          This will help WebLogic Kubernetes Operator users running into WDT issues to see the details normally hidden in
          the log files.
- #1583 - Eliminated the `-domain_home` argument from tools running in online mode.
- #1586 - Simplified variable injector configuration and customization.
- #1587 - Removed deprecated RCU-related command-line arguments from the Create Domain Tool.
- #1588 - Deprecated the `domainInfo` section's `OPSSSecrets` attribute and replaced it with `OPSSWalletPassphrase` to
          better represent the purpose of the attribute.
- #1592 - Deprecated Verrazzano support.
- #1598 - Added support for online wallet distribution to managed servers in 14.1.2.
- #1599 - Added support for the 12.2.1.4 and 14.1.1 January 2024 PSUs.
- #1605 - Deprecated the Deploy Applications Tool.  The intention going forward is that users should be able to use
          the Update Domain Tool, which already does everything that the Deploy Applications Tool does and more.
- #1613 - Added ability to use variable tokens in the SAML 2 data initialization property files that will be replaced
          during domain creation or update processing.
- #1614 - Updated Discover Domain Tool to overwrite existing variable and archive files if they already exist. 
- #1616 - Improved `RCUDbInfo` validation in Create Domain tool.
- #1630 - Replaced the `-variable_property_file` argument in the Inject Variables tool with `-variable_file`
 
#### Bug Fixes
- #1555 - Fixed issues with creating and discovering `UnixMachine` objects in online mode.
- #1562 - Added missing default values for `RCUDbInfo` attributes.
- #1563 - Fixed an issue with Compare Model where it was trying to compare an invalid field.
- #1565 - Suppressed logging of domain typedef information by the exit context used to handle unexpected errors.
- #1575 - Added support for storing the `CreateTableDDLFile` script referenced by the `TransactionLogJDBCStore` in the
          archive file.
- #1579 - Fixed an issue that limited the number of secret keys that could be referenced by the model. 
- #1584 - Fixed an issue where online updates that required restarts were using a 12.2.1+ API even with older versions.
- #1603 - Fixed a bug related to online WLST error message formatting.
- #1608 - Fixed a bug in creating Security groups that are members of another group.
- #1610 - Fixed a bug where the Create Domain and Update Domain Tools were trying to create a security provider that
          is not valid in the current WebLogic Server version.
- #1615 - Fixed an issue where certain errors during online update or deploy operations could leave a pending edit
          state that caused subsequent invocations to fail due to the pending edit state.
- #1619 - Fixed a bug that was causing offline discovery to omit the `LogRotation` attribute when the value was set to `none`.
- #1631 - Fixed an issue where the Update Domain and the Deploy Applications Tools running in online mode were trying to
          call start on an application when earlier changes required a server restart.
- #1634 - Fixed an issue with the `ResourceManagement` MBean when running the Discover Domain Tool in online mode with
          WebLogic Server 14.1.1 and newer.
- #1636 - Fixed an issue with Update Domain and Deploy Applications Tools when using the `-remote` option that was
          causing a TODO message to be generated when there was nothing for the user to do.
- #1638 - Fixed an issue with Update Domain and Deploy Applications Tools where the application specified a `PlanDir`
          and a `PlanPath` but the online deployment was ignoring the `PlanDir`, resulting in a file does not exist
          error when attempting to deploy the application.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```

- SSH support for the Update Domain Tool and Deploy Apps Tool do not work when using an archive file and the remote 
  WebLogic Server is running on Windows using the optional, Windows-provided, OpenSSH component.  This is due to an
  issue with the SSHJ library WDT is using.  See https://github.com/hierynomus/sshj/issues/929 for more information.

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
