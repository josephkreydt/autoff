# autoff
Python script to format CSV data into a flat file based on a JSON mapping file.

1. Place CSV in the same directory as the Python script

2. If you run the script without a JSON map file, a sample JSON file will be created in the same directory as the Python script

3. Open the Python script and edit the json_map_file_path and output_file_path variables
- json_map_file_path should be set to the file/path of the JSON mapping file
- output_file_path is where the formatted file will be saved

4. Run the Python script (python3 autoff.py)

5. There will be a log file in the same directory as the Python script so you can see if there were any errors
