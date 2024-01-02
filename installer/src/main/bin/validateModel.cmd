@ECHO OFF
@rem **************************************************************************
@rem validateModel.cmd
@rem
@rem Copyright (c) 2017, 2023, Oracle and/or its affiliates.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       validateModel.cmd - WLS Deploy tool to validate artifacts
@rem
@rem     DESCRIPTION
@rem        This script validates the model and archive structure
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

SET WLSDEPLOY_PROGRAM_NAME=validateModel

SET SCRIPT_NAME=%~nx0
SET SCRIPT_ARGS=%*
SET SCRIPT_PATH=%~dp0
FOR %%i IN ("%SCRIPT_PATH%") DO SET SCRIPT_PATH=%%~fsi
IF %SCRIPT_PATH:~-1%==\ SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

@rem check for deprecated -print_usage argument
FOR %%a IN (%*) do (
    IF "%%a" == "-print_usage" (
      ECHO.
      ECHO The -print_usage functionality has been moved to modelHelp.cmd
      EXIT /B 99
    )
)

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

call "%SCRIPT_PATH%\shared.cmd" :runJython validate.py
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
ECHO              [-variable_file ^<variable_file^>]
ECHO              [-archive_file ^<archive_file^>]
ECHO              [-target ^<target^>]
ECHO              [-target_version ^<target_version^>]
ECHO              [-target_mode ^<target_mode^>]
ECHO              [-domain_type ^<domain_type^>]
ECHO              [-method ^<method^>]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This argument is required unless the ORACLE_HOME
ECHO                           environment variable is set.
ECHO.
ECHO         model_file      - the location of the model file to use.  This can also
ECHO                           be specified as a comma-separated list of model
ECHO                           locations, where each successive model layers on top
ECHO                           of the previous ones.  This argument is required.
ECHO.
ECHO         variable_file   - the location of the property file containing the
ECHO                           variable values for all variables used in the model.
ECHO                           If the variable file is not provided, validation will
ECHO                           only validate the artifacts provided.
ECHO.
ECHO         archive_file    - the path to the archive file to use.  If the archive
ECHO                           file is not provided, validation will only validate the
ECHO                           artifacts provided.  This can also be specified as a
ECHO                           comma-separated list of archive files.  The overlapping
ECHO                           contents in each archive take precedence over previous
ECHO                           archives in the list.
ECHO.
ECHO         target          - target platform (wko, etc.).  This determines the
ECHO                           structure of the kubernetes section.
ECHO.
ECHO         target_version - the target version of WebLogic Server the tool
ECHO                          should use to validate the model content.  This
ECHO                          version number can be different than the version
ECHO                          being used to run the tool.  If not specified, the
ECHO                          tool will validate against the version being used
ECHO                          to run the tool.
ECHO.
ECHO         target_mode    - the target WLST mode that the tool should use to
ECHO                          validate the model content.  The only valid values
ECHO                          are online or offline.  If not specified, the tool
ECHO                          defaults to WLST offline mode.
ECHO.
ECHO         domain_type    - the type of domain (e.g., WLS, JRF).  If not specified,
ECHO                          the default is WLS.
ECHO.
ECHO         method         - the validation method to apply. Options: lax, strict.
ECHO                          The lax method will skip validation of external model
ECHO                          references like @@FILE@@.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
