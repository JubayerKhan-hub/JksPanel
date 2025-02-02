from flask import Flask, render_template, request, jsonify, send_file
import os
import subprocess
import shutil
import time
import threading
import re

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SERVERS_DIR = os.path.join(BASE_DIR, 'servers')

console_buffers = {}
server_processes = {}

def log_console_output(server_name):
    log_path = os.path.join(SERVERS_DIR, server_name, 'logs', 'latest.log')
    while True:
        try:
            with open(log_path, 'r') as f:
                f.seek(0, 2)  # Seek to end
                while True:
                    line = f.readline()
                    if line:
                        if server_name not in console_buffers:
                            console_buffers[server_name] = []
                        console_buffers[server_name].append(line.strip())
                        if len(console_buffers[server_name]) > 200:
                            console_buffers[server_name].pop(0)
                    else:
                        time.sleep(0.1)
        except FileNotFoundError:
            time.sleep(1)

def get_screen_pid(server_name):
    try:
        output = subprocess.check_output(['screen', '-ls'], stderr=subprocess.STDOUT).decode()
        match = re.search(r'\t(\d+)\.%s\t' % server_name, output)
        return match.group(1) if match else None
    except subprocess.CalledProcessError:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/servers', methods=['GET'])
def list_servers():
    servers = [d for d in os.listdir(SERVERS_DIR) if os.path.isdir(os.path.join(SERVERS_DIR, d))]
    return jsonify({"servers": servers})

@app.route('/server/create', methods=['POST'])
def server_create():
    name = request.json.get('name')
    if not name:
        return jsonify({"error": "Server name is required"}), 400
    
    server_dir = os.path.join(SERVERS_DIR, name)
    try:
        os.makedirs(server_dir, exist_ok=False)
    except FileExistsError:
        return jsonify({"error": "Server already exists"}), 400

    jar_path = os.path.join(server_dir, 'server.jar')
    try:
        subprocess.run([
            'wget', '-q', '-O', jar_path,
            'https://papermc.io/api/v2/projects/paper/versions/latest/builds/latest/downloads/paper-latest.jar'
        ], check=True)
    except subprocess.CalledProcessError:
        shutil.rmtree(server_dir)
        return jsonify({"error": "Failed to download server jar"}), 500

    # Create start script
    start_script = os.path.join(server_dir, 'start.sh')
    with open(start_script, 'w') as f:
        f.write(f'''#!/bin/bash
cd "{server_dir}"
java -Xmx1G -jar server.jar nogui
''')
    os.chmod(start_script, 0o755)
    
    # Start log monitoring
    threading.Thread(target=log_console_output, args=(name,), daemon=True).start()
    
    return jsonify({"message": f"Server {name} created"})

@app.route('/server/status/<name>')
def server_status(name):
    return jsonify({'status': 'running' if get_screen_pid(name) else 'stopped'})

@app.route('/server/control', methods=['POST'])
def server_control():
    name = request.json.get('name')
    action = request.json.get('action')
    
    if not name or not action:
        return jsonify({"error": "Missing parameters"}), 400
    
    server_dir = os.path.join(SERVERS_DIR, name)
    if not os.path.exists(server_dir):
        return jsonify({"error": "Server not found"}), 404

    try:
        if action == "start":
            pid = get_screen_pid(name)
            if pid:
                return jsonify({"error": "Server already running"}), 400
            subprocess.Popen(
                ['screen', '-dmS', name, os.path.join(server_dir, 'start.sh')],
                cwd=server_dir
            )
        elif action == "stop":
            pid = get_screen_pid(name)
            if pid:
                subprocess.run(['kill', pid], check=True)
        elif action == "restart":
            pid = get_screen_pid(name)
            if pid:
                subprocess.run(['kill', pid], check=True)
            subprocess.Popen(
                ['screen', '-dmS', name, os.path.join(server_dir, 'start.sh')],
                cwd=server_dir
            )
        else:
            return jsonify({"error": "Invalid action"}), 400
        
        return jsonify({"message": f"Server {name} {action}ed"})
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/server/console/<name>')
def get_console(name):
    return jsonify({'output': console_buffers.get(name, [])})

@app.route('/server/console', methods=['POST'])
def server_console():
    name = request.json.get('name')
    command = request.json.get('command')
    
    if not name or not command:
        return jsonify({"error": "Missing parameters"}), 400
    
    pid = get_screen_pid(name)
    if not pid:
        return jsonify({"error": "Server not running"}), 400
    
    try:
        subprocess.run(
            ['screen', '-S', f'{pid}.{name}', '-X', 'stuff', f'{command}\n'],
            check=True
        )
        return jsonify({"message": "Command sent"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    os.makedirs(SERVERS_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=80, debug=True)
