+++
title = "Release 3.2.1"
date = 2019-02-22T15:27:38-05:00
weight = 88
pre = "<b> </b>"
+++


### Changes in Release 3.2.1
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1465 - Initial, limited i18n translation bundles added.

#### Bug Fixes
- #1466 - Updated `Server` and `ServerTemplate` aliases to add new offline attributes in upcoming versions of WebLogic Server.
- #1467 - Updated `CoherenceSystemResource` aliases to add `SecuredProduction` online attribute used in upcoming versions of WebLogic Server.
- #1468 - Fixed an error related to tool initialization with WebLogic Server versions earlier than 12.2.1 (Issue #1466).
- #1469 - Corrected method names used for logging so that they are the same as the actual method name in which they are
          being used.
- #1470 - Fixed system-test test 35 to allow it to succeed when run on machines other than the Jenkins agents.
- #1471 - Fixed a `discoverDomain` issue that was causing errors while looking for `SecureMode` on WebLogic Server
          versions earlier than 12.2.1.1 (Issue #1467).

#### Known Issues
