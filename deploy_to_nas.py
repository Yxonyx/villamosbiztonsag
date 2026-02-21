import paramiko

host = '100.87.221.65'
user = 'admin1'
password = 'admin'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {host}...")
    client.connect(host, username=user, password=password, timeout=10)
    print("Connected.")
    
    commands = [
        "git clone https://github.com/Yxonyx/villamosbiztonsag.git || (cd villamosbiztonsag && git pull)",
        "cd villamosbiztonsag && echo 'admin' | sudo -S docker compose up -d --build || echo 'admin' | sudo -S docker-compose up -d --build"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Wait for command to finish
        exit_status = stdout.channel.recv_exit_status()
        
        print("STDOUT:")
        print(stdout.read().decode())
        print("STDERR:")
        print(stderr.read().decode())
        print(f"Exit status: {exit_status}\n")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
