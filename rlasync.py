#!/usr/bin/env python3
import readline
import asyncio
import sys
import code
import select
import keyword
import re
import ast
from pprint import pprint

console = code.InteractiveConsole(globals())
ps1 = ">>> "
ps2 = "... "
prompt = ps1


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


identifier_re = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
def is_valid_python_identifier(key) -> bool:
    return (
        isinstance(key, str) and
        identifier_re.match(key) is not None and
        not keyword.iskeyword(key)
    )


def blocking_run_single_line(source_code):

    try:
        tree = ast.parse(source_code, mode="exec")
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        return None

    if not is_ast_naked_await(tree):
        # No wrapping required.
        if is_ast_expression(tree):
            # !!!!!! BUG: This prints None when the call is print()
            ret = eval(source_code)
            if ret:
                print(ret)
        else:
            exec(source_code, globals(), globals())
    else:
        # Need to wrap await.
        raise NotImplementedError("Calling await from sync REPL not supported.")


async def async_run_single_line(source_code):

    try:
        tree = ast.parse(source_code, mode="exec")
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        return None

    is_expr = is_ast_expression(tree)

    if not is_ast_naked_await(tree):
        # No wrapping required.
        if is_expr:
            ret = eval(source_code)
            if ret:
                print(ret)
        else:
            # Note: This code is blocking!
            exec(source_code, globals(), globals())
    else:
        # Need to wrap await.
        # TODO: Consider UUID for all unique variables.

        # Wrapper header.
        wrapped_source = [
            'import asyncio',
            'async def __thirdparty_sandbox_async_def():']

        # Expose all the global variables to function.
        for key in globals():
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
        exec('\n'.join(wrapped_source), globals(), globals())

        # Run the function in the event loop.
        ret = await __thirdparty_sandbox_async_def()

        # If original source was an expression, print it.
        # TODO: Consider not printing Calls? print() prints None
        if is_expr and ret:
            print(ret)

        # TODO: Consider wiping the created state?


async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def async_repl():
    global prompt
    global ps1
    global ps2

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
                        completed_input_string = await async_input(prompt)
                        buffer.append(completed_input_string)
                        
                        has_input, _, _ = select.select([sys.stdin], [], [], 0)
                        if not has_input:
                            break
                        prompt = ps2

                    # Move current buffer to final_buffer to detect lone newline.
                    final_buffer.extend(x for x in buffer if x != '')

                    # Continue loop if buffer is no single statement or newline.
                    if len(buffer) > 1:
                        continue
                    break

                final_buffer.append('')
                final_src = '\n'.join(final_buffer)

                if len(final_buffer) == 2 and len(final_src) > 1:
                    await async_run_single_line(final_buffer[0])
                else:
                    more = console.runsource(final_src, symbol="exec")  # <---- No longer push()
                    prompt = ps2 if more else ps1
                
                # Ensure event loop has time to execute.
                await asyncio.sleep(0)

            except KeyboardInterrupt:
                prompt = ps1
                print("\nKeyboardInterrupt")

    except EOFError:
        print()
        pass


def blocking_repl():
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
                        completed_input_string = input(prompt)
                        buffer.append(completed_input_string)
                        has_input, _, _ = select.select([sys.stdin], [], [], 0.01)
                        if not has_input:
                            break
                        prompt = ps2

                    # Move current buffer to final_buffer to detect lone newline.
                    final_buffer.extend(x for x in buffer if x != '')

                    # Continue loop if buffer is no single statement or newline.
                    if len(buffer) > 1:
                        continue
                    break

                final_buffer.append('')
                final_src = '\n'.join(final_buffer)

                if len(final_buffer) == 2 and len(final_src) > 1:
                    blocking_run_single_line(final_buffer[0])
                else:
                    more = console.runsource(source, symbol=mode)  # <---- No longer push()
                    prompt = ps2 if more else ps1

            except KeyboardInterrupt:
                prompt = ps1
                print("\nKeyboardInterrupt")

    except EOFError:
        print()
        pass


if __name__ == "__main__":
    asyncio.run(async_repl())





'''



def func():
    print("first")

    print("second")

    print("third")

    print("forth")



print("one")
print("two")



async def m():
    await asyncio.sleep(1)
    return 5

await m()



'''