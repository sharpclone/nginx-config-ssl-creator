# nginx-config-ssl-creator
This can be one of the most useful scripts out there for those who manage tons of nginx sites/proxies.

**What it does?**
1. Takes a template as input. A template has variables such as @domain, @web_host, @allow_table. The script then asks for the value of each of these variables and automatically compiles a config and deploys it.
2. Has an function to automatically obtain the SSL certificate right after compiling the config.
3. You can add any variables you want to a template. The script finds variables that start with @, for example @location, @picture, and then asks the user for their value at runtime

**Compatability**
- Works with any linux distro that supports python3, certbot and nginx.
- Works with openBSD, use openbsd_acme in the config to use acme_client

**Special Variables**
-  **#% @ssl** - used for ssl certificate automation
-  **@allow_table** - used to alllow specific subnets. For instance in the wordpress template example i deny access to the admin page to everyone except the subnets in the allow table ( for example 192.168.1.1/24 )
-  **@acme_challenge** - used for ssl certificate automation  on OpenBSD's acme client

All other other variables will be treated as simple variables which have just a simple value. (e.g @domain = example.com )


**Specific notes for SSL**
1. The ssl template should **HAVE** #% @ssl ( it first deploys the unsecure version , then generates the certificates, then replaces #%  @ssl with the ssl certificate locations and then restarts nginx)
2. If you are on OpenBSD you should also have @acme_challenge to make acme_client work.