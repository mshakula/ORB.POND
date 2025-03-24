"""Common configuration support file for stderr logging.
"""

import sys
import logging
import functools
import re
import argparse

from typing import *


def common_logger_config(
    silent: bool = False,
    debug: bool = False,
    module_regex: List[str] = [],
    module_regex_n: List[str] = [],
    message_regex: List[str] = [],
    message_regex_n: List[str] = []
) -> None:
    """Configure the basic logger to output nicely to stdout.

    :param silent: Suppress all non-error output. Overrides debug.
    :param debug: Output extra debug information.
    :param message_regex: List of regex to filter stderr logs by message.
    :param message_regex_n: List of negative regex to filter stderr logs by message.
    :param module_regex: List of regex to filter stderr logs by module.
    :param module_regex_n: List of negative regex to filter stderr logs by module.
    """

    class DefaultFormatter(logging.Formatter):
        """Handle the default output formatting."""

        _FORMAT = "%(relativeCreated)dms - %(name)s - %(levelname)s - (%(filename)s:%(lineno)d) %(message)s"

        @classmethod
        def format(cls, record: Any) -> str:
            return logging.Formatter(cls._FORMAT).format(record)

    class ColoredFormatter(DefaultFormatter):
        """From https://stackoverflow.com/a/56944256 and https://stackoverflow.com/a/33206814"""

        _COLORS = {
            logging.DEBUG: "\x1b[2;39m",  # light default
            logging.INFO: "\x1b[0;39m",  # default
            logging.WARNING: "\x1b[0;33m",  # yellow
            logging.ERROR: "\x1b[0;31m",  # red
            logging.CRITICAL: "\x1b[1;31m",  # bold red
        }
        _RESET = "\x1b[0;39m"

        @classmethod
        def format(cls, record: Any) -> str:
            return "{}{}{}".format(
                cls._COLORS.get(record.levelno),
                super(ColoredFormatter, cls).format(record),
                cls._RESET)

    stderr_handler = logging.StreamHandler(sys.stderr)
    if silent:
        stderr_handler.setLevel(logging.ERROR)
    elif debug:
        stderr_handler.setLevel(logging.DEBUG)
    else:
        stderr_handler.setLevel(logging.INFO)
    if sys.stderr.isatty():
        stderr_handler.setFormatter(ColoredFormatter)
    else:
        stderr_handler.setFormatter(DefaultFormatter)

    filter_set = []
    for r in module_regex:
        filter_set.append(functools.partial(
            lambda x, r: re.match(r, x.name),
            r=r))
    for r in module_regex_n:
        filter_set.append(functools.partial(
            lambda x, r: not re.match(r, x.name),
            r=r))
    for r in message_regex:
        filter_set.append(functools.partial(
            lambda x, r: re.match(r, x.getMessage()),
            r=r))
    for r in message_regex_n:
        filter_set.append(functools.partial(
            lambda x, r: not re.match(r, x.getMessage()),
            r=r))
    stderr_handler.addFilter(lambda x: all(f(x) for f in filter_set))

    logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger().addHandler(stderr_handler)
    logging.getLogger().info("Logging configured")


def set_argparse_common_log_options(parser: argparse.ArgumentParser) -> None:
    """Add common options to the argument parser that will get all parameters necessary for the common logger config.
    """

    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help="enable debug logging")
    parser.add_argument(
        '-s',
        '--silent',
        action='store_true',
        help="disable non-error logging")
    parser.add_argument(
        '-I',
        '--log-exclude',
        action='append',
        type=str,
        help="negative regex used to filter stderr log by name.")
    parser.add_argument(
        '-N',
        '--message-exclude',
        action='append',
        type=str,
        help="negative regex used to filter stderr log by message.")
    parser.add_argument(
        '-L',
        '--log-include',
        action='append',
        type=str,
        help="positive regex used to filter stderr log by name.")
    parser.add_argument(
        '-R',
        '--message-include',
        action='append',
        type=str,
        help="positive regex used to filter stderr log by message.")
    return parser


def common_logger_config_args(args: argparse.Namespace) -> None:
    """Call the common logger config with an argument namespace that was created with the common logger argparse options.
    """

    assert isinstance(args.silent, bool)
    assert isinstance(args.debug, bool)
    assert not args.log_include or isinstance(args.log_include, list)
    assert not args.log_exclude or isinstance(args.log_exclude, list)
    assert not args.message_include or isinstance(args.message_include, list)
    assert not args.message_exclude or isinstance(args.message_exclude, list)

    common_logger_config(
        silent=args.silent,
        debug=args.debug,
        module_regex=args.log_include or [],
        module_regex_n=args.log_exclude or [],
        message_regex=args.message_include or [],
        message_regex_n=args.message_exclude or [])
