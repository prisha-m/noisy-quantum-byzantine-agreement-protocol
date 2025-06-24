
from netqasm.sdk.connection import BaseNetQASMConnection
from netqasm.sdk.qubit import Qubit

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from squidasm.util.routines import teleport_send, teleport_recv

from time import sleep, time

class S(Program):
    def __init__(self):
        pass

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="S",
            csockets=["R"],
            epr_sockets=["R"],
            max_qubits=4,
        )

    def run(self, context: ProgramContext):
        q0, q1, q2, q3 = self.create_shared_state(context.connection)
        yield from context.connection.flush()
        print("Shared state created")

        yield from teleport_send(q2, context, peer_name="R")
        yield from teleport_send(q3, context, peer_name="R")

        q0 = q0.measure()
        q1 = q1.measure()
        yield from context.connection.flush()

        print(f"Qubit measurements: {q0}, {q1}")

        return int(q0), int(q1)



        
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
    
class R(Program):
    def __init__(self):
        pass

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="R",
            csockets=["S"],
            epr_sockets=["S"],
            max_qubits=4,
        )

    def run(self, context: ProgramContext):
        print("Receiver program running")
        q2 = yield from teleport_recv(context, peer_name="S")
        q3 = yield from teleport_recv(context, peer_name="S")
        yield from context.connection.flush()  # Simulate some processing

        q2 = q2.measure()
        q3 = q3.measure()
        yield from context.connection.flush()

        print(f"Receiver measurements: {q2}, {q3}")

        return int(q2), int(q3)