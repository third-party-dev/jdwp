#!/usr/bin/env python3

import asyncio
from thirdparty.sandbox.repl import Repl

# asdf = 654

# async def mine():
#     await asyncio.sleep(1)
#     return asdf

asyncio.run(Repl(namespace=globals()).start_repl_server(socket_path="/tmp/asyncrepl.sock"))
#aio.run(Repl(namespace=globals()).async_repl_client(socket_path="/tmp/asyncrepl.sock"))