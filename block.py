class Block:
	"""docstring for Block"""
	def __init__(self, width, height):
		self.width = width
		self.height = height

W = 2.0

# gate
gate = Block(0.18, W+0.22)

# 边缘处的 contact 
edge_contact = Block(0.48, W)

# 两个 gate 之间的 contact
gate_contact = Block(0.54, W)

# 两个 gate 之间没有 contact
gate_gate = Block(0.26, W)

print(round(gate.width + edge_contact.width, 2)) #round(num, 2) 后面一个数字用来控制返回精度

