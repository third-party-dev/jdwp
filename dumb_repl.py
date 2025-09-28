import asyncio
import thirdparty.sandbox as __sandbox__

async def main_with_sandbox():
    # Note: Need to send the globals() from this scope or we get the module's globals().
    sandbox_coro = __sandbox__.start_sandbox(repl_socket_path="/tmp/repl.sock", repl_namespace=globals())
    sandbox_task = asyncio.create_task(sandbox_coro)
    await asyncio.gather(sandbox_task)

if __name__ == "__main__":
    asyncio.run(main_with_sandbox())