from pypsi.shell import Shell
from pypsi.core import Command
import sys
import logging
from swk import swk_classes
from swk import swk_exceptions
from pypsi.commands.exit import ExitCommand
from pypsi.commands.pwd import PwdCommand
from pypsi.commands.chdir import ChdirCommand
from pypsi.commands.system import SystemCommand
import os
from pypsi.plugins.history import HistoryCommand, HistoryPlugin
from pypsi.core import Plugin
from pypsi.cmdline import StringToken, WhitespaceToken, OperatorToken

class SWKShellCmdlinePP(Plugin):
    def __init__(self, preprocess=80, postprocess=None, **kwargs):
        super(SWKShellCmdlinePP, self).__init__(preprocess=preprocess,
                                               postprocess=postprocess, **kwargs)

    def setup(self, shell):
        pass

    def on_tokenize(self, shell, tokens, origin):
        if origin != 'input':
            return tokens

        result = []
        i = 0
        for (i, token) in enumerate(tokens):
            if isinstance(token, StringToken):
                if token.quote:
                    result.append(StringToken(i, "{quote}{s}{quote}".format(
                        quote=token.quote or '',
                        s=token.text.replace('\\', '\\\\\\')), quote=None))
                else:
                    result.append(StringToken(i, "{quote}{s}{quote}".format(
                        quote=token.quote or '',
                        s=token.text), quote=None))
            else:
                result.append(token)

        return result


help_command_name = 'help'
swk_shell_prompt = "swk> "


class SWKChdirCommand(ChdirCommand):
    def run(self, shell, args):
        super(SWKChdirCommand, self).run(shell, args)
        shell.prompt = swk_shell_prompt.format(os.getcwd())


class SWKCommand(Command):
    def __init__(self, command_name, command_help, command_module, swk_instance):
        super(SWKCommand, self).__init__(command_name, usage=command_help)
        self._command_name = command_name
        self._command_help = command_help
        self._command_module = self._command_executer_class = command_module
        self._command_executer_name = command_module.__name__
        self._hostlist = ""
        self._command_args = list()
        self._swk_instance = swk_instance
        self._expanded_hostlist = list()
        self._cwd = ""

    def _die(self, diemsg):
        logging.error(diemsg)
        sys.stderr.write(diemsg + '\n')

    def run(self, shell, args):
        #DEBUG PRINT
        #print(args)
        #self._hostlist = ""
        #self._command_args = list()
        #self._expanded_hostlist = list()

        self._cwd = os.getcwd()

        if self._command_module.requires_hostlist(self._command_name):
            try:
                self._hostlist = args[0]
            except IndexError:
                self._die("Hostlist is required for command {0}, but is not provided".format(self._command_name))
                return
            self._command_args = args[1:]

            self._swk_instance._hostlist = self._hostlist
            try:
                self._expanded_hostlist = self._swk_instance._expand_hostlist()
            except swk_classes.SWKParsingError as e:
                self._die("Parser error: {0}".format(str(e)))
                return
            except swk_exceptions.ExpandingHostlistError as e:
                self._die("Expanding hostlist expression error: {0}".format(str(e)))

        else:
            self._command_args = args

        self._swk_instance._config[self._command_executer_name] = \
            self._swk_instance._update_config(self._command_executer_name,
                                             hostlist=self._expanded_hostlist,
                                             command=self._command_name,
                                             command_args=self._command_args,
                                             swk_dir=self._swk_instance._swk_dir,
                                             swk_path=self._swk_instance._swk_path,
                                             cwd=self._cwd,
                                             cache_folder=self._swk_instance._cache_folder_expanded)

        logging.info("Executing command with config: {0}".format(self._swk_instance._config[self._command_executer_name]))
        obj = self._command_executer_class(**self._swk_instance._config[self._command_executer_name])
        try:
            obj.run_command()
        except swk_classes.SWKCommandError as e:
            self._die("Command error: {0}".format(str(e)))


class SWKShell(Shell):
    exit_cmd = ExitCommand()
    pwd_cmd = PwdCommand()
    cd_cmd = SWKChdirCommand()
    system_cmd = SystemCommand(name='sys')
    swk_shell_preprocessor_plugin = SWKShellCmdlinePP()
    help_forward_dict = {'exit': exit_cmd, 'pwd': pwd_cmd, 'sys': system_cmd, 'cd': cd_cmd}
    history_plugin = HistoryPlugin()
    history_command = HistoryCommand()

    def __init__(self, swk_instance):
        try:
            _, columns = os.popen('stty size 2>/dev/null', 'r').read().split()
        except ValueError:  # we're not running in a terminal
            columns = 80
        super(SWKShell, self).__init__(shell_name='swk', width=int(columns))
        self.prompt = swk_shell_prompt.format(os.getcwd())


class SWKShellPrepare:
    def __init__(self, swk_instance):
        for command_name, command_module in swk_instance._available_commands.items():
            setattr(SWKShell, command_name, SWKCommand(command_name, 'no help yet', command_module, swk_instance))
        setattr(SWKShell, help_command_name, SWKShellHelp(swk_instance))


class SWKShellHelp(Command):
    def __init__(self, swk_instance):
        super(SWKShellHelp, self).__init__(help_command_name)
        self._commands_help_message = swk_instance._commands_help_message
        self._parsers_help_message = swk_instance._parsers_help_message
        self._swk_instance = swk_instance

    def run(self, shell, args):
        builtin_commands_string = ""
        for builtin_command in sorted(shell.help_forward_dict.keys()):
            builtin_commands_string += builtin_command + ', '
        builtin_commands_string = builtin_commands_string[:-2]
        if len(args) == 0:
            sys.stdout.write("{0}{1}".format(self._commands_help_message, self._parsers_help_message))
            sys.stdout.write("\nBuilt-in commands available: {0}\n".format(builtin_commands_string))
            sys.stdout.write("\nFor verbose help, please run 'help <command_name>' or 'help <parser_modifier>'\n")
            return
        help_topic_name = args[0]
        if help_topic_name in shell.help_forward_dict.keys():
            sys.stdout.write("{0}\n".format(shell.help_forward_dict[help_topic_name].brief))
            return
        try:
            sys.stdout.write(self._swk_instance._available_commands[help_topic_name].get_command_help(help_topic_name))
        except KeyError:
            try:
                sys.stdout.write(self._swk_instance._available_parsers[help_topic_name].get_parser_help(help_topic_name))
            except KeyError:
                sys.stderr.write("Sorry, no help on this topic\n")


