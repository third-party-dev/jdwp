#!/usr/bin/env python3
import readline
import asyncio
import sys
import code
import select

console = code.InteractiveConsole()
ps1 = ">>> "
ps2 = "... "
prompt = ps1


async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def repl():
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
                # !!! This is synchronous. !!!
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


if __name__ == "__main__":
    asyncio.run(repl())





'''



def func():
    print("first")

    print("second")

    print("third")

    print("forth")



print("one")
print("two")



'''