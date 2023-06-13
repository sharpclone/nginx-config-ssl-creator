import subprocess, configparser

def restart_nginx():
    su = config_get("root_method")
    nginx_cmd = config_get("nginx_restart_cmd")
    subprocess.run(f"{su} {nginx_cmd}", shell=True)
    
def config_get(key :str):
    #Setting up the config file
    settings = configparser.ConfigParser()
    settings.read("/home/mihu/Documents/Workspace/Py/nginx_proxy_creator/creator.conf")
    cfg = settings["Settings"]
    return cfg[key].strip("\"' ")

if __name__ == "__main__":
    restart_nginx()