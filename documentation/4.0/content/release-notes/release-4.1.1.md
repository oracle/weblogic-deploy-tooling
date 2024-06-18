+++
title = "Release 4.1.1"
date = 2024-01-09T18:27:38-05:00
weight = 71
pre = "<b> </b>"
+++


### Changes in Release 4.1.1
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1685 - Filtered out the default `OptionalFeatures` folders when they have no attributes so that they do not show up
          in the online discovered model.

#### Bug Fixes
- #1677 - Fixed a bug where creating a user with extra attributes would result in invalid LDIFT entries.
- #1678 - Fixed a bug that was causing errors when deploying a new application and the server required a restart.
- #1679 - Fixed a bug where the SSHJ libraries (that only work with JDK 8 and later) were causing the tools to fail
          when running with JDK 7.
- #1680 - Fixed the `DataSourceLogFile` and `WebServerLog` folders default value for the `DateFormatPattern` attribute
          for WLS versions prior to 12.2.1 so that they no longer show up in the online discovered model.
- #1681 - Worked around a pre-12.2.1 WLST bug that was preventing the online tools from determining the server's WLS version.
- #1683 - Fixed a bug with the Model Help Tool where our use of JLine libraries (that only work with JDK 8 and later)
          were causing the Model Help tool to fail when run with JDK 7.

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
