+++
title = "Release 4.4.8"
date = 2024-01-09T18:27:38-05:00
weight = 50
pre = "<b> </b>"
+++


### Changes in Release 4.4.8
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1932 - Added support for November 2026 CSPUs.

#### Bug Fixes
- #1930 - Fixed an issue with handling string with `${...}` that were not referring to WDT placeholders.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```
