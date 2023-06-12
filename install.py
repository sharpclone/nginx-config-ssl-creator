import os, subprocess, pathlib, configparser

def config_get(key :str):
    #Setting up the config file
    settings = configparser.ConfigParser()
    settings.read("creator.conf")
    cfg = settings["Settings"]
    return cfg[key].strip("\"' ")

def write_to_root_file(content, file_path):
    # Create a temporary file to hold the content
    temp_file = '/tmp/tempfile.txt'
    with open(temp_file, 'w') as f:
        f.write(content)

    root_method = config_get("root_method")

    # Check if the file already exists and delete it if it does
    if os.path.exists(file_path):
        subprocess.run([root_method, 'rm', file_path])

    # Use subprocess to execute the write operation with the appropriate root method
    subprocess.run([root_method, 'cp', temp_file, file_path])

    # Remove the temporary file
    subprocess.run([root_method, 'rm', temp_file])


settings = configparser.ConfigParser()
settings.read("creator.conf")
cfg = settings["Settings"]

prefix="/etc/nginx-proxy-creator/"
su = config_get("root_method")
subprocess.run([su,'mkdir','-p',f'{prefix}templates'])
write_to_root_file(open("nginx_create_proxy.py").read(), f'{prefix}nginx-proxy-creator.py')
write_to_root_file(open("creator.conf").read(), f"{prefix}creator.conf")
write_to_root_file(open("return301.conf").read(), f"{prefix}return301.conf")
write_to_root_file(open("acme_challenge").read(), f"{prefix}acme_challenge")
subprocess.run([su,"ln","-s", prefix+"nginx-proxy-creator.py","/usr/bin/"])
subprocess.run(["source","/etc/profile"])

entries = pathlib.Path("templates")
for entry in entries.iterdir():
    write_to_root_file(open(entry).read(),prefix+"templates/"+entry.name)