@ECHO OFF
@rem **************************************************************************
@rem prepareModel.cmd
@rem
@rem Copyright (c) 2020, 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       prepareModel.sh - prepare the model(s) for deploying to a target environment,
@rem                         such as WebLogic Kubernetes Operator.
@rem
@rem     DESCRIPTION
@rem       This script applies a target configuration to the specified model(s), and creates any scripts
@rem       or configuration files that are required.
@rem
@rem This script uses the following variables:
@rem
@rem JAVA_HOME             - The location of the JDK to use.  The caller must set
@rem                         this variable to a valid Java 7 (or later) JDK.
@rem
@rem WLSDEPLOY_HOME        - The location of the WLS Deploy installation.
@rem                         If the caller sets this, the callers location will be
@rem                         honored provided it is an existing directory.
@rem                         Otherwise, the location will be calculated from the
@rem                         location of this script.
@rem
@rem WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
@rem                         can use this environment variable to add additional
@rem                         system properties to the Java environment.
@rem

SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=prepareModel

SET SCRIPT_NAME=%~nx0
SET SCRIPT_ARGS=%*
SET SCRIPT_PATH=%~dp0
FOR %%i IN ("%SCRIPT_PATH%") DO SET SCRIPT_PATH=%%~fsi
IF %SCRIPT_PATH:~-1%==\ SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

call "%SCRIPT_PATH%\shared.cmd" :checkJythonArgs %SCRIPT_ARGS%
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

@rem Java 7 is required, no encryption is used
call "%SCRIPT_PATH%\shared.cmd" :javaSetup 7
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

call "%SCRIPT_PATH%\shared.cmd" :runJython prepare_model.py
SET RETURN_CODE=%ERRORLEVEL%

:done
set SHOW_USAGE=false
if %RETURN_CODE% == 100 set SHOW_USAGE=true
if %RETURN_CODE% == 99 set SHOW_USAGE=true
if "%SHOW_USAGE%" == "false" (
    GOTO exit_script
)
:usage
ECHO.
ECHO Usage: %SCRIPT_NAME%
ECHO           [-help]
ECHO           [-oracle_home ^<oracle_home^>]
ECHO           -model_file ^<model file^>
ECHO           -target ^<target_name^>
ECHO           -output_dir ^<output_dir^>
ECHO           [-variable_file ^<variable file^>]
ECHO           [-archive_file ^<archive file^>]
ECHO.
ECHO     where:
ECHO         oracle_home   - the existing Oracle Home directory for the domain.
ECHO                         This argument is required unless the ORACLE_HOME
ECHO                         environment variable is set.
ECHO.
ECHO         model_file    - the location of the model file to use.  This can also
ECHO                         be specified as a comma-separated list of model
ECHO                         locations, where each successive model layers on top
ECHO                         of the previous ones.  This argument is required.
ECHO.
ECHO         target        - the target output type. This argument is required.
ECHO.
ECHO         output_dir    - the location for the target output files.  This argument
ECHO                         is required.
ECHO.
ECHO         variable_file - the location of the property file containing the values
ECHO                         for variables used in the model.  This can also be
ECHO                         specified as a comma-separated list of property files,
ECHO                         where each successive set of properties layers on top
ECHO                         of the previous ones.
ECHO.
ECHO         archive_file  - the path to the archive file to use.  This can also be
ECHO                         specified as a comma-separated list of archive files.
ECHO                         The overlapping contents in each archive take precedence
ECHO                         over previous archives in the list.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
