# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import sys
import platform

from .completion import get_completion_args
from .log import CLILogging, get_logger
from .util import CLIError
from .config import CLIConfig

logger = get_logger(__name__)


def _default_exception_handler(ex):
    logger.exception(ex)
    return 1


class CLIContext(object):

    def __init__(self):
        self.config = None


class CLIApp(object):  # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 app_name,
                 config_name,
                 out_file=sys.stdout,
                 on_pre_execute=None,
                 on_post_execute=None,
                 on_execute_exception=None,
                 on_get_version=None):
        self.app_name = app_name
        self.on_pre_execute = on_pre_execute or (lambda _: None)
        self.on_post_execute = on_post_execute or (lambda _: None)
        self.on_execute_exception = on_execute_exception or _default_exception_handler
        self.on_get_version = on_get_version or (lambda: None)
        self.out_file = out_file
        self.ctx = CLIContext()
        self.config = CLIConfig(config_name)
        self.ctx.config = self.config
        self.logging = CLILogging(self.app_name, ctx=self.ctx)

    def _execute(self, args):  # pylint: disable=no-self-use
        print(args)
        # APPLICATION.initialize(Configuration())
        # cmd_result = APPLICATION.execute(args)
        # if cmd_result and cmd_result.result is not None:
        #     from azure.cli.core._output import OutputProducer
        #     formatter = OutputProducer.get_formatter(APPLICATION.configuration.output_format)
        #     OutputProducer(formatter=formatter, file=file).out(cmd_result)

    @staticmethod
    def _should_show_version(args):
        return args and (args[0] == '--version' or args[0] == '-v')

    def _show_version_info(self):
        version_info = self.on_get_version() or ''
        version_info += '\n\n'
        version_info += 'Python ({}) {}'.format(platform.system(), sys.version)
        version_info += '\n\n'
        version_info += 'Python location \'{}\''.format(sys.executable)
        version_info += '\n'
        print(version_info, file=self.out_file)

    @staticmethod
    def _remove_logger_flags(args):
        return [x for x in args if x not in (CLILogging.VERBOSE_FLAG, CLILogging.DEBUG_FLAG)]

    def run(self, args):
        """ Run the CLI and return the exit code """
        try:

            args = get_completion_args() or args

            self.logging.configure(args)
            args = CLIApp._remove_logger_flags(args)
            logger.debug('Command arguments %s', args)

            # TODO Add telemetry support
            self.on_pre_execute(self.ctx)
            if CLIApp._should_show_version(args):
                self._show_version_info()
            else:
                self._execute(args)
            self.on_post_execute(self.ctx)
            exit_code = 0
        except CLIError as ex:
            logger.error(ex)
            exit_code = 1
        except KeyboardInterrupt:
            exit_code = 1
        except Exception as ex:  # pylint: disable=broad-except
            exit_code = self.on_execute_exception(ex)
        finally:
            pass
        return exit_code
