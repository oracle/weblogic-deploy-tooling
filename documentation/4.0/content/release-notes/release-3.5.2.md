+++
title = "Release 3.5.2"
date = 2019-02-22T15:27:38-05:00
<<<<<<< HEAD:documentation/3.0/content/release-notes/release-3.5.2.md
weight = 77
=======
weight = 75
>>>>>>> develop-4.0:documentation/4.0/content/release-notes/release-3.5.2.md
pre = "<b> </b>"
+++


<<<<<<< HEAD:documentation/3.0/content/release-notes/release-3.5.2.md
### Changes in Release 3.5.2
=======
### Changes in Release 3.5.4
>>>>>>> develop-4.0:documentation/4.0/content/release-notes/release-3.5.2.md
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
<<<<<<< HEAD:documentation/3.0/content/release-notes/release-3.5.2.md
- #1557 - Added support for provisioning the WebLogic Remote Console domain extension WAR file.

#### Bug Fixes
- #1547 -  Fixed a bug with password validation causing a `NullPointerException` when the `domainInfo` section was
  missing from the model.
- #1554 - Fixed a problem where the Discover Domain tool would hang when running in online mode and an edit lock exists.
=======
- #1600 - Added alias updates to support the Jan 2024 PSUs.

#### Bug Fixes
- #1607 - Fixed an issue with assigning groups to parent groups.
- #1620 - Fixed an issue that caused an attribute with the WLST value `none` to be interpreted as a Python `None`.
- #1635 - Fixed an issue with the `ResourceManagement` attribute in WebLogic Server 14.1.1 and higher.
>>>>>>> develop-4.0:documentation/4.0/content/release-notes/release-3.5.2.md

#### Known Issues
None

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
