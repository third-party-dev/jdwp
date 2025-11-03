from ppadb.client import Client as AdbClient

class AdbObject():
    
    def target(self, tgt_pkg, device_name='emulator-5554'):
        self.tgt_pkg = tgt_pkg
        self.client = AdbClient(host="127.0.0.1", port=5037)
        # Connection sanity.
        print(f'ADB Client Version: {self.client.version()}')
        self.device = self.client.device(device_name)

        # Configure the tgt_pkg to wait for debugger on start.
        cmd = f'am set-debug-app -w {self.tgt_pkg}'
        print(cmd)
        print(self.device.shell(cmd))

        # Get the main activity name. (Note: This is a bit wonky.)
        cmd = f'cmd package resolve-activity -c android.intent.category.LAUNCHER {self.tgt_pkg}'
        print(cmd)
        pkg_act_info = self.device.shell(cmd)

        import re
        # Get text following "name=" until end of line.
        pattern = re.compile(r'(?<=name=)\S+')
        matches = []
        for line in pkg_act_info.split('\n'):
            found = pattern.findall(line)
            matches.extend(found)
        #print(matches)
        
        pkg_main_act = matches[0].replace(self.tgt_pkg, f'{self.tgt_pkg}/')
        print(pkg_main_act)

        # Start the tgt_pkg's main activity.
        cmd = f'am start -n {pkg_main_act}'
        print(cmd)
        self.device.shell(cmd)

        import time
        time.sleep(0.5)

        # Get the process id (PID) of the running tgt_pkg.
        adb_procs = self.device.shell(f'ps -A')
        self.proc_pid = None
        for proc in adb_procs.split('\n'):
            if proc.find(self.tgt_pkg) < 0:
                continue
            self.proc_pid = int(proc.split()[1])
            break
        if not self.proc_pid:
            print("Target process not found.")
            exit(1)
        
        # Port forward internal JDWP port (same as PID) to localhost:8700
        cmd = f'adb forward tcp:8700 jdwp:{self.proc_pid}'
        print(cmd)
        self.device.forward('tcp:8700', f'jdwp:{self.proc_pid}')

        time.sleep(3)