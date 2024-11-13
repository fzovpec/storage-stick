import random
import numpy as np

spawn_center = [0, 0]
spawn_stdev = [100, 100]
preferential_attachment = 0.7

players_num = 30

players = [f'player_{player}' for player in range(0, players_num)]
trace_command = lambda action, argument: f'{action} {argument} \n'
positions = []

with open(f'setup_traces/join_setup_{preferential_attachment}_pref_{players_num}_player_{spawn_stdev[0]}_{spawn_stdev[1]}.txt', '+w') as f:
    for player in players:
        if(random.random() < preferential_attachment) and len(positions) > 0:
            point = positions[random.randint(0, len(positions) - 1)]
            positions.append(point)
        
        else:
            point = np.random.normal(spawn_center, spawn_stdev)
            positions.append(point)

        f.write(trace_command('spawn', f'{player} {point[0]} {point[1]}'))
