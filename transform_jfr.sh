#!/bin/sh

INPUT_DIR="jfr-recordings"
OUTPUT_DIR="jfr-json"
EVENTS="minecraft.ServerTickTime"

mkdir -p $OUTPUT_DIR

for file in "$INPUT_DIR"/*.jfr; do
    if [ -f "$file" ]; then
        # Get the base name of the file (e.g., recording_1 from recording_1.jfr)
        base_name=$(basename "$file" .jfr)

        # Convert JFR to text output and format it for JSON compatibility
        jfr print --json --events "$EVENTS" "$file" > "$OUTPUT_DIR/$base_name.json"
        
        echo "Processed $file -> $OUTPUT_DIR/$base_name.json"
    fi
done
