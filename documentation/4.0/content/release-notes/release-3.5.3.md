+++
title = "Release 3.5.3"
date = 2019-02-22T15:27:38-05:00
weight = 76
pre = "<b> </b>"
+++


### Changes in Release 3.5.3
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1573 - Enhanced the `wlsdeploy.debugToStdout` system property to also include exception stacktraces when set to `true`.
<<<<<<< HEAD:documentation/3.0/content/release-notes/release-3.5.3.md
          This will help WebLogic Kubernetes Operator users running into WDT issues to see the details normally hidden in
          the log files.
=======
  This will help WebLogic Kubernetes Operator users running into WDT issues to see the details normally hidden in
  the log files.
>>>>>>> develop-4.0:documentation/4.0/content/release-notes/release-3.5.3.md

#### Bug Fixes
- #1561 - Fixed a NullPointerException when there is missing fields in the `RCUDbInfo` section.
- #1590 - Fixed an issue with the `ServiceProviderSingleLogoutRedirectUri` attribute in the October 2023 PSUs for
<<<<<<< HEAD:documentation/3.0/content/release-notes/release-3.5.3.md
          12.2.1.4 and 14.1.1 that was causing an error.
- #1590 - Fixed an issue with exception creation in 14.1.1 that was causing error messages not to be properly populated
          due to Jython 2.7.1 vararg method binding being broken.
=======
  12.2.1.4 and 14.1.1 that was causing an error.
- #1590 - Fixed an issue with exception creation in 14.1.1 that was causing error messages not to be properly populated
  due to Jython 2.7.1 vararg method binding being broken.
>>>>>>> develop-4.0:documentation/4.0/content/release-notes/release-3.5.3.md

#### Known Issues
None

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
