from .consts import *
from .exceptions import InvalidAwaitException

from ast import *

class AwaitTransformer(NodeTransformer):
    """Translates 'await' statements.
    """

    def __init__(self, info):
        NodeTransformer.__init__(self)
        self.counter = 0

    def visit_Expr(self, node):
        if (not (isinstance(node.value, Call) and 
                 isinstance(node.value.func, Name) and
                 node.value.func.id == "await")):
            return node

        self.counter += 1
        timerVar = TIMER_VARNAME + str(self.counter)

        # We only deal with one await cond (plus timeout) for now:
        if (len(node.value.args) > 2):
            raise InvalidAwaitException()

        body = []
        # Invert the await condition
        op = node.value.args[0]
        cond = UnaryOp(Not(), op)

        # _process_event_(_event_patterns, True)
        whilebody = [Expr(Call(Name(EVENT_PROC_FUNNAME, Load()),
                               [Name(EVENT_PATTERN_VARNAME, Load()),
                                Name("True", Load())],
                               [], None, None))]

        if (len(node.value.args) > 1):
            # __await_timer_N = time.time()
            timerdef = Assign([Name(timerVar, Store())],
                              Call(Attribute(Name("time", Load()),
                                             "time", Load()),
                                   [], [], None, None))

            # _timeout = False
            timeoutdef = Assign([Name(TIMEOUT_VARNAME, Store())],
                                Name("False", Load()))

            body.append(timerdef)
            body.append(timeoutdef)
            
            # if (time.time() - __await_timer_N > TIMEOUT):
            #     _timeout = True
            #     break
            breakcond = Compare(BinOp(Call(Attribute(Name("time", Load()),
                                                     "time", Load()),
                                           [], [], None, None),
                                      Sub(), Name(timerVar, Load())),
                                [Gt()], [node.value.args[1]])
            breakbody = [Assign([Name(TIMEOUT_VARNAME, Store())],
                                Name("True", Load())),
                         Break()]
            whilebody.append(If(breakcond, breakbody, []))

        whilestmt = While(cond, whilebody, [])
        body.append(whilestmt)

        # TODO: clean up message queue here??
        # rsf = AwaitTransformer.RecvStmtFinder()
        # rsf.visit(node)
        # if (len(rsf.recvs) > 0):
        #     cleanup = [Assign([Name(v, Load())],
        #                       Call(Name("set", Load()), [], [], None, None))
        #                for v in rsf.recvs]
        #     body.extend(cleanup)

        return body
