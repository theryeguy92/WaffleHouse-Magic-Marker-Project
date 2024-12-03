#!/bin/bash

# Monitor /app/smv_files for new .smv files
inotifywait -m /app/smv_files -e close_write |
while read path action file; do
  if [[ "$file" == *.smv ]]; then
    echo "Processing $file..."
    nuXmv /app/smv_files/"$file" > /app/smv_files/"$file".output 2>&1
    echo "Finished processing $file."
  fi
done