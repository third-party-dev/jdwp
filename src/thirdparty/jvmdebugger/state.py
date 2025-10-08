
from thirdparty.jdwp import Jdwp, Byte, Boolean, Int, String, ReferenceTypeID, ThreadID, MethodID, ClassID, FieldID
from pydantic import BaseModel
from typing import Optional, List, Tuple






class FieldInfo():
    fieldID: Optional[FieldID] = None
    name: Optional[String] = None
    signature: Optional[String] = None
    modBits: Optional[Int] = None

class MethodInfo():
    methodID: Optional[MethodID] = None
    name: Optional[String] = None
    signature: Optional[String] = None
    modBits: Optional[Int] = None

    bytecode = None

class ClassInfo():
    refTypeTag: Optional[Byte] = None
    typeID: Optional[ReferenceTypeID] = None
    signature: Optional[String] = None
    generic: Optional[String] = None

    methods_by_id = {}
    methods_by_name = {} # unused?
    methods_by_signature = {}

    fields_loaded = False
    fields_by_id = {}
    fields_by_signature = {}
    #fields_by_name = {}



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