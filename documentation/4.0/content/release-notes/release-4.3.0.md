+++
title = "Release 4.3.0"
date = 2024-01-09T18:27:38-05:00
weight = 68
pre = "<b> </b>"
+++


### Changes in Release 4.3.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1731, #1735, #1736, #1738, #1743, #1748 - Updated aliases for WebLogic Server 14.1.2 GA release.
- #1732 - Changed default value when using `-target` to include the domain's bin directory contents.
- #1737 - Optimized offline discovery of default values in 14.1.2.
- #1739 - Added aliases for `SNMPAgent`, `SNMPDeploymentAgent`, `EJBContainer`, and Cluster's `JtaRemoteDomain` folders.
- #1741 - Added support for deploying and discovering customer resources.
- #1746 - Added support for the WebLogic Server 12.2.1.4 and 14.1.1 October 2024 PSUs.
- #1750 - Changed file path resolution to not convert symbolic links to the actual paths.
- #1751 - Changed JDK validation to allow the user to run WDT tools with OpenJDK and removed broken support for GraalVM.
- #1752 - Moved away from using jline's deprecated `jansi` provider to using the `jni` provider. 
- #1758 - Enhanced Create Domain Tool to allow creating a JRF domain using fully specified RCU Data Sources
          in the `resources:/JDBCSystemResource` section of the model without requiring the `domainInfo:/RCUDbInfo`
          section.
- #1760 - Modified WDT's usage of JAXB classes to prepare for supporting the Jakarta EE 9+ of JAXB runtime.

#### Bug Fixes
- #1732 - Fixed bad error message when WLST assign() invocation fails.
- #1734 - Fixed validation error caused by trying to validate prior to resolving tokens.
- #1744 - Squelched SLF4J startup messages from printing to `stderr`.
- #1748 - Fixed target injector paths causing discovery to fail with sub-deployments.
- #1749 - Fixed JMS Foreign Server discovery issue when the URL is not using a `file`, `http`, or `https` protocol.
- #1753 - Cleaned up exiting from the interactive Model Help Tool using Control-D.
- #1755 - Fixed bug with command-line handling of the WDT encryption passphrase from `stdin`.

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
