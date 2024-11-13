import pexpect
import os
import time
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-it", "--Input_Trace", help = "Input Trace File")
parser.add_argument("-ii", "--Input_Folder", help = "Input Instance Folder")
parser.add_argument("-o", "--Output", help = "Output Folder")

args = parser.parse_args()

def execute_and_wait(cmd, timeout=10):
    process = pexpect.spawn('/bin/sh', ['-c', cmd], encoding='utf-8')
    process.expect(pexpect.EOF, timeout=timeout)
    output = process.before  # Capture the output
    process.wait()

    return process.exitstatus, output

def execute_and_detach(cmd):
    child = pexpect.spawn(cmd, encoding='utf-8')
    try:
        child.expect(pexpect.EOF, timeout=0.5)
        print('I executed cmd', cmd)
        print(child.before)
    except Exception:
        pass
    return child

original_dir = os.getcwd()

os.chdir(args.Input_Folder)
minecraft = execute_and_detach(f'java -Xmx12288M -Xms12288M -jar server.jar')
minecraft.expect('Done', timeout=300)

print('Started Minecraft. Start logging players in')

os.chdir(original_dir)

player_emulation = execute_and_detach(f'node player_emulation/player.js')

with open(args.Input_Trace) as f:
    line = f.readline().strip()
    while line:
        print(line)
        action, name, x, z = line.split(' ')
        
        player_emulation.sendline(f'login {name}')
        player_emulation.expect('Spawned', timeout=200)

        minecraft.sendline(f'/spawnpoint {name} {int(float(x))} 300 {int(float(z))}')
        minecraft.expect('Set spawn point', timeout=200)

        minecraft.sendline(f'/kill {name}')
        minecraft.expect('Killed')

        line = f.readline().strip()
        time.sleep(10)