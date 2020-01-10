
from opcos22 import *
from symtab22 import *
import KBHIT

kbd = KBHIT.KBHit()

symkeys = sorted(symtab.keys())

RAM_SIZE = 0x7000
STACKS_SIZE = 128
SCRATCH_SIZE = 128

TRUE = 0xFFFF
FALSE = 0x0000

ram = [0xFF for i in range(RAM_SIZE)]

stacks = [0xFFFF for i in range(STACKS_SIZE)]

tib = [0 for i in range(SCRATCH_SIZE)]

pad = [0 for i in range(SCRATCH_SIZE)]

pc = 0; ip = 0; w = 0; sp = 0; rp = STACKS_SIZE - 1
up = 0; ir = 0; top = 0; tmp = 0; nxt = False

debug = -1

#debug = 183

def loadHexfile(fName):
    global ram
    objfile = open(fName, 'r')
    objlines = objfile.readlines()
    for objline in objlines:
        listline = objline.split()
        if len(listline):
            loco = int(listline[0], 16)
            listline = listline[1:]
            while len(listline):
                ram[loco] = int(listline[0], 16); loco += 1
                listline = listline[1:]


# ------------------------------------------------------------
# Helper functions

def getw(A):
    return (ram[A] + (ram[A + 1] << 8))

def putw(A, W):
    global ram
    ram[A]     = W & 0xFF
    ram[A + 1] = W >> 8
    return W

def sym(addr):
    for i in range(len(symkeys)):
        if addr < symkeys[i]: break
    if addr == symkeys[i - 1]: delta = ''
    else: delta = '+%d' % (addr - symkeys[i - 1])
    return ('%s%s' % (symtab[symkeys[i - 1]], delta))

def brkpt(header = ''):
    marker = ''
    print(header)
    print('pc=%s(%04x) ir=%s(%02x)%1s ip=%s(%04x) w=%s(%04x) up=%s(%04x)' \
            % (sym(pc), pc, opCodes[ir], ir, marker, \
                sym(ip), ip, sym(w), w, sym(up), up))
    print('PC--> ', end = '')
    for i in range(pc, pc + 8): print('%02x ' % ram[i], end = '')
    print()
    print('IP--> ', end = '')
    for i in range(ip, ip + 8): print('%02x ' % ram[i], end = '')
    print()
    print('DS[%02x]: ' % sp, end = '')
    for i in range(1, sp + 1): print('%04x ' % stacks[i], end = '')
    print()
    print('RS[%02x]: ' % rp, end = '')
    for i in range(STACKS_SIZE-1, rp, -1): print('%04x ' % stacks[i - 1], end = '')
    print()
    print('Debug: %d' % abs(debug))
    print()
    input()

def dump(header = 'OOPS!'):
    print(header)
    print('pc=%04x ir=%02x ip=%04x w=%04x sp=%02x rp=%02x up=%02x' \
            % (pc, ir, ip, w, sp, rp, up))
    print('PC--> ', end = '')
    for i in range(pc, pc + 8): print('%02x ' % ram[i], end = '')
    print()
    print('IP--> ', end = '')
    for i in range(ip, ip + 8): print('%02x ' % ram[i], end = '')
    print()
    print('DS[%02x]: ' % sp, end = '')
    for i in range(1, sp + 1): print('%04x ' % stacks[i], end = '')
    print()
    print('RS[%02x]: ' % rp, end = '')
    for i in range(STACKS_SIZE-1, rp, -1): print('%04x ' % stacks[i - 1], end = '')
    print()
    input()

def push(W):
    global stacks, sp
    sp += 1; stacks[sp] = W

def pop():
    global stacks, sp
    tmp = stacks[sp]; sp -= 1
    return tmp

def rpush(W):
    global stacks, rp
    rp -= 1; stacks[rp] = W

def rpop():
    global stacks, rp
    tmp = stacks[rp]; rp += 1
    return tmp

def lit():
    global pc
    tmp = getw(pc); pc += 2
    return tmp

def add16(X, Y):
    return (X + Y) & 0xFFFF

# ------------------------------------------------------------
# OPCODES

def do_next():
    global pc
    pc += 1

def do_NEXT():
    global ip, w, pc
    w = ram[ip] + (ram[ip + 1] << 8); ip += 2
    pc = ram[w] + (ram[w + 1] << 8); w  += 2

def do_lit():
    global pc
    push(getw(pc)); pc += 2

def do_LIT():
    global ip
    push(getw(ip)); ip += 2

def do_exec():
    global pc
    pc = pop()
    
def do_EXEC():
    global ip
    ip = pop()
    
def do_bran():
    global pc
    pc = add16(pc, getw(pc))

def do_BRAN():
    global ip
    ip = add16(ip, getw(ip))

def do_zbran():
    global pc
    tmp = pop()
    if tmp == 0: pc = add16(pc, getw(pc))
    else: pc += 2

def do_ZBRAN():
    global ip
    tmp = pop()
    if tmp == 0: ip = add16(ip, getw(ip))
    else: ip += 2

def do_XLOOP():
    global stacks, rp, ip
    stacks[rp] += 1
    if stacks[rp] < stacks[rp + 1]:
        ip =  add16(ip, getw(ip))
    else:
        rp += 2
        ip += 2

def do_XPLOO():
    global stacks, rp, ip
    tmp = pop()
    stacks[rp] = add16(stacks[rp], tmp)
    if tmp & 0x8000 and stacks[rp] > stacks[rp + 1]:
        ip =  add16(ip, getw(ip))
    elif stacks[rp] < stacks[rp + 1]:
        ip =  add16(ip, getw(ip))
    else:
        rp += 2
        ip += 2

def do_XDO():
    tmp = pop()
    rpush(pop())
    rpush(tmp)

def do_I():
    push(stacks[rp])

def do_DIGIT():
    base = pop()
    tmp = pop()
    tmp -= 48
    if tmp > 9:
        tmp -= 7
        if tmp < 10: push(FALSE)
        elif tmp >= base: push(FALSE)
    else:
        push(tmp); push(TRUE)

def do_PFIND():
    nfa = pop(); arg = pop(); lby = ram[arg]
    while nfa:
        nflby = ram[nfa] & 0x3F
        if nflby == lby:
            for i in range(1, lby + 1):
                if (ram[nfa + i] & 0x7F) != ram[arg + i]: break
                push(nfa + i + 4)
                push(lby)
                push(TRUE)
                return
        else:
            nfa = getw(nfa + nflby + 1)
    push(FALSE)

def do_ENCL():
    global stacks
    deli = pop()
    addr = stacks[sp]
    i = 0
    while ram[addr + i] == deli: i += 1
    push(i)
    while ram[addr + i] != deli:
        if ram[addr] == 0x00:
            push(i); push(i)
            return
    push(i)
    push(i + 1)

def do_EMIT():
    tmp = pop()
    print('%s' % chr(tmp), end = '')

def do_KEY():
    push(ord(kbd.getch()))

def do_QTERM():
    if kbd.kbhit(): push(TRUE)
    else: push(FALSE)

def do_CR():
    print()

def do_CMOVE():
    global ram
    cnt = pop(); trg = pop(); src = pop()
    for i in range(cnt):
        ram[trg] = ram[src]; src += 1; trg += 1

def do_USTAR():
    res = pop() * pop()
    push(res & 0xFFFF); push(res >> 16)

def do_USLAS():
    U2 = pop(); U1 = pop()
    push(int(U1/U2))
    push(U1%U2)

def do_AND():
    global stacks
    stacks[sp] = pop() & stacks[sp]

def do_OR():
    global stacks
    stacks[sp] = pop() | stacks[sp]

def do_XOR():
    global stacks
    stacks[sp] = pop() ^ stacks[sp]

def do_SPSTO():
    global sp
    sp = 0

def do_RPSTO():
    global rp
    rp = STACKS_SIZE - 1

def do_UPSTO():
    global up
    up = getw(0x0000+16)    # UP = (ORIGIN+18)

def do_semis():
    global pc
    pc = rpop()

def do_SEMIS():
    global ip
    ip = rpop()

def do_LEAVE():
    global stacks
    stacks[rp + 1] = stacks[rp]

def do_TOR():
    rpush(pop())

def do_FROMR():
    push(rpop())

def do_R():
    push(stacks[rp])

def do_ZEQU():
    global stacks
    if stacks[sp] == 0: stacks[sp] = 0xFFFF
    else: stacks[sp] = 0

def do_ZLESS():
    global stacks
    if stacks[sp] & 0x8000: stacks[sp] = 0xFFFF
    else: stacks[sp] = 0
    

def do_PLUS():
    global stacks
    tmp = pop()
    stacks[sp] = add16(stacks[sp], tmp)

def do_DPLUS():
    D1 = pop() << 16 + pop()
    D2 = pop() << 16 + pop()
    Dsum = D1 + D2
    push(Dsum & 0xFFFF); push(Dsum >> 16 & 0xFFFF)

def do_MINUS():
    global stacks
    stacks[sp] = -stacks[sp] & 0xFFFF

def do_DMINU():
    D = pop() << 16 + pop()
    D = -D
    push(D & 0xFFFF); push(D >> 16 & 0xFFFF)

def do_OVER():
    push(stacks[sp - 1])

def do_DROP():
    global sp
    sp -=1

def do_SWAP():
    a = pop(); b = pop()
    push(a); push(b)

def do_DUP():
    push(stacks[sp])

def do_PSTOR():
    global ram
    A = pop()
    ram[A] = add16(ram[A], pop())

def do_TOGGL():
    global ram
    pattern = pop(); A = pop()
    ram[A] = ram[A] ^ pattern

def do_AT():
    global stacks
    stacks[sp] = getw(stacks[sp])

def do_CAT():
    global stacks
    stacks[sp] = ram[stacks[sp]]

def do_STORE():
    global sp
    putw(stacks[sp], stacks[sp - 1]); sp -= 2

def do_CSTOR():
    global ram, sp
    ram[stacks[sp]] = stacks[sp - 1] & 0xFF; sp -= 2

def do_ONEP():
    global stacks
    stacks[sp] += 1

def do_TWOP():
    global stacks
    stacks[sp] += 2

def do_docol():
    global pc
    rpush(pc + 2)
    pc = getw(ram[pc])

def do_DOCOL():
    global ip
    rpush(ip)
    ip = w

def do_DOCON():
    push(getw(w))

def do_DOVAR():
    push(w)

def do_DOUSE():
    push(up + getw(w))

def do_DODOE():
    global ip, w
    rpush(ip)
    ip = getw(w); w += 2
    push(w)

def do_STOD():
    if stacks[sp] & 0x8000: push(0xFFFF)
    else: push(0x0000)

def do_MSTAR():
    n+++

def do_MSLAS():
    n+++

def do_RW():
    n+++


# ------------------------------------------------------------
# THE ACTUAL INNER INTERPRETER

def do_op(opc):
    global debug, nxt
    if debug == 0: brkpt('do_op() entry')
    try:
        switcher = {
            0x00: do_next,
            0x80: do_NEXT,
            0x01: do_lit,
            0x81: do_LIT,
            0x02: do_exec,
            0x82: do_EXEC,
            0x03: do_bran,
            0x83: do_BRAN,
            0x04: do_zbran,
            0x84: do_ZBRAN,
            0x05: do_XLOOP,
            0x85: do_XLOOP,
            0x06: do_XPLOO,
            0x86: do_XPLOO,
            0x07: do_XDO,
            0x87: do_XDO,
            0x08: do_I,
            0x88: do_I,
            0x09: do_DIGIT,
            0x89: do_DIGIT,
            0x0A: do_PFIND,
            0x8A: do_PFIND,
            0x0B: do_ENCL,
            0x8B: do_ENCL,
            0x0C: do_EMIT,
            0x8C: do_EMIT,
            0x0D: do_KEY,
            0x8D: do_KEY,
            0x0E: do_QTERM,
            0x0E: do_QTERM,
            0x0F: do_CR,
            0x8F: do_CR,
            0x10: do_CMOVE,
            0x90: do_CMOVE,
            0x11: do_USTAR,
            0x91: do_USTAR,
            0x12: do_USLAS,
            0x92: do_USLAS,
            0x13: do_AND,
            0x93: do_AND,
            0x14: do_OR,
            0x94: do_OR,
            0x15: do_XOR,
            0x95: do_XOR,
            0x17: do_SPSTO,
            0x97: do_SPSTO,
            0x18: do_RPSTO,
            0x98: do_RPSTO,
            0x19: do_UPSTO,
            0x99: do_UPSTO,
            0x1A: do_semis,
            0x9A: do_SEMIS,
            0x1B: do_LEAVE,
            0x9B: do_LEAVE,
            0x1C: do_TOR,
            0x9C: do_TOR,
            0x1D: do_FROMR,
            0x9D: do_FROMR,
            0x1E: do_R,
            0x9E: do_R,
            0x1F: do_ZEQU,
            0x9F: do_ZEQU,
            0x20: do_ZLESS,
            0xA0: do_ZLESS,
            0x21: do_PLUS,
            0xA1: do_PLUS,
            0x22: do_DPLUS,
            0xA2: do_DPLUS,
            0x23: do_MINUS,
            0xA3: do_MINUS,
            0x24: do_DMINU,
            0xA4: do_DMINU,
            0x25: do_OVER,
            0xA5: do_OVER,
            0x26: do_DROP,
            0xA6: do_DROP,
            0x27: do_SWAP,
            0xA7: do_SWAP,
            0x28: do_DUP,
            0xA8: do_DUP,
            0x29: do_PSTOR,
            0xA9: do_PSTOR,
            0x2A: do_TOGGL,
            0xAA: do_TOGGL,
            0x2B: do_AT,
            0xAB: do_AT,
            0x2C: do_CAT,
            0xAC: do_CAT,
            0x2D: do_STORE,
            0xAD: do_STORE,
            0x2E: do_CSTOR,
            0xAE: do_CSTOR,
            0x2F: do_ONEP,
            0xAF: do_ONEP,
            0x30: do_TWOP,
            0xB0: do_TWOP,
            0x31: do_docol,
            0xB1: do_DOCOL,
            0xB2: do_DOCON,
            0x33: do_DOVAR,
            0xB3: do_DOVAR,
            0x34: do_DOUSE,
            0xB4: do_DOUSE,
            0x35: do_DODOE,
            0xB5: do_DODOE,
            0x36: do_STOD,
            0xB6: do_STOD,
            0x37: do_MSTAR,
            0xB7: do_MSTAR,
            0x38: do_MSLAS,
            0xB8: do_MSLAS,
            0x39: do_RW,
            0xB9: do_RW,
        }
        func = switcher.get(opc)
        func()
        if opc & 0x80: do_NEXT()
    except:
        dump('*** WARNING ***')
#    if debug == 0: brkpt('do_op() exit')
    if debug > 0: debug -= 1

def execute():
    global pc, ir
    while (True):
        ir = ram[pc]; pc += 1
        do_op(ir)

loadHexfile('forth22.hex')
execute()

