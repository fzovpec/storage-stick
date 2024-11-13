#!/bin/bash
OUTPUT_DIR="/home/user/storage-stick-3/jfr-recordings"
SOURCE_DIR="/home/user/storage-stick-3/workloads/setup/instances"
TRACES_DIR="/home/user/storage-stick-3/traces"
LIST_NULL=("/dev/nullb0" "/dev/nullb1")

mkdir -p $OUTPUT_DIR
for i in $(seq 1 30); do
    echo "Iteration $i"

    for device in "${LIST_NULL[@]}"; do
        echo "testing device $device";
        sudo mount $device /mnt/ext4
    	for subdir in "$SOURCE_DIR"/*/; do
		    echo "Instance: $subdir"
        	for file in "$TRACES_DIR"/*; do
            	if [ -f "$file" ]; then
			        echo "Trace $file"
                	output_path="${OUTPUT_DIR}/results$device${instance}_$(basename "$subdir")_$(basename "$file")/${i}"
                	mkdir -p "$output_path"
                	sudo cp -r "$subdir" /mnt/ext4

                	cd /mnt/ext4/$(basename "$subdir")

                	sudo java -Xmx12G -Xms12G -XX:StartFlightRecording=name=ServerRun,dumponexit=true,filename=$output_path/recording_$i.jfr -jar server.jar &
                	PID=$!
                	echo "Started Java process with PID: $PID"
                	sleep 40

                	JAVA_PID=$(pgrep -u $(whoami) -f 'java.*server.jar' | tail -n 1)
                	echo "Java PID for non-sudo user: $JAVA_PID"
                	cd /home/user/storage-stick-3/

                	python3 benchmark.py -i "$file" -o "${output_path}"

                	sudo jcmd $JAVA_PID JFR.stop name=ServerRun filename=$output_path/recording_$i.jfr
                	sudo kill -15 $JAVA_PID
                	sudo kill -9 $PID
                	pkill -9 java

                	echo "Killed Java process with PID: $PID"

                	sudo rm -rf /mnt/ext4/instance

                	cat /home/user/storage-stick-3/player_emulation/bot_log.txt >> /home/user/storage-stick-3/player_emulation/result.txt
                	sleep 2
                
                	sleep 5
            	fi
    		done    
    	done
    done
done

