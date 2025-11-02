import subprocess
import argparse
import json
import os
import signal

def run_applescript(command):
    """Executes an AppleScript command to open a new Terminal window."""
    try:
        subprocess.run(['osascript', '-e', command], check=True)
    except Exception as e:
        print(f"Failed to run AppleScript command: {e}")

def start_servers():
    """
    Starts all 6 servers by opening new Terminal windows
    and executing the required commands.
    """
    print("Starting all 6 servers in new terminal windows...")
    
    # 1. Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        rust_path = config['rust_backend_path']
        pwa_path = config['pwa_folder_path']
        
        if not os.path.isdir(rust_path) or not os.path.isdir(pwa_path):
            print(f"Error: A path in config.json is not a valid directory.")
            print(f"Rust path: {rust_path}")
            print(f"PWA path: {pwa_path}")
            return
            
    except FileNotFoundError:
        print("Error: config.json not found.")
        print("Please create it with 'rust_backend_path' and 'pwa_folder_path'.")
        return
    except KeyError:
        print("Error: config.json is missing a required path.")
        return

    # 2. Define the 6 AppleScript commands
    commands = {
        "Ollama": 'tell app "Terminal" to do script "ollama serve"',
        "ChromaDB": 'tell app "Terminal" to do script "docker start chromadb"',
        "Rust_Backend": f'tell app "Terminal" to do script "cd {rust_path} && cargo run --release"',
        "PWA_Frontend": f'tell app "Terminal" to do script "cd {pwa_path} && python3 -m http.server 3000 --bind 0.0.0.0"',
        "Ngrok_Backend": 'tell app "Terminal" to do script "ngrok http 8080"',
        "Ngrok_Frontend": 'tell app "Terminal" to do script "ngrok http 3000"'
    }

    # 3. Execute all commands
    for name, cmd in commands.items():
        print(f"[STARTING]... {name}")
        run_applescript(cmd)
    
    print("\nAll servers should be starting up.")
    print("Check your new Terminal windows for ngrok URLs and status.")

def stop_servers():
    """
    The "Kill Switch". Finds all processes by name and terminates them.
    This is a forceful stop, but effective.
    """
    print("Activating Kill Switch...")
    
    commands_to_kill = {
        # Process name to search for
        "Ollama": "ollama serve",
        "Rust_Backend": "cargo run --release",
        "PWA_Frontend": "http.server 3000",
        "Ngrok": "ngrok http",
        "ChromaDB": 'tell app "Terminal" to do script "docker start chromadb"'
    }
    
    for name, process_str in commands_to_kill.items():
        try:
            # Find and kill the process. `pkill -f` searches the full command.
            # This is more robust than killing by PID.
            subprocess.run(['pkill', '-f', process_str], check=True)
            print(f"[STOPPED]... {name} ({process_str})")
        except subprocess.CalledProcessError:
            # This just means the process wasn't found (it wasn't running)
            print(f"[INFO]... {name} process not found (already stopped).")
        except Exception as e:
            print(f"Error stopping {name}: {e}")

    # Special handling for Docker
    try:
        subprocess.run(['docker', 'stop', 'chromadb'], check=True, capture_output=True)
        print("[STOPPED]... ChromaDB (docker)")
    except Exception:
        print("[INFO]... ChromaDB container not running.")
        
    print("\nAll server processes terminated.")

def main():
    parser = argparse.ArgumentParser(description="Server Manager for the Offline AI Council")
    parser.add_argument(
        'command', 
        choices=['start', 'stop'], 
        help="The action to perform: 'start' (spin up all servers) or 'stop' (kill switch)."
    )
    
    args = parser.parse_args()
    
    if args.command == 'start':
        start_servers()
    elif args.command == 'stop':
        stop_servers()

if __name__ == "__main__":
    main()