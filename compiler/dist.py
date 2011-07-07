from .base import InsertSelf, ProcessMembers, ProcessRun
from .info import ClassInfo
from .send import SendTransformer
from .await import AwaitTransformer
from .event import EventTransformer
from .label import LabelTransformer
from .mesgcomp import SentReceivedTransformer

from ast import *

DISTALGO_BASE_CLASS = "DistProcess"

class DistalgoTransformer(NodeTransformer):
    """The main driver transformer for DisAlgo.
    """

    def visit_ClassDef(self, node):
        if (self.isPClass(node)):
            return self.processPClass(node)
        else:
            return self.processClass(node)

    def isPClass(self, node):
        """Checks whether the class defined by 'node' is a P(rocess)Class.

        A PClass is any class that is derived from 'DisProcess'.
        """
        result = False
        for b in node.bases:
            if (isinstance(b, Name)):
                if (b.id == "DistProcess"):
                    result = True
                    break
        return result

    def processClass(self, node):
        """Compiles a normal class.

        For normal (non-P) classes we simply support omitting the 'self'
        identifier before member references.
        """
        info = ClassInfo(node.name)

        # 1. gather member funcs and vars
        ProcessMembers(info).visit(node)

        # 2. Take care of 'self'
        iself = InsertSelf(info)
        node = iself.visit(node)

        return node
        

    def processPClass(self, node):
        """Transforms a DisProcess Class.
        """
        info = ClassInfo(node.name)
        info.memberfuncs.add("work")
        info.memberfuncs.add("send")
        info.memberfuncs.add("receive")
        info.memberfuncs.add("output")
        info.memberfuncs.add("logical_clock")
        info.memberfuncs.add("incr_logical_clock")

        # 0. gather member funcs and vars
        ProcessMembers(info).visit(node)

        node = SendTransformer(info).visit(node)

        # 1. Transform query primitives 'sent' and 'received'
        node = SentReceivedTransformer(info).visit(node)

        # 2. Transform 'await'
        node = AwaitTransformer(info).visit(node)

        # 3. Transform and gather labels
        node = LabelTransformer(info).visit(node)

        # 4. Transform and gather events
        node = EventTransformer(info).visit(node)

        # 5. Add in new member funcs
        node.body.extend(info.newdefs)

        # 6. Take care of 'self'
        node = InsertSelf(info).visit(node)

        # 7. Generate the __init__ method
        node.body.insert(0, self.genInitFunc(info))

        return node

    def genInitFunc(self, inf):
        body = []
        body.append(Call(Attribute(Name("DistProcess", Load()),
                                   "__init__", Load()),
                         [Name("self", Load()), Name("pid", Load()),
                          Name("pipe", Load()), Name("perf_pipe", Load())],
                         [], None, None))
        body.append(inf.genEventPatternStmt())
        body.append(inf.genSentPatternStmt())
        body.append(inf.genLabelEventsStmt())
        body.extend(inf.newstmts)

        arglist = [arg("self", None), arg("pid", None), arg("pipe", None),
                   arg("perf_pipe", None)]
        args = arguments(arglist, None, None, [], None,
                         None, [], None)
        return FunctionDef("__init__", args, body, [], None)


##########
