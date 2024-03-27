+++
title = "Release 3.2.2"
date = 2019-02-22T15:27:38-05:00
weight = 87
pre = "<b> </b>"
+++


### Changes in Release 3.2.2
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1475 - Added support for upcoming SAML2 data initialization files in the archive file.
- #1476 - Added support for upcoming SAML2 data initialization files in the Discover Domain, Create Domain, and Update Domain tools.

#### Bug Fixes
- #1482 - Fixed an issue related to secret naming that was causing the generated secret names to overlap in locations with multiple credential or password fields. 
- #1483 - Filtered out the `OPSSSecrets` field in the `domainInfo` section of the model when targeting WebLogic Kubernetes Operator or Verrazzano MII and PV targets.
- #1484 - Fixed aliases for the 12.2.1.4 and 14.1.1 July 2023 PSU versions.

#### Known Issues
