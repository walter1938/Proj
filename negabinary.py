def neg(i):
	st = ''.join(str(e) for e in i)
	reversd = st[::-1]
	inc = len(st)
	decimal = 0
	for x in reversd:
		"""
		making a decimal from a negative binary
		"""
		y = int(x) * pow(-2, inc - 1)
		inc -= 1
		decimal += y
	print(decimal) # only for step viewing purpose!
	inverted = decimal * -1 # inverting the decimal
	print(inverted) # only for step viewing purpose!
	negative_binary = []
	while inverted != 0:
		"""
		making a negative binary from an inverted decimal
		"""
		inverted, remainder = divmod(inverted, -2)
		if remainder < 0:
			inverted, remainder = inverted + 1, remainder + 2
		negative_binary.insert(0, int(remainder))
	return negative_binary #or make it print() so you could see a result
