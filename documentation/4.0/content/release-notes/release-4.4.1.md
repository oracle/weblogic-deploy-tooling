+++
title = "Release 4.4.1"
date = 2024-01-09T18:27:38-05:00
weight = 56
pre = "<b> </b>"
+++


### Changes in Release 4.4.1
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1856 - Added non-public commands to the Archive Helper Tool to facilitate integration with the WebLogic Kubernetes
  Toolkit UI 2.0 so that it can handle archive files larger than 2 GB.

#### Bug Fixes
- #1855 - Fixed alias `wlst_type` fields on the `FatalErrorCodes` attribute of the `JDBCConnectionPoolParams` folder and
  the `Arguments` attribute of both the `StartupClass` and `ShutdownClass` folders to reflect that they are delimited
  strings.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```
