# swiss-knife
An extendable utility for doing everything with self-defined hosts/hostgroups, utilizing API of your environment,
with parallel ssh out of the box.

Destroying all your databases at once has never been this simple!
```
swk pssh ^mysql 'rm -rf /var/lib/mysql'
```
(yeah, you really shouldn't do that in production environment. Unless...)

### What can it do?
The basic idea is: you specify what to do (a command), a list of hosts or hostgroups to do that with, and
additional arguments if needed (depends on what you want to do). You can easily define your own commands
through the plugin interface, as well as your own hostgroup parsers (usually they'll just ask some API in
your environment about which hosts are included in provided hostgroup). Basic Foreman, Zabbix API and ssh
 functions are supported out of the box.

Please note that this is *not* `fabric`.

### Installation

As for now, just download it somewhere, and run

```
pip install <some_path>/swk
```
If you need plugins for casp, Foreman or Zabbix, also run

```
pip install <some_path>/swk_plugins/swk_casp_plugin
pip install <some_path>/swk_plugins/swk_foreman_plugin
pip install <some_path>/swk_plugins/swk_zabbix_plugin
```

Installation script will also create **~/.swk** directory, where you should find **swk.ini** configuration
file, and that's used to store shell mode command history, program's log, various plugins' cache, etc.

Please note that you should use python3.2+ for shell mode to work. Everything else should work with
python2.7.


### Usage
Typical usage looks like

```swk pssh "%hostgroup1[,[-]^hostgroup2,..,host1,[-]host2]" uptime```

which executes uptime on all the hosts over ssh in parallel fashion.

`%`, `^` and other non-alphabetical characters can be treated as hostgroup modifiers which indicate which parser should expand a given hostgroup into a host list.
hyphen (`-`) in front of hostgroup or a host means that hostgroup or host will be excluded from resulting list.
A host may be a simple regex (no * quantificator or anychar (.), no lookahead/lookbehinds, no commas as comma is a hostgroups separator,
so no {n,m} style regexes), `swk` will
generate strings that match it and use it as hosts. If you're excluding hosts that aren't included yet, nothing happens. Hostlist is expanded from left to right. Example:

```swk pssh "^g1,-host[1234]" echo Yay```

will execute `echo Yay` in parallel fashion on each host that's in zabbix hostgroup `g1` except hosts `host1`, `host2`, `host3` and `host4`.

### Available and bundled plugins
From the box, swk supports:
- running commands over ssh (`ssh` and `pssh` commands), copying files over ssh to multiple hosts
(`dist` command, recursive and without preserving times by default), copying files from multiple
hosts over ssh (`gather`)
- and just displaying results of hostlist expansion (`dr` for 'dry-run')

By installing additional packages named `swk_*_plugin`, you also get
- expanding **zabbix** hostgroups (`^` modifier), **caspd** hostgroups (`%` modifier), special `ALL` hostgroup expanding to all the hosts
- getting and setting hosts environments in **Foreman** (`getenv`
and `setenv` commands), getting, adding and removing classes linked to hosts and hostgroups (`getcls`, `addcls`,
`rmcls`, `getgcls`, `addgcls`, `rmgcls` respectively), and listing available classes (`lscls`)
- expanding **casp** hostgroups (those are really Foreman's, but casp's API is simpler and faster. However,
I really doubt you have **casp** installed)

To install them, please refer to [Installation](#Installation) section above.

Hopefully, there are more coming.

### Examples
Imagine that you need to grep all your frontend nginx logs for string '/api/do_something'. Your frontend hostnames
are `frontend00`, `frontend01`, ..., `frontend99`. You could use something like

```swk pssh frontend[0-9][0-9] grep '/api/do_something' /var/log/nginx/access.log```

You can interrupt the command execution at any moment with Ctrl-C.

Suppose your servers are named a bit more sophisticated, like `frontend01`, `frontend02`, ..., `frontend25`. This command
would do the trick (note the quotes around host expression):

```swk pssh 'frontend([0-1][0-9]|2[0-5]),-frontend00' grep '/api/do_something' /var/log/nginx/access.log```

You can always verify if you did the host expression right:

```swk dr 'frontend([0-1][0-9]|2[0-5]),-frontend00'```

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

```swk pssh 'frontend([0-1][0-9]|2[0-5]),-frontend00,backend(0[1-9]|10)' uptime```

Now imagine you have to execute a certain script named `test.sh` on those 25 frontends locally. First, copy it to target hosts:

```swk dist 'frontend([0-1][0-9]|2[0-5]),-frontend00' ./my_scripts/test.sh /usr/share/```

and then execute it:

```swk pssh 'frontend([0-1][0-9]|2[0-5]),-frontend00' /usr/share/test.sh```

Imagine you need to do something with nginx logs locally on your computer (say, a simple statistics calculation).
You can gather all the logs to your machine with one command:

```swk gather 'frontend([0-1][0-9]|2[0-5]),-frontend00' /var/log/nginx/access.log ./nginx-logs-from-production```

This will create 'nginx-logs-from-production' directory in your current working directory, and copy over all
the access.log files, appending a suffix so you can tell from which host each log has been copied.

Say you have a Zabbix installation in your environment, and all the frontends are in 'frontend' hostgroup.
You can do the same as above using zabbix hostgroup expansion (note that `zabbix` module is disabled by
 default. More on that in [Available plugins](#available-and-bundled-plugins) section above)

```swk gather ^frontend /var/log/nginx/access.log ./nginx-logs-from-production```

Imagine that you have Foreman installation and you need to set all the frontends' environments to 'development'
(note that you still use ^ here, so host expansion mechanism works with Zabbix hostgroups)

```swk setenv ^frontend development```

...or add to frontend Foreman hostgroup your brand new `nginx::verbose_access_logs` Puppet class

```swk addgcls frontend nginx::verbose_access_logs```

Remember to use and escape quotes when needed!

```swk pssh ^mysql mysql -e 'show variables like "read_only"'``` won't work (due to shell quote processing,
it represents `mysql -e show variables like "read only"`), but

```swk pssh ^mysql "mysql -e 'show variables like \"read_only\"'"``` will.


You can get more info on available parsers, commands and arguments by running `swk -h` .

If you need to change your default SSH user, parallel processes count, API credentials or such,
 take a look at `swk.ini` file.

##### Shell mode

If you run `swk` without any arguments, it starts in shell mode. Like this:

```
trueneu$ swk
swk>
```

You can do absolutely all the same like in command line mode, but shell mode has a few advantages:

- you don't need to think about quote escaping in tricky commands, because the arguments
are treated literally even if not quoted
- tab completion command support thanks to `pypsi`

For example, that ugly mysql example above would look like this in shell mode:

```
swk> pssh ^mysql mysql -e 'show variables like "read_only"'
```

Additionally, you may call any system utility from inside `swk` shell via `sys` command:
```
swk> pssh ^mysql mysql -e 'show variables like "%format%"' | sys grep innodb
```

It also supports history through `hist` command, etc. To get help on any command, issue `help <command>` or `help`
without arguments to get an overview.

### Details
Commands, hostgroup modifiers and parsers code are defined through swk plugins. They can be connected
to the main program in three ways: being included in main package under **swk/swk_plugins** dir,
having a defined **swk_plugin** entry point in their setup.py and installed or just being put in
one of **plugins_directories** dir from **swk.ini** file.

You can find some working plugins there mentioned above, as well as dummy examples in **swk_plugins_examples** .
Further help can be found in **swk/swk_classes.py**, which you MUST import when defining your own
command and/or parser modules.

For example, if you use Nagios in your environment, you can create a parser that will expand a Nagios hostgroup into a hostlist,
or a command that will take a Nagios hostgroup and do something with it using Nagios API (say, downtime it or something).
Information that's used for modules to work (such as authentication information for various APIs) may (and should)
be stored in config named **swk.ini**.

##### Shell mode parsing details
When in shell mode, every argument starting with the third *to the end of the line* is passed literally
even if not quoted except for built-in `pypsi` commands (that includes `pwd`, `cd`, `sys` etc,
full list can be found via `help` command in shell mode). It sounds a little bit confusing at first,
but it has its benefits. You do not need to escape backslash character, and you don't need the
outer level of quoting when ssh`ing this way.

Trade-offs:
- you have to implement your own argument parsing in command plugins for them
to work correctly (using a whitespace or something else as a delimiter).
- you have to escape chaining/io redirection characters for those to be passed
as arguments to commmand
instead of work locally. For example, `ssh remote echo ABC > file` creates `file` on local machine, but
 `ssh remote echo ABC \> file` does the same on remote.


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

As this is an alpha version, author wouldn't recommend to think of `swk` as of a reliable tool suitable for running important
(say, potentially destructive) tasks. i.e. restarting/reinstalling important services,
`sed`ing mission critical configs, etc. Always double-check command's result on one host before applying it to whole production,
use `dr` command.



The code itself should work on python2.7+, python3.2+.

###### Usage notes

- currently, host cannot start with non-alphanumerical character. This breaks using something like (host|hos)123 as a host as
left bracket will be treated as a hostgroup modifier.
- ssh module needs a running ssh-agent with private keys added, or private keys need to remain password free
- username for ssh specified in **swk.ini** will override your current username and username from .ssh/config if present
- Ctrl-C works poorly when pssh'ing (providing you unneeded tracebacks from multiprocessing)
- interactive user input is NOT supported when running a command

###### Dev notes

- if a parser doesn't return any hosts, its job is considered failed and desired command doesn't start
- all the information needed to run a command is added to class attributes, more info on that in **swk_classes**
- all the information you've mentioned in config is also added to class attributes. Section must be named the same as the class that is being configured for this to work; **[Main]** section is for swk program
- `caspd` is a nice piece of software written by my former colleague Stan E. Putrya. It's not yet released to opensource, but I'm sure it will eventually.

##### Dependencies

- for main program:
    [exrex](https://github.com/asciimoo/exrex)
    [pypsi](https://github.com/ameily/pypsi)
- for swk-casp plugin:
    [requests](https://github.com/kennethreitz/requests)
- for swk-zabbix plugin:
    [pyzabbix](https://github.com/lukecyca/pyzabbix)
- for swk-ssh-module plugin:
    [paramiko](https://github.com/paramiko/paramiko)
    [scp](https://github.com/jbardin/scp.py)
- for swk-foreman plugin:
    [python-foreman](https://github.com/david-caro/python-foreman)

### Contributions
Please do! Don't forget to exclude sensitive details from `swk.ini`.

(c) Pavel "trueneu" Gurkov, 2016