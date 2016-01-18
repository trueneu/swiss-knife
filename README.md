# swiss-knife
A tiny extendable utility for running commands against multiple hosts.

Installation:

As for now, just download it somewhere, and make sure you have installed

for sk-casp plugin:
    [requests](https://github.com/kennethreitz/requests)
    
for sk-zabbix plugin:
    [pyzabbix](https://github.com/lukecyca/pyzabbix)
    
for sk-ssh-module plugin:
    [paramiko](https://github.com/paramiko/paramiko)
    [scp](https://github.com/jbardin/scp.py)

for sk-foreman plugin:
    [python-foreman](https://github.com/david-caro/python-foreman)

AFAIK, all of these can be installed via `pip`. For more information, please refer to corresponding sites. At this moment there is no setup/dependency mechanism at all.

Typical usage looks like

```sk pssh %hostgroup1[,[-]^hostgroup2,...,host1,[-]host2] uptime```

which executes uptime on all the hosts over ssh in parallel fashion.

`%`, `^` and other non-alphabetical characters can be treated as hostgroup modifiers which indicate which parser should expand a given hostgroup into a host list.
hyphen (`-`) in front of hostgroup or a host means that hostgroup or host will be excluded from resulting list.

All the commands, hostgroup modifiers and parsers code is defined through plugins in sk-modules dir.
You can find some working modules there mentioned above, as well as dummy examples in sk-modules/sk-modules-examples .
Further help can be found in sk_classes.py, which you should import when defining your own command and/or parser modules.

For example, if you use Nagios in your environment, you can write a parser that will expand a Nagios hostgroup into a hostlist, or a command that will take a Nagios hostgroup and do something with it using Nagios API.
Information that's used for modules to work (such as authentication information for various APIs) may be stored in config named sk.ini.

Please note that:
    if a parser doesn't return any hosts, its job is considered failed and program stops;
    all the information needed to run a command is added to class attributes, more info on that in sk_classes
    all the information you've mentioned in config is also added to class attributes. Section must be named the same as the class that is being configured for this to work; [Main] section is for sk program

From the box, sk supports expanding zabbix hostgroups (`^` modifier), caspd hostgroups (`%` modifier), running commands over ssh (`ssh` and `pssh` commands), copying files over ssh (`dist` command, recursive and without preserving times by default), and getting and setting hosts environments in `foreman` (`getenv` and `setenv` commands).

As this is an alpha version, author wouldn't recommend to think of sk as of a reliable tool suitable for running important (say, potentially destructive) tasks. i.e. restarting/reinstalling important services, seding mission critical configs, etc. Always double-check command's result on one host before applying it to whole production.

There may be some issues with configparser. If there are, please notify me.

The code itself should work on python2.7.10+, python3+ but it haven't been tested at all on python3+ (ssh module doesn't work properly in 3.5 due to either author's stupidity or paramiko bug. Author hasn't tried other versions).

Pavel "trueneu" Gurkov
