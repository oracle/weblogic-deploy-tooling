@ECHO OFF
@rem **************************************************************************
@rem injectVariables.cmd
@rem
@rem Copyright (c) 2018, 2024, Oracle and/or its affiliates.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       injectVariables.cmd - Inject variables into the model.
@rem
@rem     DESCRIPTION
@rem        This script will inject variable tokens into the model and persist the variables to the
@rem        indicated variable file. This can be run against a model that has injected variables. Any
@rem        injected variables will not be replaced. If the existing variable file was provided, the
@rem        new injected variables will be appended to the file.
@rem
@rem This script uses the following variables:
@rem
@rem JAVA_HOME            - The location of the JDK to use.  The caller must set
@rem                        this variable to a valid Java 7 (or later) JDK.
@rem
@rem WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
@rem                         can use this environment variable to add additional
@rem                         system properties to the Java environment.
@rem

SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=injectVariables

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

call "%SCRIPT_PATH%\shared.cmd" :runJython variable_inject.py
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
ECHO              [-oracle_home ^<oracle_home^>]
ECHO              -model_file ^<model_file^>
ECHO              [-variable_injector_file ^<variable_injector_file^>]
ECHO              [-variable_properties_file ^<variable_file^>]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This argument is required unless the ORACLE_HOME
ECHO                           environment variable is set.
ECHO.
ECHO         model_file      - the location of the model file in which variables will
ECHO                           be injected.  This argument is required.
ECHO.
ECHO         variable_injector_file - the location of the variable injector file
ECHO                           which contains the variable injector keywords for this
ECHO                           model injection run. If this argument is not provided,
ECHO                           the model_variable_injector.json file must exist in
ECHO                           the lib directory in the WLSDEPLOY_HOME location.
ECHO.
ECHO         variable_file   - the location of the property file in which to store
ECHO                           any variable names injected into the model. This
ECHO                           argument overrides the value in the model injector
ECHO                           file.  If the variable file is not listed in the
ECHO                           model injector file, and this command-line argument
ECHO                           is not used, the variable properties will be located
ECHO                           and named based on the model file or archive file name
ECHO                           and location.  If the variable file exists, new
ECHO                           variable values will be appended to the file.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
