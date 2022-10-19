@ECHO OFF
@rem **************************************************************************
@rem validateModel.cmd
@rem
@rem Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
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
ECHO              [-model_file ^<model_file^>]
ECHO              [-variable_file ^<variable_file^>]
ECHO              [-archive_file ^<archive_file^>]
ECHO              [-target ^<target^>]
ECHO              [-target_version ^<target_version^>]
ECHO              [-target_mode ^<target_mode^>]
ECHO              [-domain_type ^<domain_type^>]
ECHO              [-wlst_path ^<wlst_path^>]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This is required unless the ORACLE_HOME environment
ECHO                           variable is set.
ECHO.
ECHO         context         - specify the context for printing out the model structure.
ECHO                           By default, the specified folder attributes and subfolder
ECHO                           names are printed.  Use one of the optional control
ECHO                           switches to customize the behavior.  Note that the
ECHO                           control switches are mutually exclusive.
ECHO.
ECHO         model_file      - the location of the model file to use.  This can also be specified as a
ECHO                           comma-separated list of model locations, where each successive model
ECHO                           layers on top of the previous ones.
ECHO                           If not specified, the tool will look for the model in the archive.
ECHO                           If the model is not found, validation will only
ECHO                           validate the artifacts provided.
ECHO.
ECHO         variable_file   - the location of the property file containing
ECHO                           the variable values for all variables used in the model.
ECHO                           If the variable file is not provided, validation will
ECHO                           only validate the artifacts provided.
ECHO.
ECHO         archive_file    - the path to the archive file to use.  If the archive file is
ECHO                           not provided, validation will only validate the
ECHO                           artifacts provided.  This can also be specified as a
ECHO                           comma-separated list of archive files.  The overlapping contents in
ECHO                           each archive take precedence over previous archives in the list.
ECHO.
ECHO         target          - target platform (wko, etc.).
ECHO                           this determines the structure of the kubernetes section.
ECHO.
ECHO         target_version  - the target version of WebLogic Server the tool
ECHO                           should use to validate the model content.  This
ECHO                           version number can be different than the version
ECHO                           being used to run the tool.  If not specified, the
ECHO                           tool will validate against the version being used
ECHO                           to run the tool.
ECHO.
ECHO         target_mode     - the target WLST mode that the tool should use to
ECHO                           validate the model content.  The only valid values
ECHO                           are online or offline.  If not specified, the tool
ECHO                           defaults to WLST offline mode.
ECHO.
ECHO         domain_type     - the type of domain (e.g., WLS, JRF).
ECHO                           Used to locate wlst.cmd if -wlst_path not specified
ECHO.
ECHO         wlst_path       - the Oracle Home subdirectory of the wlst.cmd
ECHO                           script to use (e.g., ^<ORACLE_HOME^>\soa)
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
