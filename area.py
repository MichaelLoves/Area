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
		self.list_of_blocks = []	   #用处储存根据 path 生成的 block 的排列

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

class Group:
	"""保存 NMOS tree 之中每一小块的 mos 信息"""
	def __init__(self):
		self.top_mos = []
		self.mid_mos = []
		self.bot_mos = []
		self.mos_list = []
		self.main_path_list = []
		self.path_list = []
		self.top_node_list = []

	#遍历寻找 group 中的 main_path 并添加到 main_path_list 之中
	def find_main_path(self):
		main_path_list = []
		for top_mos in self.top_mos:
			path = []

			mid_mos_list = []
			for mid_mos in self.mid_mos:
				if find_shared_node(top_mos, mid_mos):
					mid_mos_list.append(mid_mos)

			for mid_mos in mid_mos_list:
				bot_mos_list = []
				for bot_mos in self.bot_mos:
					if find_shared_node(mid_mos, bot_mos):
						bot_mos_list.append(bot_mos)

			for mid_mos in mid_mos_list:
				for bot_mos in bot_mos_list:
					path.append([top_mos, mid_mos, bot_mos])

			self.main_path_list.extend(path)

	#查找并返回除了 main_path 之外的 mos
	def find_unsearched_mos(self, main_path):
		mos_list = deepcopy(self.mos_list)
		main_path = deepcopy(main_path)
		unsearched_mos_list = []

		#初始化所有 mos 的 searched 状态
		for mos in mos_list:
			mos.searched = 0
		
		#标记 main_path 中的 mos 的 searched 为1
		for mos1 in mos_list:
			for mos2 in main_path:
				if mos1.number == mos2.number:
					mos1.searched = 1

		#抽取其他 searched == 0 的 mos
		for mos in mos_list:
			if mos.searched == 0:
				unsearched_mos_list.append(mos)

		return(unsearched_mos_list)


class Pipeline:
	"""在寻找 path 的时候用来储存 top_level_mos, bot_level_mos 和 path"""
	def __init__(self):
		self.precharge_PMOS = []
		self.foot_NMOS = []
		self.top_node_1 = ''
		self.top_node_2 = ''
		self.bot_node = ''
		self.top_mos = []
		self.mid_mos = []
		self.bot_mos = []
		self.top_mid_node = []
		self.mid_bot_node = []
		self.path = []

class Circuit:
	"""保存 netlist 中各部分 circuit 的 cell name 和 netlist"""
	def __init__(self, name, netlist):
		self.name = name        			    #circuit 的 cell name
		self.netlist = netlist   				#circuit 的 netlist 类型为 list
		self.mos_list = []						#用来储存 circuit 中所有 mos 的信息  mos 每部分均为 class mosfet 的 instance  ['m0', 'm1'...]
		self.path = []
		self.subcircuit_netlist = []			#储存 subcircuit 的类型
		self.subcircuit_num = {}				#储存 subcircuit 对应的数量
		self.block = []
		self.block_length = 0
		self.pipeline = []

	def create_mos_list(self):           	    #返回 netlist 中仅以 m 开头的部分
		list = []
		for part in self.netlist:
			if re.findall(r'\bm\w*\b', part):   #判断这行首字母是否以 m 开头
				list.append(part)				#若首字母以"m"开头 填加到 list 里面
		return(list)

	def line_m_list(self):                      #返回读入 mos_list 的行数, 即 m 部分的个数
		return(len(self.create_mos_list()))

	def create_mosfet(self, list_of_m):                #读取一个包含 m 信息的 list 之后封装在每个 MOSFET 类型的 instance 中 最后保存在 self.mos_list list 中
		line_num = len(self.create_mos_list())
		for i in range(line_num):
			self.mos_list.append('m%d' %i)  #把列表填满 m1, m2... 之后再用每一项去创建一个class MOSFET 的 instance
			self.mos_list[i] = (MOSFET(list_of_m[i][0], list_of_m[i][1], list_of_m[i][2], \
							 list_of_m[i][3], list_of_m[i][4], list_of_m[i][5], list_of_m[i][6].strip("L=").strip("e-9"), list_of_m[i][7].strip('W=')))
			self.mos_list[i].L = float(self.mos_list[i].L)/1000.   #把gate的L(比如180)换算为0.18 单位为 u
			if 'e-6' in self.mos_list[i].W:
				self.mos_list[i].W = float(self.mos_list[i].W.strip('e-6'))
			else:
				self.mos_list[i].W = float(self.mos_list[i].W.strip('e-9'))/1000.

	def create_subcircuit(self, circuit_list):
		"""用来给 CD circuit 等包含进一层 subcircuit 的 subcircuit 填加 subcircuit """
		#找出都有哪些 subcircuit
		subcircuit_list = []
		temp = []
		for line in self.netlist:
			if re.findall(r'\bxi\w*\b', line):
				temp.append(line.split()[-1])
		subcircuit_list = sorted(set(temp), key = temp.index)

		#在整个 netlist 中寻找那些 subcircuit 并填加到 subcircuit_netlist 中
		for circuit in circuit_list:
			if circuit.name in subcircuit_list:
				self.subcircuit_netlist.append(circuit)

	def calculate_subcircuit(self):
		"""用来计算一个电路中的 subcircuit 的个数"""

		#储存从电路的 netlist 中获取的 subcircuit 的信息, 即以 xi 开头的部分
		subcircuit_list = []
		for line in self.netlist:
			if re.findall(r'\bxi\w*\b', line):
				subcircuit_list.append(line.split()[-1])

		#储存 subcircuit 的名称
		subcircuit_names = []
		for part in self.subcircuit_netlist:
			subcircuit_names.append(part.name)

		#统计各个 subcircuit 的数量
		for part in subcircuit_list:
			self.subcircuit_num[part] = 0
		for part in subcircuit_list:
			if part in subcircuit_names:
				self.subcircuit_num[part] += 1

	#貌似没什么用了呀...
	def select_top_mos(self, top_mos, pipeline):
		top_mos_list = []

		for mid_mos in pipeline.mid_mos:
			if find_shared_node(mid_mos, top_mos):
				middle_mos = mid_mos

		for top_mos in pipeline.top_mos:
			if find_shared_node(top_mos, middle_mos):
				top_mos_list.append(top_mos)

		if len(top_mos_list) == 1:
			return(top_mos_list[0])
		else:
			top_mos = self.fork(mid_mos, top_mos_list)
			return(top_mos)


	def fork(self, ori_mos, fork_mos_list):
		'''用来确定所读入 mos 的端子存在并联情况时优先选择哪一方'''
		'''读入需要分析的 mos 和与其并联的 mos 的 list'''
		path_list = []
		fork_mos_block_list = []

		#对于每一个分歧的 mos 创建一个与 ori_mos 串联的 path
		for mos in fork_mos_list:       
			temp = []
			temp.append(ori_mos)
			shared_node = Node(find_shared_node(ori_mos, mos))
			temp.append(shared_node)
			temp.append(mos)
			path_list.append(temp)

		#利用内建的 creat_block 函数获取每个 path 的长度 并添加到列表的最末端
		for path in path_list:      
			path.append(self.create_block(path).L)  

		#根据长度重新排列并返回最小L的path中的 mos
		path_list.sort(key = lambda path:path[-1])

		return(path_list[0][2])

	#对于读入的 path 生成 block 返回 block 的 list 
	def create_block(self, path):
		"""根据读入的 path 生成 layout 模块, path的内容为 MOSFET 和 Node 类型的混合 list
		   返回一个 block, 其中包含的内容为: 作为 block_name 的 path_name, L, W, block 列表
		"""
		entire_block = []     #用于储存每个小 block
		path_name = []		  #读入 path 的名称, 用来当做 block_name
		entire_block_L = 0    #整个 block 的宽度
		entire_block_W = 0	  #整个 block 的高度
		list_of_block_W = []  #储存每个 block 的高度, 以便找出最高的部分

		#先判断需要计算的 path 中是否只包含一个 mos
		if len(path) == 1:
			entire_block.append(Block('edge_contact' ,0.48, path[0].W)) 		  #填加一个边缘处的 edge_contact
			entire_block.append(Block('gate', 0.18, path[0].W+0.22*2))			  #填加一个 gate
			entire_block.append(Block('edge_contact' ,0.48, path[0].W))			  #填加一个边缘处的 edge_contact
		else:
			#填加 gate 时的 W 需要再根据左右连接处的 W 来判断一下
			entire_block.append(Block('edge_contact' ,0.48, path[0].W)) 		  #填加一个边缘处的 edge_contact
			for part in path[:-2]:
				if isinstance(part, MOSFET):
					entire_block.append(Block('gate', part.L, part.W+0.22*2))       #填加一个 gate
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
			entire_block.append(Block('gate', 0.18, path[-1].W+0.22*2))		  #因为上面逻辑只能填加到倒数第二个 mos 的右侧的部分 所以手动填加最右侧的 gate
			entire_block.append(Block('edge_contact' ,0.48, path[-1].W))      #填加最右面的 edge_contact
			entire_block.append(Block('diff_space', 0.28, path[-1].W))

		#用 path 的名称来命名此 block
		for part in path:
			path_name.append(part.number)

		#决定 block 中最大的高度 W
		for part in entire_block:
			if part.block_name == 'gate':
				list_of_block_W.append(round(part.W, 2))
		entire_block_W = max(list_of_block_W)

		#决定 block 的长度 L
		for block in entire_block:
			entire_block_L += block.L
		entire_block_L = round(entire_block_L, 2)

		path_block = Block(path_name, entire_block_L, entire_block_W)
		path_block.list_of_blocks = entire_block

		return(path_block)

	#输入两个点 找出两点间(未被搜索过)的 mos
	def search_mid_mos(self, top_node, bot_node):
		list = []
		for mos in self.mos_list:
			if mos.searched == 0:
				if (mos.drain == top_node or mos.source == top_node) and (mos.drain == bot_node or mos.source == bot_node):
					list.append(mos)
		return(list)

	def create_path_for_subcircuit(self, subcircuit):
		subcircuit_path = []
		main_path = []
		top_mos_list = []
		mid_mos_list = []
		bot_mos_list = []

		if subcircuit.name == 'inv' or subcircuit.name == 'inv2':
			for mos in subcircuit.mos_list:
				if mos.drain == 'vdd' or mos.source == 'vdd':
					top_mos = mos
				else:
					bot_mos = mos
			subcircuit_path.append(top_mos)
			shared_node_name = find_shared_node(top_mos, bot_mos)
			shared_node = Node(shared_node_name)
			subcircuit_path.append(shared_node)
			subcircuit_path.append(bot_mos)
			return(subcircuit_path)

		if subcircuit.name == 'inv_with_reset':
			for mos in subcircuit.mos_list:
				if mos.drain == 'vdd' or mos.source == 'vdd':
					top_mos = mos
				elif mos.drain == 'gnd' or mos.source == 'gnd':
					bot_mos_list.append(mos)
				else:
					mid_mos = mos
			main_path.append(top_mos)
			shared_node_1_name = find_shared_node(top_mos, mid_mos)
			shared_node_1 = Node(shared_node_1_name)
			main_path.append(shared_node_1)
			main_path.append(mid_mos)
			bot_mos = self.fork(mid_mos, bot_mos_list)
			bot_mos.searched = 1
			shared_node_2_name = find_shared_node(mid_mos, bot_mos)
			shared_node_2 = Node(shared_node_2_name)
			main_path.append(shared_node_2)
			main_path.append(bot_mos)
			isolated_bot_mos = []
			for bot_mos in bot_mos_list:
				if bot_mos.searched == 0:
					isolated_bot_mos.append(bot_mos)
			subcircuit_path.append(main_path)
			subcircuit_path.append(isolated_bot_mos)
			return(subcircuit_path)

		if subcircuit.name == 'or':
			for mos in subcircuit.mos_list:
				if mos.drain == 'vdd' or mos.source == 'vdd':
					top_mos_list.append(mos)
				elif mos.drain == 'gnd' or mos.source == 'gnd':
					bot_mos = mos
				else:
					mid_mos = mos
			top_mos = self.fork(mid_mos, top_mos_list)
			main_path.append(top_mos)
			top_mos.searched = 1
			shared_node_1_name = find_shared_node(top_mos, mid_mos)
			shared_node_1 = Node(shared_node_1_name)
			shared_node_1.fork = 1
			main_path.append(shared_node_1)
			main_path.append(mid_mos)
			shared_node_2_name = find_shared_node(mid_mos, bot_mos)
			shared_node_2 = Node(shared_node_2_name)
			main_path.append(shared_node_2)
			main_path.append(bot_mos)
			isolated_top_mos = []
			for top_mos in top_mos_list:
				if top_mos.searched == 0:
					isolated_top_mos.append(top_mos)
			subcircuit_path.append(main_path)
			subcircuit_path.append(isolated_top_mos)
			return(subcircuit_path)

		#if subcircuit.name == 'cd circuit'

	def create_path_for_mid_bot(self, mid_mos, pipeline):
		'''为了 mid_mos 和 bot_mos 生成 path'''
		mid_bot_path = []
		bot_mos_list = []

		if mid_mos.drain in pipeline.mid_bot_node:
			bot_mos_list.extend(self.search_mid_mos(mid_mos.drain, pipeline.bot_node))
		else:
			bot_mos_list.extend(self.search_mid_mos(mid_mos.source, pipeline.bot_node))

		if len(bot_mos_list) == 1:
			bot_mos = bot_mos_list[0]
			mid_bot_path.append(mid_mos)
			shared_node_name = find_shared_node(mid_mos, bot_mos)
			same_node_number = same_node_num(shared_node_name, self.mos_list)
			shared_node = Node(shared_node_name)
			if same_node_number > 2:
				shared_node.fork = 1
			mid_bot_path.append(shared_node)
			mid_bot_path.append(bot_mos)
			bot_mos.searched = 1
			pipeline.path.append(mid_bot_path)

		elif len(bot_mos_list) >= 2:
			bot_mos = self.fork(mid_mos, bot_mos_list)
			mid_bot_path.append(mid_mos)
			shared_node_name = find_shared_node(mid_mos, bot_mos)
			same_node_number = same_node_num(shared_node_name, self.mos_list)
			shared_node = Node(shared_node_name)
			if same_node_number > 2:
				shared_node.fork = 1
			mid_bot_path.append(shared_node)
			mid_bot_path.append(bot_mos)
			bot_mos.searched = 1
			pipeline.path.append(mid_bot_path)

		else:
			isolated_mid_mos = []
			isolated_mid_mos.append(mid_mos)
			pipeline.path.append(isolated_mid_mos)

	def create_path_for_top_mid_bot(self, top_mos, pipeline):
		"""生成整个 pipeline 的 path 原 find_entire_path 函数中最后的部分
		为了减少根据 mos 的 drain 和 source 不同位置的两种情况而产生的冗长性, 定义为一个函数
		根据找到的 mid_mos_list 中 mos 的个数分为三种情况
		1个的时候 直接添加进去; 2个以上的时候 用 fork 函数选出连接部分较小的一个; 没有的时候直接填加 top_mos 到 path 中
		虽然代码存在一定的重复性 但是比起再定义一个单独的函数 结构上更加简洁 不易造成混乱"""
		top_mid_bot_path = []
		mid_mos_list = []

		#分为 top_mos.drain 在 top_search_node列表中还是 top_mos.source 在列表中两种情况
		#因此在 creat_pipeline_path 中的第一个参数 search_node 不同					
		if top_mos.drain in pipeline.top_mid_node:			
			search_node = top_mos.drain
		else:
			search_node = top_mos.source

		# 查找top_level_nmos 的下端和 pipeline.bot_node 之间的仍未被搜索过的 mos
		for node in pipeline.mid_bot_node:
			mid_mos_list.extend(self.search_mid_mos(search_node, node))

		#根据 mid_mos_list 的长度来判断连接情况
		#长度为1是串联 长度大于等于2是并联 若不包含任何元素则直接将 top_level_nmos 作为独立 part 填加到 pipeline_path
		#mos 与下面的 mos 串联时 直接将 mid_mos 填加到 path 中
		if len(mid_mos_list) == 1:
			#mid_mos 就是list 中的唯一一个元素
			mid_mos = mid_mos_list[0]	
			
			#首先先在 top_mid_bot_path 中添加 top_mos 并标记 searched = 1
			top_mid_bot_path.append(top_mos)
			top_mos.searched = 1

			#查找最上层 mos 和中间 mos 的 shared_node, 并判断此 shared_node 是否为分歧点
			shared_node_1_name = find_shared_node(top_mos, mid_mos)
			same_node_number_1 = same_node_num(shared_node_1_name, self.mos_list)
			shared_node_1 = Node(shared_node_1_name)
			if same_node_number_1 > 2:
				shared_node_1.fork = 1
			top_mid_bot_path.append(shared_node_1)
			top_mid_bot_path.append(mid_mos)
			mid_mos.searched = 1 #标记搜索过的中间 mos

			#寻找 mid_mos 和 bot_mos 的连接点
			if mid_mos.drain == shared_node_1_name:
				shared_node_2_name = mid_mos.source
			else:
				shared_node_2_name = mid_mos.drain
			same_node_number_2 = same_node_num(shared_node_2_name, self.mos_list)
			shared_node_2 = Node(shared_node_2_name)
			if same_node_number_2 > 2:
				shared_node_2.fork = 1

			#填加最下层的 mos
			bot_mos_list = [] 
			bot_mos_list.extend(self.search_mid_mos(shared_node_2_name ,pipeline.bot_node))
			if len(bot_mos_list) == 1:
				top_mid_bot_path.append(shared_node_2)
				top_mid_bot_path.extend(bot_mos_list)
				bot_mos_list[0].searched = 1
			elif len(bot_mos_list) >= 2:
				top_mid_bot_path.append(shared_node_2)
				bot_mos = self.fork(mid_mos, bot_mos_list)
				top_mid_bot_path.append(bot_mos)
				bot_mos.searched = 1
			elif len(bot_mos_list) == 0:
				pass
			pipeline.path.append(top_mid_bot_path)

		#mos 与下面的 mos 并联时 需要从 mid_mos_list 中挑选与 mos 连接部分面积较小的一方
		elif len(mid_mos_list) >= 2:
			#mid_mos 为 list 中与 top_mos 连接部分较小的一个 之后的内容与上面相同
			mid_mos = self.fork(top_mos, mid_mos_list)	

			#首先先在 top_mid_bot_path 中添加 top_mos 并标记 searched = 1
			top_mid_bot_path.append(top_mos)
			top_mos.searched = 1

			#查找最上层 mos 和中间 mos 的 shared_node, 并判断此 shared_node 是否为分歧点
			shared_node_1_name = find_shared_node(top_mos, mid_mos)
			same_node_number_1 = same_node_num(shared_node_1_name, self.mos_list)
			shared_node_1 = Node(shared_node_1_name)
			if same_node_number_1 > 2:
				shared_node_1.fork = 1
			top_mid_bot_path.append(shared_node_1)
			top_mid_bot_path.append(mid_mos)
			mid_mos.searched = 1 #标记搜索过的中间 mos

			#寻找 mid_mos 和 bot_mos 的连接点
			if mid_mos.drain == shared_node_1_name:
				shared_node_2_name = mid_mos.source
			else:
				shared_node_2_name = mid_mos.drain
			same_node_number_2 = same_node_num(shared_node_2_name, self.mos_list)
			shared_node_2 = Node(shared_node_2_name)
			if same_node_number_2 > 2:
				shared_node_2.fork = 1

			#填加最下层的 mos
			bot_mos_list = [] 
			bot_mos_list.extend(self.search_mid_mos(shared_node_2_name ,pipeline.bot_node))
			if len(bot_mos_list) == 1:
				top_mid_bot_path.append(shared_node_2)
				top_mid_bot_path.extend(bot_mos_list)
				bot_mos_list[0].searched = 1
			elif len(bot_mos_list) >= 2:
				top_mid_bot_path.append(shared_node_2)
				bot_mos = self.fork(mid_mos, bot_mos_list)
				top_mid_bot_path.append(bot_mos)
				bot_mos.searched = 1
			pipeline.path.append(top_mid_bot_path)

		#若下侧的 mid_mos 都被搜索过了 则这个 top_mos 作为独立元素填加到 pipeline_path 中		
		else:
			isolated_top_mos = []
			isolated_top_mos.append(top_mos)
			top_mos.searched = 1
			pipeline.path.append(isolated_top_mos)

	#下面三个函数可以留作以后写其他版本的时候使用
	def find_next_mos(self, ori_mos, search_node, search_list):
		next_mos_list = []

		for node in search_list:
			next_mos_list.extend(self.search_mid_mos(search_node, node))

		if len(next_mos_list) == 1:
			next_mos_list[0].searched = 1
			return(next_mos_list[0])
		elif len(next_mos_list) >= 2:
			next_mos = self.fork(ori_mos, next_mos_list)
			next_mos.searched = 1
			return(next_mos)
		else:
			#return(ori_mos)
			return(None)

	def merge_path(self, path_1, path_2):
		'''读入两个 path 去除其中重复的 mos 
		以长度 L 短的一方作为 main_path 去除相同元素后的另一方作为 isolated_path'''

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

	def create_path_2(self, top_mos, pipeline):
		if top_mos.drain in pipeline.top_mid_node:
			mid_mos = self.find_next_mos(top_mos, top_mos.drain, pipeline.mid_bot_node)
			if mid_mos.drain in pipeline.mid_bot_node:
				bot_mos = self.find_next_mos(mid_mos, mid_mos.drain, pipeline.bot_node)
			else:
				temp = []
				temp.append(pipeline.bot_node)
				bot_mos = self.find_next_mos(mid_mos, mid_mos.source, temp)
		else:
			pipeline.path.append(top_mos)
			mid_mos = self.find_next_mos(top_mos, top_mos.source, pipeline.mid_bot_node)
			if mid_mos:
				pipeline.path.append(mid_mos)
				if mid_mos.drain in pipeline.mid_bot_node:
					bot_mos = self.find_next_mos(mid_mos, mid_mos.drain, pipeline.bot_node)
					pipeline.path.append(bot_mos)
				else:
					temp = []
					temp.append(pipeline.bot_node)
					bot_mos = self.find_next_mos(mid_mos, mid_mos.source, temp)
					pipeline.path.append(bot_mos)


	def find_all_path(self):
		print('test for find all path' + '*'*40)

		#因为还在调试阶段 使用前先初始化所有 mos.searched 的状态为0
		#*** 此部分需要后续更改 ***#	
		pipeline = deepcopy(self.pipeline[0])
		for mos in pipeline.top_mos:
			mos.searched = 0
		for mos in pipeline.mid_mos:
			mos.searched = 0
		for mos in pipeline.bot_mos:
			mos.searched = 0

		#寻找 NMOS tree 中的每一小部分 作为一个 group 保存起来
		group_list = []
		top_node_list = [pipeline.top_node_1, pipeline.top_node_2]

		#以top_mid_node 和 mid_bot_node 中个数较少的一方来决定 group 的个数
		#以 top_mid_node 为基准时 从上往下找; 以 mid_bot_node 为基准时 从下往上找
		if len(pipeline.top_mid_node) < len(pipeline.mid_bot_node):
			for top_mid_node in pipeline.top_mid_node:
				#以每个 node 为基点创建一个 group
				group = Group()

				#填加 group 中的 top_mos
				for top_node in top_node_list:
					top_mos = find_mid_mos(pipeline.top_mos, top_node, top_mid_node)
					if top_mos:
						group.top_mos.extend(top_mos)

				#top_mos 存在复数的情况 可随意从中抽取一个用来寻找 mid_mos
				top_mos = group.top_mos[0]
				for mid_mos in pipeline.mid_mos:
					if find_shared_node(top_mos, mid_mos):
						group.mid_mos.append(mid_mos)

				#判断 mid_mos 处是否存在分歧, 即 mid_mos 的不与 top_mos 连接的一端是否分开
				if len(group.mid_mos) == 1:
					mid_mos = group.mid_mos[0]
					for bot_mos in pipeline.bot_mos:
						if find_shared_node(mid_mos, bot_mos):
							group.bot_mos.append(bot_mos)
				else:
					for mid_mos in group.mid_mos:
						for bot_mos in pipeline.bot_mos:
							if find_shared_node(mid_mos, bot_mos):
								group.bot_mos.append(bot_mos)

				#除去重复数据 并将 group 填加到 group_list 中
				group.top_mos = sorted(set(group.top_mos), key = group.top_mos.index)
				group.mid_mos = sorted(set(group.mid_mos), key = group.mid_mos.index)
				group.bot_mos = sorted(set(group.bot_mos), key = group.bot_mos.index)
				group.top_node_list = top_node_list
				group_list.append(group)

		else:
			for mid_bot_node in pipeline.mid_bot_node:
				group = Group()
				bot_mos = find_mid_mos(pipeline.bot_mos, mid_bot_node, pipeline.bot_node)
				if bot_mos:
					group.bot_mos.extend(bot_mos)

				bot_mos = group.bot_mos[0]
				for mid_mos in pipeline.mid_mos:
					if find_shared_node(mid_mos, bot_mos):
						group.mid_mos.append(mid_mos)

				if len(group.mid_mos) == 1:
					mid_mos = group.mid_mos[0]
					for top_mos in pipeline.top_mos:
						if find_shared_node(mid_mos, top_mos):
							group.top_mos.append(top_mos)
				else:
					for mid_mos in group.mid_mos:
						for top_mos in pipeline.top_mos:
							if find_shared_node(mid_mos, top_mos):
								group.top_mos.append(top_mos)

				group.top_mos = sorted(set(group.top_mos), key = group.top_mos.index)
				group.mid_mos = sorted(set(group.mid_mos), key = group.mid_mos.index)
				group.bot_mos = sorted(set(group.bot_mos), key = group.bot_mos.index)
				group.mos_list.extend(group.top_mos)
				group.mos_list.extend(group.mid_mos)
				group.mos_list.extend(group.bot_mos)
				group.top_node_list = top_node_list
				group_list.append(group)

		
		#输出各个 group 的信息	
		'''
		print('group_list')
		for group in group_list:
			print('top_mos')
			for mos in group.top_mos:
				print(mos.number)
			print('mid_mos')
			for mos in group.mid_mos:
				print(mos.number)
			print('bot_mos')
			for mos in group.bot_mos:
				print(mos.number)
			print()
		'''


		#寻找每个 group 中的 main_path 并添加到自己的 main_path_list 中
		for group in group_list:
			group.find_main_path()

		'''
		#输出每个 group 的 main_path 的信息
		for group in group_list:
			print('main_path_list')
			for path in group.main_path_list:
				display('path', path)
			print()	
		#'''

		for group in group_list:
			sub_path_list = find_combination(group)
			#print('sub_path_list')
			#print(sub_path_list)
			
		
		'''
		#print('group.path_list')
		#print(group.path_list)
		for part in group.path_list:
			print('***'*10)
			display('main path', part[0], newline = 0)	
			print('left part')
			for item in part[1]:
				if isinstance(item, MOSFET):
					print(item.number + ' ', end = '')
				else:
					display('', item, newline = 0)
			print()
			print('***'*10)
		print()
		'''


	def find_pipeline_path(self, pipeline):
		"""对于读入的 pipeline 返回其 path"""

		#首先 根据已知的 precharge_PMOS 和 foot_NMOS 来查找各种信息
		#top_node_1, top_node_2, bot_node, top_mos, mid_mos, bot_mos, top_mid_node, mid_bot_node
		#top_node_1: precharge PMOS 下面 NAND 侧的编号 
		#top_node_2: precharge PMOS 下面 AND 侧的编号
		#bot_node: foot NMOS 上面的编号
		#因为 netlist 中的 drain 和 source 是对称的 所以需要考虑两次
		if pipeline.precharge_PMOS[0].drain == 'vdd':
			pipeline.top_node_1 = pipeline.precharge_PMOS[0].source
		else:
			pipeline.top_node_1 = pipeline.precharge_PMOS[0].drain
		if pipeline.precharge_PMOS[1].drain == 'vdd':
			pipeline.top_node_2 = pipeline.precharge_PMOS[1].source
		else:
			pipeline.top_node_2 = pipeline.precharge_PMOS[1].drain
		if pipeline.foot_NMOS[0].drain == 'gnd':
			pipeline.bot_node = pipeline.foot_NMOS[0].source
		else:
			pipeline.bot_node = pipeline.foot_NMOS[0].drain
		
		#找出与最上面的 precharge_PMOS 相连的一排 top_mos
		for mos in self.mos_list:
			if mos.type == 'N' and (pipeline.top_node_1 == mos.drain or pipeline.top_node_1 == mos.source or pipeline.top_node_2 == mos.drain or pipeline.top_node_2 == mos.source):
				pipeline.top_mos.append(mos)

		#找出与最下面的 foot_NMOS 相连的一排 bot_mos
		for mos in self.mos_list:
			if mos.type == 'N' and (mos.drain == pipeline.bot_node or mos.source == pipeline.bot_node) and mos.drain != 'gnd' and mos.source != 'gnd':
				pipeline.bot_mos.append(mos)

		#top_mos 下面的 net 编号 top_mid_node
		temp1 = []
		for mos in pipeline.top_mos:
			if mos.drain == pipeline.top_node_1 or mos.drain == pipeline.top_node_2:
				temp1.append(mos.source)
				pipeline.top_mid_node = sorted(set(temp1), key = temp1.index)
			else:
				temp1.append(mos.drain)
				pipeline.top_mid_node = sorted(set(temp1), key = temp1.index)
			
		#bot_mos 上面的 net 编号 mid_bot_node
		temp2 = []
		for mos in pipeline.bot_mos:
			if mos.drain == pipeline.bot_node and mos.source != 'gnd':
				temp2.append(mos.source)
				pipeline.mid_bot_node = sorted(set(temp2), key = temp2.index)
			elif mos.source == pipeline.bot_node:
				temp2.append(mos.drain)
				pipeline.mid_bot_node = sorted(set(temp2), key = temp2.index)

		#找出 top_mos 与 bot_mos 中间的 mid_mos
		temp3 = []
		for mos in pipeline.top_mos:
			if mos.drain in pipeline.top_mid_node:
				for node in pipeline.mid_bot_node:
					temp3.extend(self.search_mid_mos(mos.drain, node))
					pipeline.mid_mos = sorted(set(temp3), key = temp3.index)
			else:
				for node in pipeline.mid_bot_node:
					temp3.extend(self.search_mid_mos(mos.source, node))
					pipeline.mid_mos = sorted(set(temp3), key = temp3.index)

		'''从每一个 top_level_nmos 里的 mos 出发 因为还是涉及到 drain 和 source 对称的问题 所以分为两个部分 但是做的事情是完全一致的
		确认最上排 mos 下面的点和最下排 mos 上面的点 比如 net28 和 net16 之后找到两个点之间所有可能的路径 作为一个 list 返回
		之后对于 list 中的每条路径 加上最上排的 mos 和最下排的 mos 组成完整的三段路径'''
		#top_mos 的总数, 用来控制循环的总次数
		num_of_top_mos = len(pipeline.top_mos)
		#记录 top_mos 里面被 search 过了的个数, 一旦与 top_mos 总数相等, 进入 mid_mos 的遍历
		num_of_searched_top_mos = 0

		while num_of_searched_top_mos < num_of_top_mos:
			for top_mos in pipeline.top_mos:
				if top_mos.searched == 0:
					#寻找 top_mos 和下方 mid_mos 的连接点
					shared_node_list = []
					for mid_mos in pipeline.mid_mos:
						shared_node = find_shared_node(top_mos, mid_mos)
						if shared_node:
							shared_node_list.append(shared_node)
					shared_node = shared_node_list[0]

					#查找与下方 mid_mos 连接的 top_mos 并判断是否存在两个以上
					top_mos_list = []
					for top_mos in pipeline.top_mos:
						if (top_mos.drain == shared_node or top_mos.source == shared_node) and top_mos.searched == 0:
							top_mos_list.append(top_mos)
					for mos in pipeline.mid_mos:
						if mos.searched == 0:
							if mos.drain == shared_node or mos.source == shared_node:
								mid_mos = mos

					#有多个 top_mos 与 mid_mos 连接 需要选择一个连接部分最小的一方来创建 path
					if len(top_mos_list) >= 2:
						top_mos = self.fork(mid_mos, top_mos_list)
						self.create_path_for_top_mid_bot(top_mos, pipeline)
						num_of_searched_top_mos += 1

					#只有一个或者0个 top_mos 与此 mid_mos 连接时
					elif len(top_mos_list) == 1:
						self.create_path_for_top_mid_bot(top_mos_list[0], pipeline)
						num_of_searched_top_mos += 1


		#遍历完 top_mos 之后遍历 mid_mos 选出还未被 search 过的, 判断能不能与 bot_mos 组成一个 path
		for mid_mos in pipeline.mid_mos:
			if mid_mos.searched == 0:
				self.create_path_for_mid_bot(mid_mos, pipeline)

		#最后遍历 bot_mos 选出还未被 search 的 mos
		for bot_mos in pipeline.bot_mos:
			if bot_mos.searched == 0:
				isolated_bot_mos = []
				isolated_bot_mos.append(bot_mos)
				pipeline.path.append(isolated_bot_mos)

		return(pipeline)

	def find_entire_path(self):
		"""找出两个 pipeline 的 path 并一起返回"""
		#先找到所有的 precharge_PMOS 和 foot_NMOS 之后分给每个 pipeline
		precharge_PMOS = []
		precharge_PMOS_gate = []
		foot_NMOS = []

		#找出 precharge PMOS 和 foot NMOS
		temp1 = []
		temp2 = []
		temp3 = []
		for part in self.mos_list:		
			for part2 in self.mos_list:
				if part.type == 'P' and part.gate == part2.gate and part.number != part2.number:
					temp1.append(part)
		precharge_PMOS = sorted(set(temp1), key=temp1.index)  #去处相同元素而不打乱顺序

		for mos in precharge_PMOS:             #获得两边最上端 PMOS 的 gate 的信号 好找到与之对应的 foot NMOS 
			temp2.append(mos.gate)
		precharge_PMOS_gate = list(set(temp2)) #[cd_n, precharge]
		
		for part in self.mos_list:
			if part.type == 'N' and part.gate in precharge_PMOS_gate:
				foot_NMOS.append(part)

		#创建两个 pipeline class 用来保存各自的 precharge_PMOS 和 foot_NMOS 但每次 pipeline 的顺序有可能改变
		pipeline1 = Pipeline()
		pipeline2 = Pipeline()
		for mos in precharge_PMOS:
			if mos.gate == precharge_PMOS_gate[0]:
				pipeline1.precharge_PMOS.append(mos)
			else:
				pipeline2.precharge_PMOS.append(mos)
		for mos in foot_NMOS:
			if mos.gate == pipeline1.precharge_PMOS[0].gate:
				pipeline1.foot_NMOS.append(mos)
			else:
				pipeline2.foot_NMOS.append(mos)
		'''
		print('Pipeline1')
		print('precharge_PMOS : ', end = '')
		for mos in pipeline1.precharge_PMOS:
			print(mos.number + '  ', end = '')
		print()
		print('foot_NMOS      : ', end = '')
		print(pipeline1.foot_NMOS[0].number)

		print('Pipeline2')
		print('precharge_PMOS : ', end = '')
		for mos in pipeline2.precharge_PMOS:
			print(mos.number + '  ', end = '')
		print()
		print('foot_NMOS      : ', end = '')
		print(pipeline2.foot_NMOS[0].number)
		'''
		self.find_pipeline_path(pipeline1)
		self.find_pipeline_path(pipeline2)

		self.pipeline.append(pipeline1)
		self.pipeline.append(pipeline2)

		return(pipeline1, pipeline2)
		
def display(func_name, list, newline = 1):
	print(func_name)
	if newline == 1:
		for item in list:
			if hasattr(item, 'number'):
				print(item.number)
			elif hasattr(item, 'name'):
				print(item.name)
			elif hasattr(item, 'block_name'):
				print(item.block_name)
	elif newline == 0:
		for item in list:
			if hasattr(item, 'number'):
				print(item.number + '  ', end = '')
			elif hasattr(item, 'name'):
				print(item.name + '  ', end = '')
			elif hasattr(item, 'block_name'):
				print(item.block_name + '   ', end = '')				
	print()

def display_pipeline(pipeline, pipeline_name, circuit):
	print(pipeline_name)
	total_length = 0
	for index, path in enumerate(pipeline):
		print('path  : ', end = '')
		for part in path:
			#if isinstance(part, Node):
			#	if part.fork == 1:
			#		print(part.number + '(fork)' + '   ', end = '')
			#	else:
			#		print(part.number + '   ', end = '')
			#else:
			#	print(part.number + '   ', end = '')
			print(part.number + '   ', end = '')
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

def find_mid_mos(search_list, top_node, bot_node):
	list = []
	for mos in search_list:
		if (mos.drain == top_node or mos.source == top_node) and (mos.drain == bot_node or mos.source == bot_node):
			list.append(mos)
	return(list)		

def find_shared_node(mos1, mos2):
	"""寻找两个 mos 之间连接的 node"""
	if mos1.drain == mos2.drain or mos1.drain == mos2.source:
		return(mos1.drain)
	elif mos1.source == mos2.drain or mos1.source == mos2.source:
		return(mos1.source)

def has_path(path_list, path):
	for every_path in path_list:
		for mos1 in every_path:
			for mos2 in path:
				if mos1.number == mos2.number:
					return(True)

def has_mos(path_list, mos):
	for mos1 in path_list:
		if mos1.number == mos.number:
			return(True)

def find_path(mos_list, top_node_list):
	path_list = []
	if mos_list:
		for mos1 in mos_list:
			start_mos = mos1
			for mos2 in mos_list:
				if find_shared_node(start_mos, mos2) and (find_shared_node(start_mos, mos2) not in top_node_list) and (mos2.number!= start_mos.number):
					path = []
					path.append(start_mos)
					start_mos.searched = 1
					path.append(mos2)
					mos2.searched = 1
				else:
					continue
			for mos in mos_list:
				if mos.searched == 0:
					path.append([mos])
			if not has_path(path_list, path):
				path_list.append(path)
	print('test for find_path')
	display('mos_list', mos_list)
	for part in path_list:
		display('path_list', part)
	return(path_list)


def find_combination(group):
	path_list = []
	temp_group = deepcopy(group)
	for main_path in temp_group.main_path_list:
		for mos in main_path:
			mos.searched = 1

		for top_mos in temp_group.top_mos:
			if top_mos.searched == 0:
				print('step1', top_mos.number)
				path = []
				path.append(main_path)

				mid_mos_list = []
				for mid_mos in temp_group.mid_mos:
					if find_shared_node(top_mos, mid_mos) and mid_mos.searched == 0:
						mid_mos_list.append(mid_mos)

				for mid_mos in mid_mos_list:
					bot_mos_list = []
					for bot_mos in temp_group.bot_mos:
						if find_shared_node(mid_mos, bot_mos) and bot_mos.searched == 0:
							bot_mos_list.append(bot_mos)

				if mid_mos_list:
					for mid_mos in mid_mos_list:
						path.append([top_mos, mid_mos])
						top_mos.searched = 1
						mid_mos.searched = 1
				else:
					path.append([top_mos])
					top_mos.searched = 1


				for mos in group.mos_list:
					unsearched_mos_list = []
					if (not has_mos([top_mos, mid_mos], mos)) and (not has_mos(main_path, mos)):
						unsearched_mos_list.append(mos)
					if len(unsearched_mos_list) == 1:
						path.append([unsearched_mos_list[0]])
					else:
						for mos1 in unsearched_mos_list:
							for mos2 in unsearched_mos_list:
								if find_shared_node(mos1, mos2) and mos1.number != mos2.number:
									path.append([mos1, mos2])
								else:
									path.append([mos1])
									path.append([mos2])

				top_mos.searched = 0
				for mid_mos in mid_mos_list:
					mid_mos.searched = 0

				for item in path:
					display('path', item, newline = 0)
				print()

				path_list.append(path)

		for mos in temp_group.mos_list:
			mos.searched = 0
		
		#print('path_list')
		#for item in path_list:
		#	if isinstance(item, list):
		#		display('path', item, newline = 0)
		#	else:
		#		print(item.number)
		print()

	return(list)




def has_subcircuit(netlist):
	for line in netlist:
		if re.findall(r'\bxi\w*\b', line):
			return(True)
		else:
			return(False)

def has_next_level_mos(mos, next_level_mos_list):
	for next_mos in next_level_mos_list:
		if mos.drain == next_mos.drain or mos.drain == next_mos.source or mos.source == next_mos.drain or mos.source == next_mos.source:
			return(True)

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
		list_of_circuits[i] = Circuit(file_list[splitter_list[i][0]+1].replace('** Cell name: ', '').strip('\n'), file_list[splitter_list[i][0]+4:splitter_list[i][1]]) #填加各 subcircuit 的 name 和 netlist
	list_of_circuits.append(Circuit(file_list[splitter_list[i][1]+2].replace('** Cell name: ', '').strip('\n'), file_list[splitter_list[i][1]+1:]))
	return(list_of_circuits)

def get_netlist_data(input_file, output_file = 'output.txt', subtract = 0):
	try:
		output = open(output_file, 'w')     		   #创建一个文件用来保存结果
		with open(input_file) as netlist_file:
			#做一个 standard cell, 其中包含一个 main_circuit(有N和P Pipeline)以及若干 subcircuit(inv, cd_circuit etc.)
			main_circuit = ''
			subcircuit_list = []


			list_of_circuits = break_into_part(netlist_file, '** End of subcircuit definition.\n') #读入每一行: 用于读取真的 netlist 文件
	
			#主要部分的 circuit 为列表最后一个部分, 上面的部分均为 subcircuit
			main_circuit = list_of_circuits[-1]
			#调试个别电路时使用
			#for circuit in list_of_circuits:
			#	if circuit.name == 'test_for_NMOS_tree':
			#		main_circuit = circuit


			#把 circuit 以 m 开头的部分填加到 mos_list list 中
			#[]部分:对于 circuit_mos_list 中的每个部分以空格分隔开来 ['m1 out in'] -> ['m1', 'out', 'in']
			#之后调用 circuit 类型的 mosfet 函数把每个 m 的信息保存成一个 mosfet
			main_circuit.create_mosfet([mos.split() for mos in main_circuit.create_mos_list()])

			#输出 circuit 中 netlist 部分的信息
			#print('Netlist')
			#for i in main_circuit.mos_list:
			#	print(i.number, i.drain, i.gate, i.source, i.bulk, i.type, i.L, i.W)

			#抽取 netlist 中 subcircuit 的信息 并对有进一层 subcircuit 的 subcircuit 进行填加
			#并填加到 main_circuit 的 subcircuit_netlist 中
			for subcircuit in list_of_circuits[:-1]:
				"""!!!填加下面这一行是为了去除测试用的 test_for_NMOS_tree !!! 按理说是没有这一行的!!!"""
				if subcircuit.name != 'test_for_NMOS_tree':
					#抽取subcircuit 中的 mos 信息
					subcircuit.create_mosfet([mos.split() for mos in subcircuit.create_mos_list()])

					#若 subcircuit 中存在另一层的 subcircuit 则进行填加
					subcircuit.create_subcircuit(list_of_circuits)

					#把所有的 subcircuit 都填加到 main_circuit 中
					main_circuit.subcircuit_netlist.append(subcircuit)

			#print('main_circuit : ', main_circuit.name)
			pipeline1, pipeline2 = main_circuit.find_entire_path()
			#display_pipeline(pipeline1.path, 'pipeline1', main_circuit)
			#display_pipeline(pipeline2.path, 'pipeline2', main_circuit)
			#统计 main_circuit 中的 subcircuit 的信息
			main_circuit.calculate_subcircuit()

			'''
			#输出 main_circuit 中的 subcircuit 的相关信息
			print('main_circuit subcircuit_netlist')
			for part in main_circuit.subcircuit_netlist:
				print(part.name + '  ', end = '')
			print()
			print('main_circuit.subcircuit_num')
			print(main_circuit.subcircuit_num)
			print()
			'''
			#统计 subcircuit 中的 subcircuit 的信息
			for subcircuit in main_circuit.subcircuit_netlist:
				subcircuit.calculate_subcircuit()
				'''
				#输出 subcircuit 中的 subcircuit 的信息
				print(subcircuit.name)
				print('subcircuit_netlist', end = ' ')
				for part in subcircuit.subcircuit_netlist:
					print(part.name + ' ', end = '')
				print()
				print('subcircuit.subcircuit_num')
				print(subcircuit.subcircuit_num)
				print()
				'''

			#subcircuit 总数量的统计
			total_subcircuit_num = {}

			#初始化字典
			for part in main_circuit.subcircuit_netlist:
				total_subcircuit_num[part.name] = 0

			#若发现在 main_circuit 中的 subcircuit 填加数量至字典
			for subcircuit in main_circuit.subcircuit_num:
				total_subcircuit_num[subcircuit] += main_circuit.subcircuit_num[subcircuit]


			'''
			#输出 main_circuit 中的 subcircuit 的数量
			print('total_subcircuit_num')
			print(total_subcircuit_num)

			#对于有 subcircuit 的 subcircuit, 输出数量
			print('subcircuit with subcircuit')
			for subcircuit in main_circuit.subcircuit_netlist:
				if subcircuit.subcircuit_num:
					print(subcircuit.name)
					display('mos_list', subcircuit.mos_list)
					for part in  subcircuit.subcircuit_netlist:
						print(part.name)
					print(subcircuit.subcircuit_num)
			'''

			for part in pipeline1.path:
				main_circuit.block.append(main_circuit.create_block(part))
			for part in pipeline2.path:
				main_circuit.block.append(main_circuit.create_block(part))

			'''
			#输出 main_circuirt 中的 block 信息
			print('main_circuit.block')
			for part in main_circuit.block:
				print(part.block_name, part.W, part.L)
				print(part)
				display('block list', part.list_of_blocks)
			'''

			print()
			main_circuit.find_all_path()

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