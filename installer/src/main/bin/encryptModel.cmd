@ECHO OFF
@rem **************************************************************************
@rem encryptModel.cmd
@rem
@rem Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
@rem Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       encryptModel.cmd - WLS Deploy tool to encrypt the password fields in
@rem                          the model and any referenced variables.
@rem
@rem     DESCRIPTION
@rem       This script searches the model file and variable file, if provided,
@rem       looking for password fields and encrypts them using the supplied
@rem       passphrase.  This passphrase must be passed to other tools in
@rem       order for them to be able to decrypt the passwords.  Please note
@rem       this feature requires JDK 1.8 or higher due to the encryption
@rem       algorithms selected.
@rem
@rem This script uses the following variables:
@rem
@rem JAVA_HOME             - The location of the JDK to use.  The caller must set
@rem                         this variable to a valid Java 8 (or later) JDK.
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

SET WLSDEPLOY_PROGRAM_NAME=encryptModel

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

@rem Java 8 is required for encryption library
call "%SCRIPT_PATH%\shared.cmd" :javaSetup 8
SET RETURN_CODE=%ERRORLEVEL%
if %RETURN_CODE% NEQ 0 (
  GOTO done
)

call "%SCRIPT_PATH%\shared.cmd" :runJython encrypt.py
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
ECHO Usage: %SCRIPT_NAME% [-help] [-manual]
ECHO              [-oracle_home ^<oracle_home^>]
ECHO              [-model_file ^<model_file^>]
ECHO              [-variable_file ^<variable_file^>]
ECHO              [-passphrase_env ^<passphrase_env^>]
ECHO              [-passphrase_file ^<passphrase_file^>]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This is required unless the ORACLE_HOME environment
ECHO                           variable is set.
ECHO.
ECHO         model_file      - the location of the model file to use. This can also
ECHO                           be a comma-separated list of locations of a set of
ECHO                           models. All models will be written back to the
ECHO                           original locations.
ECHO.
ECHO         variable_file   - the location and name of the property file containing
ECHO                           the variable values for all variables used in
ECHO                           the model(s).
ECHO.
ECHO         passphrase_env  - An alternative to entering the encryption passphrase at a prompt. The value is a
ECHO                           ENVIRONMENT VARIABLE name that WDT will use to retrieve the passphrase.
ECHO.
ECHO         passphrase_file - An alternative to entering the encryption passphrase at a prompt. The value is a
ECHO                           the name of a file with a string value which WDT will read to retrieve the passphrase.
ECHO.
ECHO     The -manual switch can be used to run the tool without a model and get
ECHO     the encrypted value for a single password.
ECHO.
ECHO     NOTE: This tool requires the use of JDK version 1.8 or higher.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
