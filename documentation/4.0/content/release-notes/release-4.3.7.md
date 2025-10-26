+++
title = "Release 4.3.7"
date = 2024-01-09T18:27:38-05:00
weight = 61
pre = "<b> </b>"
+++


### Changes in Release 4.3.7
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1816 - Added support for 12.2.1.4, 14.1.1, and 14.1.2 July 2025 PSUs.
- #1826 - Improved support for DBClientData directories by adding model support.
- #1827 - Removed Verrazzano support that was deprecated in 4.0.0.
- Various - Added support for 15.1.1 GA release.

#### Bug Fixes
- #1811 - Fixed an issue to allow support for null default values for attributes during discovery
- #1830 - Fixed 12.2.1.3 alias values for OracleIdentityCloudIntegrator
- #1831 - Fixed variable injection for security providers

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
