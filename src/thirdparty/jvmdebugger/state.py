
from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, ThreadID
from pydantic import BaseModel
from typing import Optional, List, Tuple

class ThreadInfo():
    threadID: Optional[ThreadID] = None
    pass

class ClassInfo(BaseModel):
    refTypeTag: Optional[Byte] = None
    typeID: Optional[ReferenceTypeID] = None
    signature: Optional[String] = None
    generic: Optional[String] = None

class JvmDebuggerState():
  def __init__(self):
    self.jdwp = None

    self.classes_by_id = {}
    self.classes_by_signature = {}

    # TODO: What is the best way to store unloaded classes, consider recycled signatures and ids.
    self.unloaded_classes = []

    self.threads_by_id = {}
    #self.thread_by_name = {}
    self.dead_threads = []