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

### Bundled modules (plugins)
From the box, sk supports:
- expanding **zabbix** hostgroups (`^` modifier), **caspd** hostgroups (`%` modifier), special `ALL` hostgroup expanding to all the hosts
- running commands over ssh (`ssh` and `pssh` commands), copying files over ssh to multiple hosts
(`dist` command, recursive and without preserving times by default), copying files from multiple
hosts over ssh (`gather`)
- getting and setting hosts environments in **Foreman** (`getenv`
and `setenv` commands), getting, adding and removing classes linked to hosts and hostgroups (`getcls`, `addcls`,
`rmcls`, `getgcls`, `addgcls`, `rmgcls` respectively), and listing available classes (`lscls`)
- and just displaying results of hostlist expansion (`dr` for 'dry-run')

**By default, all the modules but `dr` and `ssh` module are turned off.**
To enable them, you need to copy corresponding files from sk-modules/sk-modules-bundle to sk-modules dir, or
just symlink them (**symlink names have to end with '.py'**). To symlink all the modules present at once, run `enable-all-modules.sh`
script.

### Examples
Imagine that you need to grep all your frontend nginx logs for string '/api/do_something'. Your frontend hostnames
are `frontend00`, `frontend01`, ..., `frontend99`. You could use something like

```sk pssh frontend[0-9][0-9] grep '/api/do_something' /var/log/nginx/access.log```

You can interrupt the command execution at any moment with Ctrl-C.

Suppose your servers are named a bit more sophisticated, like `frontend01`, `frontend02`, ..., `frontend25`. This command
would do the trick (note the quotes around host expression):

```sk pssh 'frontend([0-1][0-9]|2[0-5]),-frontend00' grep '/api/do_something' /var/log/nginx/access.log```

You can always verify if you did the host expression right:

```sk dr 'frontend([0-1][0-9]|2[0-5]),-frontend00'```

Output:

```
frontend01
frontend02
<...skipped...>
frontend24
frontend25
```

Suppose you also have servers `backend01`, `backend02`, ..., `backend10`, and you want to run `uptime` on both
frontends and backends. Try this one:

```sk pssh 'frontend([0-1][0-9]|2[0-5]),-frontend00,backend(0[1-9]|10)' uptime```

Now imagine you have to execute a certain script named `test.sh` on those 25 frontends locally. First, copy it to target hosts:

```sk dist 'frontend([0-1][0-9]|2[0-5]),-frontend00' ./my_scripts/test.sh /usr/share/```

and then execute it:

```sk pssh 'frontend([0-1][0-9]|2[0-5]),-frontend00' /usr/share/test.sh```

Imagine you need to do something with nginx logs locally on your computer (say, a simple statistics calculation).
You can gather all the logs to your machine with one command:

```sk gather 'frontend([0-1][0-9]|2[0-5]),-frontend00' /var/log/nginx/access.log ./nginx-logs-from-production```

This will create 'nginx-logs-from-production' directory in your current working directory, and copy over all
the access.log files, appending a suffix so you can tell from which host each log has been copied.

Say you have a Zabbix installation in your environment, and all the frontends are in 'frontend' hostgroup.
You can do the same as above using zabbix hostgroup expansion (note that `zabbix` module is disabled by
 default. More on that in [bundled modules](#bundled-modules-plugins) section above)

```sk gather ^frontend /var/log/nginx/access.log ./nginx-logs-from-production```

Imagine that you have Foreman installation and you need to set all the frontends' environments to 'development'
(note that you still use ^ here, so host expansion mechanism works with Zabbix hostgroups)

```sk setenv ^frontend development```

...or add to frontend Foreman hostgroup your brand new `nginx::verbose_access_logs` Puppet class

```sk addgcls frontend nginx::verbose_access_logs```

Remember to use and escape quotes when needed!

```sk pssh ^mysql mysql -e 'show variables like "read_only"'``` won't work (due to shell quote processing,
it represents `mysql -e show variables like "read only"`), but

```sk pssh ^mysql "mysql -e 'show variables like \"read_only\"'"``` will.


You can get more info on available parsers, commands and arguments by running `sk -h` .

If you need to change your default SSH user, parallel processes count, API credentials or such,
 take a look at `sk.ini` file.

### Details
All the commands, hostgroup modifiers and parsers code is defined through plugins in **sk-modules** dir.
You can define your own rather easily.
You can find some working modules there mentioned above, as well as dummy examples in **sk-modules/sk-modules-examples** .
Further help can be found in **sk_classes.py**, which you should import when defining your own command and/or parser modules.

For example, if you use Nagios in your environment, you can write a parser that will expand a Nagios hostgroup into a hostlist,
or a command that will take a Nagios hostgroup and do something with it using Nagios API (say, downtime it or something).
Information that's used for modules to work (such as authentication information for various APIs) may (and should) be stored in config named **sk.ini**.

### Why did I do this and why you may need this?
I did it simply because there was no such instruments in my environment, and I needed them from time to time.
As a side note, I hate GUIs and web interfaces for everything that shouldn't be necessary visualized (like UML or statistic charts).
And I just can't accept that I need to make 10 mouse clicks to change a host's environment in Foreman when I know hostname
and environment name exactly. So `swiss-knife` is a simple instrument to make simple operations and its functionality
can be extended rather easily.

There's a few possible reasons you'll find it useful:
- You are a system administrator. If you're not, it's doubtfully be useful for you in any way
- You hate clicking GUIs just like me, and your GUI instrument(s) has an API you could use
- There's no such an instrument in your environment: it's either de-centralized and/or you don't use configuration
management software and its tools heavily
- You'd like to glue altogether all the stuff you use in your environment to classify or group hosts and you know
a little bit of python

### Known issues and notes

As this is an alpha version, author wouldn't recommend to think of sk as of a reliable tool suitable for running important
(say, potentially destructive) tasks. i.e. restarting/reinstalling important services,
`sed`ing mission critical configs, etc. Always double-check command's result on one host before applying it to whole production,
use `dr` command.

There may be some issues with configparser. If there are, please notify me. In fact, there may be issues with anything.

The code itself should work on python2.7.10+, python3+ but it haven't been tested at all on python3+
(ssh module doesn't work properly in 3.5 due to either author's stupidity or `paramiko` bug. Author
hasn't tried other versions).

###### Usage notes

- currently, host cannot start with non-alphanumerical character. This breaks using something like (host|hos)123 as a host as
left bracket will be treated as a hostgroup modifier.
- ssh module needs a running ssh-agent with private keys added, or private keys need to remain password free
- username for ssh specified in sk.ini will override your current username and username from .ssh/config if present

###### Dev notes

- if a parser doesn't return any hosts, its job is considered failed and program stops
- all the information needed to run a command is added to class attributes, more info on that in **sk_classes**
- all the information you've mentioned in config is also added to class attributes. Section must be named the same as the class that is being configured for this to work; **[Main]** section is for sk program
- `caspd` is a nice piece of software written by my former colleague Stan E. Putrya. It's not yet released to opensource, but I'm sure it will eventually.

### Contributions
Please do! Don't forget to exclude sensitive details from `sk.ini` and change `SwissKnife`
`_environment` attribute to `production` when pushing.

(c) Pavel "trueneu" Gurkov, 2016