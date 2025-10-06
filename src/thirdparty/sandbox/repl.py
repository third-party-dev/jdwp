#!/usr/bin/env python3

import readline
import asyncio
import sys
import code
import select
import keyword
import re
import ast
import codeop
import os
import json
import io
import contextlib
import traceback


identifier_re = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def is_ast_naked_await(tree) -> bool:
    # Set parent for each child
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent

    def inside_async_function(node):
        # Walk up ancestry tree to see if await is wrapped.
        while node:
            if isinstance(node, ast.AsyncFunctionDef):
                return True
            node = getattr(node, "parent", None)
        return False

    # Check if all awaits are wrapped or not.
    for node in ast.walk(tree):
        if isinstance(node, ast.Await) and not inside_async_function(node):
            return True
    return False


def is_ast_expression(tree) -> bool:

    if not tree.body:
        # Empty string is not an expression
        return False

    return all(isinstance(node, ast.Expr) for node in tree.body)


def is_valid_python_identifier(key) -> bool:
    return (
        isinstance(key, str) and
        identifier_re.match(key) is not None and
        not keyword.iskeyword(key)
    )


def blocking_run_single_line(source_code, namespace):

    try:
        tree = ast.parse(source_code, mode="exec")
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        return None

    if not is_ast_naked_await(tree):
        # No wrapping required.
        if is_ast_expression(tree):
            # !!!!!! BUG: This prints None when the call is print()
            ret = eval(source_code, namespace, namespace)
            if ret is not None:
                print(ret)
        else:
            exec(source_code, namespace, namespace)
    else:
        # Need to wrap await.
        raise NotImplementedError("Calling await from sync REPL not supported.")


# Note: This function needs to stay in global scope.
async def async_run_single_line(source_code, namespace):

    try:
        tree = ast.parse(source_code, mode="exec")
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        return None

    is_expr = is_ast_expression(tree)

    if not is_ast_naked_await(tree):
        # No wrapping required.
        if is_expr:
            ret = eval(source_code, namespace, namespace)
            if ret is not None:
                print(ret)
        else:
            # Note: This code is blocking!
            exec(source_code, namespace, namespace)
    else:
        # Need to wrap await.
        # TODO: Consider UUID for all unique variables.
        # TODO: Consider checking to see if symbol exists.

        # Wrapper header.
        wrapped_source = [
            'import asyncio',
            'async def __thirdparty_sandbox_async_def():']

        # Expose all the global variables to function.
        for key in namespace:
            if is_valid_python_identifier(key):
                wrapped_source.append(f'    global {key}')

        # If its an expression, save the result.
        if is_expr:
            wrapped_source.append(f"    __thirdparty_sandbox_ret = {source_code}")
        else:
            # TODO: Check for (premature) return or yield?
            wrapped_source.append(f"    {source_code}")

        # Update globals() with any local assignments.
        wrapped_source.append('    globals().update(locals())')
        if is_expr:
            wrapped_source.append('    return __thirdparty_sandbox_ret')

        # Run the function definition in global scope.
        exec('\n'.join(wrapped_source), namespace, namespace)

        # Run the function in the event loop.
        #ret = await __thirdparty_sandbox_async_def()
        # TODO: UGH! I still need a way to await in another namespace!

        # If original source was an expression, print it.
        # TODO: Consider not printing Calls? print() prints None
        if is_expr and ret:
            print(ret)

        # TODO: Consider wiping the created state?


async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


def async_def_complete(final_buffer):
    # Check for completeness
    async_wrap = ['    ' + x for x in final_buffer]
    async_wrap.insert(0, 'async def __thridparty_sandbox_asyncdef():')
    final_src = '\n'.join([*async_wrap, ''])
    complete = False
    if len(final_src) > 0:
        try:
            complete = codeop.compile_command(final_src, "<string>", "exec")
        except SyntaxError as e:
            if 'await' in e.msg and 'outside' in e.msg:
                complete = True
            else:
                raise
    return complete


class Repl():

    def __init__(self, namespace={}):
        self.namespace = namespace
        self.console = code.InteractiveConsole(self.namespace)
        self.ps1 = ">>> "
        self.ps2 = "... "
        self.prompt = self.ps1


    async def async_repl(self):
        try:
            # REPL Loop
            while True:

                try:

                    final_buffer = []

                    # Atomic Input Loop (e.g. Multiline Paste)
                    while True:
                        buffer = []

                        # Ensure event loop has time to execute.
                        await asyncio.sleep(0)

                        # Line Input
                        while True:
                            completed_input_string = await async_input(self.prompt)
                            buffer.append(completed_input_string)
                            
                            has_input, _, _ = select.select([sys.stdin], [], [], 0)
                            if not has_input:
                                break
                            self.prompt = self.ps2

                        # Move current buffer to final_buffer to detect lone newline.
                        final_buffer.extend(x for x in buffer if x != '')

                        if len(final_buffer) == 0:
                            # Ignore empty input.
                            continue

                        # Continue loop if buffer is not single statement or newline.
                        # (i.e. extra Enter after multi-line paste.)
                        if len(buffer) > 1:
                            continue

                        # Check for code completeness.
                        # Note: "async def" wrap to ignore await outside function error.
                        complete, final_src = wrap_in_async_def(final_buffer)
                        if not complete:
                            self.prompt = self.ps2
                            continue

                        # Note: Assume complete and good syntax below.
                        break

                    final_src = '\n'.join([*final_buffer, ''])
                    if len(final_src) > 0:
                        if len(final_buffer) == 1:
                            await async_run_single_line(final_buffer[0])
                        else:
                            # TODO: Use exec and self.namespace
                            more = self.console.runsource(final_src, symbol="exec")
                            self.prompt = self.ps2 if more else self.ps1
                    
                    # Ensure event loop has time to execute.
                    await asyncio.sleep(0)

                except KeyboardInterrupt:
                    self.prompt = self.ps1
                    print("\nKeyboardInterrupt")
                except SyntaxError as e:
                    print(f"\nSyntaxError: {e}")

        except EOFError:
            print()
            pass


    @staticmethod
    async def _read_available(areader, timeout=0.01):
        chunks = []
        while True and len(chunks) == 0:
            try:
                # Try reading a small chunk with timeout=0 to avoid blocking
                chunk = await asyncio.wait_for(areader.read(1024), timeout=timeout)
                if not chunk:  # EOF
                    raise EOFError()
                chunks.append(chunk)
            except asyncio.TimeoutError:
                # No more data available right now
                break
        #sys.stdout.write(output.decode().replace('\n', '\r\n'))
        #sys.stdout.flush()
        return b"".join(chunks)


    async def async_repl_client(self, socket_path: str = None, host: str = None, port: int = None):
        try:
            reader = None
            writer = None
            if socket_path:
                reader, writer = await asyncio.open_unix_connection(socket_path)
            else:
                reader, writer = await asyncio.open_connection(host, port)
            print(f"Connected to {host}:{port}")
            banner = await Repl._read_available(reader)
            print(banner.decode())
        
            # REPL Loop
            while True:

                try:
                    final_buffer = []

                    # Atomic Input Loop (e.g. Multiline Paste)
                    while True:
                        buffer = []

                        # Ensure event loop has time to execute.
                        await asyncio.sleep(0)

                        # Line Input
                        while True:
                            completed_input_string = await async_input(self.prompt)
                            buffer.append(completed_input_string)
                            
                            has_input, _, _ = select.select([sys.stdin], [], [], 0)
                            if not has_input:
                                break
                            self.prompt = self.ps2

                        # Move current buffer to final_buffer to detect lone newline.
                        final_buffer.extend(x for x in buffer if x != '')

                        if len(final_buffer) == 0:
                            # Ignore empty input.
                            continue

                        # Continue loop if buffer is not single statement or newline.
                        # (i.e. extra Enter after multi-line paste.)
                        if len(buffer) > 1:
                            continue

                        # Check for code completeness.
                        # Note: "async def" wrap to ignore await outside function error.
                        complete = async_def_complete(final_buffer)
                        if not complete:
                            self.prompt = self.ps2
                            continue

                        # Note: Assume complete and good syntax below.
                        break

                    # Strictly command and response.
                    writer.write(json.dumps(final_buffer).encode())
                    await writer.drain()
                    self.prompt = self.ps1

                    # Wait for response.
                    resp_json = await Repl._read_available(reader, timeout=None)
                    if len(resp_json) > 0:
                        resp = json.loads(resp_json.decode())
                        if resp[0] > 0:
                            sys.stdout.write(resp[1])
                            sys.stdout.flush()
                    
                    # Ensure event loop has time to execute.
                    await asyncio.sleep(0)

                except KeyboardInterrupt:
                    self.prompt = self.ps1
                    print("\nKeyboardInterrupt")
                except SyntaxError as e:
                    print(f"\nSyntaxError: {e}")
                


        except EOFError:
            print()
            pass
        except ConnectionResetError as e:
            print(f"\nClient disconnected: {e}")
            pass
        except SystemExit:
            pass
        except Exception as e:
            print(f"Exception: {e} Line:{e.__traceback__.tb_lineno}")
        
        finally:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), timeout=1.0)


    @staticmethod
    async def _handle_repl_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, namespace):
        try:
            addr = writer.get_extra_info("peername") or "unix-client"
            print(f"Client connected: {addr}")

            writer.write(b"Welcome to the asyncio Python console!\r\nType Python code.\r\n")
            await writer.drain()

            while True:
                
                final_buffer_json = await Repl._read_available(reader)
                if len(final_buffer_json) == 0:
                    continue
                final_buffer = json.loads(final_buffer_json.decode())
                final_src = '\n'.join([*final_buffer, ''])

                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    try:
                        if len(final_src) > 0:
                            if len(final_buffer) == 1:
                                await async_run_single_line(final_buffer[0], namespace)
                            else:
                                exec(final_src, namespace, namespace)
                    except EOFError:
                        raise
                    except Exception as e:
                        print(f"Exception: {e} Line:{traceback.format_exc()}")
                    
                captured = output.getvalue().replace('\n', '\r\n')
                #print(captured.encode())
                resp = json.dumps([len(captured), captured])
                print(resp.encode())
                #if captured:
                writer.write(resp.encode())
                #else:
                #    writer.write(json.dumps)
                await writer.drain()
            
        except EOFError as e:
            print("Client disconnected.")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Exception: {e} Line:{e.__traceback__}")
                
    # dbg.cli_frame_count()

    async def start_repl_server(self, socket_path: str=None, host: str=None, port: int=None):
        try:
            async def handle_repl_client_wrapper(reader, writer):
                await Repl._handle_repl_client(reader, writer, self.namespace)

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


    def blocking_repl(self):
        try:
            # REPL Loop
            while True:

                try:

                    final_buffer = []

                    # Atomic Input Loop (e.g. Multiline Paste)
                    while True:
                        buffer = []

                        # Line Input
                        while True:
                            completed_input_string = input(self.prompt)
                            buffer.append(completed_input_string)
                            has_input, _, _ = select.select([sys.stdin], [], [], 0.01)
                            if not has_input:
                                break
                            self.prompt = self.ps2

                        # Move current buffer to final_buffer to detect lone newline.
                        final_buffer.extend(x for x in buffer if x != '')

                        if len(final_buffer) == 0:
                            # Ignore empty input.
                            continue

                        # Continue loop if buffer is no single statement or newline.
                        if len(buffer) > 1:
                            continue

                        # Check for code completeness.
                        # Note: "async def" wrap to ignore await outside function error.
                        complete = async_def_complete(final_buffer)
                        if not complete:
                            self.prompt = self.ps2
                            continue

                        # Note: Assume complete and good syntax below.
                        break


                    final_src = '\n'.join([*final_buffer, ''])
                    if len(final_src) > 0:
                        if len(final_buffer) == 1:
                            blocking_run_single_line(final_buffer[0], self.namespace)
                        else:
                            # TODO: use exec instead with self.namespace
                            more = self.console.runsource(final_src, symbol="exec")
                            self.prompt = self.ps2 if more else self.ps1

                except KeyboardInterrupt:
                    self.prompt = self.ps1
                    print("\nKeyboardInterrupt")
                except SyntaxError as e:
                    print(f"\nSyntaxError: {e}")

        except EOFError:
            print()
            pass


if __name__ == "__main__":
    #asyncio.run(Repl().async_repl())
    #Repl().blocking_repl()
    asyncio.run(Repl().start_repl_server(socket_path="/tmp/asyncrepl.sock"))

'''



def func():
    print("first")

    print("second")

    print("third")

    print("forth")



print("one")
print("two")
func()



async def m():
    await asyncio.sleep(1)
    return 5

await m()



'''