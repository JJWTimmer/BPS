def enum(**enums):
	'''
	>>> Numbers = enum(ONE=1, TWO=2, THREE='three')
	>>> Numbers.ONE
	1
	>>> Numbers.TWO
	2
	>>> Numbers.THREE
	'three'
	'''
	return type('Enum', (), enums)