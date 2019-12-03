loco = 0
latest = 0

'''
NEXT

'''

ram = [0] * 65536

symtab = {}
vlist = ''

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
					ram[backref[0]] = loco - backref[0]
				else:
					ram[backref[0]] = loco
			symtab[name] = loco
		else:
			print('Error: Label %s redefined.' % name)
	else:
		symtab[name] = loco
		
def addr(label, rel = False):
	if label in symtab:
		if type(symtab[label]) == type(0):
			if rel:
				dw(loco - symtab[label])
			else:
				dw(symtab[label])
		else:
			symtab[label].append((loco, rel))
			dw(0xffff)
	else:
		symtab[label] = [(loco, rel)]
		dw(0xffff)
		
def words(forthline):
	while len(forthline):
		spc = forthline.find(' ')
		if spc > -1:
			word = forthline[:spc]; forthline = forthline[spc + 1:]
		else:
			word = forthline; forthline = ''
		if len(word): addr(word)

def getw(addr):
	return (ram[addr] + (ram[addr+1] << 8))

def putw(addr, data16):
	global ram
	ram[addr] = data16 & 0xff
	ram[addr+1] = data16 >> 8 & 0xff

def org(addr):
	global loco
	loco = addr

def db(byte):
	global loco
	ram[loco] = byte; loco += 1

def dw(word):
	global loco
	putw(loco, word); loco += 2

def prim(wordName, name, opCode):
	global loco
	global latest
	global opCodes
	global vlist
	vlist = vlist + wordName + ' '
	opCodes['_' + name] = opCode
	thisHeader	= loco
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
	db(opCode)
	if wordName != 'NEXT': db(opCodes['_NEXT'])

def precomp(wordName, name = None):
	global loco, latest
	global vlist
	vlist = vlist + wordName + ' '
	thisHeader = loco
	wn = wordName
	db(len(wn) | 0x80)
	while len(wn) > 1:
		db(ord(wn[0]))
		wn = wn[1:]
	db(ord(wn[0]) | 0x80)
	dw(latest)
	latest = thisHeader
	if name: label(name)



# --------------------------------------------------------------------------------
# The Actual FORTH

org(16)

# --------------------
# Nucleus


# prim('', '', nextOp())
prim('NEXT', 'NEXT', nextOp());			prim('LIT', 'LIT', nextOp())
prim('EXECUTE', 'EXEC', nextOp());		prim('BRANCH', 'BRAN', nextOp())
prim('0BRANCH', 'ZBRAN', nextOp());		prim('(LOOP)', 'XLOOP', nextOp())
prim('(+LOOP)', 'XPLOO', nextOp());		prim('(DO)', 'XDO', nextOp())
prim('I', 'I', nextOp());				prim('DIGIT', 'DIGIT', nextOp())
prim('(FIND)', 'PFIND', nextOp());		prim('ENCLOSE', 'ENCL', nextOp())
prim('EMIT', 'EMIT', nextOp());			prim('KEY', 'KEY', nextOp())
prim('?TERMINAL', 'QTERM', nextOp());	prim('CR', 'CR', nextOp())
prim('CMOVE', 'CMOVE', nextOp());		prim('U*', 'USTAR', nextOp())
prim('U/', 'USLAS', nextOp());			prim('AND', 'AND', nextOp())
prim('OR', 'OR', nextOp());				prim('XOR', 'XOR', nextOp())
prim('SP@', 'SPAT', nextOp());			prim('SP!', 'SPSTO', nextOp())
prim('RP!', 'RPSTO', nextOp());			prim(';S', 'SEMIS', nextOp())
prim('LEAVE', 'LEAVE', nextOp());		prim('>R', 'TOR', nextOp())
prim('R>', 'FROMR', nextOp());			prim('R', 'R', nextOp())
prim('0=', 'ZEQU', nextOp());			prim('0<', 'ZLESS', nextOp())
prim('+', 'PLUS', nextOp());			prim('D+', 'DPLUS', nextOp())
prim('MINUS', 'MINUS', nextOp());		prim('DMINUS', 'DMINU', nextOp())
prim('OVER', 'OVER', nextOp());			prim('DROP', 'DROP', nextOp())
prim('SWAP', 'SWAP', nextOp());			prim('DUP', 'DUP', nextOp())
prim('+!', 'PSTOR', nextOp());			prim('TOGGLE', 'TOGGL', nextOp())
prim('@', 'AT', nextOp());				prim('C@', 'CAT', nextOp())
prim('!', 'STORE', nextOp());			prim('C!', 'CSTOR', nextOp())
prim('1+', 'ONEP', nextOp());			prim('2+', 'TWOP', nextOp())
#prim('', '', nextOp())

opCodes['_DOCOL'] = nextOp();			opCodes['_DOCON'] = nextOp();
opCodes['_DOVAR'] = nextOp();			opCodes['_DOUSE'] = nextOp();
opCodes['_DODOE'] = nextOp()


# --------------------
# Bordeline Precompiled

precomp(':')
words('DOCOL QEXEC SCSP CURR AT CONT STORE CREAT RBRAC PSCOD')
label('DOCOL')
db(opCodes['_DOCOL'])
db(opCodes['_NEXT'])

precomp(';')
words('DOCOL QCSP COMP SEMIS SMUDG LBRAC SEMIS')

precomp('CONSTANT', 'CON')
words('DOCOL CREAT SMUDG COMMA PSCOD')
label('DOCON')
db(opCodes['_DOCON'])
db(opCodes['_NEXT'])

precomp('VARIABLE', 'VAR')
words('DOCOL CON PSCOD')
label('DOVAR')
db(opCodes['_DOVAR'])
db(opCodes['_NEXT'])

precomp('USER', 'USER')
words('DOCOL CON PSCOD')
label('DOUSE')
db(opCodes['_DOUSE'])
db(opCodes['_NEXT'])

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
words('LIT ORIGIN PLUS SEMIS')

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
words('DOCOL DUP ZBRAN'); addr('DDU10', True)
words('DUP')
label('DDU10'); words('SEMIS')


precomp('TRAVERSE', 'TRAV')
words('DOCOL SWAP')
label('TRA10'); words('OVER PLUS LIT'); dw(0x7f)
words('OVER CAT LESS ZBRAN'); addr('TRA10', True)
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
words('DOCOL SWAP ZBRAN'); addr('QER10', True)
words('ERROR BRAN'); addr('QER20', True)
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

precomp('[', 'LBRAC')
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
label('DODOE')
db(opCodes['_DODOE'])
db(opCodes['_NEXT'])

precomp('COUNT', 'COUNT')
words('DOCOL DUP ONEP SWAP CAT SEMIS')

precomp('TYPE', 'TYPE')
words('DOCOL DDUP ZBRAN'); addr('TYP20', True)
words('OVER PLUS SWAP XDO')
label('TYP10'); words('I CAT EMIT XLOOP'); addr('TYP10', True)
words('BRAN'); addr('TYP30')
label('TYP20'); words('DROP')
label('TYP30'); words('SEMIS')

precomp('-TRAILING', 'DTRAI')
words('DOCOL DUP ZERO XDO')
label('DTR10'); words('OVER OVER PLUS ONE SUB CAT')
words('BL SUB ZBRAN'); addr('DTR20', True)
words('LEAVE BRAN'); addr('DTR30', True)
label('DTR20'); words('ONE SUB')
label('DTR30'); words('XLOOP'); addr('DTR10', True)
words('SEMIS')

precomp('(.")', 'PDOTQ')
words('DOCOL R COUNT DUP ONEP FROMR PLUS TOR TYPE SEMIS')

precomp('."', 'DOTQ')
words('DOCOL LIT'); dw(34); words('STATE AT ZBRAN'); addr('DOT10', True)
words('COMP PDOTQ WORD HERE CAT ONEP ALLOT BRAN'); addr('DOT20', True)
label('DOT10'); words('WORD HERE COUNT TYPE')
label('DOT20'); words('SEMIS')

precomp('EXPECT', 'EXPEC')
words('DOCOL OVER PLUS OVER XDO')
label('EXP10'); words('KEY DUP LIT'); dw(22);
words('PORIG AT EQUAL ZBRAN'); addr('EXP20', True)
words('DROP LIT'); dw(8); words('OVER I EQUAL DUP FROMR')
words('TWO SUB PLUS TOR SUB BRAN'); addr('EXP30', True)
label('EXP20'); words('DUP LIT'); dw(21); words('EQUAL ZBRAN'); addr('EXP40', True)
words('LEAVE DROP BL ZERO BRAN'); addr('EXP50', True)
label('EXP40'); words('DUP')
label('EXP50'); words('I CSTOR ZERO I ONEP CSTOR ZERO I TWOP CSTOR')
label('EXP30'); words('EMIT XLOOP'); addr('EXP10', True)
words('SEMIS')
 
precomp('QUERY', 'QUERY')
words('DOCOL TIB AT LIT'); dw(80); words('EXPEC ZERO IN STORE SEMIS')

precomp('\0x00', 'NULL')
words('DOCOL BLK AT ZBRAN'); addr('NUL20', True)
words('ONE BLK PSTOR ZERO IN STORE BLK AT BSCR MOD')
words('ZEQU ZBRAN'); addr('NUL10', True)
words('QEXEC FROMR DROP')
label('NUL10'); words('BRAN'); addr('NUL40', True)
label('NUL20'); words('FROMR DROP')
label('NUL40'); words('SEMIS')

precomp('FILL', 'FILL')
words('DOCOL SWAP TOR OVER CSTOR DUP ONEP SEMIS')

precomp('ERASE', 'ERASE')
words('DOCOL ZERO FILL SEMIS')

precomp('BLANKS', 'BLANKS')
words('DOCOL BL FILL SEMIS')

precomp('HOLD', 'HOLD')
words('DOCOL LIT'); dw(-1); words('HLD PSTOR HLD AT CSTOR SEMIS')

precomp('PAD', 'PAD')
words('DOCOL HERE LIT'); dw(84); words('PLUS SEMIS')

precomp('WORD', 'WORD')
words('DOCOL BLK AT ZBRAN'); addr('WOR10', True)
words('BLK AT BLOCK BRAN'); addr('WOR20', True)
label('WOR10'); words('TIB AT')
label('WOR20'); words('IN AT PLUS SWAP')
words('ENCL HERE LIT'); dw(34); words('BL IN')
words('PSTOR OVER SUB TOR R HERE CSTOR PLUS')
words('HERE ONEP FROMR CMOVE SEMIS')

'''
precomp('', '')
words('DOCOL SEMIS')

precomp('', '')
words('DOCOL SEMIS')

precomp('', '')
words('DOCOL SEMIS')

precomp('', '')
words('DOCOL SEMIS')

precomp('', '')
words('DOCOL SEMIS')

precomp('', '')
words('DOCOL SEMIS')

precomp('', '')
words('DOCOL SEMIS')

precomp('', '')
words('DOCOL SEMIS')
'''
# --------------------------------------------------------------------------------
# Write HEX file

'''
for i in range(0, 512):
	if i % 16 == 0:
		print(); print(format(i, '04x') + ': ', end = '')  
	print(format(ram[i], '02x') + ' ', end = '')
print()
print()
'''



#print(symtab)
print(vlist)
