"""
Copyright (c) 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import sys
readDomain(sys.argv[1])
cd('AppDeployment/simple-app')
print('SRCPATH=' + get('SourcePath'))
exit()
