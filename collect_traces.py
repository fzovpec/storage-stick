import pexpect
import os
import pandas as pd
import datetime
import psutil
import time
import threading
import logging


run_id = f'[{datetime.datetime.now()}]'
MINECRAFT_PATH = 'server.jar'
PRESENT_DIR = os.getcwd()
ROOT_PATH = "traces"

run_folder = os.path.join(ROOT_PATH, run_id)
current_dir = "./"

if not os.path.exists(ROOT_PATH):
    os.makedirs(ROOT_PATH)

if not os.path.exists(run_folder):
    os.makedirs(run_folder)

def get_memory_usage(process):
    mem_info = process.memory_info()
    rss_mb = mem_info.rss
    vms_mb = mem_info.vms
    memory_percent = process.memory_percent()
    return rss_mb, vms_mb, memory_percent

def log_memory_usage(pid, interval, log_file):
    # Configure logging
    with open(log_file, 'w') as f:
        f.write('time; pid; rtt; vtt \n')

    logging.basicConfig(filename=log_file, level=logging.INFO, 
                        format='%(asctime)s; %(process)d; %(message)s')
    
    process = psutil.Process(pid)
    
    try:
        while True:
            total_rss = 0
            total_vms = 0
            total_percent = 0
            
            # Get memory usage of the main process
            rss_mb, vms_mb, memory_percent = get_memory_usage(process)
            total_rss += rss_mb
            total_vms += vms_mb
            total_percent += memory_percent
            
            # Get memory usage of child processes
            for child in process.children(recursive=True):
                rss_mb, vms_mb, memory_percent = get_memory_usage(child)
                total_rss += rss_mb
                total_vms += vms_mb
                total_percent += memory_percent
            
            logging.info(f"{total_rss:.2f}; {total_vms:.2f}")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("Logging stopped.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

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
    logs_file = os.path.join(run_folder, 'logs.txt')
    with open(logs_file, 'a') as f:
        f.write(f'[{datetime.datetime.now()}] {log_msg} \n')

def start_minecraft():
    log('Starting Minecraft')
    return execute_and_detach(f'java -jar server.jar')

minecraft = start_minecraft()

threading.Thread(target=log_memory_usage, args=(minecraft.pid, 0.001, os.path.join(run_folder, 'mem_cons.txt')), daemon=True).start()

total_run_logs_file = os.path.join(run_folder, 'storage_traces.txt')
total_run_logs = execute_and_detach(f'sudo strace -f -tt -T -y -yy -s 2048 -e trace=file,openat,creat,read,write,pread64,pwrite64,open,close,mmap -o "{total_run_logs_file}" -p {minecraft.pid}')

minecraft.expect('Done', timeout=300)
log("Minecraft started")

log("Terminating Minecraft")
minecraft.terminate()
minecraft.expect(pexpect.EOF, timeout=1200)
log("Minecraft terminated")

total_run_logs.terminate(force=True)

