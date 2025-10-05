#!/usr/bin/env python3

import readline
import sys
import select
import code

console = code.InteractiveConsole()
ps1 = ">>> "
ps2 = "... "
prompt = ps1

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
            more = console.runsource(final_src, symbol="exec")  # <---- No longer push()
            prompt = ps2 if more else ps1

        except KeyboardInterrupt:
            prompt = ps1
            print("\nKeyboardInterrupt")

except EOFError:
    print()
    pass


'''



def func():
    print("first")

    print("second")

    print("third")

    print("forth")



print("one")
print("two")



'''
