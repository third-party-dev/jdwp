'''
Copyright (c) 2025 Vincent Agriesti

This file is part of the thirdparty JDWP project.
Licensed under the MIT License. See the LICENSE file in the project root
for full license text.
'''

import argparse

import asyncio
import aiofiles
from ppadb.client import Client as AdbClient


class AdbCommand():

    def __init__(self, cmd_input):
        self.cmd_input = cmd_input
        self.app = cmd_input.app
        self.argparser = argparse.ArgumentParser(prog='adb')
        self.argparser.set_defaults(func=lambda *args, **kwargs: 'Nothing to do.')
        subparsers = self.argparser.add_subparsers(help='subcommand help')
        adb_debug = subparsers.add_parser('debug')
        adb_debug.add_argument('package_name')
        adb_debug.set_defaults(func=self.do_debug)

        # Hard coding for now.
        self.client = AdbClient(host="127.0.0.1", port=5037)
        self.device = self.client.device("emulator-5554")

    def handle(self, argv):
        if '--help' in argv:
            return self.argparser.format_help()

        try:
            args = self.argparser.parse_args(argv[1:])
        except argparse.ArgumentError:
            pass
        except SystemExit:
            return self.argparser.format_help()
            
        return args.func(args)


    def do_debug(self, args):
        self.cmd_input.cmd_log(f"Setting up debug session for: {args.package_name}")

        self.cmd_input.cmd_log(f"adb shell am set-debug-app -w {args.package_name}")
        self.device.shell(f"am set-debug-app -w {args.package_name}")

        self.cmd_input.cmd_log(f"adb shell cmd package resolve-activity -c android.intent.category.LAUNCHER {args.package_name}")
        main_act = None
        for raw_line in self.device.shell(f"cmd package resolve-activity -c android.intent.category.LAUNCHER {args.package_name}").split('\n'):
            line = raw_line.strip()
            if line.startswith("name="):
                main_act = line.split('=', 1)[1].replace(args.package_name, '')
                break

        self.cmd_input.cmd_log(f"adb shell am start -n {args.package_name}/{main_act}")
        self.device.shell(f"am start -n {args.package_name}/{main_act}")

        results = []
        proc_list = self.device.shell("ps -A")
        for line in proc_list.split('\n'):
            if args.package_name in line:
                results.append(line)
        
        if len(results) == 1:
            # Lets try to attach to it.
            pid = results[0].split()[1]
            self.cmd_input.cmd_log(f"adb forward tcp:8700 jdwp:{pid}")
            self.device.forward('tcp:8700', f'jdwp:{pid}')

        return 'Done.'
