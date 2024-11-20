# utils/bash_executor.py
import subprocess
import os

def execute_bash_file(file_path):
    try:
        if file_path.endswith(".sh"):
            subprocess.run(["bash", file_path], check=True)
        else:
            subprocess.run(["cmd", "/c", file_path], check=True)
        print(f"File executed successfully: {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing file: {e}")
    
    # Read and return the log file content (optional, depending on whether a log is generated)
    log_file = "log.txt"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return f.read()
    else:
        return "Log file not found"