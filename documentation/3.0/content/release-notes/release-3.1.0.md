+++
title = "Release Notes 3.1.0"
date = 2019-02-22T15:27:38-05:00
weight = 90
pre = "<b> </b>"
+++


### Changes in Release 3.1.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1431 - Added new `OPSSInitialization` section to `domainInfo` in order to support ODI and OIG domain creation.
- #1432 - Added database connectivity check to validate RCU database connection details prior to creating a domain
  using RCU schemas when not running RCU.
- #1434 - Added JSON output of restart and non-dynamic change information (#1154)
- #1438 - Deprecated the use of all RCU-related arguments that provide database connectivity information with
  the Create Domain tool.

#### Bug Fixes
- #1428 - Added command-line usage for OPSS Wallet related arguments to Create Domain.  Enhanced the documentation to
  describe how to use the OPSS Wallet to recreate a domain that connects to existing RCU schemas.
- #1429 - Updated Discover Domain `-target` argument usage.  Updated the documentation related to `-target` to reflect
  recent changes.
- #1436 - Fixed an issue with deleting machines created by a template.
- #1437 - Fixed offline discovery issues when discovering domains that have used slashes in their object names (e.g., SOA Suite)
- #1438 - Fixed issues where Create Domain RCU-related command-line arguments were not override model-supplied values.
- #1439 - Worked around a discovery issue for domains with the `Trust Service Identity Asserter` when the Oracle Home
  has not been patched to contain the security provider's schema JAR file. 

#### Known Issues
