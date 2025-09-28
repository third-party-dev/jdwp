import asyncio
from thirdparty.sandbox import start_dict_client

shared_dict = start_dict_client(socket_path="/tmp/dict.sock")
shared_dict['value'] = 2345
print(str(shared_dict))

