+++
title = "Release 4.3.4"
date = 2024-01-09T18:27:38-05:00
weight = 64
pre = "<b> </b>"
+++


### Changes in Release 4.3.4
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1792 - Segregated ServerTemplate keystores in the archive file.
- #1798 - Added `ClusterAddress`, `ListenAddress`, `InterfaceAddress`, and `MulticastAddress` to the WKO filter
          when using Discover Domain and Prepare Model tools with the `-target` argument.
- #1799 - Added the `oracle_database_admin_role` field to the `RCUDbInfo` section for users that need to
          use a role that is not `SYSDBA`.

#### Bug Fixes
- #1784 - Prevent Discover Domain tool from trying to discover passwords unless the user specified to do so.
- #1785 - Change logging level from `INFO` to `FINE` for unrecognized attributes when using online operations.
- #1786 - Fixed RCU discovery issue to properly handle passwords.
- #1787 - Fixed issue with WKO filter to eliminate errors when traversing the model.
- #1788 - Restored internal method call to compare WLS versions in the Discover Domain tool.
- #1789 - Fixing issues with the `-target wko` filter.
- #1790 - Add missing 14.1.2 JDK version information to the installation documentation.
- #1794 - Fixing an issue with the RCU password not being properly decrypted while trying to validate the
          RCU data when running the Create Domain tool.
- #1795 - Fixing a bug introduced by change #1792 that was causing an error when discovering `Server` and
          `ServerTemplate` keystores. 
- #1796 - Fixed an issue where the datasource password was not being decrypted properly when using the
          Discover Domain tool with the `-discover_passwords` argument.


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
