import re
import configparser
from pathlib import Path
import subprocess
import os


def config_get(key :str):
    #Setting up the config file
    settings = configparser.ConfigParser()
    settings.read("/etc/nginx_proxy_creator/creator.conf")
    cfg = settings["Settings"]
    return cfg[key].strip("\"' ")


def config_set(key, value):
    config = ConfigParser()
    config.read("/etc/nginx_proxy_creator/creator.conf")
    parser = config['Settings']
    parser[key] = value
    with open('/etc/nginx_proxy_creator/creator.conf', 'w') as configfile:
        config.write(configfile)


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


def find_variables(config_string : str):
    variables = re.findall(r'@([a-zA-Z_]\w+)(?!\w|\s*\()', config_string)
    unique_variables = sorted(set(variables))
    return unique_variables


def restart_nginx():
    su = config_get("root_method")
    nginx_cmd = config_get("nginx_restart_cmd")
    subprocess.run(f"{su} {nginx_cmd}", shell=True)


def modify_variables(config_string : str):
    final_cfg = config_string
  #Find the variables
    variables = find_variables(config_string)
    print(f"Found variables: {variables}")
    variable_dict = dict()
    for var in variables:

        #Allow table specific
        if var == "allow_table":
            table = ""
            useDef = input(f"Do you want to use {config_get('allow_table')} for the allowed IPs that are allowed to access the location? [Y/n] " ).lower() or 'Y'
            if useDef == 'n':
                val = input(f"Give the allowed CIDR noted IPs (separated by comma) that are allowed to access the location :")
                val = val.split(",")
                for ip in val:
                    table += f"\tallow {ip};\n"
            else:
                ips = config_get("allow_table").split(",")
                for ip in ips:
                    table += f"\tallow {ip};\n"
            final_cfg = final_cfg.replace(f"@allow_table", table)
            variable_dict[var] = table
        #SSL 
        if var == "ssl":
            pass

        #acme
        if var == "acme":
            acme_config = open("/etc/nginx_proxy_creator/acme_challenge").read()
            acme_path = config_get("acme_root")
            is_ok = input(f"Is {acme_path} the correct path for the acme? [Y/n]").lower() or 'y'
            if is_ok == 'n':
                print("You can change the acme root from the config")
                exit()
            acme_config = acme_config.replace("@acme", acme_path)
            final_cfg = final_cfg.replace("@acme", acme_config)
            variable_dict[var] = acme_config

        #Other simple variables
        else:
            val = input(f"Give the value of {var}: ")
            variable_dict[var] = val
            final_cfg = final_cfg.replace(f"@{var}", val)
    return final_cfg,variable_dict


def choose_template(folder):
    #Listing AvailableTemplates
    templates = []
    for template in folder.iterdir():
        templates.append(template)
    valid_input = False
    while not valid_input:
        print("Which template would you like to use? [default 0]: ")
        option = 0
        choice = 0
        for template in templates:
            print(f"[{option}] {template.name}")
            option+=1
        valid_input = True
        try:
            choice = int(input(">> ") or "0" ) 
        except:
            print("Invalid Option, try again ")
            valid_input = False
        if choice < 0 or choice > option:
            print("Invalid Option, try again ")
            valid_input = False
        
    return templates[choice]


def restart_nginx():
    su = config_get("root_method")
    nginx_cmd = config_get("nginx_restart_cmd")
    subprocess.run([su, nginx_cmd])


def get_ssl(config, variables):
    ssl_method = config_get("ssl_method")
    has_installed_ssl_method = config_get("has_installed_ssl_method")
    if not has_installed_ssl_method:
        has_installed_ssl_method = input(f"Have you installed {ssl_method}? [y/N]: ").lower() or 'n'
        if has_installed_ssl_method == 'y':
            config_set("has_installed_ssl_method", 1)
        else:
            print(f"You should install {ssl_method} and then run this script again")
            exit()
    print("Note that you should use a SSL template ")

    


if __name__ == "__main__":
    #Selecting the template
    template = choose_template(Path("/etc/nginx-proxy-creator/templates"))

    #Open the template
    template = open(template,"r").read()
    # config_string = conf.read()
    mod_cfg,variables = modify_variables(template)
    conf_path = config_get("nginx_conf_path") + variables["domain"] + ".conf"

    #Asking if user wants ssl
    want_ssl = input("Do you want to get the ssl-cert automatically? [y/N]: ") or 'n'
    if want_ssl.lower() != 'n':
        get_ssl(mod_cfg,variables)
     
    else:
        print(mod_cfg)
        want_to_write_config = input(f"\nDo you want to write this config to {conf_path}? [N/y]")  or 'n' 
        if want_to_write_config != 'n':   
            write_to_root_file(mod_cfg, conf_path)
            restart_nginx()
    print("Thanks for using my script")