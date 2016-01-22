# swiss-knife
A tiny extendable utility for running commands against multiple hosts (and a little bit more).

### Installation

As for now, just download it somewhere, and make sure you have installed

for main program:
    [exrex](https://github.com/asciimoo/exrex)

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

### Why I did this and why do you need this?
I did it simply because there was no such instruments in my environment, and I needed them from time to time.
As a side note, I hate GUIs and web interfaces for everything that shouldn't be necessary visualized (e.g. UML).
And I just can't accept that I need to make 10 mouse clicks to change a host's environment in Foreman when I know hostname
and environment name exactly. So `swiss-knife` is a simple instrument to make simple operations and its functionality
can be extended rather easily.

There's a few possible reasons you'll find it useful:
- You are a system administrator. If you're not, it's doubtfully be useful for you in any way
- You hate clicking GUIs just like me, and your GUI instrument has an API you could use
- There's no such an instrument in your environment: it's either de-centralized and/or you don't use configuration
management software and its tools heavily
- You'd like to glue altogether all the stuff you use in your environment to classify or group hosts

### Usage
Typical usage looks like

```sk pssh "%hostgroup1[,[-]^hostgroup2,..,host1,[-]host2]" uptime```

which executes uptime on all the hosts over ssh in parallel fashion.

`%`, `^` and other non-alphabetical characters can be treated as hostgroup modifiers which indicate which parser should expand a given hostgroup into a host list.
hyphen (`-`) in front of hostgroup or a host means that hostgroup or host will be excluded from resulting list.
A host may be a simple regex (no * quantificator or anychar (.), no lookahead/lookbehinds, no commas as comma is a hostgroups separator,
so no {n,m} style regexes), `sk` will
generate strings that match it and use it as hosts. If you're excluding hosts that aren't included yet, nothing happens. Hostlist is expanded from left to right. Example:

```sk pssh "^g1,-host[1234]" echo Yay```

will execute `echo Yay` in parallel fashion on each host that's in zabbix hostgroup `g1` except hosts `host1`, `host2`, `host3` and `host4`.


### Details
All the commands, hostgroup modifiers and parsers code is defined through plugins in **sk-modules** dir.
You can find some working modules there mentioned above, as well as dummy examples in **sk-modules/sk-modules-examples** .
Further help can be found in **sk_classes.py**, which you should import when defining your own command and/or parser modules.

For example, if you use Nagios in your environment, you can write a parser that will expand a Nagios hostgroup into a hostlist, or a command that will take a Nagios hostgroup and do something with it using Nagios API.
Information that's used for modules to work (such as authentication information for various APIs) may be stored in config named **sk.ini**.

From the box, sk supports:
- expanding **zabbix** hostgroups (`^` modifier), **caspd** hostgroups (`%` modifier), special `ALL` hostgroup expanding to all the hosts
- running commands over ssh (`ssh` and `pssh` commands), copying files over ssh to multiple hosts
(`dist` command, recursive and without preserving times by default), copying files from multiple
hosts over ssh (`gather`)
- getting and setting hosts environments in **Foreman** (`getenv`
and `setenv` commands), getting classes linked to hosts (`getcls`)
- and just displaying results of hostlist expansion (`dr` for 'dry-run')

As this is an alpha version, author wouldn't recommend to think of sk as of a reliable tool suitable for running important (say, potentially destructive) tasks. i.e. restarting/reinstalling important services, seding mission critical configs, etc. Always double-check command's result on one host before applying it to whole production.

There may be some issues with configparser. If there are, please notify me. In fact, there may be issues with anything.

The code itself should work on python2.7.10+, python3+ but it haven't been tested at all on python3+ (ssh module doesn't work properly in 3.5 due to either author's stupidity or paramiko bug. Author hasn't tried other versions).

#### Notes:
- currently, host cannot start with non-alphanumerical character. This breaks using something like (host|hos)123 as a host as
left bracket will be treated as a hostgroup modifier.
- if a parser doesn't return any hosts, its job is considered failed and program stops
- all the information needed to run a command is added to class attributes, more info on that in **sk_classes**
- all the information you've mentioned in config is also added to class attributes. Section must be named the same as the class that is being configured for this to work; **[Main]** section is for sk program
- `caspd` is a nice piece of software written by my former colleague Stan E. Putrya. It's not yet released to opensource, but I'm sure it will eventually.

(c) Pavel "trueneu" Gurkov, 2016