---
title: "Tool Exit Codes"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
description: "Helps you create and modify archive files."
---

WebLogic Deploy Tooling uses operating system exit codes to determine whether the command succeeded or not.  WDT
follows the normal conventions exiting with a zero exit code when the tool completes successfully.  When various
situations are encountered, non-zero exit codes are used to communicate what happened to the user. The exit codes
and their meanings are as shown in the table below.  Unless otherwise noted, all tools use these exit codes.

### Exit code table

|  Exit Code | Meaning                                                                               |
|------------|---------------------------------------------------------------------------------------|
| 0          | The tool exited successfully.                                                         |
| 1          | The tool ran to completion but encountered 1 or more warnings.                        |
| 2          | The tool did not complete its execution and encountered 1 or more errors.             |
| 98         | The tool did not complete its execution due to 1 or more parameter validation errors. |
| 99         | The tool did not complete its execution due to 1 or more usage errors.                |
| 100        | The user ran the tool with the -help argument so the tool echoed the help message.    |
| 101        | The tool completed successfully but with 1 or more deprecation messages^1^.           |
| 103        | The tool completed successfully but the online changes require server restarts^2^.    |
| 104        | The tool completed successfully but the online changes were cancelled^3^.             |

##### Footnotes
1. By default, WDT tools do not exit with a 101 exit code for deprecation messages unless explicitly configured by
   setting `use.deprecation.exit.code=true` in `${WDT_HOME}/lib/tool.properties` or the equivalent Java
   System Property `-Dwdt.config.use.deprecation.exit.code=true` passed using the `WLSDEPLOY_PROPERTIES` environment
   variable.
2. This is primarily applicable to the Update Domain Tool when invoked in online mode.  Certain WebLogic Server MBean
   changes require a server or even a complete domain restart.  See the WebLogic Server documentation for the version
   you are using for more information.
3. This is primarily applicable to the Update Domain Tool when invoked in online mode with the 
   `-cancel_changes_if_restart_required` command-line argument.  The exit code simply indicates that a server or domain
   restart would have been required so the execution was cancelled.