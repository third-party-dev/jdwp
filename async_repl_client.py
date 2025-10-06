#!/usr/bin/env python3



import asyncio
from thirdparty.sandbox.repl import Repl

asyncio.run(Repl().async_repl_client(socket_path="/tmp/asyncrepl.sock"))