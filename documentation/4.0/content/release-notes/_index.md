+++
title = "Release Notes"
date = 2024-01-09T18:27:38-05:00
weight = 73
pre = "<b> </b>"
+++


### Changes in Release 4.0.1
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1664 - Added support for the `OptionalFeatureDeployment` top-level folder.
- #1665, #1667 - Formalized support for both the replicated `config/wlsdeploy/custom/` and non-replicated 
          `wlsdeploy/custom` locations.  Added support in the Archive Helper Tool and tweaked the validation message
          to only notify the user if they are only using the non-replicated location.
- #1669 - Enhanced the WLS Policy support to allow users to modify built-in policies.
- #1674 - Added 12.2.1.4 and 14.1.1 April 2024 PSU support.

#### Bug Fixes
- #1666 - Fixed a bug with extracting the WebLogic Remote Console extension that caused an error if the archive file
          includes a directory entry.
- #1670 - Worked around a Jython 2.2.1 bug with `posixpath.isfile()` where it was returning `False` when the answer
          should have been `True`.
- #1672 - Added None checks around plan file name calculations.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```

- SSH support for the Update Domain Tool and Deploy Apps Tool do not work when using an archive file and the remote 
  WebLogic Server is running on Windows using the optional, Windows-provided, OpenSSH component.  This is due to an
  issue with the SSHJ library WDT is using.  See https://github.com/hierynomus/sshj/issues/929 for more information.

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
