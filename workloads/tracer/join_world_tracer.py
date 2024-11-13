import os

max_players = 25
burstiness = 5
workload_length = 60

trace_file = os.path.join('traces', f'join_trace_{max_players}_players_{workload_length}_length_{burstiness}_burstiness.txt')

players_offline = [f'player_{player}' for player in range(max_players)]
players_online = []

trace_command = lambda timestamp, action, argument: f'{timestamp} {action} {argument} \n'

moment_now = 0

print(players_offline)

with open(trace_file, '+w') as f:
    while moment_now < workload_length:
        step_size = (workload_length / max_players) * burstiness

        players_joining = [players_offline.pop() for _ in range(min(burstiness, max_players -  len(players_online)))]
        [players_online.append(player) for player in players_joining]

        for player in players_joining:
            f.write(trace_command(moment_now, 'player_join', player))

        # players_leaving = [players_online.pop() for _ in range(-burstiness)]
        # [players_offline.append(player) for player in players_leaving]

        # for player in players_leaving:
        #     f.write(trace_command(moment_now, 'player_leave', player))

        moment_now += step_size
    
    f.write(trace_command(moment_now + 30, 'wait', 'empty'))