import re
import configparser
from pathlib import Path
import subprocess
import os


def config_get(key :str):
    #Setting up the config file
    settings = configparser.ConfigParser()
    settings.read("config")
    cfg = settings["Settings"]
    return cfg[key].strip("\"' ")


def config_set(key, value):
    config = configparser.ConfigParser()
    config.read("config")
    parser = config['Settings']
    parser[key] = value
    with open('config', 'w') as configfile:
        config.write(configfile)


def write_to_root_file(content, file_path):
    # Create a temporary file to hold the content
    temp_file = '/tmp/tmp-nginx-compiled.txt'
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
        special_vars = ['allow_table','ssl','acme_challenge']
        #Allow table specific
        if var == "allow_table":
            table = ""
            useDef = input(f"Do you want to use {config_get('allow_table')} for the allowed IPs that are allowed to access the location? [Y/n] " ).lower() or 'y'
            if useDef == 'n':
                val = input(f"Give the allowed CIDR noted IPs (separated by comma) that are allowed to access the location :").strip()
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
        if var == "acme_challenge":
            acme_challenge = open("acme_challenge").read()
            acme_root = config_get("acme_root")
            is_ok = input(f"Is {acme_root} the correct path for the acme root ? [Y/n]: ").lower() or 'y'
            if is_ok == 'n':
                acme_root = input("Input the correct path for the acme root (it will change the config): ").strip()
                config_set("acme_root", acme_root)
            acme_challenge = acme_challenge.replace("@acme_root", acme_root)
            final_cfg = final_cfg.replace("@acme_challenge", acme_challenge)
        

        #Other simple variables
        elif var not in special_vars:
            val = input(f"Give the value of {var}: ").strip()
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


def get_ssl(config, variables):
    su = config_get("root_method")
    ssl_method = config_get("ssl_method")
    has_installed_ssl_method = config_get("has_installed_ssl_method")
    if has_installed_ssl_method == "0":
        has_installed_ssl_method = input(f"Have you installed {ssl_method}? [y/N]: ").lower() or 'n'
        if has_installed_ssl_method == 'y':
            config_set("has_installed_ssl_method", '1')
        else:
            print(f"You should install {ssl_method} and then run this script again")
            exit()


    print("Note that you should use a SSL template ")


    write_to_root_file(config, variables["config_path"])
    restart_nginx()


    domain = variables["domain"]

    if ssl_method == 'certbot':
        webroot_path = input("Please enter the webroot path for certbot: ").strip()
        subprocess.run(f"{su} certbot certonly --dry-run --webroot -w {webroot_path} -d {domain}", shell=True)
        is_ok = input("Did the dry-run complete succesfully? [y/N]: ").lower() or 'n'
        if is_ok == 'n':
            print("Check your configuration and try again")
            exit()
        else:
            subprocess.run(f"{su} certbot certonly  --webroot -w {webroot_path} -d {domain}", shell=True)

    if ssl_method == 'openbsd_acme':
        subprocess.run(f"{su} acme-client -v {domain}", shell=True)

    cert_path = config_get("ssl_cert_path")
    key_path = config_get("ssl_cert_key_path")
    
    is_ok = input(f"Is {cert_path} the correct certificate path? [Y/n]: ").lower() or 'y'
    if is_ok == 'n':
        cert_path = input("Please input the template for your certificate path (it will update the config): ").strip()
        config_set("ssl_cert_path", cert_path)

    is_ok = input(f"Is {cert_path} the correct key path? [Y/n]: ").lower() or 'y'
    if is_ok == 'n':
        key_path = input("Please input the template for your key path (it will update the config): ").strip()
        config_set("ssl_cert_key_path", key_path)

    config =  config.replace("#%", "")
    config =  config.replace("listen 80;", "listen 443 ssl http2;")
    certificates =  f"ssl_certificate {cert_path.replace('@domain', domain)};\nssl_certificate_key {key_path.replace('@domain', domain)};\n"
    config =  config.replace("@ssl", certificates)


    return301 = open("return301.conf")\
        .read()\
        .replace("@domain", domain)
    
    config = config + '\n' + return301;

    write_to_root_file(config, variables["config_path"])
    restart_nginx()


if __name__ == "__main__":
    #Selecting the template
    template = choose_template(Path("templates"))

    #Open the template
    template = open(template,"r").read()
    # config_string = conf.read()
    mod_cfg,variables = modify_variables(template)
    conf_path = config_get("nginx_conf_path") + variables["domain"] + ".conf"
    variables["config_path"] = conf_path

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