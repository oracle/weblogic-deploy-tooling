+++
title = "Release 2.4.0"
date = 2022-11-02T15:27:38-05:00
weight = 5
pre = "<b> </b>"
+++

### Changes in Release 2.4.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
- None

#### Other Changes
- #1193 - Added support for changing the RCU Data Source type during JRF domain creation (WDT-636).
- #1210 - Improved the speed of remote discovery by bypassing remote calls to determine if a field was set (WDT-663).
- #1218 - Added `-target` support for WebLogic Kubernetes Operator 4.0 to generate the domain and cluster schema resources.
- #1220 - Added support for application modules for JDBC, JMS, and WLDF with normal WDT tokenization mechanisms (WDT-675).

#### Bug Fixes
- #1194: Resolved an ordering issue when setting the `FrontendHost` and `FrontendHTTPPort` with dynamic clusters (WDT-668).
- #1196: Fixed issue #1170 which was causing an unexpected `NameError`.
- #1197: Log a warning when the security provider schematype file is missing (WDT-645) .
- #1208: Refactored tool exit handling to simplify the logic and resolve various errors.
- #1209: Resolved an issue with structured applications where the model data was not being honored for the deployment plan file name.
- #1214: Resolved an issue with structured application discovery causing duplicate override files to show up in the archive file.
- #1217: Resolved an issue with ATP database support that was not handling connect strings with multiple description fields.
- #1229: Resolved an alias issue where the `TopicSubscriptionParams` was incorrectly available on `UniformDistributedQueue` and not `UniformDistributedTopic`.

#### Known Issues
- Due to the changes made for WDT-663, the resulting remotely discovered model contains extra fields that would not normally be there.
  This is an area of ongoing work to clean up the online aliases to not depend on these extra remote calls to produce a clean model.


