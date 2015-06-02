import re, os, sys, getopt, operator, csv
from copy import deepcopy
import write_into_sp_file


class Node:
	"""用于储存两个 mos 之间的连接点的名称和是否为并联点 以判断 contact 的类型"""
	def __init__(self, number):
		self.number = number
		self.fork = 0
		self.timing_error_rate = 0
		self.area_ratio = 0

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
	'''searched 则在后续的 create_pipeline 函数中记录 mos 是否被使用过'''
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
		self.top_mid_node = []
		self.mid_bot_node = []
		self.all_pattern_list = []
		self.top_node_list = []
		self.bot_node = ''
		self.block_list = []

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
		self.node_list = []
		self.list_of_group_pattern_list = []

class Circuit:
	"""保存 netlist 中各部分 circuit 的 cell name 和 netlist"""
	def __init__(self, name, netlist):
		self.name = name        			    #circuit 的 cell name
		self.netlist = netlist   				#circuit 的 netlist 类型为 list
		self.mos_list = []						#用来储存 circuit 中所有 mos 的信息  mos 每部分均为 class mosfet 的 instance  ['m0', 'm1'...]
		self.subcircuit_netlist = []			#储存 subcircuit 的类型
		self.subcircuit_num = {}				#储存 subcircuit 对应的数量
		self.block = []
		self.block_length = 0
		self.pipeline = []
		self.layout_block = []
		self.list_of_block_info_in_every_single_pattern = {}  #用来储存每一个 pattern 中的 block 的具体信息

	def create_mos_list(self):
		'''返回 netlist 中仅以 m 开头的部分'''
		list = []
		for part in self.netlist:
			if re.findall(r'\bm\w*\b', part):   #判断这行首字母是否以 m 开头
				list.append(part)				#若首字母以"m"开头 填加到 list 里面
		return(list)

	def line_m_list(self):   
		'''返回读入 mos_list 的行数, 即 m 部分的个数'''                   
		return(len(self.create_mos_list()))

	def create_mosfet(self, list_of_m): 
		'''读取一个包含 m 信息的 list 之后封装在每个 MOSFET 类型的 instance 中 最后保存在 self.mos_list list 中'''               
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

	def create_block_for_pattern_list(self, list_of_group_pattern_list):
		"""读入 pipeline 的 pattern_list, pattern_list 的内容为 mos 和 node 类型的混合 list
		   返回一个 block, 其中包含的内容为: 以pattern中的元素名称作为命名的 block_name, 长度 L, 高度 W, 生成的 block的 列表"""

		pattern_block_list = []       #用于储存所有的 pattern 的 block

		for group_pattern_list in list_of_group_pattern_list:
			group_pattern_block_list = []
			group_pattern_block_list_detailed = []
			for single_pattern in group_pattern_list:
				single_pattern_block_list = []
				single_pattern_block_list_detailed = []
				for pattern_part in single_pattern:    #parttern_part 为 pattern 中的每个小部分

					pattern_block_name = []     #读入 pattern 中所有元素的名称, 用来当做 block_name
					pattern_block = []          #用于储存每个 pattern 的 block
					pattern_block_L = 0         #block 的整体宽度
					pattern_block_W = 0         #block 的整体宽度
					pattern_block_W_list = []   #储存每个 block 的高度, 用于找出最高的部分

					#单个 mos [node, mos, node]
					if len(pattern_part) == 3:
						pattern_block.append(Block('edge_contact', 0.48, pattern_part[1].W))    #填加一个边缘处的 edge_contact
						pattern_block.append(Block('gate', 0.18, pattern_part[1].W + 0.22*2))   #填加一个 gate
						pattern_block.append(Block('edge_contact', 0.48, pattern_part[1].W))    #填加一个边缘处的 edge_contact
						pattern_block.append(Block('diff_space', 0.28, pattern_part[1].W))

					#多个 mos [left_node, mos, shared_node, mos, right_node]
					else:
						#填加 gate 时的 W 需要根据 gate 左右两侧的 mos 的高度来决定
						pattern_block.append(Block('edge_contact', 0.48, pattern_part[1].W))    
						for part in pattern_part[:-3]:  #part 为 pattern_part 中的每个小部分 有可能是 Node 有可能是 MOSFET 类型
							if isinstance(part, MOSFET):    							    			   #以 pattern 中的 mos 作为循环的标准
								pattern_block.append(Block('gate', part.L, part.W + 0.22*2))               #遇到一个 mos 便增加一个 gate
								if part.W == pattern_part[pattern_part.index(part)+2].W:				   #比较当前的 gate 和下一个 gate 的 W 是否相同
									if pattern_part[pattern_part.index(part)+1].fork == 0:				   #判断两个 gate 之间的 node 是否为分歧点, 是则填加一个 contact
										pattern_block.append(Block('gate_gate_sw', 0.26, part.W))		   #两个 gate 高度一致 中间没有 contact
									else:
										pattern_block.append(Block('gate_contact_gate_sw', 0.54, part.W))  #两个 gate 高度一致 中间有 contact
								else:
									if pattern_part[pattern_part.index(part)+1].fork == 0:				   #当前 gate 和下一个 gate 的 W 不同情况
										pattern_block.append(Block('gate_gate_dw', 0.1, part.W))           #两个 gate 高度不一致 没有 contact
										pattern_block.append(Block('gate_gate_dw', 0.32, pattern_part[pattern_part.index(part)+2].W))
									else:					
										pattern_block.append(Block('gate_contact_gate_dw', 0.16, part.W))  #两个 gate 高度一致 有 contact
										pattern_block.append(Block('gate_contact_gate_dw', 0.38, pattern_part[pattern_part.index(part)+2].W))
							else:
								continue
						pattern_block.append(Block('gate', 0.18, pattern_part[-2].W + 0.22*2))		#上面的处理只能填加到倒数第二个 mos 的右侧部分, 所以手动填加最右侧的 gate
						pattern_block.append(Block('edge_contact', 0.48, pattern_part[-2].W))		#填加最右侧的 edge_contact
						pattern_block.append(Block('diff_space', 0.28, pattern_part[-2].W))

					#用 pattern 中所有元素的名称来命名此 block
					for part in pattern_part:
						pattern_block_name.append(part.number)

					#找出 block 中最大的高度 W
					for part in pattern_block:
						if part.block_name == 'gate':
							pattern_block_W_list.append(round(part.W, 2))
					pattern_block_W = max(pattern_block_W_list)

					#计算 block 的长度 L
					for block in pattern_block:
						pattern_block_L += block.L
					pattern_block_L = round(pattern_block_L, 2)

					#根据决定的宽度和高度来创建新的 block
					final_pattern_block = Block(pattern_block_name, pattern_block_L, pattern_block_W)
					final_pattern_block.list_of_blocks = pattern_block

					#填加每个小 pattern_part 的 block
					single_pattern_block_list.append(final_pattern_block)

					#填加每个小 pattern_block 的 name 和所包含的所有 block 的具体信息到 self.list_of_block_info_in_every_single_pattern中
					#字典的 key 必须为数字、字符串、只含不可变类型元素的元组, 故将原为 list 类型的 pattern_block_name 转换为 str 类型
					self.list_of_block_info_in_every_single_pattern[' '.join(pattern_block_name)] = pattern_block

				#填加每个 pattern 的 block
				group_pattern_block_list.append(single_pattern_block_list)

			#填加每个 group 的所有 pattern 的 block 
			self.layout_block.append(group_pattern_block_list)
	
	def calculate_area_for_single_pattern(self, single_pattern):
		#用于储存所有 block
		single_pattern_block_list = []

		#single pattern 中所有 block 的面积和
		single_pattern_block_area = 0

		for pattern_part in single_pattern:    #pattern_part 为 pattern 中的每个小部分

			pattern_block_name = []     #读入 pattern 中所有元素的名称, 用来当做 block_name
			pattern_block = []          #用于储存每个 pattern 的 block
			pattern_block_L = 0         #block 的整体宽度
			pattern_block_W = 0         #block 的整体宽度
			pattern_block_W_list = []   #储存每个 block 的高度, 用于找出最高的部分

			#单个 mos [node, mos, node]
			if len(pattern_part) == 3:
				pattern_block.append(Block('edge_contact', 0.48, pattern_part[1].W))    #填加一个边缘处的 edge_contact
				pattern_block.append(Block('gate', 0.18, pattern_part[1].W + 0.22*2))   #填加一个 gate
				pattern_block.append(Block('edge_contact', 0.48, pattern_part[1].W))    #填加一个边缘处的 edge_contact
				pattern_block.append(Block('diff_space', 0.28, pattern_part[1].W))

			#多个 mos [left_node, mos, shared_node, mos, right_node]
			else:
				#填加 gate 时的 W 需要根据 gate 左右两侧的 mos 的高度来决定
				pattern_block.append(Block('edge_contact', 0.48, pattern_part[1].W))    
				for part in pattern_part[:-3]:  #part 为 pattern_part 中的每个小部分 有可能是 Node 有可能是 MOSFET 类型
					if isinstance(part, MOSFET):    							    			   #以 pattern 中的 mos 作为循环的标准
						pattern_block.append(Block('gate', part.L, part.W + 0.22*2))               #遇到一个 mos 便增加一个 gate
						if part.W == pattern_part[pattern_part.index(part)+2].W:				   #比较当前的 gate 和下一个 gate 的 W 是否相同
							if pattern_part[pattern_part.index(part)+1].fork == 0:				   #判断两个 gate 之间的 node 是否为分歧点, 是则填加一个 contact
								pattern_block.append(Block('gate_gate_sw', 0.26, part.W))		   #两个 gate 高度一致 中间没有 contact
							else:
								pattern_block.append(Block('gate_contact_gate_sw', 0.54, part.W))  #两个 gate 高度一致 中间有 contact
						else:
							if pattern_part[pattern_part.index(part)+1].fork == 0:				   #当前 gate 和下一个 gate 的 W 不同情况
								pattern_block.append(Block('gate_gate_dw', 0.1, part.W))           #两个 gate 高度不一致 没有 contact
								pattern_block.append(Block('gate_gate_dw', 0.32, pattern_part[pattern_part.index(part)+2].W))
							else:					
								pattern_block.append(Block('gate_contact_gate_dw', 0.16, part.W))  #两个 gate 高度一致 有 contact
								pattern_block.append(Block('gate_contact_gate_dw', 0.38, pattern_part[pattern_part.index(part)+2].W))
					else:
						continue
				pattern_block.append(Block('gate', 0.18, pattern_part[-2].W + 0.22*2))		#上面的处理只能填加到倒数第二个 mos 的右侧部分, 所以手动填加最右侧的 gate
				pattern_block.append(Block('edge_contact', 0.48, pattern_part[-2].W))		#填加最右侧的 edge_contact
				pattern_block.append(Block('diff_space', 0.28, pattern_part[-2].W))

			#用 pattern 中所有元素的名称来命名此 block
			for part in pattern_part:
				pattern_block_name.append(part.number)

			#找出 block 中最大的高度 W
			for part in pattern_block:
				if part.block_name == 'gate':
					pattern_block_W_list.append(round(part.W, 2))
			pattern_block_W = max(pattern_block_W_list)

			#计算 block 的长度 L
			for block in pattern_block:
				pattern_block_L += block.L
			pattern_block_L = round(pattern_block_L, 2)

			final_pattern_block = Block(pattern_block_name, pattern_block_L, pattern_block_W)
			final_pattern_block.list_of_blocks = pattern_block

			#填加每个小 pattern_part 的 block
			single_pattern_block_list.append(final_pattern_block)

			single_pattern_block_area += final_pattern_block.L * final_pattern_block.W

		return(single_pattern_block_area)

	def calculate_area_for_node(self, single_pattern, node):

		#计算 node 的面积, 分 sw 和 dw 两种情况
		for single_block in single_pattern:

			single_block_parts = []
			for part in single_block:
				single_block_parts.append(part.number)
			print('single_block_parts', single_block_parts)

			if node.number in single_block_parts:
				position = part.block_name.index(node.number)
				node_block = part.list_of_blocks[position]

				#根据 node 所在的 part 的类型来进行面积计算
				#sw 和 edge_contact 的时候, 直接用长乘以高; dw 的时候, 把两块小 part 的面积合算
				if 'sw' in node_block.block_name or 'edge_contact' in node_block.block_name:
					node_area = node_block.L * node_block.W
				elif 'dw' in node_block.block_name:
					node_block_1 = node_block
					node_block_2 = pattern_block.list_of_blocks[position+2]
					node_area = node_block_1.L * node_block_1.W + node_block_2.L * node_block_2.W
			else:
				continue
		return(node_area)

	def search_mid_mos(self, top_node, bot_node):
		#输入两个点 找出两点间(未被搜索过)的 mos
		list = []
		for mos in self.mos_list:
			if mos.searched == 0:
				if (mos.drain == top_node or mos.source == top_node) and (mos.drain == bot_node or mos.source == bot_node):
					list.append(mos)
		return(list)

	def find_all_pattern(self, pipeline):
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
				group.bot_node = pipeline.bot_node
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
				group.bot_node = pipeline.bot_node
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
		#'''

		#top_mos 下面的 net 编号 top_mid_node
		for group in group_list:
			temp = []
			for mos in group.top_mos:
				if mos.drain in group.top_node_list:
					temp.append(mos.source)
					group.top_mid_node = sorted(set(temp), key = temp.index)

				else:
					temp.append(mos.drain)
					group.top_mid_node = sorted(set(temp), key = temp.index)		

		#bot_mos 上面的 net 编号 mid_bot_node
		for group in group_list:
			temp = []
			for mos in group.bot_mos:
				if mos.drain == group.bot_node and mos.source != 'gnd':
					temp.append(mos.source)
					group.mid_bot_node = sorted(set(temp), key = temp.index)
				elif mos.source == group.bot_node:
					temp.append(mos.drain)
					group.mid_bot_node = sorted(set(temp), key = temp.index)


		#用每两个 mos 创建一个小 block 并保存至 group.block_list 之中
		#保存形式为: ['net**', mos1, mos2] 在列表的最前端保存 node 名称信息是为了下一步中找到某个 node 所有的 block 而服务
		for group in group_list:
			for top_mid_node in group.top_mid_node:
				top_mos_list = []
				mid_mos_list_1 = []
				mid_mos_list_2 = []
				bot_mos_list = []
				if same_node_num(top_mid_node, group.mos_list) > 2:
					for top_mos in group.top_mos:
						if has_node(top_mos, top_mid_node):
							top_mos_list.append(top_mos)
					for mid_mos in group.mid_mos:
						if has_node(mid_mos, top_mid_node):
							mid_mos_list_1.append(mid_mos)
					for top_mos in top_mos_list:
						for mid_mos in mid_mos_list_1:
							group.block_list.append([top_mid_node,top_mos, mid_mos])
				else:
					for top_mos in group.top_mos:
						if has_node(top_mos, top_mid_node):
							top_mos_list = top_mos
					for mid_mos in group.mid_mos:
						if has_node(mid_mos, top_mid_node):
							mid_mos_list_1 = mid_mos
					group.block_list.append([top_mid_node, top_mos_list, mid_mos_list_1])


			for mid_bot_node in group.mid_bot_node:
				if same_node_num(mid_bot_node, group.mos_list) > 2:
					for mid_mos in group.mid_mos:
						if has_node(mid_mos, mid_bot_node):
							mid_mos_list_2.append(mid_mos)
					for bot_mos in group.bot_mos:
						if has_node(bot_mos, mid_bot_node):
							bot_mos_list.append(bot_mos)
					for mid_mos in mid_mos_list_2:
						for bot_mos in bot_mos_list:
							group.block_list.append([mid_bot_node, mid_mos, bot_mos])
				else:
					for mid_mos in group.mid_mos:
						if has_node(mid_mos, mid_bot_node):
							mid_mos_list_2 = mid_mos
					for bot_mos in group.bot_mos:
						if has_node(bot_mos, mid_bot_node):
							bot_mos_list = bot_mos
					group.block_list.append([mid_bot_node,mid_mos_list_2, bot_mos_list])
			'''
			#输出 block 的信息
			print('group block list')
			for block in group.block_list:
				print(block)
				#display('block', block, newline = 0)
			print()
			#'''
		

		for group in group_list:
			#把各个 node 的 block 归纳到一个 list 当中 
			#比如: 某个 top_mid_node 为 [[<>, <>], [<>, <>]], mid_bot_node 为 [[<>, <>], [<>, <>], [<>, <>]]
			#再将所有的 list 归纳到一个 list(node_block_list) 当中
			#node_block_list = [ [[<>, <>], [<>, <>]],  [[<>, <>],[<>, <>],[<>, <>]] ]
			node_block_list = []
			#寻找所有 top_mid_node 的 block
			for top_mid_node in group.top_mid_node:
				top_mid_node_block = []
				for block in group.block_list:
					#在 group.block_list中的 block = ['net01', <>, <>]
					if top_mid_node == block[0]:
						top_mid_node_block.append(block[1:])
				node_block_list.append(top_mid_node_block)

			#寻找所有 mid_bot_node 的 block
			for mid_bot_node in group.mid_bot_node:
				mid_bot_node_block = []
				for block in group.block_list:
					if mid_bot_node == block[0]:
						mid_bot_node_block.append(block[1:])
				node_block_list.append(mid_bot_node_block)
			
			'''
			#输出所有组合的 block 
			print('block list')
			for part in node_block_list:
				for item in part:
					print('[', end = '')
					for item2 in item:
						print(item2.number + '  ' , end = '')
					print(']', end = '')
			print()
			#'''

			#寻找所有的 pattern 组合
			pattern_list = block_combination(node_block_list)
			
			#输出所有 block 组合
			#print('pattern combination (num =', len(pattern_list) ,")")
			'''
			for pattern in pattern_list:
				for block in pattern:
					print('[', end = '')
					for mos in block:
						print(mos.number + ' ', end = '')
					print(']', end = '')
				print('  ||  ', end = ' ')
			print()
			print()
			#'''

			#去掉每两个 pattern 中相同的 mos
			new_pattern_list = []
			for pattern in pattern_list:
				new_pattern = [deepcopy(pattern[0])]
				#print('new_pattern', new_pattern)
				for block1 in pattern:
					for block2 in pattern[pattern.index(block1)+1:]:
						merged_list = eliminate_same_mos(block1, block2)
						if merged_list:
							pattern.remove(block1)
							pattern.remove(block2)
							pattern.append(merged_list)
				new_pattern_list.append(pattern)

			#添加 pattern 中未有的 block 或单个 mos
			#对于 group.mos_list 和 pattern 中的 mos 进行对比, 未使用的储存在 unused_mos_list
			for pattern in new_pattern_list:
				pattern_mos_list = []
				for block in pattern:
					for mos in block:
						pattern_mos_list.append(mos)
				for mos1 in group.mos_list:
					mos1.searched = 0
					for mos2 in pattern_mos_list:
						if mos1.number == mos2.number:
							mos1.searched = 1

				unused_mos_list = []
				for mos in group.mos_list:
					if mos.searched == 0:
						unused_mos_list.append(mos)

				if unused_mos_list:
					#寻找是否可以用 block 来填充 但是此判断方法应该有局限性
					#*************** 判断方法需要修改 *****************
					if len(unused_mos_list) == 2:
						#若在 block 中存在与未用 mos 相同的模块, 则添加 block
						unused_mos_number_list = []
						for mos in unused_mos_list:
							unused_mos_number_list.append(mos.number)
						for block in group.block_list:
							mos_number_list = []
							for mos in block[1:]:
								mos_number_list.append(mos.number)
							if unused_mos_number_list == mos_number_list:
								pattern.append(block[1:])
								
					#若剩余为单个 mos 则直接添加
					else:
						pattern.append([unused_mos_list[0]])

			#填加两个 mos 之间的 node 信息(net***)
			for pattern in new_pattern_list:
				for block in pattern:
					#若 block 中存在多个 mos, 先填加中间的 shared_node, 之后填加两侧的 node
					if len(block) >= 2:
						for mos in block[:-1]:
							shared_node = Node(find_shared_node(mos, block[block.index(mos)+1]))
							if same_node_num(shared_node.number, group.mos_list) > 2 :
								shared_node.fork = 1
							block.insert(block.index(mos)+1, shared_node)

						#为 block 的两侧填加 Node(net***) 信息
						#当下的 block = [mos, net, mos, net, mos] 两侧也需要填加 net
						#如果第一个 mos 的 drain 和右侧的 net 一致 则左侧的 node 为 mos 的 source
						if block[0].drain == block[1].number:
							left_node = Node(block[0].source)
						else:
							left_node = Node(block[0].drain)

						#如果最后一个 mos 的 drain 和左侧的 net 一直 则右侧的 node 为 mos 的 source
						if block[-1].drain == block[-2].number:
							right_node = Node(block[-1].source)
						else:
							right_node = Node(block[-1].drain)

						#将两侧的 node 分别填加到 block 之中
						block.insert(0, left_node)
						block.append(right_node)

					#如果此 block 中只有一个 mos 则直接在两侧填加 mos 的 drain 和 source
					elif len(block) == 1:
						left_node = Node(block[0].drain)
						right_node = Node(block[0].source)
						block.insert(0, left_node)
						block.append(right_node)

			
			'''
			print('new_pattern_list')
			for pattern in new_pattern_list:
				for block in pattern:
					print('[', end = '')
					for mos in block:
						print(mos.number + ' ', end = '')
					print(']', end = '')
				print('  ||  ', end = ' ')
				print()
			print()
			print()
			#'''


			pipeline.list_of_group_pattern_list.append(new_pattern_list)
	
	def choose_pattern(self, target_node_list, list_of_group_pattern_list):

		for node in target_node_list:
			print('node number', node.number)
			for group_pattern_list in list_of_group_pattern_list:
				if group_pattern_list_part_has_node(group_pattern_list, node):
					print('*'*110)
					#寻找 node 应该在这个层面进行
					for group_pattern_list in group_pattern_list:
						print('*'*50)
						for pattern in group_pattern_list:
							display('', pattern, newline = 0)
						print(self.calculate_area_for_single_pattern(group_pattern_list))
						print('*'*50)
					print('*'*110)

	def process_pipeline(self, pipeline):
		"""对于 pipeline 抽取更多的信息 比如各种 node 的信息"""

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


		return(pipeline)

	def create_pipeline(self):
		"""为 circuit 创建两侧的 pipeline"""

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
				if part.type == 'P' and part2.type == 'P' and part.gate == part2.gate and part.number != part2.number:
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

		'''输出 Pipeline 的相关信息'''
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
		#'''

		#抽取 pipeline 中更详细的信息
		self.process_pipeline(pipeline1)
		self.process_pipeline(pipeline2)

		self.pipeline.append(pipeline1)
		self.pipeline.append(pipeline2)

		return(pipeline1, pipeline2)


def display(func_name, list, newline = 1):
	print(func_name + '\n')
	if newline == 1:
		for item in list:
			if hasattr(item, 'number'):
				print(item.number)
			elif hasattr(item, 'name'):
				print(item.name)
			elif hasattr(item, 'block_name'):
				print(item.block_name)
			else:
				print(item + ' ')
	elif newline == 0:
		for item in list:
			if hasattr(item, 'number'):
				print(item.number + '  ', end = '')
			elif hasattr(item, 'name'):
				print(item.name + '  ', end = '')
			elif hasattr(item, 'block_name'):
				print(item.block_name + '   ', end = '')				
			else:
				print(item + ' ', end = '')
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

def has_node(mos, node):
	if mos.drain == node or mos.source == node:
		return(True)

def same_node_num(node, list):
	'''用来寻找在一个 list 中某个 node 跟几个 node 相连 进而判断是串联(same_node_number = 2)还是并联(大于2)'''
	same_node_number = 0
	for mos in list:
		if mos.source == node or mos.source == node or mos.drain == node or mos.drain == node:
			same_node_number += 1
	return(same_node_number)

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

def has_subcircuit(netlist):
	for line in netlist:
		if re.findall(r'\bxi\w*\b', line):
			return(True)
		else:
			return(False)

def block_combination(list_of_block_list):
	list_number = len(list_of_block_list)

	for i in range(list_number):
		#开始第一次循环时, 读取列表中的第一项作为 final_list 保存
		if i == 0:
			temp_pattern_list = deepcopy(list_of_block_list[0])
		else:
			temp1 = []
			for pattern in temp_pattern_list:
				temp2 = []
				for block in list_of_block_list[i]:
					temp2 = deepcopy(pattern)
					temp2.extend(block)
					temp1.append(temp2)
			temp_pattern_list = temp1

	#手动把 temp_pattern_list 中每个 pattern 中的每两个 mos 变成一个 block [mos1, mos2]
	final_pattern_list = []
	for pattern in temp_pattern_list:
		single_pattern = []
		for i in range(0, len(pattern), 2):
			temp1 = deepcopy(pattern[i])
			temp2 = deepcopy(pattern[i+1])
			temp = [temp1, temp2]
			single_pattern.append(temp)
		final_pattern_list.append(single_pattern)

	return(final_pattern_list)

def eliminate_same_mos(block1, block2):
	mos_list = []
	for mos in block1:
		mos_list.append(mos)
	for mos in block2:
		mos_list.append(mos)

	has_same_mos = 0
	for mos1 in mos_list:
		for mos2 in mos_list[mos_list.index(mos1)+1:]:
			if mos2.number == mos1.number:
				has_same_mos = 1
				mos_list.remove(mos2)

	if has_same_mos:
		return(mos_list)
	else:
		return(None)

def group_pattern_list_part_has_node(group_pattern_list, node):
	#判断一个 group 中是否包含 node

	#在一个列表中保存 group 中所有 mos 和 node 的信息	
	for group_pattern in group_pattern_list:
		#保存 pattern 中所有 mos 的名字, 用来判断 node 是否在其中
		group_pattern_parts = []
		for pattern in group_pattern:
			for part in pattern:
				group_pattern_parts.append(part.number)

	#判断此列表中是否包含 node			
	if node.number in group_pattern_parts:
		return(True)
	else:
		return(False)

def add_pipeline_node(pipeline):
	#把 pipeline 中的所有 node 填加到 pipeline.node_list 列表中
	pipeline.node_list.extend([pipeline.top_node_1, pipeline.top_node_2])
	pipeline.node_list.append(pipeline.bot_node)
	pipeline.node_list.extend(pipeline.top_mid_node)
	pipeline.node_list.extend(pipeline.mid_bot_node)

def select_target_node():
	#根据读入的 csv 文件, 与 sp 文件进行对比, 确定与定电流源连接的 node 信息

	#读取 Hspice 模拟后生成的 CSV 文件, 并保存其中除了第一行之外的信息
	with open('./shift_timing_error_calculation.csv', 'r') as temp_file:
		csv_file = csv.reader(temp_file)
		line_num = 0
		error_data = []
		for line in csv_file:
			if line_num == 0:
				pass
			else:
				error_data.append(line)
			line_num += 1

	#在 sp 文件中找出定电流源连接着的 node 番号
	current_source_dict = {}
	target_node = []
	for data in error_data:
		current_source_dict[data[3]] = data[5]

	with open('./3NAND_2_NP_errorall.sp', 'r') as sp_file:
		temp_file = sp_file.readlines()
		for source in current_source_dict:
			for line in temp_file:
				if source in line:
					node = Node(line.split(' ')[2])
					node.timing_error_rate = current_source_dict[source]
					target_node.append(node)

	return(target_node)

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
		with open(input_file, 'r') as netlist_file:
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
				#if subcircuit.name != 'test_for_NMOS_tree':
				#抽取subcircuit 中的 mos 信息
				subcircuit.create_mosfet([mos.split() for mos in subcircuit.create_mos_list()])

				#若 subcircuit 中存在另一层的 subcircuit 则进行填加
				subcircuit.create_subcircuit(list_of_circuits)

				#把所有的 subcircuit 都填加到 main_circuit 中
				main_circuit.subcircuit_netlist.append(subcircuit)

			#print('main_circuit : ', main_circuit.name)
			pipeline1, pipeline2 = main_circuit.create_pipeline()
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

			'''
			#输出 main_circuit 中的 block 信息
			print('main_circuit.block')
			for part in main_circuit.block:
				print(part.block_name, part.W, part.L)
				print(part)
				display('block list', part.list_of_blocks)
			'''
			
			#Node-based pattern search
			#print('pipeline1')
			main_circuit.find_all_pattern(pipeline1)
			main_circuit.create_block_for_pattern_list(pipeline1.list_of_group_pattern_list)

			#print('pipeline2')
			main_circuit.find_all_pattern(pipeline2)
			main_circuit.create_block_for_pattern_list(pipeline2.list_of_group_pattern_list)

			'''
			print('main_circuit')
			#print(main_circuit.layout_block)
			for group_pattern in main_circuit.layout_block:
				#print('group_pattern', len(group_pattern), '\n')
				output.write('group pattern %s \n' %len(group_pattern))
				for single_pattern in group_pattern:
					#print('single_pattern\n')
					output.write('single_pattern\n')
					for block in single_pattern:
						#print(block.block_name, block.L, block.W)
						output.write('%s   [L :  %s    W : %s] \n' %(' '.join(block.block_name), block.L, block.W) )
					output.write('\n')
				output.write('\n')
			#'''
			

			print('write_into_sp_file')
			write_into_sp_file.write_into_file(pipeline1, pipeline2, main_circuit, input_file)

			'''
			#print('test for choose_pattern()')
			add_pipeline_node(pipeline1)
			add_pipeline_node(pipeline2)

			#选择目标 node
			target_node_list = select_target_node()

			#根据 node 所在 pipeline 不同, 传递不同的 pipeline 给 choose_pattern()函数
			for target_node in target_node_list:
				if target_node.number in pipeline1.node_list:
					#print('target_node', target_node.number)
					main_circuit.choose_pattern(target_node_list, pipeline1.list_of_group_pattern_list)
				else:
					#print('target_node', target_node.number)					
					main_circuit.choose_pattern(target_node_list, pipeline2.list_of_group_pattern_list)
			'''
			output.close()

	except IOError as err:
		print("File error: " + str(err))
		return(None)

opts, args = getopt.getopt(sys.argv[2:], "hi:o:s:")   #命令行输入
input_file, output_file, subtract = '', '', ''

def usage():
	print('Usage: ' + sys.argv[0] + ' -i input_file -o output_file -s extract_subcircuit')
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
