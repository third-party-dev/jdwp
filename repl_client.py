import asyncio
from thirdparty.sandbox import start_socket_client

if __name__ == "__main__":
    try:
        asyncio.run(start_socket_client(socket_path="/tmp/repl.sock"))
    except KeyboardInterrupt:
        print("\nClient exiting")