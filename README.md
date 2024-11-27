## Description

This script facilitates downloading deployment logs for specified deployments. It creates a working directory named `logdir` to store and access the logs. At the start, the script checks the `logdir` for any existing files and deletes them. If you choose to create a ZIP archive, any remaining logs in the directory will also be deleted after the archive is created.

The script also scans the logs for personal data, such as *Codice Fiscale* and }email addresses}. For each log file, it identifies the first occurrence of personal data and prints the corresponding line number and file name.

### Usage Examples:

```bash
.\ocp_logs.py -u username -e t DEPLOYMENT_NAME DEPLOYMENT_NAME DEPLOYMENT_NAME
.\ocp_logs.py -u username -e p DEPLOYMENT_NAME
```

- The deployment name can be specified with or without comma.
- If you specify more than one deployment or more than one pod is found, you will be asked if you want to zip the logs.

## Configuration

A `known_hosts` file must exist in the same directory as the script. Each entry in the `known_hosts` file should be formatted as follows:

```
[XX.XX.XX.XX]:22
```

Additionally, specify the hostname or IP of the machine that can access the OpenShift CLI (OC CLI), as well as the OCP Console URL, for login via the `oc login` command. Configure these parameters in the script as follows:

```python
hostname = 'HOSTNAME_OR_IP'
console = 'CONSOLE_URL'
```

The script also supports validating deployment names using a regex pattern if your environment follows a naming convention. This pattern can be configured in `name_check` function under the `pattern` variable.

## Dependencies

This script requires the `Paramiko` library. You can find installation instructions [here](https://www.paramiko.org/installing.html).
