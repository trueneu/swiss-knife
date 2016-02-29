"""
Main program module.

swk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see swk/main.py for more information on License and contacts
"""

import logging
import os
import glob

from swk import classes
import inspect
from swk import exceptions
import argparse
import configparser
import sys
import exrex
import pkg_resources
from swk import version
import shutil
from swk import check_updates
import datetime

shell_mode_off = False
try:
    import swk.shell
except SyntaxError:
    #logging.warning("swk shell mode has been disabled. Seems like you're using Python 2")
    shell_mode_off = True
except ImportError:
    #logging.warning("swk shell mode has been disabled. Seems like you haven't installed pypsi package")
    shell_mode_off = True


class SwissKnife(object):
    _version = version.__version__

    swk_plugin_dir_default = "plugins"
    _swk_config_path = "~/.swk/"
    _swk_config_filename = "swk.ini"
    _swk_config_full_path = os.path.join(os.path.expanduser(_swk_config_path), _swk_config_filename)
    _swk_package_name = 'swk'
    _swk_check_updates_marker_filename = 'checked_updates'
    _swk_check_updates_marker_full_path = os.path.join(os.path.expanduser(_swk_config_path),
                                                       _swk_check_updates_marker_filename)
    _swk_check_updates_period = 60 * 60 * 24

    def _write_default_config(self):
        if not os.path.isdir(os.path.dirname(self._swk_config_full_path)):
            try:
                os.mkdir(os.path.dirname(self._swk_config_full_path))
            except IOError:
                msg = "Couldn't create directory {path}, aborting.".format(
                    path=os.path.dirname(self._swk_config_full_path))
                self._die(msg)

        if not os.path.isfile(self._swk_config_full_path):
            try:
                shutil.copy(os.path.join(os.path.dirname(classes.__file__), self._swk_config_filename),
                            self._swk_config_full_path)
            except IOError:
                msg = "Couldn't create default config at {path}, aborting.".format(path=self._swk_config_full_path)
                self._die(msg)

    def _check_updates(self, package_version_dict):
        now = datetime.datetime.utcnow()
        now_timestamp = (now - datetime.datetime(1970, 1, 1)).total_seconds()
        try:
            check_updates_marker_mtime = os.path.getmtime(self._swk_check_updates_marker_full_path)
        except (IOError, OSError):
            check_updates_marker_mtime = now_timestamp - (self._swk_check_updates_period + 1)
        if now_timestamp - check_updates_marker_mtime > self._swk_check_updates_period:
            try:
                cheese_shop = check_updates.CheeseShop()
            except:
                msg = "Couldn't run check for new versions. Please check your Internet settings or turn " \
                      "checking for updates off " \
                      "in {0}.".format(self._swk_config_filename)
                logging.error(msg)
                sys.stderr.write(msg + '\n')
                sys.stderr.flush()
                return
            for k, v in package_version_dict.items():
                package_name = k
                installed_version = v
                try:
                    last_version = cheese_shop.package_releases(package_name)[0]
                except:
                    msg = "Couldn't run check for new versions of {package}. " \
                          "Please check your Internet settings or turn " \
                          "checking for updates off " \
                          "in {conf_file}.".format(conf_file=self._swk_config_filename, package=package_name)
                    logging.error(msg)
                    sys.stderr.write(msg + '\n')
                    sys.stderr.flush()
                    last_version = installed_version
                if check_updates.get_highest_version([installed_version, last_version]) != installed_version:
                    sys.stderr.write("You're using {package} v{old}, but v{new} is available! Please upgrade.\n".format(
                        old=installed_version, new=last_version, package=package_name
                    ))
                    logging.info("You're using {package} v{old}, but v{new} is available! Please upgrade.\n".format(
                        old=installed_version, new=last_version, package=package_name
                    ))

            with open(self._swk_check_updates_marker_full_path, mode='w'):
                pass

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, "_{0}".format(k), v)

        self._write_default_config()
        self._config = self._read_config()
        
        self._logging_init()

        package_version_dict = {self._swk_package_name: self._version}

        self._disabled_plugins = [plugin for plugin in self._config["Main"].get("disabled_plugins", "").split()]

        self._cache_directory_expanded = os.path.abspath(os.path.expanduser(self._config["Main"].get("cache_directory",
                                                                                                  "~/.swk")))
        self._cache_directory_init()

        self._swk_plugins_dirs = [os.path.expanduser(x) for x in self._config["Main"].get("plugins_directories", "").split()]
        self._swk_plugins_dirs.append("{0}/{1}".format(self._swk_dir, self.swk_plugin_dir_default))
        self._plugin_modules, self._plugin_command_modules, self._plugin_parser_modules,\
            modules_package_version_dict = self._modules_import()

        package_version_dict.update(modules_package_version_dict)
        if self._config["Main"].get("check_for_updates", "no") == "yes":
            self._check_updates(package_version_dict)

        self._available_commands, self._available_parsers = self._get_available_commands_and_parsers()
        self._commands_help_message, self._parsers_help_message, \
            self._commands_help_string, self._parsers_help_string = self._form_commands_and_parsers_help()

        self._config = self._add_empty_sections_to_config()  # now that we know what's imported

        self._args = self._parse_args()

        self._command = self._args["command"]

        if self._command == 'shell':
            pass
        else:
            """almost all this stuff below we do based on arguments we got so it gotta be excluded from shell variant"""
            self._command_executer_class = self._find_command_executer_class()
            self._command_executer_name = self._command_executer_class.__name__
            self._command_requires_hostlist = self._command_executer_class.requires_hostlist(self._args["command"])
            self._args = self._arguments_magic()

            self._command_args = self._args["command_args"]
            self._hostlist = self._args["hostlist"]



    def _logging_init(self):
        loglevel_string = self._config["Main"].get("loglevel", "error")
        try:
            loglevel = {"debug": logging.DEBUG,
                        "info": logging.INFO,
                        "warning": logging.WARNING,
                        "error": logging.ERROR,
                        "critical": logging.CRITICAL}[loglevel_string]
        except KeyError:
            loglevel = logging.ERROR
        if loglevel == logging.DEBUG:
            self._dbg_prints = True
        else:
            self._dbg_prints = False
        logfile = os.path.expanduser(self._config["Main"].get("logfile", "~/.swk/swk.log"))
        logging.basicConfig(filename=logfile, filemode='a', level=loglevel,
                            format='[%(asctime)s] %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.debug("swk started")

    def _cache_directory_init(self):
        if not os.path.exists(self._cache_directory_expanded):
            try:
                os.mkdir(self._cache_directory_expanded)
            except OSError:
                self._die("Couldn't create {0} directory. Check permissions".format(self._cache_directory_expanded))


    @staticmethod
    def _die(diemsg):
        logging.error(diemsg)
        sys.stderr.write(diemsg + '\n')
        logging.debug("swk died")
        exit(2)

    def _modules_import(self):

        module_filenames = list()
        plugin_modules = list()
        plugin_command_modules = list()
        plugin_parser_modules = list()
        package_version_dict = dict()
        oldcwd = os.getcwd()

        # directory imports

        for swk_plugins_dir in self._swk_plugins_dirs:
            try:
                swk_plugins_dir_abspath = os.path.abspath(swk_plugins_dir)
                os.chdir(swk_plugins_dir_abspath)
                module_filenames = glob.glob("*.py")
            except OSError:
                self._die("{0} does not exist.".format(swk_plugins_dir_abspath))

            """import all the plugin modules and put them into list"""

            for module_filename in module_filenames:
                module_name, _, _ = module_filename.rpartition('.py')
                if module_name in self._disabled_plugins or module_name in ['__init__']:
                    continue

                try:
                    sys.path.append(os.getcwd())
                    module = __import__(module_name)
                except ImportError as e:
                    # self._die("Couldn't import module {0}: {1}.".format(module_name, str(e)))
                    logging.error("Couldn't import module {0}: {1}.".format(module_name, str(e)))
                plugin_modules.extend([(name, obj) for (name, obj) in inspect.getmembers(module)
                                       if inspect.isclass(obj) and issubclass(obj, classes.SWKPlugin)])
        os.chdir(oldcwd)

        # entry_points imports
        for entry_point in pkg_resources.iter_entry_points(group='swk_plugin', name=None):
            #first variant
            module_name = entry_point.module_name

            if module_name in self._disabled_plugins or module_name in ['__init__']:
                continue
            try:
                module = __import__(module_name, fromlist=[module_name[:module_name.rfind('.')]])
            except ImportError as e:
                # self._die("Couldn't import module {0}: {1}.".format(module_name, str(e)))
                logging.error("Couldn't import module {0}: {1}.".format(module_name, str(e)))
            try:
                package_version = __import__(module_name[:module_name.rfind('.')] + '.version',
                                             fromlist=[module_name[:module_name.rfind('.')]])
                package_version_dict[module_name[:module_name.rfind('.')]] = package_version.__version__
            except ImportError:
                pass

            plugin_modules.extend([(name, obj) for (name, obj) in inspect.getmembers(module)
                                   if inspect.isclass(obj) and issubclass(obj, classes.SWKPlugin)])

            #second variant
            """
            package_name = entry_point.module_name
            package = __import__(package_name)
            for module in inspect.getmembers(package):
                plugin_modules.extend([(name, obj) for (name, obj) in inspect.getmembers(module)
                                           if inspect.isclass(obj) and issubclass(obj, swk_classes.SWKPlugin)])
            """


        """then sort them into command modules and parser modules"""
        plugin_command_modules.extend([(name, obj) for (name, obj) in plugin_modules
                                       if issubclass(obj, classes.SWKCommandPlugin)])
        plugin_parser_modules.extend([(name, obj) for (name, obj) in plugin_modules
                                      if issubclass(obj, classes.SWKParserPlugin)])

        logging.debug("Imported modules")
        logging.debug("All modules: {0}".format(plugin_modules))
        logging.debug("Command modules: {0}".format(plugin_command_modules))
        logging.debug("Parser modules: {0}".format(plugin_parser_modules))
        return plugin_modules, plugin_command_modules, plugin_parser_modules, package_version_dict

    def _get_available_commands_and_parsers(self):
        available_commands = dict()
        available_parsers = dict()
        for plugin_command_module in self._plugin_command_modules:
            module_name, module_class = plugin_command_module
            commands = module_class.get_commands()
            for command in commands:
                if command not in available_commands.keys():
                    available_commands[command] = module_class
                else:
                    self._die("Command {0} is defined in both plugins {1} and {2}. Ambigous definition".format(
                        command, available_commands[command].__name__, module_class.__name__))

        for plugin_parser_module in self._plugin_parser_modules:
            module_name, module_class = plugin_parser_module
            parsers = module_class.get_parsers()
            for parser in parsers:
                if parser not in available_parsers.keys():
                    available_parsers[parser] = module_class
                else:
                    self._die("Parser {0} is defined in both plugins {1} and {2}. Ambigous definition".format(
                        parser, available_parsers[parser].__name__, module_class.__name__))

        logging.debug("Available commands: {0}".format(available_commands))
        logging.debug("Available parsers: {0}".format(available_parsers))
        return available_commands, available_parsers

    def _form_commands_and_parsers_help(self):
        commands_help_message = "Commands help:\n"
        parsers_help_message = "Parsers help:\n"
        commands_help_string = ""
        parsers_help_string = ""

        for plugin_command_module in self._plugin_command_modules:
            module_name, module_class = plugin_command_module
            commands_help_message += module_class.commands_help()

        for plugin_parser_module in self._plugin_parser_modules:
            module_name, module_class = plugin_parser_module
            parsers_help_message += module_class.parsers_help()

        for k, v in self._available_commands.items():
            commands_help_string += ' ' + k

        for k, v in self._available_parsers.items():
            if k == "%":
                parsers_help_string += ' %%'  # argparse placeholders escape
            else:
                parsers_help_string += ' ' + k

        return commands_help_message, parsers_help_message, commands_help_string, parsers_help_string

    def _parse_args(self):
        argparse_epilog = '{0}'.format(self._commands_help_message) + "\n" + \
                          "{0}".format(self._parsers_help_message)

        result = dict()

        argparser = argparse.ArgumentParser(description="Swiss knife for doing everything in your infrastructure.",
                                            epilog=argparse_epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
        argparser.add_argument('command', help='command. Valid choices are: {0}'.format(self._commands_help_string),
                               default='shell', nargs='?', type=str)
        argparser.add_argument('hostlist', help='hosts and/or hostgroups for command to apply to, divided by commas (,). '
                                                'Valid hostgroup modifiers are: {0}'.format(self._parsers_help_string),
                               nargs='?')
        argparser.add_argument('command_args', help='additional arguments for chosen command.', nargs=argparse.REMAINDER)
        argparser.add_argument('--version', action="version", version="%(prog)s {0}".format(self._version))

        args = argparser.parse_args(sys.argv[1:])

        result['command'] = args.command
        result['hostlist'] = args.hostlist

        result['command_args'] = args.command_args

        return result

    def _read_config(self):
        result = dict()

        config_path = self._swk_config_full_path
        if not os.path.exists(config_path):
            raise exceptions.ConfigNotFoundError("Config file not found: {0}".format(config_path))

        config = configparser.ConfigParser()
        config.read(config_path)

        for section in config.sections():
            result[section] = dict()
            for k in config.items(section):
                name, value = k
                result[section][name] = value

        return result

    def _add_empty_sections_to_config(self):
        config = self._config
        for module_name, _ in self._plugin_command_modules:
            if module_name not in config:
                config[module_name] = dict()

        for module_name, _ in self._plugin_parser_modules:
            if module_name not in config:
                config[module_name] = dict()
        logging.debug("Added missing sections to config. Now config is: {0}".format(config))
        return config

    def _find_command_executer_class(self):
        try:
            command_executer_class = self._available_commands[self._args["command"]]
        except KeyError:
            self._die("Unsupported command {0}".format(self._args["command"]))
        logging.debug("Command executer class is: {0}".format(command_executer_class))
        return command_executer_class

    def _arguments_magic(self):
        """this magic is required because hostlist is always the second parameter. if we don't need it
            we simply ignore it."""
        args = self._args
        if self._command_requires_hostlist:
            try:
                if len(args["hostlist"]) == 0:
                    self._die("Hostlist is required for command {0}, but is not provided".format(args["command"]))
            except TypeError:
                self._die("Hostlist is required for command {0}, but is not provided".format(args["command"]))
        else:
            args["command_args"].insert(0, args["hostlist"])
            args["hostlist"] = ""
        logging.debug("Did some arguments magic. Now args are: {0}".format(args))
        return args

    def _update_config(self, class_name, **kwargs):
        config = self._config[class_name]
        for k, v in kwargs.items():
            config[k] = v
        logging.debug("Updated config for class {0}. Now its config is: {1}".format(class_name, config))
        return config

    def _escape_unsafe_characters(self, string):
        return string.replace('.', r'\.')


    def _die_if_unsafe_characters(self, string):
        if string.find('*') != -1:
            self._die("Unsafe characters found in hostlist. Exiting")


    def _read_hostlist_from_stdin(self):
        hostlist_lines = sys.stdin.readlines()
        self._hostlist += '\n'.join(hostlist_lines)

    def _expand_hostlist(self):
        expanded_hostlist = list()  # expanded

        if (self._hostlist[0] == "'" and self._hostlist[-1] == "'") or \
                (self._hostlist[0] == '"' and self._hostlist[-1] == '"'):
            self._hostlist = self._hostlist[1:-1]

        # yeah, maybe we'll need that dirty hack in the future

        if len(self._hostlist) == 1 and self._hostlist[0] == '-':
            # special case for reading stdin instead of command args
            self._read_hostlist_from_stdin()

        hostgroups = self._hostlist.split()

        for hostgroup in hostgroups:
            hostlist_addition = list()
            negation = False
            hostgroup_modifier = hostgroup[0]  # the first symbol
            hostgroup_remainder = hostgroup[1:]

            if hostgroup_modifier == '-':
                negation = True
                hostgroup_modifier = hostgroup[1]
                hostgroup_remainder = hostgroup[2:]
                hostgroup = hostgroup[1:]

            if hostgroup_modifier not in self._available_parsers:
                if not hostgroup_modifier.isalnum():
                    raise exceptions.ExpandingHostlistError("Couldn't find corresponding parser for {0} modifier.".format(hostgroup_modifier))
                else:  # hostgroup is a host or a regex, not a group
                    escaped_hostgroup = self._escape_unsafe_characters(hostgroup)
                    self._die_if_unsafe_characters(escaped_hostgroup)
                    hostlist_addition = list(exrex.generate(escaped_hostgroup, limit=1000))
                    # hostlist_addition.append(hostgroup)
            else:  # we must call a parser
                parser = self._available_parsers[hostgroup_modifier]
                parser_name = parser.__name__
                self._config[parser_name] = self._update_config(parser_name, hostgroup_modifier=hostgroup_modifier,
                                                                hostgroup=hostgroup_remainder)
                obj = parser(**self._config[parser_name])
                try:
                    hostlist_addition = obj.parse()
                    if len(hostlist_addition) == 0:
                        raise exceptions.ExpandingHostlistError("Parser {0} didn't return any hosts for hostgroup {1}".format(
                            parser.__name__, hostgroup_remainder
                        ))
                except classes.SWKParsingError as e:
                    raise exceptions.ExpandingHostlistError("Parser {0} died with message: {1}".format(parser.__name__, str(e)))

            if not negation:
                # don't add host twice
                expanded_hostlist.extend([x for x in hostlist_addition if x not in expanded_hostlist])
            else:
                # delete host from list if present
                expanded_hostlist = [x for x in expanded_hostlist if x not in hostlist_addition]

        logging.debug("Expanded hostlist: {0}".format(expanded_hostlist))
        return sorted(expanded_hostlist)

    def run(self):
        if self._command == 'shell':
            if shell_mode_off:
                self._die("Please update python to python3+ to run shell mode")
            # this is a very special case
            swk.shell.SWKShellPrepare(self)
            shell = swk.shell.SWKShell(self)
            exit_status = shell.cmdloop()
            sys.exit(exit_status)

        if self._command_requires_hostlist:
            try:
                expanded_hostlist = self._expand_hostlist()
            except exceptions.ExpandingHostlistError as e:
                self._die(str(e))
        else:
            expanded_hostlist = list()

        self._config[self._command_executer_name] = self._update_config(self._command_executer_name,
                                                                        hostlist=expanded_hostlist,
                                                                        command=self._command,
                                                                        command_args=self._command_args,
                                                                        swk_dir=self._swk_dir,
                                                                        swk_path=self._swk_path,
                                                                        cwd=self._cwd,
                                                                        cache_directory=self._cache_directory_expanded)

        logging.info("Executing command with config: {0}".format(self._config[self._command_executer_name]))
        obj = self._command_executer_class(**self._config[self._command_executer_name])

        try:
            obj.run_command()
        except classes.SWKCommandError as e:
            self._die("Command class {0} died with message: {1}".format(self._command_executer_name, str(e)))
        logging.debug("swk finished")

