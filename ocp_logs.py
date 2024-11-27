import paramiko
import argparse
import os
import getpass
import zipfile
import re
import time

# Configure logging
#logging.basicConfig(filename='script.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Declaring bastions variables 
def env_chosen(env):
    match env:
        case 'p':
            hostname = 'HOSTNAME_OR_IP'
            console = 'CONSOLE_URL'
            environment='production'
        case 't':
            hostname = 'HOSTNAME_OR_IP'
            console = 'CONSOLE_URL'
            environment='test'
        case 'd':
            hostname = 'HOSTNAME_OR_IP'
            console = 'CONSOLE_URL'
            environment='development'
    return hostname, console, environment

# Directory existence check and cleaning any remaining log
def remote_dir_check(ssh):
    try:
        command = f'ls | grep -q logdir; echo $?'
        (stdin, stdout, stderr) = ssh.exec_command(command)
        check = stdout.read().decode().strip()

        if check == '0':
                command = 'ls -ltr logdir/'
                stdin, stdout, stderr = ssh.exec_command(command)
                check_empty = stdout.read().decode().strip()
                if check_empty == 'total 0':
                    return 0
                else:
                    command = 'rm logdir/*.log'
                    ssh.exec_command(command)
                    print('Found logs inside remote folder.\nEmptying...')
        else:
            command = f'mkdir logdir; ls | grep -q logdir; echo $?'
            (stdin, stdout, stderr) = ssh.exec_command(command)
            print('Remote dir not found, creating it...')
        return 0
    
    except paramiko.SSHException as e:
        print(f"Remote directory check failed: {e}")
        raise
    

# Downloading logs to local path
def sftp_logs(local_path, remote_path, pods, ssh):
    try:
        print ('Downloading logs on local path...')
        sftp = ssh.open_sftp()
        for pod in pods:
            sftp.get(f'{remote_path}{pod[4:]}.log', f'{local_path}\\{pod[4:]}.log')
        sftp.close()
        print ('Finished downloading')
        return 0
    
    except (paramiko.SFTPError, FileNotFoundError) as e:
        print(f"SFTP operation failed: {e}")
        raise
    
# Cleaning up remote directory
def remote_dir_cleanup (ssh, dir_path):
    try:
        print('Cleaning remote logdir...')
        command = f'rm {dir_path}'
        ssh.exec_command(command)
        return 0
    
    except paramiko.SSHException as e:
        print(f"SSH command failed: {e}")
        raise

# Creating zip archive and deleting remaining files on local path
def zip_files (local_path, zip_name):
    try:
        print('Creating a zip archive...')
        zip_path = os.path.join(local_path, zip_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for folder_name, subfolders, filenames in os.walk(local_path):
                for filename in filenames:
                    if filename != zip_name:
                        file_path = os.path.join(folder_name, filename)
                        zip_ref.write(file_path, arcname=os.path.relpath(file_path, local_path))

        files = os.listdir(local_path)
        for file in files:
            if file != zip_name:  
                    os.remove(os.path.join(local_path, file))
        return 0
    
    except (OSError, zipfile.ZipFile) as e:
        print(f"Failed to create zip archive: {e}")
        raise

# Directory existence check and cleaning any remaining log or zip archive
def local_dir_check(local_path):
    try:
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        files = os.listdir(local_path)
        if files:
            for file in files:
                os.remove(f'{local_path}\\{file}')

        return 0

    except (OSError, FileNotFoundError) as e:
        print(f"Failed to check local directory: {e}")
        raise

# Opening a channel to wait for the command execution
def ssh_channel(ssh, command):
    try:
        transport = ssh.get_transport()
        transport.set_keepalive(20)
        channel = transport.open_session()
        channel.settimeout(30)
        channel.exec_command(command)
        exit_status = channel.recv_exit_status()
        return exit_status
    
    except paramiko.SSHException as e:
        print(f"SSH channel command failed: {e}")
        raise

# Define the parser and declare arguments
def arg_parser ():
    parser = argparse.ArgumentParser(description='Type --help or -h for help')

    parser.add_argument('-e', '--environment', action="store", choices=['p', 't', 'd'],
                        help='Specify the environment - p: production, c: test, s: development')
    parser.add_argument('deployment', action="store", nargs='+',
                        help='Specify the deployment(s)')
    parser.add_argument('-u', '--username', action="store", dest='username',
                        help='Specify the username', required=True)
    
    return parser.parse_args()

# Checking for personal data inside logs
def personal_data_check(local_path):
    print('\nSearching for possible personal data...')
    
    pattern_cf = re.compile(r'\b([A-Z]{6}[0-9LMNPQRSTUV]{2}[ABCDEHLMPRST]{1}[0-9LMNPQRSTUV]{2}[A-Z]{1}[0-9LMNPQRSTUV]{3}[A-Z]{1})\b|\b([0-9]{11})\b')
    pattern_mail = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    pers_data = 0
    
    try:
        files = os.listdir(local_path)

    except OSError as e:
        print(f"Error accessing directory: {e}")
        return 1
    
    for file in files:
        file_path = os.path.join(local_path, file)
        try:
            # Using with operator makes sure the file is closed when finished
            with open(file_path, 'r') as f:
                for line_number, line in enumerate(f, start=1):
                    if pattern_cf.search(line):
                        if pers_data == 0:
                            print('\n#############################################')
                            print('#                                           #')
                            print('#       Possible personal data found        #')
                            print('#                                           #')
                            print('#############################################\n')
                            pers_data = 1
                        print(f'***** Codice fiscale - Line {line_number} - {file} *****')
                        break
                    elif pattern_mail.search(line):
                        if pers_data == 0:
                            print('\n#############################################')
                            print('#                                           #')
                            print('#       Possible personal data found        #')
                            print('#                                           #')
                            print('#############################################\n')
                            pers_data = 1
                        print(f'***** Email - Line {line_number} - {file} *****')
                        break
                        
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error reading file {file_path}: {e}")
        
    if pers_data == 1: 
        return 0
    else:
        print("No personal data found")
        return 0

# Searching for namespace    
def namespace_lookout(deployment, ssh):
    print('\nSearching for the right namespace...')
    try:
        command = f"oc get po -A | awk '/{deployment[0].lower()}/ {{print $1;exit;}}'"
        (stdin, stdout, stderr) = ssh.exec_command(command)
        time.sleep(1)
        namespace = stdout.read().decode().strip()
        if namespace:
            print(f'Namespace is: {namespace}\n')
        else:
            raise Exception
        return namespace
    except Exception:
        print(f"Error searching for namespace")

# Check for the existence of every pod in the current namespace
# and remove non existing pods from deployment variable
def namespace_check(deployment, ssh, namespace):
    deploy_remove = []
    for dp in deployment:
        command = f"oc get po -n {namespace} | grep {dp.lower()}"
        (stdin, stdout, stderr) = ssh.exec_command(command)
        deploy_check = stdout.read().decode().strip()
        if not deploy_check:
            print (f'--WARN: {dp} not found in current namespace\n')
            deploy_remove.append(dp)
            
    deployment = [dp for dp in deployment if dp not in deploy_remove]
            
    return deployment

# Check if deployments meet the naming convention
def name_check(deployment):
    pattern = re.compile(r'\bINSERT_PATTERN\b')
    deploy_remove = []
    for dp in deployment:
            if not pattern.search(dp):
                print(f'\n--WARN: It looks like \"{dp}\" does not follow the standard naming convention. ', end="")
                check = input('Is it the right name? [Y/n] ')
                if check == 'n' or check == 'N':
                    deploy_remove.append(dp)
                    
    deployment = [dp for dp in deployment if dp not in deploy_remove]
    return deployment

def ssh_connection(hostname, port, username, password):
    print('Trying SSH connection...')
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.join(os.path.dirname(__file__), 'known_hosts'))
    ssh.connect(hostname, port, username, password)
    return ssh

def ssh_login(console, username, password, ssh):
    print('Logging on OCP...') 
    command = f'oc login {console} -u {username} -p {password}'
    ssh_channel(ssh, command)
    password = 'null'

def main():
    try:
        # Parsing the command line for arguments, setting variables and asking for password
        args = arg_parser()
        hostname, console, env = env_chosen(args.environment)
        username = args.username
        deployments = args.deployment
        deployment = [item for items in deployments for item in items.split(",")]

        # Check if deployments meet the naming convention
        deployment = name_check(deployment)
        
        if len(deployment) == 0:
            raise Exception('No deployment specified')

        password = getpass.getpass('\nInsert password: ')
        port = '22' # port for SSH
        zip_name = 'ms-log.zip' # zip archive name
        remote_path = f'/home/users/{username}/logdir/' # remote path for temporary storing logs
        local_path= os.path.join(os.path.dirname(__file__),'logdir') # local path for logs download

        print(f'\nRetrieving logs from {env} of ', end="")
        print(', '.join(deployment))

        # Begin SSH connection: loading the system host keys and connecting
        # known_hosts file needs to be in the same directory of this script
        ssh = ssh_connection(hostname, port, username, password)
        
        # Logging on OCP console
        ssh_login(console, username, password, ssh)

        # Checking for the directories to store logs in and eventually creating it
        # If already existing checks for existing log files and deletes them
        remote_dir_check(ssh)
        local_dir_check(local_path)

        # Searching for namespace the pod is in
        namespace = namespace_lookout(deployment, ssh)
        if not namespace:
            raise Exception('Could not find pod')
        if len(deployment) > 1:
            deployment = namespace_check (deployment, ssh, namespace)

        # Getting pod logs and saving them in local folder /logdir/
        for dp in deployment:
            command = f'oc get po -n {namespace} -oname | grep -i {dp}'
            (stdin, stdout, stderr) = ssh.exec_command(command)
            pods = stdout.read().decode().strip().split('\n')
            if pods:
                pod_count = 0
                for pod in pods:
                    command = f'oc logs {pod} -n {namespace} > ./logdir/{pod[4:]}.log' 
                    ssh_channel(ssh, command)      
                    if pod_count > 0:
                        print(f'Saving logs of {dp} replica {pod_count + 1}')
                    else:
                        print(f'Saving logs of {dp}')
                    pod_count += 1
                sftp_logs(local_path, remote_path, pods, ssh)   
            else:
                print(f'Pod {dp} not found in current namespace') 

        # Cleaning up logdir server-side
        remote_dir_cleanup(ssh, remote_path + '*.log')

        # Checking for personal data occurencies inside logs (CF, email)
        personal_data_check(local_path)
            
        # Asking to create a zip archive if more than one log is downloaded
        if pod_count > 1 or len(deployment) > 1:
            zip = input('\nSaving more than one log, create a zip archive? [Y/n]: ')
            if zip == 'y' or zip == 'Y':
                zip_files(local_path, zip_name)

        print(f'\nDone!\nYour logs are located at {local_path}\n')

        ssh.close()

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()