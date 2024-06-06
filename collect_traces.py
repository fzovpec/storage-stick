import pexpect
import os
import pandas as pd
import datetime

run_id = f'[{datetime.datetime.now()}]'
MINECRAFT_PATH = 'server.jar'
PRESENT_DIR = os.getcwd()
current_dir = "./"

if not os.path.exists('log'):
    os.makedirs('log')

if not os.path.exists(run_id):
    os.makedirs(os.path.join('log', run_id))
    if not os.path.exists(os.path.join('log', run_id, 'traces')):
        os.makedirs(os.path.join('log', run_id, 'traces'))

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
        print(child.before)
    except Exception:
        pass
    return child

def log(log_msg):
    with open(f'log/{run_id}/logs.txt', 'a') as f:
        f.write(f'[{datetime.datetime.now()}] {log_msg} \n')

def start_minecraft():
    log('Starting Minecraft')
    return execute_and_detach(f'java -jar {MINECRAFT_PATH}')

minecraft = start_minecraft()
total_run_logs_file = f'{PRESENT_DIR}/log/{run_id}/traces/total_latency_trial.txt'
total_run_logs = execute_and_detach(f'sudo strace -f -tt -T -y -yy -s 2048 -e trace=read,write,pread64,pwrite64,open,close,mmap -o "{total_run_logs_file}" -p {minecraft.pid}')

minecraft.expect('Done', timeout=300)

minecraft.terminate()
minecraft.expect(pexpect.EOF, timeout=1200)

total_run_logs.terminate(force=True)

