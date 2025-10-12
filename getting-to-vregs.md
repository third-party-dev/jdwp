Start frida-server:

```
adb root
adb remount
adb push frida-server /data/frida-server
adb shell chmod +x /data/frida-server
adb shell "/data/frida-server &"
```

Start target application in debug mode:

```
adb shell am set-debug-app -w sh.kau.playground ; \
  adb shell am start \
    -n $(adb shell cmd package resolve-activity \
      -c android.intent.category.LAUNCHER sh.kau.playground | \
        grep -oP 'name=\K\S+' | head -n 1 | \
          sed -s 's/sh.kau.playground/sh.kau.playground\//') ; \
  adb forward \
    tcp:8700 \
      jdwp:$(adb shell ps -A | grep sh.kau.playground | awk '{print $2}') ; \
  sleep 3 && ./test.py
```

Connect to target application in Frida.

```
frida -U -p $(adb shell ps -A | grep sh.kau.playground | awk '{print $2}')
```

Trigger breakpoint and REPL into process via JDWP:

```
python src/thirdparty/sandbox/repl.py
```

Dereference thread ID as an object in REPL:

```
await dbg.deref(26097)
```

Get the nativePeer value from output:

```
>>> await dbg.deref(26097)
ObjectInfo(26097)
  Ljava/lang/Object; (classID 942)

    Methods: [skipped]

    Fields:
      - Ljava/lang/Class; shadow$_klass_ = ClassObject(22756)
      - I shadow$_monitor_ = Int(0)
  Ljava/lang/Thread; (classID 583)

    Methods: [skipped]

    Fields:
      - [Ljava/lang/StackTraceElement; EMPTY_STACK_TRACE = Object(0)
      - I MAX_PRIORITY = Int(0)
      - I MIN_PRIORITY = Int(324317448)
      - I NORM_PRIORITY = Int(1890209128)
      - Ljava/lang/RuntimePermission; SUBCLASS_IMPLEMENTATION_PERMISSION = Object(0)
      - Ljava/lang/Thread$UncaughtExceptionHandler; defaultUncaughtExceptionHandler = Object(0)
      - I threadInitNumber = Int(5)
      - J threadSeqNumber = Long(0)
      - Ljava/lang/Thread$UncaughtExceptionHandler; uncaughtExceptionPreHandler = Object(26345)
      - Lsun/nio/ch/Interruptible; blocker = Object(0)
      - Ljava/lang/Object; blockerLock = Object(26346)
      - Ljava/lang/ClassLoader; contextClassLoader = ClassLoader(26347)
      - Z daemon = Boolean(1)
      - J eetop = Long(0)
      - Ljava/lang/ThreadGroup; group = ThreadGroup(26348)
      - Ljava/lang/ThreadLocal$ThreadLocalMap; inheritableThreadLocals = Object(0)
      - Ljava/security/AccessControlContext; inheritedAccessControlContext = Object(26349)
      - Ljava/lang/Object; lock = Object(26350)
      - Ljava/lang/String; name = String(26351)
--->  - J nativePeer = Long(135557475466928)
      - Ljava/lang/Object; parkBlocker = Object(0)
      - I priority = Int(5)
      - Z single_step = Boolean(0)
      - J stackSize = Long(0)
      - Z started = Boolean(1)
      - Z stillborn = Boolean(0)
      - Z systemDaemon = Boolean(0)
      - Ljava/lang/Runnable; target = Object(0)
      - I threadLocalRandomProbe = Int(0)
      - I threadLocalRandomSecondarySeed = Int(0)
      - J threadLocalRandomSeed = Long(0)
      - Ljava/lang/ThreadLocal$ThreadLocalMap; threadLocals = Object(26352)
      - J tid = Long(49)
      - Ljava/lang/Thread$UncaughtExceptionHandler; uncaughtExceptionHandler = Object(0)
      - Z unparkedBeforeStart = Boolean(0)
  Lkotlinx/coroutines/scheduling/CoroutineScheduler$Worker; (classID 22756)

    Methods: [skipped]

    Fields:
      - Ljava/util/concurrent/atomic/AtomicIntegerFieldUpdater; workerCtl$volatile$FU = Object(0)
      - I indexInArray = Int(3)
      - Lkotlinx/coroutines/scheduling/WorkQueue; localQueue = Object(26341)
      - Z mayHaveLocalTasks = Boolean(0)
      - J minDelayUntilStealableTaskNs = Long(0)
      - Ljava/lang/Object; nextParkedWorker = Object(26342)
      - I rngState = Int(1333294357)
      - Lkotlinx/coroutines/scheduling/CoroutineScheduler$WorkerState; state = Object(26343)
      - Lkotlin/jvm/internal/Ref$ObjectRef; stolenTask = Object(26344)
      - J terminationDeadline = Long(0)
      - Lkotlinx/coroutines/scheduling/CoroutineScheduler; this$0 = Object(26339)
      - I workerCtl$volatile = Int(0)
```

Dump memory at pointer via Frida:

```
threadPtr = ptr(135557475466928);
console.log(hexdump(threadPtr, {offset:0, length:256, header: true, ansi: true}))
```

Using the following:
- https://cs.android.com/android/platform/superproject/+/android-13.0.0_r84:art/runtime/thread.h;bpv=0
- https://cs.android.com/android/platform/superproject/+/android-13.0.0_r84:art/runtime/runtime_stats.h;bpv=0
- https://cs.android.com/android/platform/superproject/+/android-13.0.0_r84:art/runtime/managed_stack.h;bpv=0

Interpret the data as art::Thread for your version of Android to get SHADOWFRAME:

```text
               0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
              flags       sus_cnt     thin_lckid  tid
7b49ef2bfeb0  01 00 00 5c 01 00 00 00 19 00 00 00 14 7d 00 00  ...\.........}..
              daemon-bool oom-bool    no_th_sus   exit_cnt
7b49ef2bfec0  01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
              xrun-bool   intr-bool   park_st     WeakRef?
7b49ef2bfed0  01 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00  ................
              dis_flip    usr_sus_cnt fint_cnt    mkvizcnt
7b49ef2bfee0  00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00  ................
              defclscnt   readers     hotness     ?ALIGNMENT?
7b49ef2bfef0  00 00 00 00 00 00 00 00 00 00 00 00 ff ff 00 00  ................
              trace_clock_base        stats[0]
7b49ef2bff00  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
              stats[1]                stats[2]
7b49ef2bff10  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
              stats[3]                stats[4]
7b49ef2bff20  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
              stats[5]                stats[6]
7b49ef2bff30  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
        struct tls_ptr_sized_values {
              IF card_Table           *Throwable Exception
7b49ef2bff40  70 10 7f 74 48 7b 00 00 00 00 00 00 00 00 00 00  p..tH{..........
                                      Start Of ManagedStack {
              *STACK_END              TaggedTopQuickFrame
7b49ef2bff50  00 00 f2 12 48 7b 00 00 00 00 00 00 00 00 00 00  ....H{..........
              ManagedStack* link_     SHADOWFRAME Pointer
7b49ef2bff60  f0 02 02 13 48 7b 00 00 00 02 02 13 48 7b 00 00  ....H{......H{..
7b49ef2bff70  00 00 00 00 00 00 00 00 90 3c 28 3f 49 7b 00 00  .........<(?I{..
7b49ef2bff80  00 00 00 00 00 00 00 00 b0 fe 2b ef 49 7b 00 00  ..........+.I{..
7b49ef2bff90  80 0a 34 13 00 00 00 00 00 00 00 00 00 00 00 00  ..4.............
7b49ef2bffa0  00 e0 f1 12 48 7b 00 00 f0 2c 10 00 00 00 00 00  ....H{...,......
```

Dump memory at ShadowPointer via Frida:

```
frame = ptr(0x7b4813020200);
console.log(hexdump(frame, {offset:0, length:256, header: true, ansi: true}))
```

Using the following:

- MAYBE: https://cs.android.com/android/platform/superproject/+/android-latest-release:art/runtime/interpreter/interpreter_common.cc
- https://cs.android.com/android/platform/superproject/+/android-13.0.0_r84:art/runtime/managed_stack.h;bpv=0
- https://cs.android.com/android/platform/superproject/+/android-latest-release:art/runtime/interpreter/lock_count_data.h
- https://cs.android.com/android/platform/superproject/+/android-latest-release:art/runtime/interpreter/shadow_frame.h


Interpret memory to get vregs array:

```
               0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
              
7b4813020200  00 00 00 00 00 00 00 00 68 e4 cf 5b 48 7b 00 00  ........h..[H{..
                                      *link_
7b4813020210  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
              *method_                local_count_data_?
7b4813020220  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
              VREG_CNT    DEX PC      FLAGS       VREGS[0]
7b4813020230  09 00 00 00 19 00 00 00 00 00 00 00 01 00 00 00  ................
              VREGS[1]    VREGS[2]    VREGS[3]    VREGS[4]
7b4813020240  58 26 d8 12 00 00 00 00 00 00 00 00 00 00 00 00  X&..............
              VREGS[5]    VREGS[6]    VREGS[7]    VREGS[8]
7b4813020250  00 00 00 00 00 00 00 00 00 00 00 00 d0 25 d8 12  .............%..
              VREG_REF[0] VREG_REF[1] VREG_REF[2] VREG_REF[3]
7b4813020260  70 7e e1 12 58 26 d8 12 00 00 00 00 00 00 00 00  p~..X&..........
              VREG_REF[4] VREG_REF[5] VREG_REF[6] VREG_REF[7]
7b4813020270  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
              VREG_REF[8] REF[8+1]?   ANOTHER OBJECT
7b4813020280  d0 25 d8 12 70 7e e1 12 8b 1a 71 79 48 7b 00 00  .%..p~....qyH{..
7b4813020290  02 00 00 00 00 00 00 00 00 00 00 00 02 00 00 00  ................
7b48130202a0  b0 fe 2b ef 49 7b 00 00 d0 03 02 13 48 7b 00 00  ..+.I{......H{..
7b48130202b0  37 24 b2 16 48 7b 00 00 90 02 02 13 48 7b 00 00  7$..H{......H{..
7b48130202c0  18 03 02 13 48 7b 00 00 00 00 00 00 00 00 00 00  ....H{..........
7b48130202d0  b6 00 00 00 00 00 00 00 b4 6b 94 16 48 7b 00 00  .........k..H{..
7b48130202e0  09 00 02 00 03 00 01 00 10 00 00 00 00 00 00 00  ................
7b48130202f0  d0 03 02 13 48 7b 00 00 10 0b 02 13 48 7b 00 00  ....H{......H{..
```

Code documents the array as:

```
// This is a two-part array:
//  - [0..number_of_vregs) holds the raw virtual registers, and each element 
//    here is always 4 bytes.
//  - [number_of_vregs..number_of_vregs*2) holds only reference registers. Each
//    element here is ptr-sized.
// In other words when a primitive is stored in vX, the second (reference) part
// of the array will be null. When a reference is stored in vX, the second 
// (reference) part of the array will be a copy of vX.
uint32_t vregs_[0];
```

You now have visibility into all registers.

'''
threadPtr = 135557475466928;

function dump_regs(threadAddr) {
    artThreadShadowFrameOffset = 0xB8;
    artShadowFrameVregOffset = 0x30;

    frame = ptr(threadPtr + artThreadShadowFrameOffset).readPointer();
    vreg_offset = artShadowFrameVregOffset;
    vreg_count = frame.add(0x30).readU32();
    console.log(`vreg cnt: ${vreg_count}d`);
    dex_pc = frame.add(vreg_offset + 0x4).readU32().toString(16);
    console.log(`dex pc: ${dex_pc}h`);
    for (var i = 0; i < vreg_count; ++i) {
        val = frame.add(vreg_offset + 0x10 + (i * 4)).readU32();
        val_hex = val.toString(16).padStart(8, " ");
        val_dec = val.toString(10).padStart(10, " ");
        console.log(`raw v${i}: ${val_hex}h  ${val_dec}d`);
    }
    for (var i = 0; i < vreg_count; ++i) {
        val = frame.add(vreg_offset + 0x10 + (vreg_count * 4) + (i * 4)).readU32();
        val_hex = val.toString(16).padStart(8, " ");
        val_dec = val.toString(10).padStart(10, " ");
        console.log(`ref v${i}: ${val_hex}h  ${val_dec}d`);
    }
}

framePtr = ptr(135557475466928 + 0xB0);
console.log(hexdump(threadPtr, {offset:0, length:256, header: true, ansi: true}))
0x7b49ef2bff60

B0
'''