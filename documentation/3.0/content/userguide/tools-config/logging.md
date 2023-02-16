---
title: "Logging"
date: 2022-02-04T17:18:00-05:00
draft: false
weight: 4
---

The WebLogic Deploy Tooling has a built-in logging framework based on `java.util.logging`.  Its logging configuration
is specified in `$WDT_HOME/etc/logging.properties`.  By default, the logging framework writes to both the console and
a log file.

#### Log file
By default, WDT tools write their log files to the `$WDT_HOME/logs` directory and the log file name reflects the name of the tool.
For example, if you run the `validateModel` tool then the log file will be `$WDT_HOME/logs/validateModel.log`.  These
log files are overwritten each time you run a particular tool so the file contains only the logs from the last tool
invocation.

If the `$WDT_HOME/logs` directory is not writable by the user running the tool, the logging framework will search for
a location to write the logs.  The user must have write permission on the directory in order for it to be selected.
The search order is as follows:

- Check the `WLSDEPLOY_LOG_DIRECTORY` environment variable.
- Check the current working directory (as defined by the `user.dir` Java system property) and create a `logs` subdirectory.
- Check the temp directory (as defined by the `java.io.tmpdir` Java system property) and create a `wdt-logs` subdirectory.

If none of these locations are writable, the logging framework prints an error message to `stderr` and exits.

#### Console output
WDT tools output logging information to `stdout` and `stderr`, as appropriate.  By default, only `INFO` level messages
are sent to `stdout`.  All `WARNING` and `SEVERE` messages are set to `stderr`.  In addition to regular log messages
generated as the tool runs, the tools will produce a summary at the end of tool execution that gives the user an
overview of the tool execution status.  For example, the `validateModel` tool execution with no warnings or errors will
produce output that looks similar to this:

```
Issue Log for validateModel version 2.0.0 running WebLogic version 12.2.1.4.0.210930 offline mode:

Total:       WARNING :     0    SEVERE :     0
```

#### Logging levels
As mentioned previously, WDT's logging framework is based on `java.util.logging` so all logging levels defined in
the `java.utiul.logging.Level` class apply to WDT loggers.  For a quick review of those levels, see the
[javadoc](https://docs.oracle.com/javase/8/docs/api/java/util/logging/Level.html).

WDT uses hierarchical loggers that align with the purpose of the code being executed.  The root logger is named `wlsdeploy`.
Many loggers exist underneath the root logger; for example, `wlsdeploy.create`, `wlsdeploy.discover`, and `wlsdeploy.util`.
By default, the WDT `logging.properties` file sets the logging level of the root and several important loggers.  If the
level for a particular logger is not set, that logger will use the level of its parent logger.  This delegation to the
parent logger is recursive up the hierarchy until it finds a level to use. 

In WDT, the log file will collect log entries from all loggers based on the logger's `level` while the console output
is limited to `INFO` and above only.  Log entries written to the console will not display any exception stack traces
associated with a log entry.  To see those, you must look at the log file.  The WDT logging framework supports using the
`wlsdeploy.debugToStdout` Java system property to allow debug log messages (those logged at the `FINE` level or below)
to appear in `stdout` as long as the loggers to which the messages are logged are not filtering those log levels.  For
example, doing the following will cause debug output to be written to the console:

```
export WLSDEPLOY_PROPERTIES=-Dwlsdeploy.debugToStdout=true
weblogic-deploy/bin/prepareModel.sh ...
```

#### Log handlers
WDT uses several log handlers to handle logging output of data to various sources.

 | Log Handler | Output Destination | Description                                                                      |
 | ----------- |----------------------------------------------------------------------------------| ----------- |
 | `java.util.logging.FileHandler` | WDT tool log file | The standard `java.util.logging` file handler.                                   |
 | `oracle.weblogic.deploy.logging.StdoutHandler` | `stdout` | WDT handler that writes `INFO` level messages to the console.                    |
 | `oracle.weblogic.deploy.logging.StderrHandler` | `stderr` | WDT handler that writes `WARNING` and `SEVERE` level messages to the console.    |
 | `oracle.weblogic.deploy.tooling.SummaryHandler` | `stdout` | WDT handler that writes the tool's execution summary information to the console. |

By default, all four handlers are used and configured appropriately.  The logging framework intentionally limits the
configurability of these handlers.  Only the following `logging.properties` file settings are allowed.

 | Property                                           | Value(s) Allowed                 | Behavior When Set                                                                                                    |
 |----------------------------------|----------------------------------------------------------------------------------------------------------------------| ---------------------------------------------------------------|
 | `handlers` | comma-separated list of handlers | The list of handlers to use (removing a handler from the list is the same as setting its `level` property to `OFF`). |
 | `java.util.logging.FileHandler.level`                | `OFF`                            | No logging output will be saved in the log file.                                                                     |
 | `oracle.weblogic.deploy.logging.StdoutHandler.level` | `OFF`                            | No `INFO` level logging output will be written to the console.                                                       |
 | `oracle.weblogic.deploy.logging.StderrHandler.level` | `OFF`                            | No `WARNING` or `ERROR` level logging output will be written to the console.                                         |
 | `oracle.weblogic.deploy.logging.SummaryHandler.level` | `OFF`                            | No tool execution summary output will be written to the console.                                                     |
 | `oracle.weblogic.deploy.logging.SummaryHandler.size` | Any number                       | Limits the number of memory-buffered `WARNING` and `ERROR` log records (default is 3000).                            |

Use the `WLSDEPLOY_LOG_HANDLERS` environment variable as an alternative to specifying the list of handlers in the
`logging.properties` file's `handlers` property.

Any attempts to set other configuration for these log handlers will simply be discarded by the WDT logging framework at startup.
