"""
sk - A tiny extendable utility for running commands against multiple hosts.

Copyright (C) 2016  Pavel "trueneu" Gurkov

see sk for more information on License and contacts
"""

import logging
import os
import glob
import sk_classes
import inspect
import sk_exceptions
import argparse
import configparser
import sys
import exrex

shell_mode_off = False
try:
    import sk_shell
except SyntaxError:
    shell_mode_off = True

class SwissKnife(object):
    _version = "0.03a"

    _environment = "testing"
    _sk_modules_dir = "sk-modules"

    if _environment == "production":
        _sk_config_path = "sk.ini"
    elif _environment == "testing":
        _sk_config_path = "sk-private.ini"

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, "_{0}".format(k), v)

        self._config = self._read_config()
        self._logging_init()

        self._cache_folder_expanded = os.path.abspath(os.path.expanduser(self._config["Main"].pop("cache_folder",
                                                                                                  "~/.sk")))
        self._cache_folder_init()

        self._plugin_modules, self._plugin_command_modules, self._plugin_parser_modules = self._modules_import()
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
        loglevel_string = self._config["Main"].pop("loglevel", "warning")
        try:
            loglevel = {"debug": logging.DEBUG,
                        "info": logging.INFO,
                        "warning": logging.WARNING,
                        "error": logging.ERROR,
                        "critical": logging.CRITICAL}[loglevel_string]
        except KeyError:
            loglevel = logging.INFO
        if loglevel == logging.DEBUG:
            self._dbg_prints = True
        else:
            self._dbg_prints = False
        logfile = self._config["Main"].pop("logfile", "sk.log")
        logging.basicConfig(filename=logfile, filemode='a', level=loglevel,
                            format='[%(asctime)s] %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.debug("sk started")

    def _cache_folder_init(self):
        if not os.path.exists(self._cache_folder_expanded):
            try:
                os.mkdir(self._cache_folder_expanded)
            except OSError:
                self._die("Couldn't create folder {0}. Check permissions".format(self._cache_folder_expanded))


    @staticmethod
    def _die(diemsg):
        logging.error(diemsg)
        sys.stderr.write(diemsg + '\n')
        logging.debug("sk died")
        exit(2)

    def _modules_import(self):

        module_filenames = list()
        plugin_modules = list()
        plugin_command_modules = list()
        plugin_parser_modules = list()
        try:
            os.chdir("{0}/{1}".format(self._sk_dir, self._sk_modules_dir))
            module_filenames = glob.glob("*.py")
        except OSError:
            self._die("{0} does not exist.".format(self._sk_modules_dir))

        """import all the plugin modules and put them into list"""

        for module_filename in module_filenames:
            module_name, _, _ = module_filename.rpartition('.py')
            module_full_name = "{0}.{1}".format(self._sk_modules_dir, module_name)
            try:
                module = __import__(module_full_name, fromlist=[self._sk_modules_dir])
            except ImportError as e:
                self._die("Couldn't import module {0}: {1}.".format(module_full_name, str(e)))
            plugin_modules.extend([(name, obj) for (name, obj) in inspect.getmembers(module)
                                   if inspect.isclass(obj) and issubclass(obj, sk_classes.SKPlugin)])

        """then sort them into command modules and parser modules"""
        plugin_command_modules.extend([(name, obj) for (name, obj) in plugin_modules
                                       if issubclass(obj, sk_classes.SKCommandPlugin)])
        plugin_parser_modules.extend([(name, obj) for (name, obj) in plugin_modules
                                      if issubclass(obj, sk_classes.SKParserPlugin)])

        logging.debug("Imported modules")
        logging.debug("All modules: {0}".format(plugin_modules))
        logging.debug("Command modules: {0}".format(plugin_command_modules))
        logging.debug("Parser modules: {0}".format(plugin_parser_modules))
        return plugin_modules, plugin_command_modules, plugin_parser_modules

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

#        #DEBUG PRINT
#        print(result['command_args'])

        return result

    def _read_config(self):
        result = dict()

        os.chdir(self._sk_dir)
        config = configparser.ConfigParser()
        config.read(self._sk_config_path)

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

    def _expand_hostlist(self):
        expanded_hostlist = list()  # expanded

        #if self._hostlist[0] == "'" and self._hostlist[:-1] == "'":
        #    self._hostlist = self._hostlist[1:-1]

        # yeah, maybe we'll need that dirty hack in the future

        hostgroups = self._hostlist.split(',')
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
                if not hostgroup_modifier.isalpha():
                    self._die("Couldn't find corresponding parser for {0} modifier.".format(hostgroup_modifier))
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
                        self._die("Parser {0} didn't return any hosts for hostgroup {1}".format(
                            parser.__name__, hostgroup_remainder
                        ))
                except sk_classes.SKParsingError as e:
                    self._die("Parser {0} died with message: {1}".format(parser.__name__, str(e)))

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
            sk_shell.SKShellPrepare(self)
            shell = sk_shell.SKShell(self)
            exit_status = shell.cmdloop()
            sys.exit(exit_status)

        if self._command_requires_hostlist:
            expanded_hostlist = self._expand_hostlist()
        else:
            expanded_hostlist = list()

        self._config[self._command_executer_name] = self._update_config(self._command_executer_name,
                                                                        hostlist=expanded_hostlist,
                                                                        command=self._command,
                                                                        command_args=self._command_args,
                                                                        sk_dir=self._sk_dir,
                                                                        sk_path=self._sk_path,
                                                                        cwd=self._cwd,
                                                                        cache_folder=self._cache_folder_expanded)

        logging.info("Executing command with config: {0}".format(self._config[self._command_executer_name]))
        obj = self._command_executer_class(**self._config[self._command_executer_name])

        try:
            obj.run_command()
        except sk_classes.SKCommandError as e:
            self._die("Command class {0} died with message: {1}".format(self._command_executer_name, str(e)))
        logging.debug("sk finished")

