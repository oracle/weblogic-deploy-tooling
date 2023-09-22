+++
title = "Release Notes"
date = 2019-02-22T15:27:38-05:00
weight = 84
pre = "<b> </b>"
+++


### Changes in Release 3.2.5
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
None

#### Bug Fixes
#1506 - Fixed an issue with online discovery of the JMS `ErrorDestination` attribute (GitHub #1494).
#1507 - Added documentation for the WDT Discover Domain tool's limitation regarding users and groups in the `DefaultAuthenticator` (GitHub #1493).
#1508 - Fixed an issue with Update Domain that was causing the Oracle JDBC driver to throw `FileNotFoundException`
        when using a JRF domain with an ATP database.
#1509 - Fixed an issue with online discovery of custom security providers that caused the implementation class name to
        be added to the model instead of the interface class name (GitHub #1495).

#### Known Issues
None

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
