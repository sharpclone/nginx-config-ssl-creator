import re
import configparser
from pathlib import Path
import subprocess
import os

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


def config_get(key :str):
    #Setting up the config file
    settings = configparser.ConfigParser()
    settings.read("/home/mihu/Documents/Workspace/Py/nginx_proxy_creator/creator.conf")
    cfg = settings["Settings"]
    return cfg[key].strip("\"' ")

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



if __name__ == "__main__":
    #Selecting the template
    template = choose_template(Path(config_get("template_folder")))

    #Open the template
    template = open(template,"r").read()
    # config_string = conf.read()
    mod_cfg,variables = modify_variables(template)
    want_ssl = input("Do you want to get the ssl-cert automatically? [y/N]: ") or 'n'
    if want_ssl.lower() != 'n':
        ssl_method = config_get("ssl_method")
        has_installed_ssl_method = input(f"Have you installed {ssl_method}? [y/N]: ") or 'n'
        if has_installed_ssl_method.lower() == 'n':
            print(f"You should install {ssl_method} and then run this script again")
            exit()
        else:
            print("Note that you should use a SSL template (that have #@ comments)")
            conf_path = config_get("nginx_conf_path") + variables["domain"] + ".conf"
            write_to_root_file(mod_cfg, file_path)

    #Final result
    print(mod_cfg)
