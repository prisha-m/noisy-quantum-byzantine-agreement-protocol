from math import ceil

class ProgramConditions:
    
    def __init__(self, _m, _x, _u = 0.272, _l = 0.94, _s_faulty = False, _r0_faulty = False, _print_status = False, _p = 0.5):
  
        self.m = _m
        self.u = _u
        self.l = _l
        self.s_faulty = _s_faulty
        self.r0_faulty = _r0_faulty
        self.x = _x

        self.f = 0
        self.t = ceil(self.m * self.u)

        self.print_status = _print_status

        self.p = _p
        

