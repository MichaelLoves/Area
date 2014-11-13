import pickle
import re
import sys, getopt
from copy import deepcopy

class Node:
	"""用于储存两个 mos 之间的连接点的名称和是否为并联点 以判断 contact 的类型"""
	def __init__(self, number):
		self.number = number
		self.fork = 0

class Block:
	"""用于生成path之后拼接的模块, 基本模块名称有 
	gate(最基本的 gate, L为固定的0.18), edge_contact(边缘处的 contact), 
	gate_contact_gate_sw(两个相同W的gate之间的 contact), gate_contact_gate_dw(两个不同W的gate之间的 contact),
	gate_gate_sw(两个相同W的gate之间的space), gate_gate_dw(两个不同W的gate之间的space)
	"""
	def __init__(self, block_name, L, W):
		self.block_name = block_name   #block 名称
		self.L = L     				   #宽度 单位:μ
		self.W = W   				   #高度

class MOSFET:
	'''用来储存 MOSFET 的番号, 四个端子, 类型和长宽的信息'''
	'''searched 则在后续的 find_entire_path 函数中记录 mos 是否被使用过'''
	def __init__(self, number, drain, gate, source, bulk, type, L, W):
		self.number = number
		self.drain = drain
		self.gate = gate
		self.source = source
		self.bulk = bulk
		self.type = type
		self.L = L
		self.W = W 
		self.searched = 0

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
							 list_of_m[i][3], list_of_m[i][4], list_of_m[i][5], list_of_m[i][6].strip("L=").strip("e-9"), list_of_m[i][7].strip('W=').strip('e-9')))
			self.mos[i].L = float(self.mos[i].L)/1000.   #把gate的L(比如180)换算为0.18 单位为 u
			self.mos[i].W = float(self.mos[i].W)/1000.

	def fork(self, ori_mos, fork_mos_list):
		'''用来确定所读入 mos 的端子存在并联情况时优先选择哪一方'''
		'''读入需要分析的 mos 和与其并联的 mos 的 list'''
		path_list = []
		fork_mos_block_list = []

		#对于每一个分歧的 mos 创建一个与 ori_mos 串联的 path
		for mos in fork_mos_list:       
			temp = []
			temp.append(ori_mos)
			temp.append(mos)
			path_list.append(temp)

		#利用内建的 creat_block 函数获取每个 path 的长度 并添加到列表的最末端
		for path in path_list:      
			path.append(self.create_block(path, return_L = 1))  

		#根据长度重新排列并返回最小L的path
		path_list.sort(key = lambda path:path[-1])
		return(path_list[0][1])

	#对于读入的 path 生成 block 返回 block 的 list 
	def create_block(self, path, return_L = 0):
		"""根据读入的 path 生成 layout 模块
			return 有三种情况: 
			默认为0 返回 entire_block
			若为1  返回 entire_block 的长度
			若为2  返回 entire_block 和 entire_block 的长度
		"""
		entire_block = []
		path_block_L = 0

		#先判断需要计算的 path 中是否只包含一个 mos
		if len(path) == 1:
			entire_block.append(Block('edge_contact' ,0.48, path[0].W)) 		  #填加一个边缘处的 edge_contact
			entire_block.append(Block('gate', 0.18, path[0].W))					  #填加一个 gate
			entire_block.append(Block('edge_contact' ,0.48, path[0].W))			  #填加一个边缘处的 edge_contact
		
		else:
			entire_block.append(Block('edge_contact' ,0.48, path[0].W)) 		  #填加一个边缘处的 edge_contact
			for part in path[:-2]:
				if isinstance(part, MOSFET):
					entire_block.append(Block('gate', part.L, part.W))            #填加一个 gate
					if part.W == path[path.index(part)+2].W:		 			  #比较当前 gate 和下面一个 gate 的 W 是否相同
						if path[path.index(part)+1].fork == 0:
							entire_block.append(Block('gate_gate_sw' ,0.26, part.W))      #两个 gate 宽度一致 没有 contact
						else:
							entire_block.append(Block('gate_contact_gate_sw', 0.54, part.W)) #两个 gate 宽度一致 有 contact
					else:
						if path[path.index(part)+1].fork == 0:
							entire_block.append(Block('gate_gate_dw', 0.1, part.W))       #两个 gate 宽度不一致 没有 contact
							entire_block.append(Block('gate_gate_dw', 0.32, path[path.index(part)+2].W)) 
						else:	
							entire_block.append(Block('gate_contact_gate_dw', 0.16, part.W))		  #两个 gate 宽度不一致 有 contact
							entire_block.append(Block('gate_contact_gate_dw' ,0.38, path[path.index(part)+2].W))
				else:
					continue
			entire_block.append(Block('gate', 0.18, path[-1].W))		  #因为上面逻辑只能填加到倒数第二个 mos 的右侧的部分 所以手动填加最右侧的 gate
			entire_block.append(Block('edge_contact' ,0.48, path[-1].W))  #填加最右面的 edge_contact
			entire_block.append(Block('diffs_space', 0.28, path[-1].W))

		if not return_L:
			return(entire_block)
		elif return_L == 1:
			for block in entire_block:
				path_block_L += block.L
			return(path_block_L)
		elif return_L == 2:
			for block in entire_block:
				path_block_L += block.L
			return(entire_block, path_block_L)

	#输入两个点 找出两点间(未被搜索过)的 mos
	def search_mid_mos(self, top_node, bot_node):
		list = []
		for mos in self.mos:
			if mos.searched == 0:
				if (mos.drain == top_node or mos.source == top_node) and (mos.drain == bot_node or mos.source == bot_node):
					list.append(mos)
		return(list)

	def create_pipeline_path(self, search_node, mos, bot_search_node, bot_level_nmos, circuit_mlist, pipeline_path):
		"""生成整个 pipeline 的 path 原 find_entire_path 函数中最后的部分
		为了减少根据 mos 的 drain 和 source 不同位置的两种情况而产生的冗长性, 定义为一个函数"""

		mid_node_list = []
		# 查找top_level_nmos 的下端和 bot_search_node 之间的仍未被搜索过的 mos
		for node in bot_search_node:
			mid_node_list.extend(self.search_mid_mos(search_node, node))

		#根据 mid_node_list 的长度来判断连接情况
		#长度为1是串联 长度大于等于2是并联 若不包含任何元素则直接讲 top_level_nmos 作为独立 part 填加到 pipeline_path
		#mos 与下面的 mos 串联时 直接讲 mid_node 填加到 path 中
		if len(mid_node_list) == 1:
			pipeline_path.append(create_path(mos, mid_node_list[0], bot_level_nmos, circuit_mlist))

		#mos 与下面的 mos 并联时 需要从 mid_node_list 中挑选与 mos 连接部分面积较小的一方
		elif len(mid_node_list) >= 2:
			mid_node = self.fork(mos, mid_node_list)
			pipeline_path.append(create_path(mos, mid_node, bot_level_nmos, circuit_mlist))

		#若下侧的 mid_node 都被搜索过了 则这个 top_level_node 作为独立元素填加到 pipeline_path 中		
		else:
			isolated_mos = []
			isolated_mos.append(mos)
			pipeline_path.append(isolated_mos)

	#读入两个 path 去除其中重复的 mos 
	#以长度 L 短的一方作为 main_path 去除相同元素后的另一方作为 isolated_path 
	def merge_path(self, path_1, path_2):
		path_1_L, path_2_L = 0, 0
		temp1 = deepcopy(path_1)
		temp2 = deepcopy(path_2)	

		for block in self.create_block(path_1):
			path_1_L += block.L

		for block in self.create_block(path_2):
			path_2_L += block.L

		if has_same_mos(temp1, temp2):
			if path_1_L <= path_2_L:
				main_path = temp1
				for mos1 in temp1:
					for mos2 in temp2:
						if mos1.number == mos2.number:
							temp2.remove(mos2)
				isolated_path = temp2
				return(main_path, isolated_path)
			else:
				main_path = temp2
				for mos1 in temp1:
					for mos2 in temp2:
						if mos1.number == mos2.number:
							temp1.remove(mos1)
				isolated_path = temp1
				return(main_path, isolated_path)
		else:
			return(temp1, temp2)

	def find_pipeline_path(self, pipeline):
		"""对于读入的 pipeline 返回其 path"""

		#top_node_1: precharge PMOS 下面 NAND 侧的编号 
		#top_node_2: precharge PMOS 下面 AND 侧的编号
		#bot_node: foot NMOS 上面的编号
		#因为 netlist 中的 drain 和 source 是对称的 所以需要考虑两次
		if pipeline.top_level_mos[0].drain == 'vdd':
			top_node_1 = pipeline.top_level_mos[0].source
		else:
			top_node_1 = pipeline.top_level_mos[0].drain
		if pipeline.top_level_mos[1].drain == 'vdd':
			top_node_2 = pipeline.top_level_mos[1].source
		else:
			top_node_2 = pipeline.top_level_mos[1].drain
		if pipeline.bot_level_mos[0].drain == 'gnd':
			bot_node_1 = pipeline.bot_level_mos[0].source
		else:
			bot_node_1 = pipeline.bot_level_mos[0].drain
		
		top_level_nmos = []
		bot_level_nmos = []
		#找出与最上面的 PMOS 相连的一排 NMOS 
		for mos in self.mos:
			if mos.type == 'N' and (top_node_1 == mos.drain or top_node_1 == mos.source or top_node_2 == mos.drain or top_node_2 == mos.source):
				top_level_nmos.append(mos)
		#找出与最下面的 foot NMOS 相连的一排 NMOS
		for mos in self.mos:
			if mos.type == 'N' and (bot_node_1 == mos.drain or bot_node_1 == mos.source) and mos.drain != 'gnd' and mos.source != 'gnd':
				bot_level_nmos.append(mos)

		#top_level_nmos 下面的 net 编号
		top_search_node = []
		for mos in top_level_nmos:
			if mos.drain == top_node_1 or mos.drain == top_node_2:
				top_search_node.append(mos.source)
			else:
				top_search_node.append(mos.drain)
			
		#bot_level_nmos 上面的 net 编号
		bot_search_node = []
		for mos in bot_level_nmos:
			if mos.drain == bot_node_1:
				bot_search_node.append(mos.source)
			else:
				bot_search_node.append(mos.drain)

		'''从每一个 top_level_nmos 里的 mos 出发 因为还是涉及到 drain 和 source 对称的问题 所以分为两个部分 但是做的事情是完全一致的
		确认最上排 mos 下面的点和最下排 mos 上面的点 比如 net28 和 net16 之后找到两个点之间所有可能的路径 作为一个 list 返回
		之后对于 list 中的每条路径 加上最上排的 mos 和最下排的 mos 组成完整的三段路径'''
		pipeline_path = []
		for mos in top_level_nmos:
			#分为 mos.drain 在 top_search_node列表中还是 mos.source 在列表中两种情况
			#因此在 creat_pipeline_path 中的第一个参数 search_node 不同
			if mos.drain in top_search_node:
				self.create_pipeline_path(mos.drain, mos, bot_search_node, bot_level_nmos, self.mos, pipeline_path)
			else:
				self.create_pipeline_path(mos.source, mos, bot_search_node, bot_level_nmos, self.mos, pipeline_path)
		
		return(pipeline_path)

	def find_entire_path(self):
		"""找出两个 pipeline 的 path 并一起返回"""
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

		print('Pipeline1')
		print('top_level_mos')
		for mos in pipeline1.top_level_mos:
			print(mos.number + '  ', end = '')
		print()
		print('bot_level_mos')
		print(pipeline1.bot_level_mos[0].number)

		print('Pipeline2')
		print('top_level_mos')
		for mos in pipeline2.top_level_mos:
			print(mos.number + '  ', end = '')
		print()
		print('bot_level_mos')
		print(pipeline2.bot_level_mos[0].number)

		pipeline1_path = self.find_pipeline_path(pipeline1)
		pipeline2_path = self.find_pipeline_path(pipeline2)

		return(pipeline1_path, pipeline2_path)
		
def display(func_name, mos_list):
	print(func_name)
	for mos in mos_list:
		print(mos.number)
	print()

def display_pipeline(pipeline, pipeline_name, circuit):
	print(pipeline_name, 'path')
	total_length = 0
	for index, path in enumerate(pipeline):
		for part in path:
			print(part.number + '   ', end = '')
		print()
		print('block : ', end = '')
		block, block_legnth = circuit.create_block(path, return_L = 2)
		for part in block:
			print(part.block_name + '   ', end = '')
		print()
		print('block_legnth =', round(block_legnth, 2), 'u')
		total_length += block_legnth
		print()
	print('total_length =', total_length, 'u')
	print()

def equal(list1, list2):
	'''判断两个列表中的 mos 是否完全相同'''
	same_node = 0
	if len(list1) != len(list2):
		return(False)
	for mos1 in list1:
		for mos2 in list2:
			if mos1.number == mos2.number:
				same_node += 1
			else:
				continue
	if same_node == len(list1):
		return(True)
	else:
		return(False)

def has_same_mos(list1, list2):
	'''判断两个列表中是否含有相同mos
 	遇到一个相同的便马上停止 返回 True'''
	for mos1 in list1:
		for mos2 in list2:
			if mos1.number == mos2.number:
				return(True)
			else:
				continue

def same_node_num(node, list):
	'''用来寻找在一个 list 中某个 node 跟几个 node 相连 进而判断是串联还是并联'''
	same_node_number = 0
	for mos in list:
		if mos.source == node or mos.source == node or mos.drain == node or mos.drain == node:
			same_node_number += 1
	return(same_node_number)

def find_shared_mos(list1, list2):
	shared_mos = []
	for mos1 in list1:
		for mos2 in list2:
			if mos1.number == mos2.number:
				shared_mos.append(mos1)
			else:
				continue
	return(shared_mos)

def find_shared_node(mos1, mos2):
	"""寻找两个 mos 之间连接的 node"""
	if mos1.drain == mos2.drain or mos1.drain == mos2.source:
		return(mos1.drain)
	elif mos1.source == mos2.drain or mos1.source == mos2.source:
		return(mos1.source)

def create_path(mos, mid_node, bot_level_nmos, circuit_mlist):
	'''根据 top_level_mos 中的 mos, 中间 node, 最下层的 bot_level_nmos 创建一个 path'''
	path = []
	#填加最上方的 mos
	path.append(mos)

	#查找最上层 mos 和中间 mos 的 shared_node, 并判断此 shared_node 是否为分歧点
	shared_node_1_name = find_shared_node(mos, mid_node)
	same_node_number_1 = same_node_num(shared_node_1_name, circuit_mlist)
	shared_node_1 = Node(shared_node_1_name)
	if same_node_number_1 > 2:
		shared_node_1.fork = 1
	path.append(shared_node_1)
	path.append(mid_node)
	mid_node.searched = 1 #标记搜索过的中间 mos

	#填加最下层的 mos
	for bot_nmos in bot_level_nmos:
		if bot_nmos.searched == 0:
			if (mid_node.drain == bot_nmos.drain or mid_node.drain == bot_nmos.source) or (mid_node.source == bot_nmos.drain or mid_node.source == bot_nmos.source):
				shared_node_2_name = find_shared_node(mid_node, bot_nmos)
				same_node_number_2 = same_node_num(shared_node_2_name, circuit_mlist)
				shared_node_2 = Node(shared_node_2_name)
				if same_node_number_2 > 2:
					shared_node_2.fork = 1
				path.append(shared_node_2)
				path.append(bot_nmos)
				bot_nmos.searched = 1 #标记被搜索过的最下层 mos
	return(path)

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
			
			#subtract部分是否要处理 以后再讨论 现在 NMOS tree 的处理已经完成 2014.11.13
			if subtract:                               #如果指定抽取某一 subcircuit
				print('Cell name :', subtract)
				for circuit in list_of_circuits:
					if re.findall(r'\b%s\b'%subtract, circuit.name):  #找到想要抽取的 subcircuit 的 instance
						list_of_m = circuit.m_list()    #把 subcircuit 以 m 开头的部分填加到 list_of_m list 中
						circuit.mosfet([m_part.split() for m_part in list_of_m]) #[]:对于 list_of_m 中的每个部分以空格分隔开来 ['m1 out in'] -> ['m1', 'out', 'in']
																				   #之后调用 circuit 类型的 mosfet 函数把每个 m 的信息保存成一个 mosfet
						#print('Netlist')
						#for i in circuit.mos:
						#	print(i.number, i.drain, i.gate, i.source, i.bulk, i.type)
						pipeline1, pipeline2 = circuit.find_entire_path()
						display_pipeline(pipeline1, 'pipeline1', circuit)
						display_pipeline(pipeline2, 'pipeline2', circuit)


			else:                     				   #若未指定 subcircuit 则输出整个 netlist
				top_level_circuit = list_of_circuits[-1]
				print('Cell name :', top_level_circuit.name)
				top_level_circuit.mosfet([m_part.split() for m_part in top_level_circuit.m_list()])
				pipeline1, pipeline2 = top_level_circuit.find_entire_path()
				display_pipeline(pipeline1, 'pipeline1', top_level_circuit)
				display_pipeline(pipeline2, 'pipeline2', top_level_circuit)

			#output.write("width =" + str(total_width) + "u")
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