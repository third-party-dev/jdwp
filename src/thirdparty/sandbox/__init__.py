import asyncio
import code
import io
import contextlib
import os
import importlib
import sys
import struct
from multiprocessing.managers import BaseManager

# HOST = "127.0.0.1"
# PORT = 9999
# SOCKET_PATH = "/tmp/repl.sock"

# class __sandbox__():

MODULE_REFS = []

class DictManager(BaseManager):
    pass

'''
    import asyncio
    from thirdparty.sandbox import start_dict_server

    # Only required for assignment.
    import multiprocessing
    shared_dict = multiprocessing.Manager().dict()
    shared_dict['thing'] = 'value'
    # Read-only version can be:
    # shared_dict = {}

    if __name__ == "__main__":
        try:
            asyncio.run(start_dict_server(socket_path="/tmp/dict.sock", shared_dict=shared_dict))
        except KeyboardInterrupt:
            print("\nClient exiting")
'''
async def start_dict_server(
        socket_path: str=None,
        host: str=None,
        port: int=None,
        authkey=b'secret',
        shared_dict: dict={}):

    print(shared_dict)
    DictManager.register('get_dict', callable=lambda: shared_dict,
        exposed=['__getitem__', '__setitem__', '__delitem__', 'keys', 'items', 'values', 'get'])

    manager = None
    if socket_path:
        manager = DictManager(address=socket_path, authkey=authkey)
    else:
        manager = DictManager(address=(host, port), authkey=authkey)

    loop = asyncio.get_running_loop()
    server = manager.get_server()
    print(f"Asyncio Python dict listening")
    await loop.run_in_executor(None, server.serve_forever)


'''
    from thirdparty.sandbox import start_dict_client

    shared_dict = start_dict_client(socket_path="/tmp/dict.sock")
    shared_dict['value'] = 2345
    print(str(shared_dict))
'''
def start_dict_client(socket_path: str=None, host: str=None, port: int=None, authkey=b'secret'):

    DictManager.register('get_dict')

    manager = None
    if socket_path:
        manager = DictManager(address=socket_path, authkey=authkey)
    else:
        manager = DictManager(address=(host, port), authkey=authkey)
    manager.connect()

    return manager.get_dict()


'''
    import asyncio
    from thirdparty.sandbox import start_socket_client

    if __name__ == "__main__":
        try:
            asyncio.run(start_socket_client(socket_path="/tmp/repl.sock"))
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
            asyncio.run(__sandbox__.start_repl_server(socket_path="/tmp/repl.sock", namespace=globals()))
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
        print(f"Asyncio Python repl listening on {addr}")

        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Exception: {e}")


'''
    import asyncio
    import thirdparty.sandbox as __sandbox__
    import thirdparty.sandbox.mymodule as mymodule
    if __name__ == "__main__":
        __sandbox__.hot_reload_module(mymodule)
        asyncio.run(__sandbox__.handle_hot_reload())
'''
async def handle_hot_reload(module_refs = MODULE_REFS):
    module_mtimes = {}
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


async def handle_exec_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, namespace):
    addr = writer.get_extra_info("peername") or "unix-client"
    print(f"Exec client connected: {addr}")

    try:
        while True:
            # Note: first 4 bytes are the length.
            resp = await reader.readexactly(4)
            res = struct.unpack(">I", resp)
            data_length = res[0]
            if data_length == 0:
                break

            data = await reader.readexactly(data_length)
            exec_data = data.decode()
            try:
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    exec(exec_data, globals=namespace)

                captured = output.getvalue().encode()
                if captured:
                    packet = struct.pack(">I", len(captured)) + captured
                    print(packet)
                    writer.write(packet)

            except Exception as e:
                msg = f"EXEC ERROR: {e}\n".encode()
                packet = struct.pack(">I", len(msg)) + msg
                print(packet)
                writer.write(packet)
            
            finally:
                await writer.drain()

    except asyncio.exceptions.IncompleteReadError:
        print(f"Nothing left to read on socket: {addr}")

    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Client disconnected: {addr}")


'''
    import asyncio
    import thirdparty.sandbox as __sandbox__
    if __name__ == "__main__":
        try:
            asyncio.run(__sandbox__.start_exec_server(socket_path="/tmp/exec.sock", namespace=globals()))
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        except SystemExit as e:
            print(f"Exception: {e}")
'''
async def start_exec_server(socket_path: str=None, host: str=None, port: int=None, namespace={}):
    try:
        async def handle_exec_client_wrapper(reader, writer):
            await handle_exec_client(reader, writer, namespace)

        server = None
        if socket_path:
            if os.path.exists(socket_path):
                os.remove(socket_path)
            server = await asyncio.start_unix_server(handle_exec_client_wrapper, path=socket_path)
        else:
            server = await asyncio.start_server(handle_exec_client_wrapper, host, port)

        addr = server.sockets[0].getsockname()
        print(f"Asyncio Python exec listening on {addr}")

        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Exception: {e}")


'''
    exec_test.py:

        ```python
        def exec_test_func():
            print("This is the exec test function")

        print("OK")
        ```

    exec_client.py:

        ```python
        import asyncio
        from thirdparty.sandbox import exec_file

        if __name__ == "__main__":
            try:
                asyncio.run(exec_file(socket_path="/tmp/exec.sock", fpath="exec_test.py", wait_timeout=2))
            except KeyboardInterrupt:
                print("\nClient exiting")
        ```
'''
async def exec_file(
        socket_path: str=None,
        host: str=None,
        port: int=None,
        fpath: str=None,
        wait_timeout: int=0,
        # TODO: Consider some kind of conditional instead of wait_timeout.
        ):

    reader = None
    writer = None
    if socket_path:
        try:    
            reader, writer = await asyncio.open_unix_connection(socket_path)
            print(f"Connected to exec server at {socket_path}")
        except FileNotFoundError:
            print(f"Unable to connect to socket path: {socket_path}")
            return
    else:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            print(f"Connected to exec server at {host}:{port}")
        except FileNotFoundError:
            print(f"Unable to connect to: {host}:{port}")
            return


    async def read_from_server():
        while True:
            data = await reader.read(1024)
            if not data:
                print("Server closed connection")
                break
            sys.stdout.write(data.decode())
            sys.stdout.flush()

    async def do_wait_timeout():
        if wait_timeout > 0:
            await asyncio.sleep(wait_timeout)
            exit(0)
        elif wait_timeout == 0:
            exit(0)
        else:
            while True:
                await asyncio.sleep(0xFFFF)

    try:    
        with open(fpath, "r") as f:
            # Read the code
            file_data = f.read()
            
            # Write the packet
            # Note: first 4 bytes are the length.
            packet = struct.pack(">I", len(file_data)) + file_data.encode()
            writer.write(packet)
            await writer.drain()

            # Wait for a response or timeout.
            await asyncio.gather(read_from_server(), do_wait_timeout())

    except ConnectionResetError:
        print("\nClient disconnected")
        pass

    except SystemExit:
        print("\nClient disconnected")


'''
    import asyncio
    import thirdparty.sandbox as __sandbox__

    # Only required for assignment.
    import multiprocessing
    shared_dict = multiprocessing.Manager().dict()
    shared_dict['thing'] = 'value'
    # Read-only version can be:
    # shared_dict = {}

    async def main_with_sandbox():
        # Note: Need to send the globals() from this scope or we get the module's globals().
        sandbox_coro = __sandbox__.start_sandbox(
            repl_socket_path="/tmp/repl.sock", repl_namespace=globals(),
            exec_socket_path="/tmp/exec.sock", exec_namespace=globals(),
            dict_socket_path="/tmp/dict.sock", dict_shared_dict=shared_dict,
        )
        sandbox_task = asyncio.create_task(sandbox_coro)
        await asyncio.gather(sandbox_task)

    if __name__ == "__main__":
        asyncio.run(main_with_sandbox())
'''
async def start_sandbox(
        repl_socket_path: str=None,
        repl_host: str=None,
        repl_port: int=None,
        repl_namespace={},
        exec_socket_path: str=None,
        exec_host: str=None,
        exec_port: int=None,
        exec_namespace={},
        dict_socket_path: str=None,
        dict_host: str=None,
        dict_port: int=None,
        dict_authkey: str=b'secret',
        dict_shared_dict: dict={},
    ):
    
    if repl_socket_path or repl_host:
        repl_server_coro = start_repl_server(
            socket_path=repl_socket_path,
            host=repl_host,
            port=repl_port,
            namespace=repl_namespace)
        repl_server_task = asyncio.create_task(repl_server_coro)

    if exec_socket_path or exec_host:
        exec_server_coro = start_exec_server(
            socket_path=exec_socket_path,
            host=exec_host,
            port=exec_port,
            namespace=exec_namespace)
        exec_server_task = asyncio.create_task(exec_server_coro)

    if dict_socket_path or dict_host:
        dict_server_coro = start_dict_server(
            socket_path=dict_socket_path,
            host=dict_host,
            port=dict_port,
            authkey=dict_authkey,
            shared_dict=dict_shared_dict)
        dict_server_task = asyncio.create_task(dict_server_coro)

    hot_reload_task = asyncio.create_task(handle_hot_reload())
    
    await asyncio.gather(repl_server_task, exec_server_task, hot_reload_task)
         

# if __name__ == "__main__":
#     try:
#         asyncio.run(__sandbox__.start())
#     except KeyboardInterrupt:
#         print("\nServer shutting down...")
#     except SystemExit as e:
#         print(f"Exception: {e}")
