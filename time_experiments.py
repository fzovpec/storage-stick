import pexpect
import os
import time
import pandas as pd
import datetime
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description='Process test arguments')
parser.add_argument('--pregenerate', type=bool, help='Control whether the world should be pre-generated or started anew', default=False)
parser.add_argument('--storage_latency', nargs='+', type=int, help='List of storage latencies to test (in ms)', default=[0])
parser.add_argument('--mem_limit', nargs='+', type=int, help='List of memory limits to test', default=[2048])
parser.add_argument('--mems_limit', nargs='+', type=int, help='List of memory+swap limits to test', default=[4096])
parser.add_argument('--num_players', nargs='+', type=int, help='Number of players to connect', default=[0])

args = parser.parse_args()
pregenerate = args.pregenerate

STORAGE_LATENCIES = args.storage_latency
MEM_LIMITS = args.mem_limit
MEMS_LIMIT = args.mems_limit
NUM_PLAYERS = args.num_players
MEM_GROUP_NAME = "minecraft_test"

start_data = []
termination_data = []
run_id = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

print(f'Starting a run with an id {run_id}')

NUM_TRIALS = 1

FOLDER_MOUNT_PATH = "/mnt/ext4"
MINECRAFT_PATH = 'server.jar'
PRESENT_DIR = os.getcwd()
current_dir = "./"


if not os.path.exists('log'):
    os.makedirs('log')

if not os.path.exists(run_id):
    os.makedirs(os.path.join(PRESENT_DIR, 'log', run_id))
    if not os.path.exists(os.path.join(PRESENT_DIR, 'log', run_id, 'traces')):
        os.makedirs(os.path.join(PRESENT_DIR, 'log', run_id, 'traces'))

def log(log_msg):
    with open(os.path.join(PRESENT_DIR, 'log', run_id, 'logs.txt'), 'a') as f:
        f.write(f'[{datetime.datetime.now()}] {log_msg} \n')

def execute_and_wait(cmd, timeout=10):
    log(f'Executing "{cmd}"')
    process = pexpect.spawn('/bin/sh', ['-c', cmd], encoding='utf-8')
    process.expect(pexpect.EOF, timeout=timeout)
    output = process.before  # Capture the output
    process.wait()

    return process.exitstatus, output

def execute_and_detach(cmd):
    log(f'Executing "{cmd}"')
    child = pexpect.spawn(cmd, encoding='utf-8')
    try:
        child.expect(pexpect.EOF, timeout=0.5)
        print('I executed cmd', cmd)
        print(child.before)
    except Exception:
        pass
    return child

def prepare_memory_groups(mem_limit, mems_limit):
    create_mgroup, output = execute_and_wait(f'sudo ./create_mgroup.sh {MEM_GROUP_NAME} {mem_limit} {mems_limit}', 10)
    if create_mgroup != 0:
        log(output)
        raise Exception('Could not create a memory group for testing')

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
    if pregenerate: 
        cp_code, output = execute_and_wait(f'sudo cp -r {PRESENT_DIR} {root_fpath}', 60)

        if cp_code != 0:
            log(output)
            raise Exception('Could not run copy into marked directory')
    else:
        print(execute_and_wait('sudo mkdir /mnt/ext4/storage-stick'))

        cp_server_code, output = execute_and_wait(f'sudo cp {PRESENT_DIR}/{MINECRAFT_PATH} {root_fpath}/storage-stick', 60)

        if cp_server_code != 0:
            log(output)
            raise Exception('Could not run copy into marked directory')
        
        cp_eula_code, output = execute_and_wait(f'sudo cp {PRESENT_DIR}/eula.txt {root_fpath}/storage-stick', 60)

        if cp_eula_code != 0:
            log(output)
            raise Exception('Could not run copy into marked directory')
        
        cp_properties, output = execute_and_wait(f'sudo cp {PRESENT_DIR}/server.properties {root_fpath}/storage-stick', 60)

        if cp_properties != 0:
            log(output)
            raise Exception('Could not run copy into marked directory')

    return root_fpath, dev_path

def start_minecraft(mems_limit):
    log('Starting Minecraft')
    return execute_and_detach(f'sudo cgexec -g memory:{MEM_GROUP_NAME} java -jar -Xmx{mems_limit}M -Xms{mems_limit}M {MINECRAFT_PATH}')

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
    
def collect_page_faults(pid, log_fpath):
    return execute_and_detach(f'{PRESENT_DIR}/collect_page_faults.sh {pid} {log_fpath}')

pd.DataFrame(start_data).to_csv(f'log/{run_id}/start_data.csv')
pd.DataFrame(termination_data).to_csv(f'log/{run_id}/termination.csv')

log(f'Starting a time experiment with parameters. Pregenerate - {pregenerate}')

def collect_data(storage_latency, mem_limit, mems_limit, num_players):
    for i in tqdm(range(NUM_TRIALS)):
        log(f'Starting the trial number {i}')

        prepare_memory_groups(mem_limit, mems_limit)
        root_dir, dev_path = prepare_storage(storage_latency)

        start_time = time.time()

        os.chdir(f'{root_dir}/storage-stick')
        minecraft = start_minecraft(mems_limit)
        
        # start_pf = collect_page_faults(minecraft.pid, os.path.join(PRESENT_DIR, 'log', run_id, 'traces', f'faults_on_start_{storage_latency}_{mems_limit}_{i}.log'))

        minecraft.expect('Done', timeout=300)
        # start_pf.terminate(force=True)

        bots = execute_and_detach(f"node {os.path.join(PRESENT_DIR, 'bot.js')} {num_players}")

        end_time = time.time()
        time_to_start = end_time-start_time

        start_data.append({
            'latency': storage_latency,
            'mem_limit': mem_limit,
            'mems_limit': mems_limit,
            'num_players': num_players,
            'sample_num': i,
            'time': time_to_start
        })

        bots.expect('Success', timeout=30)
        start_time = time.time()

        minecraft.terminate()

        # terminate_pf = collect_page_faults(minecraft.pid, os.path.join(PRESENT_DIR, 'log', run_id, 'traces', f'faults_on_termination_{storage_latency}_{mems_limit}_{i}.log'))
        minecraft.expect(pexpect.EOF, timeout=1200)
        # terminate_pf.terminate(force=True)

        end_time = time.time()
        time_to_terminate = end_time - start_time

        termination_data.append({
            'latency': storage_latency,
            'mem_limit': mem_limit,
            'mems_limit': mems_limit,
            'num_players': num_players,
            'sample_num': i,
            'time': time_to_terminate
        })

        os.chdir(PRESENT_DIR)

        clean_up(root_dir, dev_path)

        pd.DataFrame(start_data).to_csv(f'log/{run_id}/start_data.csv')
        pd.DataFrame(termination_data).to_csv(f'log/{run_id}/termination.csv')

for storage_latency in tqdm(STORAGE_LATENCIES):
    for memory_limit in tqdm(MEM_LIMITS):
        for memory_swap_limit in tqdm(MEMS_LIMIT):
            for player_count in tqdm(NUM_PLAYERS):
                collect_data(
                    storage_latency=storage_latency,
                    mem_limit=memory_limit,
                    mems_limit=memory_swap_limit,
                    num_players=player_count
                )

