+++
title = "Release Notes"
date = 2024-01-09T18:27:38-05:00
weight = 55
pre = "<b> </b>"
+++


### Changes in Release 4.4.3
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1866 - Added support for the cluster `WebLogicPluginRouting` subfolder.
- #1866, #1867, #1868 -  Added support for attributes for future WebLogic Server releases.

#### Bug Fixes
- #1865 - Fixed SSH discovery issue that was causing the tool to try to download `FileStore` directories.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```
