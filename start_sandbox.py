import asyncio
import thirdparty.sandbox as __sandbox__

# Only required for assignment.
import multiprocessing
shared_dict = multiprocessing.Manager().dict()
shared_dict['thing'] = 'value'

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