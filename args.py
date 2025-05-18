"""Argument management module."""

import argparse

from build_info import BuildInfo

_parser = argparse.ArgumentParser(description='NeoXtractor')

_parser.add_argument('--version', '-v',
                     action='version',
                     version=f'{BuildInfo.version if BuildInfo.version else "development"} (Build: {BuildInfo.commit_hash[:7] if BuildInfo.commit_hash else "unknown"})')
_parser.add_argument('--log-level',
                  help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL or integer values)',
                  dest='log_level')

_subparsers = _parser.add_subparsers(help="subcommand help", dest="subcommand")

_gui_parser = _subparsers.add_parser('gui', help='Run the NeoXtractor GUI')

arguments = _parser.parse_args()
