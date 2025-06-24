
import random

from netqasm.sdk.qubit import Qubit

from program_conditions import ProgramConditions
from constants import DOMAIN_VIOLATION, ABORT

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from squidasm.util.routines import teleport_recv

class Receiver0Program(Program):

    def __init__(self, parameters: ProgramConditions):
        self.parameters = parameters
        self.qubits = [None] * self.parameters.m
        self.xs = None
        self.PEER_SENDER = "Sender"
        self.PEER_RECEIVER1 = "Receiver1"

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="byzantine_agreement",
            csockets=[self.PEER_SENDER, self.PEER_RECEIVER1],
            epr_sockets=[self.PEER_SENDER, self.PEER_RECEIVER1],
            max_qubits=4,
        )
    
    def run(self, context: ProgramContext):
        # get classical sockets
        csocket_s = context.csockets[self.PEER_SENDER]
        csocket_r1 = context.csockets[self.PEER_RECEIVER1]

        connection = context.connection

        # INVOCATION PHASE

        self.xs = yield from csocket_s.recv()

        if self.parameters.print_status: print(f"Receiver0: Receives xs bit {self.xs} from Sender")

        # CHECK PHASE

        consistency_count = 0

        for i in range(self.parameters.m):
            q2 = yield from teleport_recv(context, peer_name=self.PEER_SENDER)
            q2 = q2.measure()
            self.qubits[i] = q2     

        check_set = yield from csocket_s.recv()
        yield from connection.flush()
        if self.parameters.print_status: print(f"Receiver0: Receives check set {check_set} from Sender")

        for i in check_set:
            if self.parameters.print_status: print(f"Receiver0: Measures {self.qubits[i]} at index {i} in the check set")
            if self.qubits[i] != self.xs:
                consistency_count += 1

        if len(check_set) < self.parameters.t:
            if self.parameters.print_status: print(f"Receiver0: check set does not meet the length condition {len(check_set)} < {self.parameters.t}")
            self.xs = ABORT

        if len(check_set) == 0 or consistency_count < len(check_set):
            if self.parameters.print_status: print(f"Receiver0: check set does not meet the consistency condition")
            self.xs = ABORT
            
        # CROSS-CALLING PHASE
        
        is_domain_violation = False

        if self.parameters.r0_faulty:
            # if r0 is faulty adjust the set & x value
            l1, l2, l3 = [], [], []
            for i in range(len(self.qubits)):
                q = self.qubits[i]
                if not i in check_set and q != self.xs:
                    l2.append(i)
                elif q == self.xs:
                    l3.append(i)
                else:
                    l1.append(i)

            self.xs = 1 - self.xs
            if self.xs == ABORT:
                self.xs = 1

            check_set = l2 

            nmin = self.parameters.t - len(l2) if len(l2) < self.parameters.t else 0 
            if len(l1) <= self.parameters.m - self.parameters.t: 
                check_set += random.sample(l3, nmin)
            else: 
                is_domain_violation = True  # Domain failure     

        csocket_r1.send(self.xs)
        csocket_r1.send(check_set)
        if self.parameters.print_status: print(f"Receiver0: Sends xs bit {self.xs} to Receiver1")
        if self.parameters.print_status: print(f"Receiver0: Sends check set {check_set} to Receiver1")

        if is_domain_violation:
            return {DOMAIN_VIOLATION}

        return {self.xs}