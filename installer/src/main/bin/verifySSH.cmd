@ECHO OFF
@rem **************************************************************************
@rem verifySSH.cmd
@rem
@rem Copyright (c) 2023, Oracle Corporation and/or its affiliates.
@rem Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
@rem
@rem     NAME
@rem       verifySSH.cmd - WLS Deploy tool to verify the environment's SSH configuration.
@rem
@rem     DESCRIPTION
@rem       This script attempts to establish an SSH connection with the provided
@rem       configuration and, optionally, download and/or upload a test file.
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

SET WLSDEPLOY_PROGRAM_NAME=verifySSH

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

call "%SCRIPT_PATH%\shared.cmd" :runWlst verify_ssh.py
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
ECHO           -ssh_host ^<ssh_host^> [-ssh_port ^<ssh_port^>]
ECHO           [-ssh_user ^<ssh_user^>]
ECHO           [
ECHO            -ssh_pass_env ^<ssh_pass_env^> ^|
ECHO            -ssh_pass_file ^<ssh_pass_file^> ^|
ECHO            -ssh_pass_prompt
ECHO           ]
ECHO           [-ssh_private_key ^<ssh_private_key^>]
ECHO           [
ECHO            -ssh_private_key_pass_env ^<ssh_private_key_pass_env^> ^|
ECHO            -ssh_private_key_pass_file ^<ssh_private_key_pass_file^> ^|
ECHO            -ssh_private_key_pass_prompt
ECHO           ]
ECHO           [-remote_test_file ^<remote_test_file^> -local_output_dir ^<local_output_dir^>]
ECHO           [-local_test_file ^<local_test_file^> -remote_output_dir ^<remote_output_dir^>]
ECHO           [-wlst_path ^<wlst_path^>]
ECHO.
ECHO     where:
ECHO         oracle_home     - the existing Oracle Home directory for the domain.
ECHO                           This argument is required unless the ORACLE_HOME
ECHO                           environment variable is set.
ECHO.
ECHO        ssh_host        - the hostname or IP address of the remote machine.  This
ECHO                          argument is required.
ECHO.
ECHO        ssh_port        - the port number to use to connect to the remote machine.
ECHO                          This argument is optional and defaults to 22, if not
ECHO                          specified.
ECHO.
ECHO        ssh_user        - the SSH user name on the remote machine.  This argument
ECHO                          is optional and defaults to the current user on the
ECHO                          local machine, as determined by the user.name Java
ECHO                          system property.
ECHO.
ECHO        ssh_pass_env    - An alternative to entering the SSH user's password
ECHO                          at a prompt. The value is an ENVIRONMENT VARIABLE
ECHO                          name that WDT will use to retrieve the password.
ECHO                          This argument should only be used when using
ECHO                          username/password-based authentication.
ECHO.
ECHO        ssh_pass_file   - An alternative to entering SSH user's password
ECHO                          at a prompt. The value is the name of a file with a
ECHO                          string value which WDT will read to retrieve the
ECHO                          password.  This argument should only be used
ECHO                          when using username/password-based authentication.
ECHO.
ECHO        ssh_private_key - the path to the private key to use for SSH
ECHO                          authentication.  This argument is optional and defaults
ECHO                          to the normal default SSH key (e.g., ~/.ssh/id_rsa).
ECHO                          This argument should only be used when using
ECHO                          public key-based authentication.
ECHO.
ECHO        ssh_private_key_pass_env - An alternative to entering the private key
ECHO                          passphrase at a prompt. The value is an ENVIRONMENT
ECHO                          VARIABLE name that WDT will use to retrieve the
ECHO                          password.  This argument should only be used when
ECHO                          using public key-based authentication and the
ECHO                          private key is encrypted with a passphrase.
ECHO.
ECHO        ssh_private_key_pass_file - An alternative to entering SSH private key
ECHO                          passphrase at a prompt. The value is the name of a
ECHO                          file with a string value which WDT will read to
ECHO                          retrieve the password.  This argument should only be
ECHO                          used when using username/password-based
ECHO                          authentication and the private key is encrypted with
ECHO                          a passphrase.
ECHO.
ECHO         wlst_path      - the Oracle Home subdirectory of the wlst.cmd
ECHO                          script to use (e.g., ^<ORACLE_HOME^>\soa).
ECHO.
ECHO    The -ssh_pass_prompt argument tells WDT to prompt for the SSH user's
ECHO    password and read it from standard input.  This is also useful for
ECHO    scripts that want to pipe the value into the tool's standard input.
ECHO.
ECHO    The -ssh_private_key_pass_prompt argument tells WDT to prompt for the
ECHO    private key passphrase and read it from standard input. This is also
ECHO    useful for scripts that want to pipe the value into the tool's
ECHO    standard input.
ECHO.

:exit_script
IF DEFINED USE_CMD_EXIT (
  EXIT %RETURN_CODE%
) ELSE (
  EXIT /B %RETURN_CODE%
)

ENDLOCAL
