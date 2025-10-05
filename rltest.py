#!/usr/bin/env python3

import readline
import sys
import select
import code

console = code.InteractiveConsole()
ps1 = ">>> "
ps2 = "... "
prompt = ps1

while True:

    final_buffer = []

    while True:

        buffer = []
        completed_input_string = input(prompt)
        buffer.append(completed_input_string)
        has_input, _, _ = select.select([sys.stdin], [], [], 0.01)

        while has_input or buffer[-1] != '':

            # If there is more input, keep going
            has_input, _, _ = select.select([sys.stdin], [], [], 0.01)
            if has_input:
                prompt = ps2
            else:
                # No more input, break.
                break

            completed_input_string = input(prompt)
            buffer.append(completed_input_string)

        # At this point, we have no more pending data...
        # Move current buffer to final_buffer to detect lone newline.
        final_buffer.extend(x for x in buffer if x != '')

        if len(buffer) > 1:
            # Input is done, lets look for lone newline before stopping.
            continue

        break

    final_buffer.append('')
    final_src = '\n'.join(final_buffer)
    more = console.runsource(final_src, symbol="exec")
    prompt = ps2 if more else ps1


    

'''



def func():
    print("first")

    print("second")



print("one")
print("two")



'''







    #final_src = '\n'.join(buffer)
    #if len(final_src) > 0:
    #    more = console.push(final_src)
    #    prompt = ps1 if more else ps2
    







    # If the last input was more than a single line, ask for another line
    

    #if len(completed_input_string):
    #    buffer.append(completed_input_string)
    # final_src = '\n'.join(buffer)
    # print(f"processed {buffer} {has_input} {buffer[-1]}")

    # if len(buffer) != 0 and buffer[-1] != '' and not has_input:
        
        

    #print(f"Line: {completed_input_string.encode()}")
    #print("Statement End")

    # not_done_reading = ""
    # completed_input_string = not_done_reading
    # buffer = ""
    # sys.stdout.write("> ")
    # sys.stdout.flush()
    # while completed_input_string == not_done_reading:
    #     ready, _, _ = select.select([sys.stdin], [], [], None)#timeout)
    #     if ready:
    #         completed_input_string = input("$ ")  # readline features are active if readline imported
    #         #print("You typed:", completed_input_string)
    #     else:
    #         print("EOF")


