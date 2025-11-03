
'''
Copyright (c) 2025 Vincent Agriesti

This file is part of the thirdparty JDWP project.
Licensed under the MIT License. See the LICENSE file in the project root
for full license text.
'''

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


class ExitReplException(Exception):
    pass

'''
This has become kind of a get nothing day. To start, I was really hoping
to find a clean way to use await from pdb to make my life simple. This
ended up not being the case.

In short, python runs a main thread when you fire it up. If you chose to
do something like asyncio.run(main()), it starts an event loop in that
thread. If any one of the coroutines or tasks in the event loop use a
blocking API (input, read, etc), it'll block the whole loop from running.

This creates a very tricky situation for REPLs like code.interact() and
pdb.set_trace(). Both of these interfaces use some blocking API like
sys.stdin.read(). This means that even if you are able to successfully
schedule a task to run in the event loop of the local thread, it wont
actually get to execute because the REPL itself will be blocking the event
loop from running.

One nasty solution is to implement our own CLI handling. In our handler,
we use select to check if there is data to read from STDIN file descriptor.
If there is data, we can read that data from the FD. Note: The FD, for
weird reasons should also be non-blocking. You can than capture the data
1 read at a time and then break out of your read loop when there is no more
data. When select() returns nothing to read, you should:
await asyncio.sleep(0) to keep the event loop executing. Without this you'll
never see anything from the server.

Note: prompt-toolkit doesn't seem to be able to do the above process. The
reason its important is because we need to detect paste events int the
terminal and split it based on line. The issue is that we currenly depend
on the server's code.interact() to determine if the next line is a >>>
or a '...'. This means that to cleanly implement this interface, we'll
need to do more of a linear command and response instead of the async
read and write from/to the server the whole team. The impact of this is
that we'll not get things that have happened on the server, but it also
fixes the issue where we'd get a mixed up set of characters on the screen
if we're reading from the server while typing a command. Meh.

At this point I think I need to rethink the various use cases here. There
is the simple socket use case that doesn't require anything fancy. It should
probably be refactored into a command/response design pattern similar to
our more complicated raw tty version. The raw tty version should be more
capable with command line history and multiline pasting, but also be 
a command/response design pattern so that the prompt is aligned from line
to line whether we're pasting or not.

Now, if we do want to have the server sending us lines while we're typing
our commands, this can be done with textual. In this case, we'd have
the server responses put into a scrollable view with statics inserted just
above where we dial in our commands. The weirdness here is that our command
will be boxed into a scrollable itself instead of being spread across the
screen. Meh.
'''

async def start_raw_tty_repl_client(socket_path: str = None, host: str = None, port: int = None):
    import termios
    import tty
    import select
    import sys, os, fcntl
    try:
        reader = None
        writer = None
        if socket_path:
            reader, writer = await asyncio.open_unix_connection(socket_path)
        else:
            reader, writer = await asyncio.open_connection(host, port)

        print(f"Connected to {host}:{port}")


        async def read_available(areader):
            chunks = []
            while True and len(chunks) == 0:
                try:
                    # Try reading a small chunk with timeout=0 to avoid blocking
                    chunk = await asyncio.wait_for(areader.read(1024), timeout=0.01)
                    if not chunk:  # EOF
                        break
                    chunks.append(chunk)
                except asyncio.TimeoutError:
                    # No more data available right now
                    break
            #sys.stdout.write(output.decode().replace('\n', '\r\n'))
            #sys.stdout.flush()
            return b"".join(chunks)


        async def write_to_server_async():
            loop = asyncio.get_running_loop()
            stdin_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(stdin_reader)

            # Put stdin in raw mode
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)

            # Connect StreamReaderProtocol to stdin
            await loop.connect_read_pipe(lambda: protocol, os.fdopen(fd, "rb"))

            line = []

            

            try:
                while True:

                    data = await read_available(stdin_reader)

                    if len(data) == 0:
                        await asyncio.sleep(0)

                    elif data == b'\x04': # Ctrl-D
                        #print(f"Ctrl D: {data}")
                        raise ExitReplException()
                    
                    elif data in (b'\x08', b'\x7f'): # Backspace
                        #print("BS")
                        if line:
                            line.pop()                                    
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                        continue

                    elif data.startswith(b'\x1b'):
                        print("Esc")
                        raise ExitReplException()
                        #handle_escape_sequence(data)
                        # b'\x1b[A' is UP

                    elif data in (b'\r', b'\n'): # Enter
                        user_input = b''.join(line) + b'\r\n'
                        #print(user_input)
                        line = []
                        sys.stdout.write('\r\n')
                        sys.stdout.flush()

                        writer.write(user_input)
                        await writer.drain()

                        server_resp = await read_available(reader)
                        sys.stdout.write(server_resp.decode())
                        sys.stdout.flush()

                    elif b'\n' in data or len(data) > 1:
                        #handle_paste(data)
                        print("PASTE DETECTED")
                        # TODO: Based on the provided input,
                        # read each line
                        # Does code.
                        continue
                    
                    else:
                        #handle_typing(data)
                        line.append(data)
                        sys.stdout.write(data.decode())
                        sys.stdout.flush()

            except ExitReplException:
                sys.exit(0)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        
        async def write_to_server():
            fd = sys.stdin.fileno()
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            old_settings = termios.tcgetattr(fd)
            
            try:
                tty.setraw(fd)  # Put terminal in raw mode
                while True:

                    line = []
                    new_line = False
                    
                    while True:
                        rlist, _, _ = select.select([fd], [], [], 0)
                        if rlist:
                            data = os.read(fd, 2048)                          

                            # if not data:
                            #     return  # nothing to read
                            #print(data)

                            if data in (b'\x04'): # Ctrl-D
                                raise ExitReplException()
                            
                            if data in (b'\x08', b'\x7f'): # Backspace
                                if line:
                                    line.pop()                                    
                                    sys.stdout.write('\b \b')
                                    sys.stdout.flush()
                                continue

                            elif data.startswith(b'\x1b'):
                                raise ExitReplException()
                                #handle_escape_sequence(data)
                                # b'\x1b[A' is UP

                            elif data in (b'\r', b'\n'): # Enter
                                user_input = b''.join(line) + b'\r\n'
                                line = []
                                sys.stdout.write('\r\n')
                                sys.stdout.flush()

                                writer.write(user_input)
                                await writer.drain()
                                await read_available()

                            elif b'\n' in data or len(data) > 1:
                                #handle_paste(data)
                                print("PASTE DETECTED")
                                # TODO: Based on the provided input,
                                # read each line
                                continue
                            
                            else:
                                #handle_typing(data)
                                line.append(data)
                                sys.stdout.write(data.decode())
                                sys.stdout.flush()



                            # # Detect escape sequences
                            # if data.startswith(b'\x1b'):
                            #     handle_escape_sequence(data)
                            # # Detect typed Enter (single newline, not part of paste)
                            # elif data in (b'\r', b'\n'):
                            #     handle_enter()
                            # # Detect paste (multiple bytes or multiple newlines)
                            # elif b'\n' in data or len(data) > 1:
                            #     handle_paste(data)
                            # # Normal characters
                            # else:
                            #     handle_typing(data)


                            # if ch == b'\x04': # Ctrl-D
                            #     raise ExitReplException()

                            # if ch == b'\x1b': # Escape Sequence
                            #     # TODO: Handle escape?
                            #     seq = ch + os.read(fd, 2)
                            #     if seq == b'\x1b[A':
                            #         print("UP")
                            #         line = []
                            #         break
                                    
                            # if ch in (b"\r", b"\n"):  # End-of-line
                            #     new_line = True
                            #     sys.stdout.write("\r\n")
                            #     sys.stdout.flush()
                            #     break

                            # if ch in (b'\x08', b'\x7f'): # Backspace
                            #     if line:
                            #         line.pop()                                    
                            #         sys.stdout.write('\b \b')
                            #         sys.stdout.flush()
                            #     continue

                            # line.append(ch)
                            # sys.stdout.write(ch.decode())
                            # sys.stdout.flush()
                        else:
                            await asyncio.sleep(0)
                
                    # if new_line:
                    #     new_line = False
                    #     user_input = b''.join(line)
                    #     writer.write(user_input + b'\r\n')
                    #     await writer.drain()
                    #     await read_available()
    
            except ExitReplException:
                sys.exit(0)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        server_hello = await read_available(reader)
        sys.stdout.write(server_hello.decode())
        sys.stdout.flush()
        await write_to_server_async()
        

    except ConnectionResetError as e:
        print(f"\nClient disconnected: {e}")
        pass
    except SystemExit:
        pass
    except Exception as e:
        print(f"Exception: {e}")



def other():
    print("wert")
    print("third")





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

            print(line_bytes)
            line = line_bytes.decode()
            
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                more = console.push(line)

            captured = output.getvalue().replace('\n', '\r\n')
            print(captured.encode())
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




# data = os.read(fd, 1024)

# if not data:
#     return  # nothing to read

# # Detect escape sequences
# if data.startswith(b'\x1b'):
#     handle_escape_sequence(data)
# # Detect typed Enter (single newline, not part of paste)
# elif data in (b'\r', b'\n'):
#     handle_enter()
# # Detect paste (multiple bytes or multiple newlines)
# elif b'\n' in data or len(data) > 1:
#     handle_paste(data)
# # Normal characters
# else:
#     handle_typing(data)













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
