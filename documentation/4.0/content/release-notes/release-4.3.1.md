+++
title = "Release 4.3.1"
date = 2024-01-09T18:27:38-05:00
weight = 67
pre = "<b> </b>"
+++


### Changes in Release 4.3.1
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1771 - Added support for January 2025 PSUs for 12.2.1.4, 14.1.1, and 14.1.2.

#### Bug Fixes
- #1762, #1764 - Fixed issues with causing Discover Domain to generate attribute not supported log entries for
  deprecated attributes.
- #1763 - Documented WebLogic Server Bug 37443991 as a known limitation.
- #1765 - Fixed AttributeError when running Discover Domain with either `-skip_archive` or `-remote` (GitHub Issue 1607).
- #1766 - Fixed AttributeError when running Discover Domain with either `-skip_archive` or `-remote`
  on different archive types (GitHub Issue 1608).
- #1767 - Fixed Discover Domain command-line argument validation that allows both `-skip_archive` and `-remote` to be
  specified when they are mutually exclusive.
- #1768 - Improved default value detection for Discover Domain when running against WebLogic Server 14.1.2.
- #1769 - Cleaned up offline Discover Domain to exclude the `JavaHome` attribute in the `NMProperties` folder.
- #1770 - Fixed secure mode detection to work properly in WebLogic Server 14.1.2.  This is critical to reducing the
  number of attributes that show up in the model when using Discover Domain in offline mode.

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
