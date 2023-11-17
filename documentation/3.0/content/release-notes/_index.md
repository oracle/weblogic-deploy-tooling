+++
title = "Release Notes"
date = 2019-02-22T15:27:38-05:00
weight = 79
pre = "<b> </b>"
+++


### Changes in Release 3.5.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1535 - Changed the timing for extracting the archive file's `custom` folder to support storing custom WebLogic Server
          security provider jar files (GitHub issue #1512).
- #1537, #1539 - Cleaned up user password validation and extended it to support customizing the default settings
         using the model's `SystemPasswordValidator` settings, if present.  See
         https://oracle.github.io/weblogic-deploy-tooling/userguide/tools/create/#user-password-validation for details
         (GitHub issue #1510).

#### Bug Fixes
- #1538 - Fixed online discovery of Coherence Cache Config files if the fix for Bug 35969096 is present.

#### Known Issues
None

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
