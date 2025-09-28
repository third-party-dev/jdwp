import asyncio
import code
import io
import contextlib
import os
import importlib
import sys

# HOST = "127.0.0.1"
# PORT = 9999
# SOCKET_PATH = "/tmp/repl.sock"

# class __sandbox__():

MODULE_REFS = []


'''
import asyncio
from thirdparty.sandbox import start_socket_client
if __name__ == "__main__":
    try:
        asyncio.run(start_socket_client())
    except KeyboardInterrupt:
        print("\nClient exiting")
'''
async def start_socket_client(socket_path: str=None, host: str=None, port: int=None):
    try:
        reader = None
        writer = None
        if socket_path:
            reader, writer = await asyncio.open_unix_connection(socket_path)
        else:
            reader, writer = await asyncio.open_connection(host, port)
        
        print(f"Connected to {host}:{port}")

        async def read_from_server():
            while True:
                data = await reader.read(1024)
                if not data:
                    print("Server closed connection")
                    break
                sys.stdout.write(data.decode())
                sys.stdout.flush()

        async def write_to_server():
            loop = asyncio.get_event_loop()
            while True:
                # Read user input asynchronously
                line = await loop.run_in_executor(None, input)
                writer.write((line + '\r\n').encode())
                await writer.drain()

        # Run reading and writing concurrently
        await asyncio.gather(read_from_server(), write_to_server())
    except ConnectionResetError:
        print("\nClient disconnected")
        pass


async def handle_repl_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, namespace):
    try:
        console = code.InteractiveConsole(namespace)
        addr = writer.get_extra_info("peername") or "unix-client"
        print(f"Client connected: {addr}")

        writer.write(b"Welcome to the asyncio Python console!\r\nType Python code.\r\n>>> ")
        await writer.drain()

        while True:
            line_bytes = await reader.readline()
            if not line_bytes:
                break  # client disconnected
            line = line_bytes.decode()

            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                more = console.push(line)

            captured = output.getvalue()
            if captured:
                writer.write(captured.encode())

            prompt = b"... " if more else b">>> "
            writer.write(prompt)
            await writer.drain()

        print(f"Client disconnected: {addr}")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Exception: {e}")


'''
import asyncio
import thirdparty.sandbox as __sandbox__
if __name__ == "__main__":
    try:
        asyncio.run(__sandbox__.start_repl_server())
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except SystemExit as e:
        print(f"Exception: {e}")
'''
async def start_repl_server(socket_path: str=None, host: str=None, port: int=None, namespace={}):
    try:
        async def handle_repl_client_wrapper(reader, writer):
            await handle_repl_client(reader, writer, namespace)

        server = None
        if socket_path:
            if os.path.exists(socket_path):
                os.remove(socket_path)
            server = await asyncio.start_unix_server(handle_repl_client_wrapper, path=socket_path)
        else:
            server = await asyncio.start_server(handle_repl_client_wrapper, host, port)

        addr = server.sockets[0].getsockname()
        print(f"Asyncio Python console listening on {addr}")

        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Exception: {e}")


'''
import asyncio
import thirdparty.sandbox as __sandbox__
import mymodule
if __name__ == "__main__":
    __sandbox__.hot_reload_module(mymodule)
    asyncio.run(__sandbox__.handle_hot_reload())
'''
async def handle_hot_reload(module_refs = MODULE_REFS):
    module_mtimes = {}
    #last_mtime = os.path.getmtime("mymodule.py")
    try:
        while True:
            await asyncio.sleep(1)
            for mod in module_refs:
                if mod not in module_mtimes:
                    module_mtimes[mod] = os.path.getmtime(mod.__file__)

                cur_mtime = os.path.getmtime(mod.__file__)
                if cur_mtime != module_mtimes[mod]:
                    importlib.reload(mod)
                    print("Module reloaded!")
                    module_mtimes[mod] = cur_mtime
    except asyncio.CancelledError:
        print("Hot reload loop stopped")


def hot_reload_module(module_ref):
    if module_ref not in MODULE_REFS:
        MODULE_REFS.append(module_ref)


'''
import asyncio
import thirdparty.sandbox as __sandbox__

async def main_with_sandbox():
    # This is where we call the actual main.
    app = asyncio.create_task(main())

    sandbox = asyncio.create_task(__sandbox__.start_repl_server(socket_path="/tmp/repl.sock"))
    await asyncio.gather(app, sandbox)

if __name__ == "__main__":
    asyncio.run(main_with_sandbox())
'''
async def start_sandbox(
        repl_socket_path: str=None,
        repl_host: str=None,
        repl_port: int=None,
        repl_namespace={}):
    repl_server_coro = start_repl_server(
        socket_path=repl_socket_path,
        host=repl_host,
        port=repl_port,
        namespace=repl_namespace)
    repl_server_task = asyncio.create_task(repl_server_coro)
    hot_reload_task = asyncio.create_task(handle_hot_reload())
    await asyncio.gather(repl_server_task, hot_reload_task)
         

# if __name__ == "__main__":
#     try:
#         asyncio.run(__sandbox__.start())
#     except KeyboardInterrupt:
#         print("\nServer shutting down...")
#     except SystemExit as e:
#         print(f"Exception: {e}")
