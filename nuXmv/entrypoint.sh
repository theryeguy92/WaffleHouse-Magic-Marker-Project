#!/bin/bash

echo "nuXmv service started. Polling for .smv files in /app/smv_files..."

# Infinite loop to poll for new .smv files
while true; do
  for smv_file in /app/smv_files/*.smv; do
    # Check if the file exists
    [ -e "$smv_file" ] || continue

    output_file="${smv_file}.output"

    # Process the file only if the output file doesn't exist
    if [ ! -e "$output_file" ]; then
      echo "Processing $(basename "$smv_file")..."
      if nuXmv "$smv_file" > "$output_file" 2>&1; then
        echo "Finished processing $(basename "$smv_file")."
      else
        echo "Error processing $(basename "$smv_file"). Check the output file for details."
      fi
    fi
  done
  sleep 1
done
