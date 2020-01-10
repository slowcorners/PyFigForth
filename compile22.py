RAM_SIZE    = 0x7000        # 28672 bytes of RAM
UAREA_SIZE  = 64            # Room for 32 user variables
TIB_SIZE    = 128
DSKBUF_SIZE = 1028
DSKBUF_NUM  = 3

NXT         = 0x80          # Autonext bit in opcodes

UPPERAREA_SIZE = \
            UAREA_SIZE + \
            DSKBUF_NUM * DSKBUF_SIZE +\
            TIB_SIZE

loco = 0
latest = 0

ram = {}
src = {}
symtab = {}
vlist = ''

prims = 0; precomps = 0

# ----------------------
# OpCodes

op = -1
opCodes = {}

def nextOp():
	global op
	op += 1
	return op

# ----------------------
# Symbol Table

def label(name):
	if name in symtab:
		if type(symtab[name]) == type([]):
			for backref in symtab[name]:
				if backref[1]:
					putw(backref[0], (loco - backref[0]))
				else:
					putw(backref[0], loco)
			symtab[name] = loco
		else:
			print('Error: Label %s redefined.' % name)
	else:
		symtab[name] = loco

def addr(label, rel = False):
	if label in symtab:
		if type(symtab[label]) == type(0):
			if rel:
				dw(symtab[label] - loco)
			else:
				dw(symtab[label])
		else:
			symtab[label].append((loco, rel))
			dw(0xffff)
	else:
		symtab[label] = [(loco, rel)]
		dw(0xffff)

def offset(label):
	addr(label, True)

def words(forthline):
	source(loco, ('  .. %s' % forthline))
	while len(forthline):
		spc = forthline.find(' ')
		if spc > -1:
			word = forthline[:spc]; forthline = forthline[spc + 1:]
		else:
			word = forthline; forthline = ''
		if len(word): addr(word)

def getw(addr):
	return (ram[addr] + (ram[addr+1] << 8))

def putb(addr, data8):
	global ram
	ram[addr] = data8 & 0xff

def putw(addr, data16):
	global ram
	ram[addr] = data16 & 0xff
	ram[addr+1] = data16 >> 8 & 0xff

def org(addr):
	global loco
	loco = addr

def ds(size):
    global loco
    loco += size

def db(byte):
	global loco
	putb(loco, byte); loco += 1

def dw(word):
	global loco
	putw(loco, word); loco += 2

def ch(char):
	db(ord(char))

def string(str):
    source(loco, '    "%s"' % str)
    for c in str: ch(c)

def source(addr, string):
    src[addr] = string

def note(text):
    global loco
    source(loco, '-- ' + text)

def prim(wordName, name):
    global loco, latest, opCodes, vlist, prims
    vlist = vlist + wordName + ' '
    prims += 1
    opCode = nextOp()
    opCodes[name] = opCode
    thisHeader	= loco
    source(loco, '* %s' % wordName)
    wn = wordName
    db(len(wn) | 0x80)
    while len(wn) > 1:
        db(ord(wn[0]))
        wn = wn[1:]
    db(ord(wn[0]) | 0x80)
    dw(latest)
    latest = thisHeader
    label(name)
    dw(loco + 2)
    db(opCode | NXT)                            # NOTE! All primaries end by calling next by default

def precomp(wordName, name, imm = False):
    global loco, latest
    global vlist, precomps
    vlist = vlist + wordName + ' '
    precomps += 1
    thisHeader = loco
    source(loco, ': %s' % wordName)
    wn = wordName
    if imm: db(len(wn) | 0xC0)
    else: db(len(wn) | 0x80)
    while len(wn) > 1:
        db(ord(wn[0]))
        wn = wn[1:]
    db(ord(wn[0]) | 0x80)
    dw(latest)
    latest = thisHeader
    label(name)



# --------------------------------------------------------------------------------
# The Actual FORTH


# --------------------
# Boot Up Table

org(0);             note('BOOT AREA')
label('ORIGIN')

note('Cold start entry point')
db(0x01); addr('COLD'); db(0x82)            # lit <COLD> EXEC
note('Warm start entry point')
db(0x01); addr('ABORT'); db(0x82)           # lit <ABORT> EXEC

note('Processor type in radix 36'); dw(22)              #  8
note('Revision'); dw(0)                                 # 10
note('Pointer to latest word defined'); addr('HFORT')   # 12
note('Backspace character'); dw(8)                      # 14
note('Pointer to user area'); addr('XUP')               # 16
note('Initial SP (index into STACKS array)'); dw(0)     # 18
note('Initial RP (index into STACKS array)'); dw(0x7F)  # 20
note('Pointer to terminal input buffer'); addr('XTIB')  # 22
note('Maximum name field width'); dw(31)                # 24
note('Initial warning mode 0:err# 1:diskMessage'); dw(0)            # 26
note('Default fence against accidental FORGET'); addr('XDP')        # 28
note('Pointer to next available dictionary location'); addr('XDP')  # 30
note('Pointer to initial vocabulary link'); addr('XXVOC')           # 32
note('Initial FIRST'); addr('DSKBUF')       # 34
note('Initial LIMIT'); addr('ENDBUF')       # 36
note('Available'); dw(0)
note('Available'); dw(0)



org(42)

# --------------------
# Nucleus

prim('NEXT', 'NEXT');           prim('LIT', 'LIT')
prim('EXECUTE', 'EXEC');		prim('BRANCH', 'BRAN')
prim('0BRANCH', 'ZBRAN');		prim('(LOOP)', 'XLOOP')
prim('(+LOOP)', 'XPLOO');		prim('(DO)', 'XDO')
prim('I', 'I');                 prim('DIGIT', 'DIGIT')
prim('(FIND)', 'PFIND');		prim('ENCLOSE', 'ENCL')
prim('EMIT', 'EMIT');			prim('KEY', 'KEY')
prim('?TERMINAL', 'QTERM');	    prim('CR', 'CR')
prim('CMOVE', 'CMOVE');		    prim('U*', 'USTAR')
prim('U/', 'USLAS');			prim('AND', 'AND')
prim('OR', 'OR');				prim('XOR', 'XOR')
prim('SP@', 'SPAT');			prim('SP!', 'SPSTO')
prim('RP!', 'RPSTO');           prim('UP!', 'UPSTO');
prim(';S', 'SEMIS')
prim('LEAVE', 'LEAVE');		    prim('>R', 'TOR')
prim('R>', 'FROMR');			prim('R', 'R')
prim('0=', 'ZEQU');			    prim('0<', 'ZLESS')
prim('+', 'PLUS');			    prim('D+', 'DPLUS')
prim('MINUS', 'MINUS');		    prim('DMINUS', 'DMINU')
prim('OVER', 'OVER');			prim('DROP', 'DROP')
prim('SWAP', 'SWAP');			prim('DUP', 'DUP')
prim('+!', 'PSTOR');			prim('TOGGLE', 'TOGGL')
prim('@', 'AT');				prim('C@', 'CAT')
prim('!', 'STORE');			    prim('C!', 'CSTOR')
prim('1+', 'ONEP');			    prim('2+', 'TWOP')

opCodes['DOCOL'] = nextOp();			opCodes['DOCON'] = nextOp();
opCodes['DOVAR'] = nextOp();			opCodes['DOUSE'] = nextOp();
opCodes['DODOE'] = nextOp();



# --------------------
# Borderline Precompiled

precomp(':', 'COLON', True)
words('DOCOL QEXEC SCSP CURR AT CONT STORE CREAT RBRAC PSCOD')
label('DOCOL'); db(opCodes['DOCOL'] | NXT)

precomp(';', 'SEMIC', True)
words('DOCOL QCSP COMP SEMIS SMUDG LBRAC SEMIS')

precomp('CONSTANT', 'CON')
words('DOCOL CREAT SMUDG COMMA PSCOD')
label('DOCON'); db(opCodes['DOCON'] | NXT);

precomp('VARIABLE', 'VAR')
words('DOCOL CON PSCOD')
label('DOVAR'); db(opCodes['DOVAR'] | NXT);

precomp('USER', 'USER')
words('DOCOL CON PSCOD')
label('DOUSE'); db(opCodes['DOUSE'] | NXT);



# ---------------------
# Misc Constants

precomp('0', 'ZERO'); words('DOCON'); dw(0)
precomp('1', 'ONE'); words('DOCON'); dw(1)
precomp('2', 'TWO'); words('DOCON'); dw(2)
precomp('3', 'THREE'); words('DOCON'); dw(3)
precomp('BL', 'BL'); words('DOCON'); dw(32)
precomp('C/L', 'CL'); words('DOCON'); dw(64)
precomp('B/BUF', 'BBUF'); words('DOCON'); dw(1024)
precomp('B/SCR', 'BSCR'); words('DOCON'); dw(1)

precomp('+ORIGIN', 'PORIG')
words('DOCOL LIT'); addr('ORIGIN'); words('PLUS SEMIS')



# ---------------------
# User Variables

precomp('S0', 'SZERO'); words('DOUSE'); dw(6)
precomp('R0', 'RZERO'); words('DOUSE'); dw(8)
precomp('TIB', 'TIB'); words('DOUSE'); dw(10)
precomp('WIDTH', 'WIDTH'); words('DOUSE'); dw(12)
precomp('WARNING', 'WARN'); words('DOUSE'); dw(14)
precomp('FENCE', 'FENCE'); words('DOUSE'); dw(16)
precomp('DP', 'DP'); words('DOUSE'); dw(18)
precomp('VOC-LINK', 'VOCL'); words('DOUSE'); dw(20)
precomp('FIRST', 'FIRST'); words('DOUSE'); dw(22)
precomp('LIMIT', 'LIMIT'); words('DOUSE'); dw(24)
# Positions 26 and 28 are reserved for future use
precomp('BLK', 'BLK'); words('DOUSE'); dw(30)
precomp('IN', 'IN'); words('DOUSE'); dw(32)
precomp('OUT', 'OUT'); words('DOUSE'); dw(34)
precomp('SCR', 'SCR'); words('DOUSE'); dw(36)
precomp('OFFSET', 'OFSET'); words('DOUSE'); dw(38)
precomp('CONTEXT', 'CONT'); words('DOUSE'); dw(40)
precomp('CURRENT', 'CURR'); words('DOUSE'); dw(42)
precomp('STATE', 'STATE'); words('DOUSE'); dw(44)
precomp('BASE', 'BASE'); words('DOUSE'); dw(46)
precomp('DPL', 'DPL'); words('DOUSE'); dw(48)
precomp('FLD', 'FLD'); words('DOUSE'); dw(50)
precomp('CSP', 'CSP'); words('DOUSE'); dw(52)
precomp('R#', 'RNUM'); words('DOUSE'); dw(54)
precomp('HLD', 'HLD'); words('DOUSE'); dw(56)
precomp('USE', 'USE'); words('DOUSE'); dw(58)
precomp('PREV', 'PREV'); words('DOUSE'); dw(60)



# ---------------------
# Lower Level Precompiled

precomp('HERE', 'HERE'); words('DOCOL DP AT SEMIS')
precomp('ALLOT', 'ALLOT'); words('DOCOL DP PSTOR SEMIS')
precomp(',', 'COMMA'); words('DOCOL HERE STORE TWO ALLOT SEMIS')
precomp('-', 'SUB'); words('DOCOL MINUS PLUS SEMIS')
precomp('=', 'EQUAL'); words('DOCOL SUB ZEQU SEMIS')
precomp('<', 'LESS'); words('DOCOL SUB ZLESS SEMIS')
precomp('>', 'GREAT'); words('DOCOL SWAP LESS SEMIS')
precomp('ROT', 'ROT'); words('DOCOL TOR SWAP FROMR SWAP SEMIS')
precomp('SPACE', 'SPACE'); words('DOCOL BL EMIT SEMIS')

precomp('-DUP', 'DDUP');
words('DOCOL DUP ZBRAN'); offset('DDU10')
words('DUP')
label('DDU10'); words('SEMIS')



# ---------------------
# FORTH word header traversing

precomp('TRAVERSE', 'TRAV')
words('DOCOL SWAP')
label('TRA10'); words('OVER PLUS LIT'); dw(0x7f)
words('OVER CAT LESS ZBRAN'); offset('TRA10')
words('SWAP DROP SEMIS')

precomp('LATEST', 'LATES')
words('DOCOL CURR AT AT SEMIS')

precomp('LFA', 'LFA')
words('DOCOL LIT'); dw(4); words('SUB SEMIS')

precomp('CFA', 'CFA')
words('DOCOL TWO SUB SEMIS')

precomp('NFA', 'NFA')
words('DOCOL LIT'); dw(5); words('SUB LIT'); dw(-1); words('TRAV SEMIS')

precomp('PFA', 'PFA')
words('DOCOL ONE TRAV LIT'); dw(5); words('PLUS SEMIS')



# ---------------------
# Compile Time Error Checks

precomp('!CSP', 'SCSP')
words('DOCOL SPAT CSP STORE SEMIS')

precomp('?ERROR', 'QERR')
words('DOCOL SWAP ZBRAN'); offset('QER10')
words('ERROR BRAN'); offset('QER20')
label('QER10'); words('DROP')
label('QER20'); words('SEMIS')

precomp('?COMP', 'QCOMP')
words('DOCOL STATE AT ZEQU LIT'); dw(17); words('QERR SEMIS')

precomp('?EXEC', 'QEXEC')
words('DOCOL STATE AT LIT'); dw(18); words('QERR SEMIS')

precomp('?PAIRS', 'QPAIR')
words('DOCOL SUB LIT'); dw(19); words('QERR SEMIS')

precomp('?CSP', 'QCSP')
words('DOCOL SPAT CSP AT SUB LIT'); dw(20); words('QERR SEMIS')

precomp('?LOADING', 'QLOAD')
words('DOCOL BLK AT ZEQU LIT'); dw(22); words('QERR SEMIS')

precomp('COMPILE', 'COMP')
words('DOCOL QCOMP FROMR DUP TWOP TOR AT COMMA SEMIS')

precomp('[', 'LBRAC', True)
words('DOCOL ZERO STATE STORE SEMIS')

precomp(']', 'RBRAC')
words('DOCOL LIT'); dw(0xc0); words('STATE STORE SEMIS')

precomp('SMUDGE', 'SMUDG')
words('DOCOL LATES LIT'); dw(0x20); words('TOGGL SEMIS')

precomp('HEX', 'HEX')
words('DOCOL LIT'); dw(16); words('BASE STORE SEMIS')

precomp('DECIMAL', 'DEC')
words('DOCOL LIT'); dw(10); words('BASE STORE SEMIS')

precomp('OCTAL', 'OCT')
words('DOCOL LIT'); dw(8); words('BASE STORE SEMIS')

precomp('(;CODE)', 'PSCOD')
words('DOCOL FROMR LATES PFA CFA STORE SEMIS')

precomp('<BUILDS', 'BUILD')
words('DOCOL ZERO CON SEMIS')

precomp('DOES>', 'DOES')
words('DOCOL FROMR LATES PFA STORE PSCOD')
label('DODOE'); db(opCodes['DODOE'] | NXT)

precomp('COUNT', 'COUNT')
words('DOCOL DUP ONEP SWAP CAT SEMIS')

precomp('TYPE', 'TYPE')
words('DOCOL DDUP ZBRAN'); offset('TYP20')
words('OVER PLUS SWAP XDO')
label('TYP10'); words('I CAT EMIT XLOOP'); offset('TYP10')
words('BRAN'); offset('TYP30')
label('TYP20'); words('DROP')
label('TYP30'); words('SEMIS')

precomp('-TRAILING', 'DTRAI')
words('DOCOL DUP ZERO XDO')
label('DTR10'); words('OVER OVER PLUS ONE SUB CAT')
words('BL SUB ZBRAN'); offset('DTR20')
words('LEAVE BRAN'); offset('DTR30')
label('DTR20'); words('ONE SUB')
label('DTR30'); words('XLOOP'); offset('DTR10')
words('SEMIS')

precomp('(.")', 'PDOTQ')
words('DOCOL R COUNT DUP ONEP FROMR PLUS TOR TYPE SEMIS')

precomp('."', 'DOTQ', True)
words('DOCOL LIT'); dw(34); words('STATE AT ZBRAN'); offset('DOT10')
words('COMP PDOTQ WORD HERE CAT ONEP ALLOT BRAN'); offset('DOT20')
label('DOT10'); words('WORD HERE COUNT TYPE')
label('DOT20'); words('SEMIS')

precomp('EXPECT', 'EXPEC')
words('DOCOL OVER PLUS OVER XDO')
label('EXP10'); words('KEY DUP LIT'); dw(14);
words('PORIG AT EQUAL ZBRAN'); offset('EXP20')
words('DROP LIT'); dw(8); words('OVER I EQUAL DUP FROMR')
words('TWO SUB PLUS TOR SUB BRAN'); offset('EXP30')
label('EXP20'); words('DUP LIT'); dw(0x0A); words('EQUAL ZBRAN'); offset('EXP40')
words('LEAVE DROP BL ZERO BRAN'); offset('EXP50')
label('EXP40'); words('DUP')
label('EXP50'); words('I CSTOR ZERO I ONEP CSTOR ZERO I TWOP CSTOR')
label('EXP30'); words('EMIT XLOOP'); offset('EXP10')
words('SEMIS')

precomp('QUERY', 'QUERY')
words('DOCOL TIB AT LIT'); dw(80); words('EXPEC ZERO IN STORE SEMIS')

precomp('\0', 'NULL', True)
words('DOCOL BLK AT ZBRAN'); offset('NUL20')
words('ONE BLK PSTOR ZERO IN STORE BLK AT BSCR MOD')
words('ZEQU ZBRAN'); offset('NUL10')
words('QEXEC FROMR DROP')
label('NUL10'); words('BRAN'); offset('NUL40')
label('NUL20'); words('FROMR DROP')
label('NUL40'); words('SEMIS')

precomp('FILL', 'FILL')
words('DOCOL SWAP TOR OVER CSTOR DUP ONEP')
words('FROMR ONE SUB CMOVE SEMIS')

precomp('ERASE', 'ERASE')
words('DOCOL ZERO FILL SEMIS')

precomp('BLANKS', 'BLANK')
words('DOCOL BL FILL SEMIS')

precomp('HOLD', 'HOLD')
words('DOCOL LIT'); dw(-1); words('HLD PSTOR HLD AT CSTOR SEMIS')

precomp('PAD', 'PAD')
words('DOCOL HERE LIT'); dw(84); words('PLUS SEMIS')

precomp('WORD', 'WORD')
words('DOCOL BLK AT ZBRAN'); offset('WOR10')
words('BLK AT BLOCK BRAN'); offset('WOR20')
label('WOR10'); words('TIB AT')
label('WOR20'); words('IN AT PLUS SWAP')
words('ENCL HERE LIT'); dw(34); words('BLANK IN')
words('PSTOR OVER SUB TOR R HERE CSTOR PLUS')
words('HERE ONEP FROMR CMOVE SEMIS')


precomp('(NUMBER)', 'PNUMB')
words('DOCOL')
label('PNU10'); words('ONEP DUP TOR CAT BASE AT DIGIT ZBRAN'); offset('PNU30')
words('SWAP BASE AT USTAR DROP ROT BASE AT USTAR DPLUS')
words('DPL AT ONEP ZBRAN'); offset('PNU20')
label('PNU20'); words('FROMR BRAN'); offset('PNU10')
label('PNU30'); words('FROMR SEMIS')

precomp('NUMBER', 'NUMB')
words('DOCOL ZERO ZERO ROT DUP ONEP CAT LIT'); dw(45); words('EQUAL')
words('DUP TOR PLUS LIT'); dw(-1);
label('NUM10'); words('DPL STORE PNUMB DUP CAT BL SUB ZBRAN'); offset('NUM20')
words('DUP CAT LIT'); dw(46); words('SUB ZERO QERR BRAN'); offset('NUM10')
label('NUM20'); words('DROP FROMR ZBRAN'); offset('NUM30'); words('DMINU')
label('NUM30'); words('SEMIS')

precomp('-FIND', 'DFIND')
words('DOCOL BL WORD HERE COUNT UPPER HERE CONT AT AT PFIND DUP ZEQU ZBRAN')
offset('DFI10'); words('DROP HERE LATES PFIND')
label('DFI10'); words('SEMIS')

precomp('UPPER', 'UPPER')
words('DOCOL OVER PLUS SWAP XDO')
label('UPP10'); words('I CAT LIT'); dw(96); words('GREAT I CAT LIT'); dw(123)
words('LESS AND ZBRAN'); offset('UPP20'); words('I LIT'); dw(32); words('TOGGL')
label('UPP20'); words('XLOOP'); offset('UPP10')
words('SEMIS')

precomp('(ABORT)', 'PABOR')
words('DOCOL ABORT SEMIS')

precomp('ERROR', 'ERROR')
words('DOCOL WARN AT ZLESS ZBRAN'); offset('ERR10'); words('PABOR')
label('ERR10'); words('HERE COUNT TYPE PDOTQ'); db(3); string(' ? ')
words('MESS SPSTO IN AT BLK AT QUIT SEMIS')

precomp('ID.', 'IDDOT')
words('DOCOL PAD LIT'); dw(32); words('LIT'); dw(95); words('FILL DUP PFA LFA')
words('OVER SUB PAD SWAP CMOVE PAD COUNT LIT'); dw(31); words('AND')
words('TYPE SPACE SEMIS')

precomp('CREATE', 'CREAT')
words('DOCOL DFIND ZBRAN'); offset('CRE10');
words('DROP NFA IDDOT LIT'); dw(4); words('MESS SPACE')
label('CRE10'); words('HERE DUP CAT WIDTH AT MIN ONEP ALLOT DUP LIT'); dw(160)
words('TOGGL HERE ONE SUB LIT'); dw(128); words('TOGGL LATES COMMA CURR AT')
words('STORE HERE TWOP COMMA SEMIS')

precomp('[COMPILE]', 'BCOMP', True)
words('DOCOL DFIND ZEQU ZERO QERR DROP CFA COMMA SEMIS')

precomp('LITERAL', 'LITER', True)
words('DOCOL STATE AT ZBRAN'); offset('LTR10'); words('COMP LIT COMMA')
label('LTR10'); words('SEMIS')

precomp('DLITERAL', 'DLITE', True)
words('DOCOL STATE AT ZBRAN'); offset('DLI10'); words('SWAP LITER LITER')
label('DLI10'); words('SEMIS')

precomp('U<', 'ULESS')
words('DOCOL TOR ZERO FROMR ZERO DMINU DPLUS SWAP DROP ZLESS SEMIS')

precomp('?STACK', 'QSTAC')
words('DOCOL SZERO AT TWO SUB SPAT ULESS ONE QERR SPAT HERE LIT'); dw(128)
words('PLUS ULESS TWO QERR SEMIS')

precomp('INTERPRET', 'INTER')
words('DOCOL')
label('INT10'); words('DFIND ZBRAN'); offset('INT40'); words('STATE AT LESS')
words('ZBRAN'); offset('INT20'); words('CFA COMMA BRAN'); offset('INT30')
label('INT20'); words('CFA EXEC')
label('INT30'); words('QSTAC BRAN'); offset('INT70')
label('INT40'); words('HERE NUMB DPL AT ONEP ZBRAN'); offset('INT50')
words('DLITE BRAN'); offset('INT60')
label('INT50'); words('DROP LITER')
label('INT60'); words('QSTAC')
label('INT70'); words('BRAN'); offset('INT10')

precomp('IMMEDIATE', 'IMMED')
words('DOCOL LATES LIT'); dw(64); words('TOGGL SEMIS')

precomp('VOCABULARY', 'VOCAB')
words('DOCOL BUILD LIT'); dw(41089); words('COMMA CURR AT CFA COMMA')
words('HERE VOCL AT COMMA VOCL STORE DOES')
label('DOVOC'); words('TWOP CONT STORE SEMIS')

precomp('DEFINITIONS', 'DEFIN')
words('DOCOL CONT AT CURR STORE SEMIS')

precomp('()', 'PAREN', True)
words('DOCOL LIT'); dw(41); words('WORD SEMIS')

precomp('QUIT', 'QUIT')
words('DOCOL ZERO BLK STORE LBRAC')
label('QUI10'); words('RPSTO CR QUERY INTER STATE AT ZEQU ZBRAN');
offset('QUI20'); words('PDOTQ'); db(3); string(' ok')
label('QUI20'); words('BRAN'); offset('QUI10')

precomp('ABORT', 'ABORT')
words('DOCOL SPSTO DEC SPACE CR PDOTQ')
db(16); string('PyFigFORTH v 0.1')
words('FORTH DEFIN QUIT')

precomp('COLD', 'COLD')
words('UPSTO SPSTO')
# Move 10 items in user area with values from boot table
words('LIT'); dw(18); words('PORIG SZERO LIT'); dw(20); words('CMOVE')
# Initialize FORTH vocabulary from boot table
words('LIT'); dw(12); words('PORIG AT LIT'); addr('FORTH')
words('LIT'); dw(6); words('PLUS STORE')
words('FIRST AT USE STORE FIRST AT PREV STORE DEC ABORT')



# ---------------------
# Some generic maths

prim('S->D', 'STOD');

precomp('ABS', 'ABS')
words('DOCOL DUP ZLESS ZBRAN'); offset('ABS10')
words('MINUS')
label('ABS10'); words('SEMIS')

precomp('DABS', 'DABS')
words('DOCOL DUP ZLESS ZBRAN'); offset('DAB10')
words('DMINU')
label('DAB10'); words('SEMIS')

precomp('MIN', 'MIN')
words('DOCOL OVER OVER GREAT ZBRAN'); offset('MIN10')
words('SWAP')
label('MIN10'); words('DROP SEMIS')

precomp('MAX', 'MAX')
words('DOCOL OVER OVER LESS ZBRAN'); offset('MAX10')
words('SWAP')
label('MAX10'); words('DROP SEMIS')

prim('M*', 'MSTAR'); prim('M/', 'MSLAS')

precomp('*', 'STAR')
words('DOCOL MSTAR DROP SEMIS')

precomp('/MOD', 'SLMOD')
words('DOCOL TOR STOD FROMR MSLAS SEMIS')

precomp('/', 'SLASH')
words('DOCOL SLMOD SWAP DROP SEMIS')

precomp('MOD', 'MOD')
words('DOCOL SLMOD DROP SEMIS')

precomp('*/MOD', 'SSMOD')
words('DOCOL TOR MSTAR FROMR MSLAS SEMIS')

precomp('*/', 'SSLA')
words('DOCOL SSMOD SWAP DROP SEMIS')

precomp('M/MOD', 'MSMOD')
words('DOCOL TOR ZERO R USLAS FROMR SWAP TOR USLAS FROMR SEMIS')



# ---------------------
# Generic disk I/O section

precomp('+BUF', 'PBUF')
words('DOCOL BBUF LIT'); dw(4); words('PLUS DUP LIMIT AT EQUAL ZBRAN')
offset('PBU10'); words('DROP FIRST AT')
label('PBU10'); words('DUP PREV AT SUB SEMIS')

precomp('UPDATE', 'UPDAT')
words('DOCOL PREV AT AT LIT'); dw(0x8000); words('OR PREV AT STORE SEMIS')

precomp('EMPTY-BUFFERS', 'MTBUF')
words('DOCOL FIRST AT LIMIT AT OVER SUB ERASE SEMIS')

precomp('FLUSH', 'FLUSH')
words('DOCOL LIMIT AT FIRST AT XDO')
label('FLU10'); words('I AT ZLESS ZBRAN'); offset('FLU20')
words('I TWOP I AT LIT'); dw(0x7FFF); words('AND ZERO RW')
label('FLU20'); words('BBUF LIT'); dw(4); words('PLUS XPLOO'); offset('FLU10')
words('MTBUF SEMIS')

precomp('DR0', 'DRZER')
words('DOCOL ZERO OFSET STORE SEMIS')

precomp('DR1', 'DRONE')
words('DOCOL LIT'); dw(160); words('OFSET STORE SEMIS')

precomp('BUFFER', 'BUFFE')
words('DOCOL USE AT DUP TOR')
label('BUF10'); words('PBUF ZBRAN'); offset('BUF10')
words('USE STORE R AT ZLESS ZBRAN'); offset('BUF20')
words('R TWOP R AT LIT'); dw(0x7FFF); words('AND ZERO RW')
label('BUF20'); words('R STORE R PREV STORE FROMR TWOP SEMIS')

precomp('BLOCK', 'BLOCK')
words('DOCOL OFSET AT PLUS TOR PREV AT DUP AT LIT'); dw(0x7FFF)
words('AND R SUB ZBRAN'); offset('BLO30')
label('BLO10'); words('PBUF ZEQU ZBRAN'); offset('BLO20')
words('DROP R BUFFE DUP R ONE RW TWO SUB')
label('BLO20'); words('DUP AT LIT'); dw(0x7FFF); words('AND R SUB ZEQU ZBRAN'); offset('BLO10')
words('DUP PREV STORE')
label('BLO30'); words('FROMR DROP TWOP SEMIS')

precomp('(LINE)', 'PLINE')
words('DOCOL TOR CL BBUF SSMOD FROMR BSCR')
words('STAR PLUS BLOCK PLUS CL SEMIS')

precomp('.LINE', 'DLINE')
words('DOCOL PLINE DTRAI TYPE SEMIS')

precomp('MESSAGE', 'MESS')
words('DOCOL WARN AT ZBRAN'); offset('MES20'); words('DDUP ZBRAN'); offset('MES10')
words('OFSET AT BSCR SLASH SUB DLINE')
label('MES10'); words('BRAN'); offset('MES30')
label('MES20'); words('PDOTQ'); db(6); string('MSG # '); words('DOT')
label('MES30'); words('SEMIS')

precomp('LOAD', 'LOAD')
words('DOCOL BLK AT TOR IN AT TOR ZERO IN STORE BSCR STAR')
words('BLK STORE INTER FROMR IN STORE FROMR BLK STORE SEMIS')

precomp('-->', 'ARROW')
words('DOCOL QLOAD ZERO IN STORE BSCR BLK AT OVER')
words('MOD SUB BLK PSTOR SEMIS')



# ---------------------
# Miscellaneous higher level

precomp("'", 'TICK', True)
words('DOCOL DFIND ZEQU ZERO QERR DROP LITER SEMIS')

precomp('FORGET', 'FORGE')
words('DOCOL CURR AT CONT AT SUB LIT'); dw(24); words('QERR TICK DUP')
words('FENCE AT LESS LIT'); dw(21); words('QERR DUP NFA DP STORE')
words('LFA AT CONT AT STORE SEMIS')

precomp('BACK', 'BACK')
words('DOCOL HERE SUB COMMA SEMIS')

precomp('BEGIN', 'BEGIN', True)
words('DOCOL QCOMP HERE SEMIS')

precomp('ENDIF', 'ENDIF', True)
words('DOCOL QCOMP TWO QPAIR HERE OVER SUB SWAP STORE SEMIS')

precomp('THEN', 'THEN', True)
words('DOCOL ENDIF SEMIS')

precomp('DO', 'DO', True)
words('DOCOL COMP XDO HERE LIT'); dw(3); words('SEMIS')

precomp('LOOP', 'LOOP', True)
words('DOCOL LIT'); dw(3); words('QPAIR COMP XLOOP BACK SEMIS')

precomp('+LOOP', 'PLOOP', True)
words('DOCOL LIT'); dw(3); words('QPAIR COMP XPLOO BACK SEMIS')

precomp('UNTIL', 'UNTIL', True)
words('DOCOL ONE QPAIR COMP ZBRAN BACK SEMIS')

precomp('END', 'END', True)
words('DOCOL UNTIL SEMIS')

precomp('AGAIN', 'AGAIN', True)
words('DOCOL ONE QPAIR COMP BRAN BACK SEMIS')

precomp('REPEAT', 'REPET', True)
words('DOCOL TOR TOR AGAIN FROMR FROMR TWO SUB ENDIF SEMIS')

precomp('IF', 'IF', True)
words('DOCOL COMP ZBRAN HERE ZERO COMMA TWO SEMIS')

precomp('ELSE', 'ELSE', True)
words('DOCOL TWO QPAIR COMP BRAN HERE ZERO COMMA')
words('SWAP TWO ENDIF TWO SEMIS')

precomp('WHILE', 'WHILE', True)
words('DOCOL IF TWOP SEMIS')



# ---------------------
# Numeric output

precomp('SPACES', 'SPACS')
words('DOCOL ZERO MAX DDUP ZBRAN'); offset('SPA20')
words('ZERO XDO')
label('SPA10'); words('SPACE XLOOP'); offset('SPA10')
label('SPA20'); words('SEMIS')

precomp('<#', 'BDIGS')
words('DOCOL PAD HLD STORE SEMIS')

precomp('#>', 'EDIGS')
words('DOCOL DROP DROP HLD AT PAD OVER SUB SEMIS')

precomp('SIGN', 'SIGN')
words('DOCOL ROT ZLESS ZBRAN'); offset('SIG10');
words('LIT'); dw(45); words('HOLD')
label('SIG10'); words('SEMIS')

precomp('#', 'DIG')
words('DOCOL BASE AT MSMOD ROT LIT'); dw(9); words('OVER LESS ZBRAN'); offset('DIG10')
words('LIT'); dw(7); words('PLUS')
label('DIG10'); words('LIT'); dw(48); words('PLUS HOLD SEMIS')

precomp('#S', 'DIGS')
words('DOCOL')
label('DGS10'); words('DIG OVER OVER OR ZEQU ZBRAN'); offset('DGS10')
words('SEMIS')

precomp('D.R', 'DDOTR')
words('DOCOL TOR SWAP OVER DABS BDIGS DIGS SIGN')
words('EDIGS FROMR OVER SUB SPACS TYPE SEMIS')

precomp('.R', 'DOTR')
words('DOCOL TOR STOD FROMR DDOTR SEMIS')

precomp('D.', 'DDOT')
words('DOCOL ZERO DDOTR SPACE SEMIS')

precomp('.', 'DOT')
words('DOCOL STOD DDOT SEMIS')

precomp('?', 'QUEST')
words('DOCOL AT DOT SEMIS')

precomp('U.', 'UDOT')
words('DOCOL ZERO DDOT SEMIS')



# ---------------------
# Utility section

precomp('LIST', 'LIST')
words('DOCOL DEC CR DUP SCR STORE PDOTQ'); db(6)
string('SCR # '); words('DOT LIT'); dw(16); words('ZERO XDO')
label('LIS10'); words('CR THREE DOTR SPACE')
words('I CR AT DLINE XLOOP'); offset('LIS10')
words('CR SEMIS')

precomp('INDEX', 'INDEX')
words('DOCOL CR ONEP SWAP XDO')
label('IND10'); words('CR I THREE DOTR SPACE ZERO I')
words('DLINE QTERM ZBRAN'); offset('IND20')
words('LEAVE')
label('IND20'); words('XLOOP'); offset('IND10')
words('SEMIS')

precomp('TRIAD', 'TRIAD')
words('DOCOL LIT'); dw(12); words('EMIT THREE SLASH THREE STAR')
words('THREE OVER SWAP PLUS XDO')
label('TRI10'); words('CR I LIST XLOOP'); offset('TRI10')
words('CR LIT'); dw(15); words('MESS CR SEMIS')

precomp('VLIST', 'VLIST')
words('DOCOL LIT'); dw(128); words('OUT STORE CONT AT AT')
label('VLI10'); words('OUT AT LIT'); dw(64); words('GREAT ZBRAN'); offset('VLI20')
words('CR ZERO OUT STORE')
label('VLI20'); words('DUP IDDOT SPACE SPACE PFA LFA AT')
words('DUP ZEQU QTERM OR ZBRAN'); offset('VLI10')
words('DROP SEMIS')

prim('R/W', 'RW');

precomp(';CODE', 'SCODE')
words('DOCOL QCSP COMP PSCOD LBRAC SMUDG SEMIS')

label('HFORT')
precomp('FORTH', 'FORTH')
words('DODOE DOVOC'); dw(0xA081); addr('HFORT')
label('XXVOC'); dw(0)

label('XDP')



# ---------------------
# USER AREA

org(RAM_SIZE - UPPERAREA_SIZE)
label('DSKBUF'); ds(DSKBUF_NUM * DSKBUF_SIZE)
label('ENDBUF')
label('XTIB'); ds(TIB_SIZE)
label('XUP'); ds(UAREA_SIZE)

label('MEMEND')


# --------------------------------------------------------------------------------
# Write output file(s)

lst = open('forth22.lst', 'w')
obj = open('forth22.hex', 'w')
opc = open('opcos22.py', 'w')
sta = open('symtab22.py', 'w')

# ----------------------------------------
# Cleanup undefined entries in symtab

for sym in symtab.keys():
    if type(symtab[sym]) == type([]): symtab[sym] = 65535

n = 16; srctext = ''; srcprev = ''

# for i in sorted(ram.keys()):
#     if i in src.keys(): srctext = src[i]
#     if srctext != srcprev or n > 15:
#         print(' ' * ((16 - n) * 3) + format('  %s' % srcprev))
#         if n > 15:
#             if srctext == srcprev: srctext = ''
#         srcprev = srctext
#         print(format(i, '04x') + ' ', end = '')
#         n = 0
#     print(format(ram[i], '02x') + ' ', end = '')
#     n += 1

# print(' ' * ((16 - n) * 3) + format('  %s' % srctext))
# print()

for i in sorted(ram.keys()):
    if i in src.keys(): srctext = src[i]
    if srctext != srcprev or n > 15:
        txt = (' ' * ((16 - n) * 3) + format('  %s' % srcprev))
        print(txt); lst.write(txt + '\n'); obj.write('\n')
        if n > 15:
            if srctext == srcprev: srctext = ''
        srcprev = srctext
        txt = format(i, '04x') + ' '
        print(txt, end = ''); lst.write(txt); obj.write(txt)
        n = 0
    txt = format(ram[i], '02x') + ' '
    print(txt, end = ''); lst.write(txt); obj.write(txt)
    n += 1

txt = (' ' * ((16 - n) * 3) + format('  %s' % srctext))
print(txt); lst.write(txt + '\n'); obj.write('\n')
print()

n = 0

opc.write('opCodes = {\n')

for opcode in sorted(opCodes.keys(), key = opCodes.get):
    if n > 5:
        print(); lst.write('\n')
        n = 0
    optext = '%6s = %02x' % (opcode, opCodes[opcode])
    optext = optext + (' ' * (16 - len(optext)))
    print(optext, end = ''); lst.write(optext)
    opctext = '\t0x%02x: "%s",\n' % (opCodes[opcode], opcode.lower())
    opc.write(opctext)
    opctext = '\t0x%02x: "%s",\n' % (opCodes[opcode] | 0x80, opcode)
    opc.write(opctext)
    n += 1

opc.write('}\n')
    
print(); lst.write('\n')
print(); lst.write('\n')

sta.write('symtab = {\n')

n = 0

for symbol in sorted(symtab.keys(), key = symtab.get):
    if n > 5:
        print(); lst.write('\n')
        n = 0
    if symtab[symbol] < 65535:
        symtext = '%6s = %04x' % (symbol, symtab[symbol])
    else:
        symtext = '%6s = %s' % (symbol, "----")
    symtext = symtext + (' ' * (16 - len(symtext)))
    print(symtext, end = ''); lst.write(symtext)
    n += 1
    sta.write('%d: "%s",\n' % (symtab[symbol], symbol))
        
print(); lst.write('\n')
print(); lst.write('\n')
sta.write('}\n')

txt = ('Primaries: %d, Precompiled: %d, Total: %d' \
        % (prims, precomps, (prims + precomps)))
print(txt); lst.write(txt + '\n')

print(); lst.write('\n')

#print(symtab)
#print(vlist)

# wrk = latest; n = 0

# while (True):
#     length = ram[wrk] & 0x3F
#     wrk += 1; nam = ''
#     while (length):
#         nam = nam + chr(ram[wrk] & 0x7F)
#         length -= 1; wrk += 1
#     if n > 80:
#         print();  lst.write('\n'); n = 0
#     txt = ('%s ' % nam); n += (len(nam) + 1)
#     print(txt, end = ''); lst.write(txt)
#     wrk = ram[wrk] + (ram[wrk + 1] << 8)
#     if wrk == 0: break
# print(); lst.write('\n')

lst.close()
obj.close()
opc.close()
sta.close()
