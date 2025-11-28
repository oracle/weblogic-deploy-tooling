+++
title = "Release Notes"
date = 2024-01-09T18:27:38-05:00
weight = 59
pre = "<b> </b>"
+++


### Changes in Release 4.3.9
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1837 - Added documentation for the tool exit codes to clarify an issue brought up in GitHub issue #1663.
- #1838 - Added a note to the Known Limitations page about delete ordering described in GitHub issue #1664.
- #1841 - Changed the alias definition for the WLDF `ScriptAction` folder's `Properties` attribute so that
          it is written to the model file as a map instead of a string.
- #1845 - Added support for the `RmiForwarding` folders added in WebLogic Server 15.1.1.

#### Bug Fixes

- #1835 - Fixed an issue that was causing Network Access Point deletion to fail (GitHub issue #1663).
- #1836 - Worked around the SSH issue for uploading files to an SSH server running Windows, removing the previously
          documented limitation.
- #1839 - Fixed the name of the `CorsExposedHeader` attribute (which was previously `CorExposedHeader`) in the
          `RestfulManagementServices` folder.
- #1840 - Fixed the alias file online MBean type for the LogFilter folder.
- #1842,#1843 - Fixed alias type issues with several attributes in the `RestfulManagementServices` folder.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```
