#!/usr/bin/expect -f
spawn %ENCRYPT_MODEL_SCRIPT% -oracle_home %MW_HOME% -model_file %MODEL_FILE%
expect "Enter the encryption passphrase to use:"
send -- "Welcome1\r"
expect "Re-enter the encryption passphrase to use:"
send -- "Welcome1\r"
expect eof
