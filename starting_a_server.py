import pexpect
import os
import time

NUM_TRIALS = 10
STORAGE_LATENCY = 100
FOLDER_MOUNT_PATH = "/mnt/ext4"
MINECRAFT_PATH = 'server.jar'
PRESENT_DIR = os.curdir

current_dir = "./"

def execute_and_wait(cmd, timeout=10):
    print(f'Executing "{cmd}"')
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

def prepare_storage():
    print('Starting to prepare a storage')
    chmod_code, _ = execute_and_wait(f'sudo chmod +x createnullblk.sh')
    if chmod_code != 0:
        raise Exception('Could not chmod nullblk')
    
    print('Creating a memory backed block device')
    nullblk_code, nullblk = execute_and_wait(f'sudo ./createnullblk.sh 512 4096 {STORAGE_LATENCY}')
    if nullblk_code != 0:
        raise Exception('Could not create nullblock space')
    
    nullblk = nullblk.strip()
    dev_path = f'/dev/{nullblk}'
    print('Creating a file system on memory backed storage device')
    
    mkfs_code, output = execute_and_wait(f'sudo mkfs.ext4 {dev_path}', 90)
    if mkfs_code != 0:
        print(output)
        raise Exception('Could not mark the space for file system')
    
    print('Creating a root folder')

    root_fpath = '/mnt/ext4'
    
    if not os.path.exists(root_fpath):
        mkdir_code, output = execute_and_wait(f'sudo mkdir {root_fpath}')
        if mkdir_code != 0:
            print(output)
            raise Exception('Could not make /mnt/ext4 folder')
    
    print('Mounting a block device onto a root folder')
    mount_code, _ = execute_and_wait(f'sudo mount {dev_path} /mnt/ext4', 60)
    if mount_code != 0:
        raise Exception('Could not mount folder')
    
    print('Copying Minecraft into a new folder')
    cp_code, output = execute_and_wait(f'sudo cp -r {PRESENT_DIR} {root_fpath}', 60)
    if cp_code != 0:
        print(output)
        raise Exception('Could not run copy into marked directory')
    
    os.chdir(root_fpath)

def start_minecraft():
    print('Starting Minecraft')
    return execute_and_detach(f'sudo java -jar {MINECRAFT_PATH}')

prepare_storage()
start_time = time.time()
minecraft = start_minecraft()
minecraft.expect('Done', timeout=60)
end_time = time.time()

print(end_time-start_time)
