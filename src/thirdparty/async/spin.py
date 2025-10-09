import asyncio

def has_running_loop() -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    else:
        return True


def spin(coro):
    loop = asyncio.get_running_loop()
    task = loop.create_task(coro)
    while not task.done():
        
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    else:
        asyncio.run(coro)


async def spin_loop(tick_delay=0):
    await sleep(tick_delay)

if not has_running_loop():
    asyncio.run(spin_loop())