# thirdparty.jdwp

A JDWP implementation in async python.

Note: Very much a work in progress.

## Example

```
import asyncio
from thirdparty.jdwp import Jdwp

async def main():
    jdwp = await Jdwp('localhost', 8700).start()

    print(await jdwp.VirtualMachine.Version())

    print(await jdwp.VirtualMachine.ClassPaths())

asyncio.run(main())
```

## References

- [Java Debug Wire Protocol](https://docs.oracle.com/javase/8/docs/technotes/guides/jpda/jdwp-spec.html)

- [JDWP Protocol Details](https://docs.oracle.com/javase/8/docs/platform/jpda/jdwp/jdwp-protocol.html)
#JDWP_VirtualMachine_AllClasses

