

from netqasm.sdk.connection import BaseNetQASMConnection
from netqasm.sdk.qubit import Qubit

from program_conditions import ProgramConditions
from constants import DOMAIN_VIOLATION

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from squidasm.util.routines import teleport_send

import random
from math import ceil

class SenderProgram(Program):

    def __init__(self, parameters: ProgramConditions):
        self.parameters = parameters
        self.xs = parameters.x
        self.PEER_RECEIVER0 = "Receiver0"
        self.PEER_RECEIVER1 = "Receiver1"

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="byzantine_agreement",
            csockets=[self.PEER_RECEIVER0, self.PEER_RECEIVER1],
            epr_sockets=[self.PEER_RECEIVER0, self.PEER_RECEIVER1],
            max_qubits=4,
        )

    def run(self, context: ProgramContext):
        # get classical sockets
        csocket_r0 = context.csockets[self.PEER_RECEIVER0]
        csocket_r1 = context.csockets[self.PEER_RECEIVER1]

        connection = context.connection

        x0, x1 = self.parameters.x, self.parameters.x

        if self.parameters.s_faulty:
            x1 = 1 - x1

        csocket_r0.send(x0)
        csocket_r1.send(x1)
        if self.parameters.print_status: print(f"Sender: Sends xs bit {x0} to Receiver0 and {x1} to Receiver1")

        # INVOCATION PHASE

        check_set_0, check_set_1 = [], []
        l1, l2, l3 = [], [], []
        q0_futures, q1_futures = [None] * self.parameters.m, [None] * self.parameters.m

        for i in range(self.parameters.m):
            q0, q1, q2, q3 = self.create_shared_state(connection)

            yield from teleport_send(q2, context, peer_name=self.PEER_RECEIVER0)
            yield from teleport_send(q3, context, peer_name=self.PEER_RECEIVER1)

            q0_futures[i] = q0.measure()
            q1_futures[i] = q1.measure()

        yield from connection.flush()

        for i in range(self.parameters.m):
            q0 = q0_futures[i]
            q1 = q1_futures[i]

            if self.parameters.print_status: print(f"Sender: Sender measures qubits {q0}{q1}")

            if q0 == self.xs and q1 == self.xs:
                l1.append(i) 
            elif q0 != self.xs and q1 != self.xs:
                l3.append(i)
            else:
                l2.append(i)

        is_domain_violation = False

        if self.parameters.s_faulty:
            q = self.parameters.t - ceil(self.parameters.l * self.parameters.t) + 1

            domain_check = self.parameters.t - q <= len(l1) and q <= len(l2) and self.parameters.t <= len(l3)

            if domain_check:
                if q > 0: 
                    check_set_0 = random.sample(l2, q) 
                if self.parameters.t - q > 0: 
                    check_set_0 += random.sample(l1, self.parameters.t - q)
            else: 
                is_domain_violation = True # Domain failure
                
            check_set_1 = l3
        else:
            check_set_0 = l1
            check_set_1 = l1

        csocket_r0.send(check_set_0)
        csocket_r1.send(check_set_1)
        if self.parameters.print_status: print(f"Sender: Sends check set {check_set_0} to Receiver0 and {check_set_1} to Receiver1")
        
        if is_domain_violation:
            return {DOMAIN_VIOLATION}

        return {self.xs}
    
    
    def create_shared_state(self, connection: BaseNetQASMConnection):
        q0 = Qubit(connection)
        q1 = Qubit(connection)
        q2 = Qubit(connection)
        q3 = Qubit(connection)

        q0.H()
        q0.rot_Z(angle=-0.73304)

        q1.H()

        q2.H()
        q2.rot_Z(angle=2.67908)

        q2.cnot(q0)

        q0.rot_Y(angle=-2.67908)

        q2.H()

        q1.cnot(q0)
        q2.cnot(q3)

        q2.rot_Z(angle=1.5708)
        
        q1.cnot(q3)
        q0.cnot(q2)

        return q0, q1, q2, q3
    
    