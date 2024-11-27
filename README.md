## Description

This script will download any given deployment logs. It creates a working directory "logdir", which is used to store and access logs by the script. At the start it checks for any file in the directory and deletes it, if you choose to create a zip archive, the remaining logs will be deleted as well. 
It will search fo personal data such as Codice Fiscale and email, printing line number and file name. It stops searching at the first occurency of PD for each log file.

Examples:

.\ocp_logs.py -u username -e t DEPLOYMENT_NAME DEPLOYMENT_NAME DEPLOYMENT_NAME

.\ocp_logs.py -u username -e p DEPLOYMENT_NAME

The deployment name can be specified with or without comma.
If you specify more than one deployment or more than one pod is found, you will be asked if you want to zip the logs.

## Configuration

A known_hosts file is needed in the same directory of the script. Every host for each entry in known_hosts is going to be formatted as follows:

[XX.XX.XX.XX]:22

Specify hostname or IP of the machine able to access OC CLI and the OCP Console url used to login via "oc login" command as follows:

hostname = 'HOSTNAME_OR_IP'
console = 'CONSOLE_URL'

You can configure the script to check the deployment names using a regex if a naming convention is adopted, configurable in function "name_check" under "pattern".

## Dependencies

[Paramiko](https://www.paramiko.org/installing.html)
