import asyncio
from thirdparty.sandbox import exec_file

if __name__ == "__main__":
    try:
        asyncio.run(exec_file(socket_path="/tmp/exec.sock", fpath="exec_test.py", wait_timeout=2))
    except KeyboardInterrupt:
        print("\nClient exiting")
    