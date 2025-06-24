
from netqasm.sdk.qubit import Qubit

from program_conditions import ProgramConditions
from constants import DOMAIN_VIOLATION, ABORT

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from squidasm.util.routines import teleport_recv

class Receiver1Program(Program):
    

    def __init__(self, parameters: ProgramConditions):
        self.parameters = parameters
        self.qubits = [None] * self.parameters.m
        self.xs = None
        self.PEER_SENDER = "Sender"
        self.PEER_RECEIVER0 = "Receiver0"

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="byzantine_agreement",
            csockets=[self.PEER_SENDER, self.PEER_RECEIVER0],
            epr_sockets=[self.PEER_SENDER, self.PEER_RECEIVER0],
            max_qubits=4,
        )
    
    def run(self, context: ProgramContext):
        # get classical sockets
        csocket_s = context.csockets[self.PEER_SENDER]
        csocket_r0 = context.csockets[self.PEER_RECEIVER0]

        connection = context.connection

        # INVOCATION PHASE

        self.xs = yield from csocket_s.recv()

        if self.parameters.print_status: print(f"Receiver1: Receives xs bit {self.xs} from Sender")

        # CHECK PHASE

        consistency_count = 0

        for i in range(self.parameters.m):
            q3 = yield from teleport_recv(context, peer_name=self.PEER_SENDER)
            q3 = q3.measure()
            self.qubits[i] = q3   

        check_set = yield from csocket_s.recv()
        yield from connection.flush()
        if self.parameters.print_status: print(f"Receiver1: Receives check set {check_set} from Sender")

        for i in check_set:
            if self.parameters.print_status: print(f"Receiver1: Measures {self.qubits[i]} at index {i} in the check set")
            if self.qubits[i] != self.xs:
                consistency_count += 1
        
        if len(check_set) < self.parameters.t:
            if self.parameters.print_status: print("Receiver1: check set does not meet the length condition")
            self.xs = ABORT
        
        if len(check_set) == 0 or consistency_count < len(check_set):
            if self.parameters.print_status: print(f"Receiver1: check set does not meet the consistency condition")
            self.xs = ABORT

        # CROSS-CALLING PHASE

        xs_r0 = yield from csocket_r0.recv()
        check_set_r0 = yield from csocket_r0.recv()
        yield from connection.flush()
        if self.parameters.print_status: print(f"Receiver1: Receives xs bit {xs_r0} from Receiver0")
        if self.parameters.print_status: print(f"Receiver1: Receives check set {check_set_r0} from Receiver0")

        # CROSS-CHECK PHASE

        consistency_count = 0

        for i in range(len(check_set_r0)):
            if self.qubits[check_set_r0[i]] == 1 - xs_r0:
                consistency_count += 1

        # case y1 = y01
        if self.xs != xs_r0 and self.xs != ABORT and xs_r0 != ABORT and len(check_set_r0) >= self.parameters.t and consistency_count >= self.parameters.l * self.parameters.t + len(check_set_r0) - self.parameters.t:
            if self.parameters.print_status: print(f"Receiver1: value agreed on is {xs_r0}")
            return {xs_r0}
        # case y1 = ~y1
        else:
            if self.parameters.print_status: print(f"Receiver1: value agreed on is {self.xs}")
            return {self.xs}