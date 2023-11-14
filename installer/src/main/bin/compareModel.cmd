@ECHO OFF
@rem **************************************************************************
@rem compareModel.cmd
@rem
@rem Copyright (c) 2020, 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
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
ECHO Usage: %SCRIPT_NAME% [-help]
ECHO           [-oracle_home ^<oracle_home^>]
ECHO           [-output_dir ^<output_dir^>]
ECHO           [-variable_file ^<variable file^>]
ECHO           ^<new_model^> ^<old_model^>
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This argument is required unless the ORACLE_HOME
ECHO                           environment variable is set.
ECHO.
ECHO        output_dir       - The directory to which the output files are written:
ECHO                             diffed_model.json - differences in JSON.
ECHO                             diffed_model.yaml - differences in YAML.
ECHO                             compare_model_stdout - compareModel tool stdout.
ECHO.
ECHO         variable_file   - the location of the property file containing the
ECHO                           values for variables used in the model. This can
ECHO                           also be specified as a comma-separated list of
ECHO                           property files, where each successive set of
ECHO                           properties layers on top of the previous ones.
ECHO.
ECHO         new_model       - the newer model to use for comparison.
ECHO.
ECHO         old_model       - the older model to use for comparison.
ECHO.
ECHO    NOTE: The model files being compared must be in the same format
ECHO          (i.e., JSON or YAML).
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
