import pexpect
import os
import time
import pandas as pd
import datetime
import random
from tqdm import tqdm
import string

start_data = []
termination_data = []
run_id = ''.join(random.choice(string.ascii_letters) for _ in range(8))
os.makedirs(run_id)

print(f'Starting a run with an id {run_id}')

NUM_TRIALS = 5
STORAGE_LATENCIES = [0, 1000, 10000, 100000, 1000000, 10000000, 100000000, 1000000000]

FOLDER_MOUNT_PATH = "/mnt/ext4"
MINECRAFT_PATH = 'server.jar'
PRESENT_DIR = os.getcwd()
current_dir = "./"

def log(log_msg):
    with open(f'{run_id}/logs.txt', 'a') as f:
        f.write(f'{datetime.datetime.now()} - {log_msg} \n')

def execute_and_wait(cmd, timeout=10):
    log(f'Executing "{cmd}"')
    process = pexpect.spawn('/bin/sh', ['-c', cmd], encoding='utf-8')
    process.expect(pexpect.EOF, timeout=timeout)
    output = process.before  # Capture the output
    process.wait()

    return process.exitstatus, output

def execute_and_detach(cmd):
    child = pexpect.spawn(cmd, encoding='utf-8')
    try:
        child.expect(pexpect.EOF, timeout=0.5)
    except:
        pass
    return child

def prepare_storage(storage_latency):
    log('Starting to prepare a storage')
    chmod_code, _ = execute_and_wait(f'sudo chmod +x createnullblk.sh')
    if chmod_code != 0:
        raise Exception('Could not chmod nullblk')
    
    log('Creating a memory backed block device')
    nullblk_code, nullblk = execute_and_wait(f'sudo ./createnullblk.sh 512 4096 {storage_latency}')
    if nullblk_code != 0:
        raise Exception('Could not create nullblock space')
    
    nullblk = nullblk.strip()
    dev_path = f'/dev/{nullblk}'
    log(f'Creating a file system on memory backed storage device {dev_path}')
    
    mkfs_code, output = execute_and_wait(f'sudo mkfs.ext4 {dev_path}', 90)
    if mkfs_code != 0:
        log(output)
        raise Exception('Could not mark the space for file system')
    
    log('Creating a root folder')

    root_fpath = '/mnt/ext4'
    
    if not os.path.exists(root_fpath):
        mkdir_code, output = execute_and_wait(f'sudo mkdir {root_fpath}')
        if mkdir_code != 0:
            log(output)
            raise Exception('Could not make /mnt/ext4 folder')
    
    log('Mounting a block device onto a root folder')
    mount_code, _ = execute_and_wait(f'sudo mount {dev_path} /mnt/ext4', 60)
    if mount_code != 0:
        raise Exception('Could not mount folder')
    
    log('Copying Minecraft into a new folder')
    cp_code, output = execute_and_wait(f'sudo cp -r {PRESENT_DIR} {root_fpath}', 60)
    if cp_code != 0:
        log(output)
        raise Exception('Could not run copy into marked directory')

    return root_fpath, dev_path

def start_minecraft():
    log('Starting Minecraft')
    return execute_and_detach(f'sudo java -jar {MINECRAFT_PATH}')

def clean_up(root_dir, dev_path):
    log('Unmounting the device')
    unmount_code, unmount_output = execute_and_wait(f'sudo umount -f {root_dir}')
    if unmount_code != 0:
        log(f'Warning: Could not unmount {dev_path}. It might not be mounted. Details: {unmount_output}')
        raise Exception('Could not unmount the device')

    log('Deleting the device')
    deletenullb_code, deletenullb_output = execute_and_wait(f'sudo rm -rf /dev/nullb*')
    if deletenullb_code != 0:
        log(deletenullb_output)
        raise Exception('Could not delete a nullblock device')

    deletenullb_conf_code, deletenullb_conf_output = execute_and_wait(f'sudo rmdir /sys/kernel/config/nullb/nullb0')
    if deletenullb_conf_code != 0:
        log(deletenullb_conf_output)
        raise Exception('Could not delete a nullblock device config')

pd.DataFrame(start_data).to_csv(f'{run_id}/start_data.csv')
pd.DataFrame(termination_data).to_csv(f'{run_id}/termination.csv')

if not os.path.exists(run_id):
    os.makedirs(run_id)

    if not os.path.exists(os.path(run_id, 'traces')):
        os.makedirs(os.path(run_id, 'traces'))

for storage_latency in tqdm(STORAGE_LATENCIES):
    print(f'Starting to test device with a storage latency of {storage_latency}')
    for i in tqdm(range(NUM_TRIALS)):
        log(f'Starting the trial number {i}')
        root_dir, dev_path = prepare_storage(storage_latency)
        os.chdir(f'{root_dir}/storage-stick')

        start_time = time.time()
        minecraft = start_minecraft()

        total_run_logs_file = f'{run_id}/total_latency_{storage_latency}_trial_{i}.txt'
        total_run_logs = execute_and_detach(f'sudo strace -f -tt -T -y -yy -s 2048 -e trace=write,writev,pwrite64,pread64,read,readv,openat,mmap -o {total_run_logs_file} -p {minecraft.pid}')

        start_run_logs_file = f'{run_id}/start_run_{storage_latency}_trial_{i}.txt'
        start_run_logs = execute_and_detach(f'sudo strace -f -tt -T -y -yy -s 2048 -e trace=write,writev,pwrite64,pread64,read,readv,openat,mmap -o {start_run_logs_file} -p {minecraft.pid}')

        minecraft.expect('Done', timeout=60)
        end_time = time.time()
        time_to_start = end_time-start_time

        start_data.append({
            'latency': storage_latency,
            'sample_num': i,
            'time': time_to_start
        })

        start_time = time.time()
        terminate_run_logs_file = f'{run_id}/start_run_{storage_latency}_trial_{i}.txt'
        terminate_run_logs = execute_and_detach(f'sudo strace -f -tt -T -y -yy -s 2048 -e trace=write,writev,pwrite64,pread64,read,readv,openat,mmap -o {terminate_run_logs_file} -p {minecraft.pid}')

        minecraft.terminate()
        minecraft.expect(pexpect.EOF, timeout=300)
        end_time = time.time()
        time_to_terminate = end_time - start_time

        termination_data.append({
            'latency': storage_latency,
            'sample_num': i,
            'time': time_to_terminate
        })

        os.chdir(PRESENT_DIR)
        clean_up(root_dir, dev_path)

    pd.DataFrame(start_data).to_csv(f'{run_id}/start_data.csv')
    pd.DataFrame(termination_data).to_csv(f'{run_id}/termination.csv')

