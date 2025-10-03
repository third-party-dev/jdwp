import asyncio
from thirdparty.sandbox import start_raw_tty_repl_client

if __name__ == "__main__":
    try:
        asyncio.run(start_raw_tty_repl_client(socket_path="/tmp/repl.sock"))
    except KeyboardInterrupt:
        print("\nClient exiting")