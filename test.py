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


def config_set(key, value):
    config = configparser.ConfigParser()
    config.read("/home/mihu/Documents/Workspace/Py/nginx_proxy_creator/creator.conf")
    parser = config['Settings']
    parser[key] = value
    with open('/tmp/cfg.temp','w+') as cfg:
        config.write(cfg)
        cfg.close()
    f = open("/tmp/cfg.temp").read()
    print(f)

if __name__ == "__main__":
    config_set("acme_root","/var/www/html/acme")