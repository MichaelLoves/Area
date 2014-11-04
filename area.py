import pickle
import re
import sys, getopt


class Block:
	"""定义连接部分的width和height"""
	def __init__(self, width, height):
		self.width = width     #宽度
		self.height = height   #高度

W = 2.0 #transistor 的宽度 单位: μ

# gate
gate = Block(0.18, W+0.22)

# 边缘处的 contact 
edge_contact = Block(0.48, W)

# 两个 gate 之间的 contact
gate_contact = Block(0.54, W)

# 两个 gate 之间没有 contact
gate_gate = Block(0.26, W)


class MOSFET:
	"""用来储存 MOSFET 的番号, 四个端子, 类型和长宽的信息"""
	def __init__(self, number, drain, gate, source, bulk, type, L, W):
		self.number = number
		self.drain = drain
		self.gate = gate
		self.source = source
		self.bulk = bulk
		self.type = type
		self.L = L
		self.W = W 

class Pipeline:
	"""在寻找 path 的时候用来储存 top_level_mos, bot_level_mos 和 path"""
	def __init__(self):
		self.top_level_mos = []
		self.bot_level_mos = []
		self.path = []

class Circuit:
	"""保存 netlist 中各部分 circuit 的 cell name 和 netlist"""
	def __init__(self, name, netlist):
		self.name = name        			    #circuit 的 cell name
		self.netlist = netlist   				#circuit 的 netlist 类型为 list
		self.mos = []							#用来储存 circuit 中所有 m 的信息  
												#m每部分均为 class mosfet 的 instance  ['m0', 'm1'...]

	def m_list(self):           			    #返回 netlist 中仅以 m 开头的部分
		list = []
		for part in self.netlist:
			if re.findall(r'\bm\w*\b', part):   #判断这行首字母是否以 m 开头
				list.append(part)				#若首字母以"m"开头 填加到 list 里面
		return(list)

	def line_m_list(self):                      #返回读入 m_list 的行数, 即 m 部分的个数
		return(len(self.m_list()))

	def mosfet(self, list_of_m):                #读取一个包含 m 信息的 list 之后封装在每个 MOSFET 类型的 instance 中 最后保存在 self.mos list 中
		line_num = len(self.m_list())
		for i in range(line_num):
			self.mos.append('m%d' %i)  #把列表填满 m1, m2... 之后再用每一项去创建一个class MOSFET 的 instance
			self.mos[i] = (MOSFET(list_of_m[i][0], list_of_m[i][1], list_of_m[i][2], \
							 list_of_m[i][3], list_of_m[i][4], list_of_m[i][5], list_of_m[i][6].strip("L="), list_of_m[i][7].strip('W='))) 

	def cal_width(self):   						#计算 circuit 的 width
		vdd_width = 0                     		#连接 vdd 处的宽度
		gnd_width = 0					  		#连接 gnd 处的宽度
		gate_gate_width = 0				  		#gate 与 gate 之间的宽度
		gate_width = 0					  		#gate 的总宽度	
		
		#判断各 m 部分之间的连接状态 需要研究 topology 理论之后重写
		for m_part in self.mos:
			if 'vdd' in m_part.drain or 'vdd' in m_part.source:
				vdd_width += edge_contact.width
			if 'gnd' in m_part.drain or 'gnd' in m_part.source:
				gnd_width += edge_contact.width

				for part in self.mos:
					if (m_part.number != part.number) and (part.drain == m_part.source):
						gate_gate_width += gate_gate.width

		gate_width = gate.width * self.line_m_list()
		width = round(vdd_width + gnd_width + gate_width + gate_gate_width, 2) #保留小数点后两位有效数字

		#print("vdd_width", vdd_width, "u")
		#print('gnd_width', gnd_width, "u")
		#print('gate_width', gate_width, "u")
		#print('gate_gate_width', gate_gate_width, "u")
		print("width =", width, "u")
		print()
		return(width)

		#寻找 path, 以其中一条为 main path, 其余部分作为独立部分处理

	#暂时不知道可以干嘛...
	def iterate_node(self, top_node, bot_node, path):       #判断上面 mos 的 source 是否等于 bot_node 若不同 将 top_node 赋值为下面 mos 的 source
		if top_node == bot_node:                       
			return(list(set(path)))                         #top_node 和 bot_node 相等之后输出 path 列表 ps 下面的判断逻辑有错误 所以会有重复元素出现
		else:
			for mos in self.mos:
				if mos.type == 'N' and top_node == mos.drain:
					path.append(mos)
					top_node = mos.source
					self.iterate_node(top_node, bot_node, path)	

	#输入两个点 找出两点间存在的 mos
	def search_mid_mos(self, top_node, bot_node):
		list = []
		for mos in self.mos:
			if mos.drain == top_node or mos.source == top_node and (mos.drain == bot_node or mos.source == bot_node):
				list.append(mos)
		return(list)

	def find_path(self):
		top_level_mos = []
		bot_level_mos = []
		top_level_mos_gate = []

		#找出 precharge PMOS 和 foot NMOS
		temp1 = []
		temp2 = []
		temp3 = []
		for part in self.mos:		
			for part2 in self.mos:
				if part.type == 'P' and part.gate == part2.gate and part.number != part2.number:
					temp1.append(part)
		top_level_mos = sorted(set(temp1), key=temp1.index)  #去处相同元素而不打乱顺序

		for mos in top_level_mos:             #获得两边最上端 PMOS 的 gate 的信号 好找到与之对应的 foot NMOS 
			temp2.append(mos.gate)
		top_level_mos_gate = list(set(temp2)) #[cd_n, precharge]
		
		for part in self.mos:
			if part.type == 'N' and part.gate in top_level_mos_gate:
				bot_level_mos.append(part)

		#创建两个 pipeline class 用来保存各自的 top_node 和 bot_node 但每次 pipeline 的顺序有可能改变
		pipeline1 = Pipeline()
		pipeline2 = Pipeline()
		for mos in top_level_mos:
			if mos.gate == top_level_mos_gate[0]:
				pipeline1.top_level_mos.append(mos)
			else:
				pipeline2.top_level_mos.append(mos)
		for mos in bot_level_mos:
			if mos.gate == pipeline1.top_level_mos[0].gate:
				pipeline1.bot_level_mos.append(mos)
			else:
				pipeline2.bot_level_mos.append(mos)

		# pipeline 1 的信息 -> 通用的事情不应该做两遍 所以可以弄一个函数出来		
		print('pipeline1:')
		print('top_level_mos')
		for mos in pipeline1.top_level_mos:
			print(mos.number)
		print('bot_level_mos')
		print(pipeline1.bot_level_mos[0].number)
		
		#寻找 top_node(precharge PMOS 下面的 net 编号) 和 bot_node(foot NMOS 上面的编号) 
		#因为 netlist 中的 drain 和 source 是对称的 所以需要考虑两次
		if pipeline1.top_level_mos[0].drain == 'vdd':   
			top_node_1 = pipeline1.top_level_mos[0].source
		else:
			top_node_1 = pipeline1.top_level_mos[0].drain     	#net038  or net018		

		if pipeline1.top_level_mos[1].drain == 'vdd':
			top_node_2 = pipeline1.top_level_mos[1].source
		else:
			top_node_2 = pipeline1.top_level_mos[1].drain		#net49   or net035		

		if pipeline1.bot_level_mos[0].drain == 'gnd':
			bot_node_1 = pipeline1.bot_level_mos[0].source
		else:
			bot_node_1 = pipeline1.bot_level_mos[0].drain       #net22 or net016
		print('top_node:', top_node_1, top_node_2)
		print('bot_node:', bot_node_1)
		print()
		

		top_level_nmos = []
		bot_level_nmos = []
		#找出与最上面的 PMOS 相连的一排 NMOS 
		for mos in self.mos:
			if mos.type == 'N' and (top_node_1 in (mos.drain or mos.source) or top_node_2 in (mos.drain or mos.source)):
				top_level_nmos.append(mos)
		#找出与最下面的 foot NMOS 相连的一排 NMOS
		for mos in self.mos:
			if mos.type == 'N' and (bot_node_1 in mos.drain or bot_node_1 in mos.source) and not ('gnd' in mos.drain or 'gnd' in mos.source):
				bot_level_nmos.append(mos)

		print('bot_level_nmos')
		for i in bot_level_nmos:
			print(i.number)


		#top_level_nmos 下面的 net 编号
		print('top_search_node')
		top_search_node = []
		for mos in top_level_nmos:
			if mos.drain == top_node_1 or mos.drain == top_node_2:
				top_search_node.append(mos.source)
			else:
				top_search_node.append(mos.drain)
		print(top_search_node)
			
		#bot_level_nmos 上面的 net 编号
		print('bot_search_node')
		bot_search_node = []
		for mos in bot_level_nmos:
			if mos.drain == bot_node_1:
				bot_search_node.append(mos.source)
			else:
				bot_search_node.append(mos.drain)
		print(bot_search_node)

		#从每一个 top_level_nmos 里的 mos 出发 因为还是涉及到 drain 和 source 对称的问题 所以分为两个部分 但是做的事情是完全一致的
		#确认最上排 mos 下面的点和最下排 mos 上面的点 比如 net28 和 net16 之后找到两个点之间所有可能的路径 作为一个 list 返回
		#之后对于 list 中的每条路径 加上最上排的 mos 和最下排的 mos 组成完整的三段路径
		for mos in top_level_nmos:
			mid_node_list = []
			if mos.drain in top_search_node:
				for node in bot_search_node:
					mid_node_list = self.search_mid_mos(mos.drain, node)
				for mid_node in mid_node_list:
					path = []
					path.append(mos)
					path.append(mid_node)
					for bot_nmos in bot_level_nmos:
						if (mid_node.drain == bot_nmos.drain or mid_node.drain == bot_nmos.source) \
						   or (mid_node.source == bot_nmos.drain or mid_node.source == bot_nmos.source):
						   path.append(bot_nmos)
			else:
				print('mos', mos.number)
				for node in bot_search_node:
					mid_node_list = self.search_mid_mos(mos.source, node)
				for mid_node in mid_node_list:
					path = []
					path.append(mos)
					path.append(mid_node)
					for bot_nmos in bot_level_nmos:
						if (mid_node.drain == bot_nmos.drain or mid_node.drain == bot_nmos.source) \
						   or (mid_node.source == bot_nmos.drain or mid_node.source == bot_nmos.source):
						   path.append(bot_nmos)
					print('path')
					for i in path:
						print(i.number)
		

#查找一个元素的所有位置
def find_all_index(arr, search):
	return [index+1 for index,item in enumerate(arr) if item == search]

#不断交换两个数的位置 
#比如一个 list 如果是[1, 10, 100], 那么输出[[1, 10],[11, 100], [101, 1000]]
#第一个数从1开始是因为 virtuoso 自动生成的 netlist_lvs 文件第一行为空行 所以从第二行开始读取
def iterate(list):
	a = 1
	temp = []
	temp.append([a , list[0]])
	for i in range(len(list)-1):
		temp.append([list[i]+1, list[i+1]])
	return(temp)	

#把 netlist 以 break_point 为分割点 分割为几部分 返回一个各部分为 class Circuit 的 list
def break_into_part(filename, break_point):
	list_of_circuits = []								#用来存放分割后的各个部分
	temp = []
	file_list = list(filename)							#先把读取的文件转换成 list 格式                              
	splitter = find_all_index(file_list, break_point)	#找到所有分割点在 list 中的位置 如 [1, 10, 100]
	splitter_list = iterate(splitter)					#找到各个部分的起始点和结束点 如 [[1, 10], [11, 100]]
	for i in range(len(splitter)):
		list_of_circuits.append('circuit%d' %i)   	#把列表填满 circuit1, circuit2... 之后用每一项去创建 class Circuit 的 instance
		list_of_circuits[i] = Circuit(file_list[splitter_list[i][0]+1].replace('** Cell name: ', ''), file_list[splitter_list[i][0]+4:splitter_list[i][1]]) #填加各 subcircuit 的 name 和 netlist
	list_of_circuits.append(Circuit(file_list[splitter_list[i][1]+2].replace('** Cell name: ', ''), file_list[splitter_list[i][1]+1:]))
	return(list_of_circuits)

def get_netlist_data(input_file, output_file = 'output.txt', subtract = 0):
	try:
		output = open(output_file, 'w')     		   #创建一个文件用来保存结果
		with open(input_file) as netlist_file:
			list_of_m = []                                 #创建一个 list 用来储存以 m 开头的数据
			list_of_circuits = break_into_part(netlist_file, '** End of subcircuit definition.\n') #读入每一行: 用于读取真的 netlist 文件
			
			if subtract:                               #如果指定抽取某一 subcircuit
				print('Cell name :', subtract)
				for circuit in list_of_circuits:
					if re.findall(r'\b%s\b'%subtract, circuit.name):  #找到想要抽取的 subcircuit 的 instance
						list_of_m = circuit.m_list()    #把 subcircuit 以 m 开头的部分填加到 list_of_m list 中
						circuit.mosfet([m_part.split() for m_part in list_of_m]) #[]:对于 list_of_m 中的每个部分以空格分隔开来 ['m1 out in'] -> ['m1', 'out', 'in']
																				   #之后调用 circuit 类型的 mosfet 函数把每个 m 的信息保存成一个 mosfet
						print('Netlist')
						for i in circuit.mos:
							print(i.number, i.drain, i.gate, i.source, i.bulk, i.type, 'L =', i.L, 'W =', i.W)
						print()
						total_width = circuit.cal_width() 
						circuit.find_path()

			else:                     				   #若未指定 subcircuit 则输出整个 netlist
				top_level_circuit = list_of_circuits[-1]
				print('Cell name :', top_level_circuit.name)
				top_level_circuit.mosfet([m_part.split() for m_part in top_level_circuit.m_list()])
				for i in top_level_circuit.mos:
					print(i.number, i.drain, i.gate, i.source, i.bulk, i.type, 'L=', i.L, 'W=', i.W)
				total_width = top_level_circuit.cal_width()

			output.write("width =" + str(total_width) + "u")
			output.close()

	except IOError as err:
		print("File error: " + str(err))
		return(None)

opts, args = getopt.getopt(sys.argv[1:], "hi:o:s:")   #命令行输入
input_file, output_file, subtract = '', '', ''

def usage():
	print('Usage: ' + sys.argv[0] + ' -i inputfile -o outputfile -s extract_subcircuit')
	print('-s: Default as 0 which means output netlist of the top level circuit')

for op, value in opts:
	if op == "-i":
		input_file = value
	elif op == "-o":
		output_file = value
	elif op == "-s":
		subtract = value
	elif op == "-h" or (len(sys.argv) <= 4):
		usage()
		sys.exit()

if __name__ == '__main__':
	get_netlist_data(input_file, output_file, subtract)