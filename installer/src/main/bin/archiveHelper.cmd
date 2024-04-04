@ECHO OFF
@rem **************************************************************************
@rem archiveHelper.cmd
@rem
@rem Copyright (c) 2023, Oracle and/or its affiliates.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       archiveHelper.sh - WLS Deploy tool to support creating and editing an archive file.
@rem
@rem     DESCRIPTION
@rem       This script provides add, extract, list, and replace functionality for
@rem       working with an archive file.
@rem
@rem This script uses the following variables:
@rem
@rem JAVA_HOME             - The location of the JDK to use.  The caller must set
@rem                         this variable to a valid Java 7 (or later) JDK.
@rem

SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=archiveHelper

SET SCRIPT_PATH=%~dp0
FOR %%i IN ("%SCRIPT_PATH%") DO SET SCRIPT_PATH=%%~fsi
IF %SCRIPT_PATH:~-1%==\ SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

SET MIN_JDK_VERSION=7
SET "WLSDEPLOY_LOG_HANDLERS=java.util.logging.FileHandler"

call "%SCRIPT_PATH%\shared.cmd" :javaOnlySetup %MIN_JDK_VERSION% quiet

%JAVA_HOME%\bin\java -Djava.util.logging.config.class=%LOG_CONFIG_CLASS% oracle.weblogic.deploy.tool.ArchiveHelper %*
SET RETURN_CODE=%ERRORLEVEL%

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
