+++
title = "Release Notes"
date = 2019-02-22T15:27:38-05:00
weight = 86
pre = "<b> </b>"
+++


### Changes in Release 3.2.3
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1496 - Added a post-createDomain script element to the typedef file definitions to accommodate extra
          offline work required for Oracle Identity Governance domain creation.
- #1499 - Added updated translation bundle files. 

#### Bug Fixes
- #1486 - Fixed JSON parser issue in handling escaped newlines.
- #1488 - Worked around a Jython 2.2.1 issue where environment variables with a newline in their value
          caused remaining environment variable values to not be visible from Jython.
- #1490 - Fixed an issue with deprecation logging statements to ensure that the class and method names
          were logged properly.
- #1494 - Changed the language for some logging/error messages to make them clearer.
- #1495 - Reworded several log messages that were confusing to users and difficult to translate.
- #1497 - Fixed sh-based shell scripts to work properly on Solaris 10.x Bourne shell
- #1498 - Corrected the error message for a deploy-related error.

#### Known Issues
