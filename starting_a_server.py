import pexpect
import os
import time

NUM_TRIALS = 10
STORAGE_LATENCY = 1000000000
FOLDER_MOUNT_PATH = "/mnt/ext4"
MINECRAFT_PATH = 'server.jar'
PRESENT_DIR = os.curdir

current_dir = "./"

def execute_and_wait(cmd):
    process = pexpect.spawn('/bin/sh', ['-c', cmd], encoding='utf-8')
    process.expect(pexpect.EOF)
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
    chmod_code, _ = execute_and_wait('sudo chmod +x createnullblk.sh')
    if chmod_code != 0:
        raise Exception('Could not chmod nullblk')

    nullblk_code, nullblk = execute_and_wait('sudo ./createnullblk.sh 512 4096 {STORAGE_LATENCY}')
    if nullblk_code != 0:
        raise Exception('Could not create nullblock space')
    
    dev_path = f'/dev/{nullblk}'

    mkfs_code, _ = execute_and_wait(f'sudo mkfs.ext4 {dev_path}')
    if mkfs_code != 0:
        raise Exception('Could not mark the space for file system')
    
    mkdir_code, _ = execute_and_wait(f'sudo mkdir /mnt/ext4')
    if mkdir_code != 0:
        raise Exception('Could not make /mnt/ext4 folder')
    
    mount_code, _ = execute_and_wait('sudo mount {dev_path} /mnt/ext4')
    if mount_code != 0:
        raise Exception('Could not mount folder')

    cp_code, _ = execute_and_wait(f'sudo cp -r {PRESENT_DIR} {dev_path}')
    if cp_code != 0:
        raise Exception('Could not run copy into marked directory')
    
    os.chdir(dev_path)

def start_minecraft():
    return execute_and_detach(f'sudo java -jar {MINECRAFT_PATH}')

prepare_storage()
start_time = time.time()
minecraft = start_minecraft()
minecraft.expect('[Server thread/INFO]: Done', timeout=60)
end_time = time.time()

print(start_time - end_time)
