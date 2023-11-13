+++
title = "Release Notes 3.3.0"
date = 2019-02-22T15:27:38-05:00
weight = 81
pre = "<b> </b>"
+++


### Changes in Release 3.3.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1517 - Added a `postCreateRcuSchemasScript` element to the typedef file definitions to accommodate extra
  schema patching work required for Oracle Identity Governance domain creation.
- #1519 - Added `rcu_admin_user` field to the `domainInfo:/RCUDbInfo` section to replace `rcu_db_user`, which is now
  deprecated and will be removed in a future release.  This field is optional and will default to the appropriate
  admin user name: `admin` when using an ATP database and `SYS` otherwise. 

#### Bug Fixes
- #1518 - Fixed an issue when using an ATP database as the RCU schema repository that was causing
  `config/fmwconfig/jps-config.xml` to contain a clear text password after JRF domain creation.

#### Known Issues
None

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
