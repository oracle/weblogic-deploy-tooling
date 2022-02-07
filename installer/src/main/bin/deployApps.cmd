@ECHO OFF
@rem **************************************************************************
@rem deployApps.cmd
@rem
@rem Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       deployApps.cmd - WLS Deploy tool to provision apps and resources.
@rem
@rem     DESCRIPTION
@rem       This script configures the base domain, adds resources, and
@rem       deploys applications.
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
@rem WLSDEPLOY_PROPERTIES  - Extra system properties to pass to WLST.  The caller
@rem                         can use this environment variable to add additional
@rem                         system properties to the WLST environment.
@rem

SETLOCAL

SET WLSDEPLOY_PROGRAM_NAME=deployApps

SET SCRIPT_NAME=%~nx0
SET SCRIPT_ARGS=%*
SET SCRIPT_PATH=%~dp0
FOR %%i IN ("%SCRIPT_PATH%") DO SET SCRIPT_PATH=%%~fsi
IF %SCRIPT_PATH:~-1%==\ SET SCRIPT_PATH=%SCRIPT_PATH:~0,-1%

call "%SCRIPT_PATH%\shared.cmd" :checkArgs %SCRIPT_ARGS%
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

SET MIN_JDK_VERSION=7
if "%USE_ENCRYPTION%" == "true" (
  SET MIN_JDK_VERSION=8
)

@rem required Java version is dependent on use of encryption
call "%SCRIPT_PATH%\shared.cmd" :javaSetup %MIN_JDK_VERSION%
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

call "%SCRIPT_PATH%\shared.cmd" :runWlst deploy.py
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
ECHO Usage: %SCRIPT_NAME% [-help] [-use_encryption]
ECHO              [-oracle_home ^<oracle_home^>]
ECHO              -domain_home ^<domain_home^>
ECHO              [-archive_file ^<archive_file^>]
ECHO              [-model_file ^<model_file^>]
ECHO              [-variable_file ^<variable_file^>]
ECHO              [-domain_type ^<domain_type^>]
ECHO              [-passphrase_env ^<passphrase_env^>]
ECHO              [-passphrase_file ^<passphrase_file^>]
ECHO              [-wlst_path ^<wlst_path^>]
ECHO              [-cancel_changes_if_restart_required]
ECHO              [-discard_current_edit]
ECHO              [-output_dir]
ECHO              [-admin_pass_env ^<admin_pass_env^>
ECHO              [-admin_pass_file ^<admin_pass_file^>
ECHO              [-admin_url ^<admin_url^>
ECHO               -admin_user ^<admin_user^>
ECHO              ]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This is required unless the ORACLE_HOME environment
ECHO                           variable is set.
ECHO.
ECHO         domain_home     - the domain home directory
ECHO.
ECHO         archive_file    - the path to the archive file to use.  If the -model_file
ECHO                           argument is not specified, the model file in this archive
ECHO                           will be used.  This can also be specified as a
ECHO                           comma-separated list of archive files.  The overlapping contents in
ECHO                           each archive take precedence over previous archives in the list.
ECHO.
ECHO         model_file      - the location of the model file to use.  This can also be specified as a
ECHO                           comma-separated list of model locations, where each successive model
ECHO                           layers on top of the previous ones.
ECHO.
ECHO         variable_file   - the location of the property file containing the values for variables used in
ECHO                           the model. This can also be specified as a comma-separated list of property files,
ECHO                           where each successive set of properties layers on top of the previous ones.
ECHO.
ECHO         domain_type     - the type of domain (e.g., WLS, JRF).
ECHO                           Used to locate wlst.cmd if -wlst_path not specified
ECHO.
ECHO         passphrase_env  - An alternative to entering the encryption passphrase at a prompt. The value is an
ECHO                           ENVIRONMENT VARIABLE name that WDT will use to retrieve the passphrase.
ECHO.
ECHO         passphrase_file - An alternative to entering the encryption passphrase at a prompt. The value is
ECHO                           the name of a file with a string value which WDT will read to retrieve the passphrase.
ECHO.
ECHO         wlst_path       - the Oracle Home subdirectory of the wlst.cmd
ECHO                           script to use (e.g., ^<ORACLE_HOME^>\soa)
ECHO.
ECHO         admin_url       - the admin server URL (used for online deploy)
ECHO.
ECHO         admin_user      - the admin username (used for online deploy)
ECHO.
ECHO         admin_pass_env  - An alternative to entering the admin password at a prompt. The value is a ENVIRONMENT
ECHO                           VARIABLE name that WDT will use to retrieve the password.
ECHO.
ECHO         admin_pass_file - An alternative to entering the admin password at a prompt. The value is a the name of a
ECHO                           file that contains a password string that the tool will read to retrieve the password.
ECHO.
ECHO         cancel_changes_if_restart_required - cancel the changes if the update requires domain restart
ECHO.
ECHO         discard_current_edit      - discard all existing changes before starting update
ECHO.
ECHO         output_dir      - if present, write restart information to this directory as restart.file, or,
ECHO                           if cancel_changes_if_restart_required used, write non dynamic changes information to non_dynamic_changes.file
ECHO.
ECHO    The -use_encryption switch tells the program that one or more of the
ECHO    passwords in the model or variables files are encrypted.  The program will
ECHO    prompt for the decryption passphrase to use to decrypt the passwords.
ECHO    Please note that Java 8 or higher is required when using this feature.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
