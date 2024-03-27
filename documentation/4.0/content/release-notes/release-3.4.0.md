+++
title = "Release 3.4.0"
date = 2019-02-22T15:27:38-05:00
weight = 80
pre = "<b> </b>"
+++


### Changes in Release 3.4.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1521 - Added alias changes to accommodate October 2023 PSUs for WebLogic Server versions 12.2.1.4 and 14.1.1.
- #1525 - Added missing MBeans to better support the WebLogic Remote Console.
- #1527 - Added missing Security Provider attributes to better support the WebLogic Remote Console.
- #1530 - Refactored the handling of Coherence Custom Cluster and Cache Config files to correct the behavior
          and expand online update and discover capabilities.
          One side effect is that the Discover Domain tool when run in online mode will generate warnings
          and skip discovery of Coherence Cache Config folders.  This is due to a shortcoming in WebLogic Server's
          Coherence configuration support that is tracked by Bug 35969096.

#### Bug Fixes
- #1522 - Fixed issues related to unicode handling that were causing errors processing typedef files.
- #1526 - Fixed an issue that was preventing custom typedefs from working properly (WDT-771/GitHub Issue #1506).
- #1528 - Fixed an issue that was causing the standalone Validate Model tool to write credentials to the log
          with certain models. Fixed an issue that was causing log level escalation (WDT-783).
- #1529 - Fixed an issue for boolean attributes with null default values. This issue was causing Discover Domain to 
          incorrectly treat attributes whose values were `False` to be omitted from the discovered model.

#### Known Issues
None

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
