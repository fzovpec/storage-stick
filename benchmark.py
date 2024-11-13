import time
import pexpect
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--Input", help = "Input Trace File")
parser.add_argument("-o", "--Output", help = "Output Folder")

args = parser.parse_args()

def execute_and_detach(cmd):
    child = pexpect.spawn(cmd, encoding='utf-8')
    try:
        child.expect(pexpect.EOF, timeout=0.5)
        print('I executed cmd', cmd)
        print(child.before)
    except Exception:
        pass
    return child

current_time = 0
player_emulation = execute_and_detach(f'node player_emulation/player.js {args.Output}/result.txt')

with open(args.Input, 'r') as f:
    line = f.readline()
    while line:
        timestamp, action, argument = line.strip().split(' ')
        timestamp = float(timestamp)

        delta = timestamp - current_time
        # TODO: Use maybe unix time. Somehow get the current time not with daytime and then see the difference if 
        # it has passed the threashold. Use busy loop 
        time.sleep(delta)
        current_time += delta

        if action == 'player_join':
            player_emulation.sendline(f'login {argument}')
        elif action == 'remove_block':
            player_emulation.sendline(f'remove_block {argument}')

        line = f.readline()
