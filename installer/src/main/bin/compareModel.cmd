@ECHO OFF
@rem **************************************************************************
@rem compareModel.cmd
@rem
@rem Copyright (c) 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       compareModel.cmd - WLS Deploy tool to compare two models (new vs old)
@rem
@rem     DESCRIPTION
@rem       This script compares two models. The models compared must be both yaml or both json files
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

SET WLSDEPLOY_PROGRAM_NAME=compareModel

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

call "%SCRIPT_PATH%\shared.cmd" :runJython compare_model.py
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
ECHO           [-oracle_home ^<oracle_home^> required unless the ORACLE_HOME environment variable is set]
ECHO           [-output_dir ^<output_dir^> write the outputs to the directory specified]
ECHO           [                        diffed_model.json - json output of the differences between the models]
ECHO           [                        diffed_model.yaml - yaml output of the differences between the models]
ECHO           [                        compare_model_stdout - stdout of the tool compareModel ]
ECHO           [-variable_file ^<variable file^>  variable file used for macro substitution]
ECHO           ^<new model^> ^<old model^>      Must be the last two arguments and must be same extensions (yaml or json)
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
