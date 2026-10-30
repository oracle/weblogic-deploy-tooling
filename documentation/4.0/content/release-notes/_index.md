+++
title = "Release Notes"
date = 2024-01-09T18:27:38-05:00
weight = 51
pre = "<b> </b>"
+++


### Changes in Release 4.4.7
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1919 - Added support for September CSPUs.
- #1921 - Preserved order in the variables file on updates.
- #1923 - Added support for WLS 26.1 Foreign JNDI properties encryption.
- #1925 - Added support for October PSUs.
- #1926 - Added support for WLS 26.1 Foreign JMS properties encryption.
- #1928 - Upgraded to JLine 4.3.1 to eliminate CVE.

#### Bug Fixes
- #1881 - Fixed Java properties file encoding issues when writing out the variables file.
- #1910 - Fixed issue with the alias type for JNDI allow lists to support lists.
- #1924 - Fixed an issue that could cause duplicate `JdbcResource` folders causing discovery to fail.
- #1927 - Fixed an issue with handling null shared library runtime references during online deployment (GitHub #1750).

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```
