+++
title = "Release Notes"
date = 2024-01-09T18:27:38-05:00
weight = 52
pre = "<b> </b>"
+++


### Changes in Release 4.4.6
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1883 - Added support for new top-level `FeatureCompatibility` folder.
- #1899 - Added support for July 2026 PSUs.
- #1905 - Added support for top-level `BatchConfig` folder.
- #1908 - Added support for August 2026 CSPUs.

#### Bug Fixes
- #1881 - Fixed encoding issues when writing variables file.
- #1890 - Fixed an issue with JMS `ForeignServer` `ConnectionURL` attribute so that it supports both files and URLs.
- #1893 - Fixed archive file handling to support large archive file copies.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```
