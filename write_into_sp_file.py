import re, os, sys, getopt, operator, glob, math
from copy import deepcopy

#C_j = 970E-18
#C_jsw = 261E-18

#来自HSPICE MOSFET Models Manual
C_j = 4.31E-4 
C_jsw = 3.96E-10

#C_j = 2E-15
#C_jsw = 0.28E-15

n_pipeline_to_p_pipeline_dict = {'m97':'m235', 'm92':'m233', 'm89':'m234', 'm98':'m228', 'm93':'m229', 
'm225':'m226', 'm222':'m223', 'm94':'m224', 'm90':'m227', 'm219':'m221', 'm95':'m220', 'm215':'m217', 'm96':'m216', 'm91':'m218'}

p_pipeline_to_n_pipeline_dict = {'m235':'m97', 'm233':'m92', 'm234':'m89', 'm228':'m98', 'm229':'m93',
'm226':'m225', 'm223':'m222', 'm224':'m94', 'm227':'m90', 'm221':'m219', 'm220':'m95', 'm217':'m215', 'm216':'m96', 'm218':'m91'}


def display_all_combination_list(pipeline_all_pattern_combination_list):
	for single_combination in pipeline_all_pattern_combination_list:
		print('single_combination')
		print(single_combination)
		print('\n'*1)
	print('\n'*2)

def create_all_pattern_combination_list(all_pattern_combination_list):
	#对于给入的 pipeline, 生成三个部分电路的所有 pattern 的组合. 共计1 * 4 * 8 = 32种. 
	#返回类型为列表, 最内侧为 string 类型, 好在 AS_AD_PS_PD 字典中寻找相对应的 key.
	group_combination_list_string = []
	for group_combination in all_pattern_combination_list:
		single_combination_list_string = []
		for single_combination in group_combination:
			for block_list in single_combination:
				block_list_string = []
				for block in block_list:
					block_list_string.append(block.number)
				single_combination_list_string.append(block_list_string)
		group_combination_list_string.append(single_combination_list_string)
	return(group_combination_list_string)

def calculate_area_and_periphery_for_block(drain, gate, source):
	#对于读入的block 计算其 AD(Drain diffusion area), AS(Source diffusion area), PD(Drain diffusion periphery), PS(Source diffusion periphery)
	AD = str(round(drain.W * drain.L, 2)) + 'p'
	AS = str(round(source.W * source.L, 2)) + 'p'
	PD = str(round(drain.W * 2 + drain.L * 2, 2)) + 'u'
	PS = str(round(source.W * 2 + source.L * 2, 2)) + 'u'

	#print('drain gate source', drain.block_name, gate.block_name, source.block_name)
	#print('AD AS PD PS', AD, AS, PD, PS)
	return([AD, AS, PD, PS])

def create_AD_AS_PD_PS_dict(pipeline, list_of_group_pattern_list, main_circuit):
	#对于读入的 pipeline, 结合 main_circuit 中详细的 block 信息, 计算每一个 mos 的 AD AS PD PS
	pipeline_AD_AS_PD_PS_dict = {}
	for group_pattern_list in list_of_group_pattern_list:
		for single_pattern_list in group_pattern_list:

			for block_list in single_pattern_list:
				block_list_name = []
				for block in block_list:
					block_list_name.append(block.number)

				for block_name in main_circuit.list_of_block_info_in_every_single_pattern.keys():
					block_AD_AS_PD_PS_dict = {}
					if ' '.join(block_list_name) == block_name:
						mos_AD_AS_PD_PS_list = []
						for block_index, block in enumerate(main_circuit.list_of_block_info_in_every_single_pattern[block_name]):
							# 以 gate block 为中心, 利用左右两侧的 block (可能是 net, 可能是 gate_gate_sw) 来计算 AD AS PD PS
							if block.block_name == 'gate':
								mos_AD_AS_PD_PS_list.append(calculate_area_and_periphery_for_block(main_circuit.list_of_block_info_in_every_single_pattern[block_name][block_index-1], block, main_circuit.list_of_block_info_in_every_single_pattern[block_name][block_index+1]))
						block_AD_AS_PD_PS_dict[block_name] = mos_AD_AS_PD_PS_list
						pipeline_AD_AS_PD_PS_dict[' '.join(block_list_name)] = mos_AD_AS_PD_PS_list

	return(pipeline_AD_AS_PD_PS_dict)

def search_AS_PS_PD_PS(single_pattern_list, AD_AS_PD_PS_dict):
	#对于读入的 single_pattern_list, 在 AD_AS_PD_PS_dict 中寻找详细信息
	for block_name in AD_AS_PD_PS_dict.keys():
		if ' '.join(single_pattern_list) == block_name:
			AD_AS_PD_PS_list = 	AD_AS_PD_PS_dict[block_name]
			
			mos_list = []
			for part in single_pattern_list:
				if 'm' in part:
					mos_list.append(part)
	
	return(mos_list, AD_AS_PD_PS_list)

def find_smaller_W(left_mos, right_mos, pattern, list_of_block_info_in_every_single_pattern):
	#直接用 pattern 的名字来当 key, 找到对应的 block
	pattern_block = list_of_block_info_in_every_single_pattern[' '.join(pattern)]

	#找到 left_mos 和 right_mos 对应的 block
	gate_list = []
	for block in pattern_block:
		if block.block_name == 'gate':
			gate_list.append(block)

	mos_list = [mos for mos in pattern if 'm' in mos]
	for index, mos in enumerate(mos_list):
		if mos == left_mos:
			left_mos_index = index
		elif mos == right_mos:
			right_mos_index = index

	left_mos_W = gate_list[left_mos_index].W
	right_mos_W = gate_list[right_mos_index].W

	if left_mos_W == right_mos_W:
		return((left_mos_W - 0.44) * pow(10, -6), 'same width')
	else:
		return((min(left_mos_W, right_mos_W) - 0.44) * pow(10, -6), 'different width')

def calculate_CD_circuit_area(main_circuit):
	'''计算 CD_circuit 的 L 和 W'''
	#找出 CD circuit 中四个 mos 同时连接的 node
	for part in main_circuit.netlist:
		line = part.split(' ')
		#若此行记述的部件为 inv_with_reset 且有一侧连着 cd_3信号, 则此部件为 CD 回路中输出端的 inverter.
		if line[-1].strip('\n') == 'inv_with_reset' and line[3] == 'cd_3':
			node = line[2]
	
	mos_W_list = {}
	for part in main_circuit.netlist:
		line = part.split(' ')
		#找到 CD circuit 中连接 n_and_3 和 n_nand_3 的两个 nmos
		if 'm' in line[0] and (line[1] == node or line[2] == node) and line[5] == 'N':
			#line 的最后元素为 'W=5e-6\n'
			mos_W = line[-1].strip('\n').split('e')[0][-1]
			mos_W_list[line[0]] = int(mos_W)

	#1个 edge_cont - gate - gate_gate_con_sw - gate - edge_con - diff
	#4个 edge_cont - gate - edge _cont - diff
	CD_circuit_L = round((0.48 + 0.18 + 0.54 + 0.18 + 0.48 + 0.28 + (0.48 + 0.18 + 0.48 + 0.28)*4   ), 4)
	CD_circuit_W = max([W for W in mos_W_list.values()]) + 0.22*2

	#在计算面积的时候, W 要加上下面 PMOS 部分的 W (4u)
	CD_circuit_area = CD_circuit_L * (CD_circuit_W + 4)

	return(CD_circuit_area)

def calculate_area_in_single_pattern_list(part, single_pattern_list, list_of_block_info_in_every_single_pattern):
	#计算读入的 single pattern list 中的给定 part 的面积和所有部分的面积, 进而可以求得整个 pattern list 的总面积
	#给定部分的面积
	part_area = 0

	#先找出所给定的 pattern list 对应的 block list 的详细信息
	for key in list_of_block_info_in_every_single_pattern:
		if ' '.join(single_pattern_list) == key:
			single_pattern_list_block = list_of_block_info_in_every_single_pattern[key]

	#之后求所给定的 part 的面积, 分为 mos 和 net 两种情况
	#从 single_pattern_list 中抽取 mos
	mos_list = []
	for item in single_pattern_list:
		if 'm' in item:
			mos_list.append(item)
	
	#从 block list 中抽取出 gate 类型的 block和其在列表中所对应的位置
	gate_list = []
	gate_index = []
	for index, block in enumerate(single_pattern_list_block):
		if block.block_name == 'gate':
			gate_list.append(block)
			gate_index.append(index)

	#如果 part 为 mos
	if 'm' in part:
		part_index = mos_list.index(part)
		part_area = gate_list[part_index].W * gate_list[part_index].L
		return(part_area, gate_list[part_index].W, gate_list[part_index].L)

	#如果 part 为 net 
	else:
		part_position = single_pattern_list.index(part)
		#若为 block list 中最左侧的 net
		if part_position == 0:
			part_area = single_pattern_list_block[0].W * single_pattern_list_block[0].L
			return(part_area, single_pattern_list_block[0].W, single_pattern_list_block[0].L)

		#若为 block list 中最右侧的 net
		elif part_position == (len(single_pattern_list) - 1):
			#因为 single_pattern_list_block[-1] 最后一个元素为 diff_space, 倒数第二个才为 edge_contact
			part_area = single_pattern_list_block[-2].W * single_pattern_list_block[-2].L

			#最后一个 net 的面积 = edge_contact 的 L 加上 diff_space 的 L(0.28)
			return(part_area, single_pattern_list_block[-2].W, single_pattern_list_block[-2].L + 0.28)

		else:
			#此情况为 net 处在 block list 的中间
			#首先通过 net 在 single_pattern_list 中的位置, 得知其左右两侧的 mos 及其位置 index
			left_mos = single_pattern_list[single_pattern_list.index(part) - 1]
			left_mos_index = mos_list.index(left_mos)
			right_mos = single_pattern_list[single_pattern_list.index(part) + 1]
			right_mos_index = mos_list.index(right_mos)

			#因为 mos_list 和 gate_index 中的元素是一对一的, gate_index 保存的是 mos 对应的 gate 在 single_pattern_list_block 的位置
			#比如 mos_list = [mos1, mos2, mos3], gate_index = [1, 3, 6]
			#得知 left_mos(mos2) - 得知其在 mos_lsit 中的位置(3) - 找到 gate_index 中对应位置的元素(4)
			#right mos 若为 mos3, 则这个 net 对应的 block 就是 single_pattern_list_block[4:6]的元素
			part_block_list = single_pattern_list_block[ gate_index[left_mos_index] + 1 : gate_index[right_mos_index] ]

			part_area_W, part_area_L = 0, 0
			W_list = []
			for block in part_block_list:
				W_list.append(block.W)
				part_area_L += block.L
				part_area += block.W * block.L
			#取两个小 block 中较大一方的 W 作为整体的 W
			part_area_W = max(W_list)

			return(part_area, part_area_W, part_area_L)

def share_node_mos(mos_replace_dict, group_pattern_list, list_of_block_info_in_every_single_pattern):
	#记录所有需要修改的 mos 和 net 信息
	# mos_replace_dict 中的顺序为 mos : AD AS PD PS
	change_list = []

	node_capacitance_dict = {}
	for single_pattern_list in group_pattern_list:
		for part in single_pattern_list:
			if 'net' in part:
				node_capacitance_dict[part] = 0

	print(mos_replace_dict)

	for pattern in group_pattern_list:
		# pattern 中的顺序为 [node1, mos1, node2, mos2, node3, mos3, node4]
		# mos 的顺序为 drain, gate, source

		if len(pattern) == 3:
			#[node1, mos1, node2]
			node1 = pattern[0]
			mos = pattern[1]
			node2 = pattern[2]
			print(pattern)

			#计算两侧 node1 和 node2 的容量
			#C_drain = C_j * AD + C_jsw * PD, C_source = C_j * AS + C_jsw * PS
			AD = float(mos_replace_dict[mos][0].strip('p')) * pow(10, -12)
			PD = float(mos_replace_dict[mos][2].strip('u')) * pow(10, -6)
			AS = float(mos_replace_dict[mos][1].strip('p')) * pow(10, -12)
			PS = float(mos_replace_dict[mos][3].strip('u')) * pow(10, -6)

			node_capacitance_dict[node1] += C_j * AD + C_jsw * PD
			node_capacitance_dict[node2] += C_j * AS + C_jsw * PS		

		if len(pattern) == 5:
			#[node1, left_mos, node2, right_mos, node3]
			print(pattern)

			node1 = pattern[0]
			left_mos = pattern[1]
			node2 = pattern[2]
			right_mos = pattern[3]
			node3 = pattern[4]

			#找出两个 mos 中较窄的 W
			smaller_W, compare_result = find_smaller_W(left_mos, right_mos, pattern, list_of_block_info_in_every_single_pattern)

			#计算两侧 node 的容量
			left_mos_AD = float(mos_replace_dict[left_mos][0].strip('p')) * pow(10, -12)
			left_mos_PD = float(mos_replace_dict[left_mos][2].strip('u')) * pow(10, -6)
			node_capacitance_dict[node1] += C_j * left_mos_AD + C_jsw * left_mos_PD

			right_mos_AS = float(mos_replace_dict[right_mos][1].strip('p')) * pow(10, -12)
			right_mos_PS = float(mos_replace_dict[right_mos][3].strip('u')) * pow(10, -6)
			node_capacitance_dict[node3] += C_j * right_mos_AS + C_jsw * right_mos_PS

			#计算中间 node 的容量
			#C_drain = C_j * AD + C_jsw * PD, C_source = C_j * AS + C_jsw * PS
			#mos_replace_dict 中的对应关系为 'mos': [AD p, AS p, PD u, PS u]
			#所以要用 left_mos 的 AS PS,  right_mos 的 AD PD
			left_mos_AS = float(mos_replace_dict[left_mos][1].strip('p')) * pow(10, -12) 
			left_mos_PS = float(mos_replace_dict[left_mos][3].strip('u')) * pow(10, -6)
			right_mos_AD = float(mos_replace_dict[right_mos][0].strip('p')) * pow(10, -12) 
			right_mos_PD = float(mos_replace_dict[right_mos][2].strip('u')) * pow(10, -6)

			if compare_result == 'same width':
				#当 width 相同时, 只算一边的就可以了. 因为在创建 AD AS PD PS dict 的时候, mos1 node1(block:gate_gate_sw) mos2
				#mos1 的 source 和 mos2 的 drain 的数据是相同的
				node_capacitance_dict[node2] += C_j * left_mos_AS + C_jsw * left_mos_PS
			elif compare_result == 'different width':
				#当 width 不同时, 需要算两边. 因为此时为 mos1 gate_gate_dw gate_gate_dw mos2
				node_capacitance_dict[node2] += C_j * left_mos_AS + C_jsw * (left_mos_PS - smaller_W) + C_j * right_mos_AD + C_jsw * (right_mos_PD - smaller_W) 
			

		elif len(pattern) == 7:
			#[node1, left_mos, node2, middle_mos, node3, right_mos, node4]
			print(pattern)

			node1 = pattern[0]
			left_mos = pattern[1]
			node2 = pattern[2]
			middle_mos = pattern[3]
			node3 = pattern[4]
			right_mos = pattern[5]
			node4 = pattern[6]

			smaller_W_1, compare_result_1 = find_smaller_W(left_mos, middle_mos, pattern, list_of_block_info_in_every_single_pattern)
			smaller_W_2, compare_result_2 = find_smaller_W(middle_mos, right_mos, pattern, list_of_block_info_in_every_single_pattern)

			#AD AS PD PS
			left_mos_AD = float(mos_replace_dict[left_mos][0].strip('p')) * pow(10, -12)
			left_mos_PD = float(mos_replace_dict[left_mos][2].strip('u')) * pow(10, -6)
			left_mos_AS = float(mos_replace_dict[left_mos][1].strip('p')) * pow(10, -12)
			left_mos_PS = float(mos_replace_dict[left_mos][3].strip('u')) * pow(10, -6)

			middle_mos_AD = float(mos_replace_dict[middle_mos][0].strip('p')) * pow(10, -12)
			middle_mos_PD = float(mos_replace_dict[middle_mos][2].strip('u')) * pow(10, -6)
			middle_mos_AS = float(mos_replace_dict[middle_mos][1].strip('p')) * pow(10, -12)
			middle_mos_PS = float(mos_replace_dict[middle_mos][3].strip('u')) * pow(10, -6)
			
			right_mos_AD = float(mos_replace_dict[right_mos][0].strip('p')) * pow(10, -12)
			right_mos_PD = float(mos_replace_dict[right_mos][2].strip('u')) * pow(10, -6)
			right_mos_AS = float(mos_replace_dict[right_mos][1].strip('p')) * pow(10, -12)
			right_mos_PS = float(mos_replace_dict[right_mos][3].strip('u')) * pow(10, -6)


			#计算两侧 node 的容量
			node_capacitance_dict[node1] += C_j * left_mos_AD + C_jsw * left_mos_PD
			node_capacitance_dict[node4] += C_j * right_mos_AS + C_jsw * right_mos_PS

			#计算中间的两个 node 的容量
			#左侧的 node
			if compare_result_1 == 'same width':
				node_capacitance_dict[node2] += C_j * left_mos_AS + C_jsw * left_mos_PS 
			elif compare_result_1 == 'different width':
				node_capacitance_dict[node2] += C_j * left_mos_AS + C_jsw * (left_mos_PS - smaller_W_1)  + C_j * middle_mos_AD + C_jsw * (middle_mos_PD - smaller_W_1 ) 

			#右侧的 node
			if compare_result_2 == 'same width':
				node_capacitance_dict[node3] += C_j * middle_mos_AS + C_jsw * middle_mos_PS 
			elif compare_result_2 == 'different width':
				node_capacitance_dict[node3] += C_j * middle_mos_AS + C_jsw * (middle_mos_PS - smaller_W_2 ) + C_j * right_mos_AD + C_jsw * (right_mos_PD - smaller_W_2 ) 

	### 测试 ###
	print('after')
	print(node_capacitance_dict)
	print()
	### 测试 ###

	return(change_list)


def create_new_sp_file(mos_replace_dict, combination_num, group_pattern_list, CD_circuit_area, main_circuit):
	#用最上面的 n 和 p pipeline 的对应表来生成另一个需要替换的 mos_replace_dict

	#以现有的 3NAND_2_NP_errorall.sp 为源文件, 对于其中的特定部分进行替换, 并生成新的 sp 文件
	with open('3NAND_2_NP_errorall.sp', 'r') as source_file:
		old_file = source_file.readlines()
		
		for mos in mos_replace_dict:
			for index, line in enumerate(old_file):
				if mos in line:
					AD = mos_replace_dict[mos][0]
					AS = mos_replace_dict[mos][1]
					PD = mos_replace_dict[mos][2]
					PS = mos_replace_dict[mos][3]

					#把原有的行以'AD'为界分为两部分, 用字典中的值替换掉后面的部分
					line = line.split('AD', 2)
					line[1] = 'AD=' + AD + ' AS=' + AS + ' PD=' + PD + ' PS=' + PS + '\n'
					old_file[index] = ''.join(line)

			#找出在另一个 pipeline 中与已经替换了的 mos 处于对称位置的 mos, 也需将其信息进行替换
			if mos in n_pipeline_to_p_pipeline_dict:
				the_other_mos = n_pipeline_to_p_pipeline_dict[mos]
			else:
				the_other_mos = p_pipeline_to_n_pipeline_dict[mos]

			for index, line in enumerate(old_file):
				if the_other_mos in line:
					AD = mos_replace_dict[mos][0]
					AS = mos_replace_dict[mos][1]
					PD = mos_replace_dict[mos][2]
					PS = mos_replace_dict[mos][3]

					#把原有的行以'AD'为界分为两部分, 用字典中的值替换掉后面的部分
					line = line.split('AD', 2)
					line[1] = 'AD=' + AD + ' AS=' + AS + ' PD=' + PD + ' PS=' + PS + '\n'
					old_file[index] = ''.join(line)


		#找出两个 mos 之间存在连接的 node 的所有情况.
		#此时, 把两侧的 mos AS/PS 或者 AD/PD 修改为0, 手动添加 C left_mos right_mos capacitance
		change_list = share_node_mos(mos_replace_dict, group_pattern_list, main_circuit.list_of_block_info_in_every_single_pattern)

		'''
		for list in change_list:
			# mos1 net mos2 仅有一个连接 node 的情况
			if list[-1] == 1:
				left_mos = list[0][0]
				right_mos = list[0][1]
				node = list[1][0]
				capacitance = list[1][1]

				#left mos 的 AD PD 重置为0, right mos 的 AS PS 重置为0
				for index, line in enumerate(old_file):
					if left_mos in line:
						new_line = line.split('AD')[0] + 'AD=0 ' + line.split('PD')[0].split(' ')[-2] + ' PD=0 ' + line.split('PD')[1].split(' ')[1]
						old_file[index] = new_line
					elif right_mos in line:
						new_line = line.split('AS')[0] + 'AS=0 ' + line.split('PS')[0].split(' ')[-2] + ' PS=0\n'
						old_file[index] = new_line
						capacitance_line = index

				#转换 capacitance 的格式 pF
				num1 = float(str(capacitance).split('e')[0])
				num2 = float(str(capacitance).split('e')[1])
				num1 = str(round(num1 * pow(10, 12 + num2), 1))
				old_file.insert(capacitance_line + 1, ''.join(['C ' + left_mos + ' ' + right_mos + ' ' + num1 + 'pF' + '\n']))
	
			elif list[-1] == 2:
			# mos1 net1 mos2 net2 mos3 有两个连接 node 的情况
				left_mos = list[0][0]
				middle_mos = list[0][1]
				right_mos = list[0][2]
				node1 = list[1][0]
				node2 = list[1][2]
				node1_capacitance = list[1][1]
				node2_capacitance = list[1][3]				

				#left mos 的 AD PD 重置为0, middle mos 的 AD PD AS PS 重置为0, right mos 的 AS PS 重置为0
				for index, line in enumerate(old_file):
					if left_mos in line:
						new_line = line.split('AD')[0] + 'AD=0 ' + line.split('PD')[0].split(' ')[-2] + ' PD=0 ' + line.split('PD')[1].split(' ')[1]
						old_file[index] = new_line
					elif middle_mos in line:
						new_line = line.split('AD')[0] + 'AD=0 AS=0 PD=0 PS=0\n'
						old_file[index] = new_line
					elif right_mos in line:
						new_line = line.split('AS')[0] + 'AS=0 ' + line.split('PS')[0].split(' ')[-2] + ' PS=0\n'
						old_file[index] = new_line
						capacitance_line = index
				
				#转换 capacitance 的格式 pF
				node1_num1 = float(str(node1_capacitance).split('e')[0])
				node1_num2 = float(str(node1_capacitance).split('e')[1])
				node1_num1 = str(round(node1_num1 * pow(10, 12 + node1_num2), 1))

				node2_num1 = float(str(node2_capacitance).split('e')[0])
				node2_num2 = float(str(node2_capacitance).split('e')[1])
				node2_num1 = str(round(node2_num1 * pow(10, 12 + node2_num2), 1))

				old_file.insert(capacitance_line + 1, ''.join(['C ' + left_mos + ' ' + middle_mos + ' ' + node1_num1 + 'pF' + '\n']))
				old_file.insert(capacitance_line + 2, ''.join(['C ' + middle_mos + ' ' + right_mos + ' ' + node2_num1 + 'pF' + '\n']))
			'''

	#将替换后的临时文件写入新的 sp 文件
	with open('./sp_file_for_all_combination/combination%s.sp' %combination_num ,'w+') as new_file:
		new_file.writelines(old_file[:-1])
		#电路的总面积, 现在暂且以两个 pipeline 的面积为准, 但日后应该修改为 standard cell 的总面积
		standard_cell_area = 0
		pipeline_W, pipeline_L = 0, 0
		part_area_W_list = []   #从中选出最宽的部分作为 pipeline_area 的 W, 整体的总和为 pipeline_area 的 L

		new_file.write('\n' + '*'*20 + ' pattern list ' + '*'*20 + '\n')
		for single_pattern_list in group_pattern_list:
			new_file.write('* ')
			for part in single_pattern_list:
				new_file.write(part + '  ')
			new_file.write('\n')
		new_file.write('*'*20 + ' pattern list ' + '*'*20 + '\n \n \n')

		#保存每一个 single pattern 的内容, 之后统计里面每个 node 的面积
		area_ratio_dict_list = []

		#计算每部分的每个 pattern 的面积和电路的总面积(standard cell 的总面积)
		for single_pattern_list in group_pattern_list:
			single_pattern_list_block_area = 0

			#保存 single pattern 中每一个 block 的面积
			single_pattern_area_dict = {}

			#用 calculate_area_in_single_pattern_list() 函数计算每个小 block 和整个 pattern 的面积
			for part in single_pattern_list:
				part_area, part_area_W, part_area_L = calculate_area_in_single_pattern_list(part, single_pattern_list, main_circuit.list_of_block_info_in_every_single_pattern)
				single_pattern_area_dict[part] = part_area 
				part_area_W_list.append((part_area_W))
				pipeline_L += part_area_L

			area_ratio_dict_list.append(single_pattern_area_dict)

		#计算 standard_cell 的总面积
		#最宽的 pmos 的 W, 为 4u
		pmos_W = 4

		#pipeline 的面积
		pipeline_W = sorted(part_area_W_list)[-1]
		pipeline_L = round(pipeline_L, 4)
		pipeline_area = (pipeline_W + pmos_W) * 2 * pipeline_L
 
		#CD circuit 的面积已知, 为 CD_circuit_area

		#其他 nmos 的面积的概算 : L * W
		other_nmos_area = (0.48 + 0.18 + 0.48 + 0.28)*7  * (4 + 0.22*2)

		standard_cell_area = pipeline_area + CD_circuit_area + other_nmos_area

		#得出无重复的 node 列表
		temp_node_list = []
		for dict in area_ratio_dict_list:
			for key in dict:
				temp_node_list.append(key)
		node_list = set(temp_node_list)

		#最终用来写入文件的每个 node 的面积信息的字典
		final_area_ratio_dict = {}
		for node in node_list:
			final_area_ratio_dict[node] = 0

		#对所有 node 的面积进行累加
		for single_pattern_dict in area_ratio_dict_list:
			for key in single_pattern_dict:
				#对于每个 single_pattern_dict 中的 key 在 area_ratio_dict 中查找, 并对面积进行累加
				for node in final_area_ratio_dict:
					if key == node:
						final_area_ratio_dict[node] += single_pattern_dict[key]

		#将 final_area_ratio_dict 中的每一个值除以电路的总面积, 以计算面积比例
		for key in final_area_ratio_dict:
			final_area_ratio_dict[key] = round(final_area_ratio_dict[key]/standard_cell_area, 4)

		#把 final_area_ratio_dict 写入到文件中
		new_file.write('*'*20 + ' area ratio list ' + '*'*20 + '\n')

		#对 final_area_ratio_dict 中的 key 做排序, 得到的结果为存有元祖的列表.
		#元祖中的第一个要素是 node, 第二个是面积比例
		sorted_list = sorted(final_area_ratio_dict.items(), key=operator.itemgetter(0))		
		for item in sorted_list:
			new_file.write('* ' + item[0] + ' : ' + str(item[1]) + '\n')

		new_file.write('*'*20 + ' area ratio list ' + '*'*20 + '\n\n')		

		#写入源文件的最后一行
		new_file.write(old_file[-1].strip('\n'))


def write_into_file(pipeline1, pipeline2, main_circuit, sp_file):
	'''根据生产的 layout block 的面积, 来替换 sp 文件中的AD, AS, PD, PS参数'''

	#先清除同目录下的 sp_file_for_all_combination 文件夹
	for file in glob.glob('./sp_file_for_all_combination/*'):
		os.remove(file)

	#因为每个 pipeline 中共有三个部分, 所以循环三次, 但其实这样的做法欠缺通用性
	pipeline1_all_pattern_combination_list = []
	for group_1 in pipeline1.list_of_group_pattern_list[0]:
		for group_2 in pipeline1.list_of_group_pattern_list[1]:
			for group_3 in pipeline1.list_of_group_pattern_list[2]:
				pipeline1_all_pattern_combination_list.append([group_1, group_2, group_3])

	#先生成每个 pipeline 的 group_pattern_name_list 之后依次在 list_of_block_info 中找到对应的具体信息
	#pipeline 的 list_of_group_pattern_list 中的分层方法
	#group_pattern_list - single_pattern_list - block_list - block
	pipeline1_all_pattern_combination_list = create_all_pattern_combination_list(pipeline1_all_pattern_combination_list)

	#对于每个 mos 计算其 AD AS PD PS, 之后插入到 sp 文件之中
	pipeline1_AD_AS_PD_PS_dict = create_AD_AS_PD_PS_dict(pipeline1, pipeline1.list_of_group_pattern_list, main_circuit)
	pipeline2_AD_AS_PD_PS_dict = create_AD_AS_PD_PS_dict(pipeline1, pipeline2.list_of_group_pattern_list, main_circuit)


	#计算 CD 回路的 L 和 W
	CD_circuit_area = calculate_CD_circuit_area(main_circuit)

	combination_num = 1
	for group_pattern_list in pipeline1_all_pattern_combination_list:
		#对于 group pattern list 中包含的所有 mos, 替换其后面的 AD AS PD PS 参数
		mos_replace_dict = {}

		#对于一个特定的 single_pattern_list, 找出其中所包含的 mos 并计算其 AD AS PD PS 信息
		for single_pattern_list in group_pattern_list:
			mos_list, AD_AS_PD_PS_list = search_AS_PS_PD_PS(single_pattern_list, pipeline1_AD_AS_PD_PS_dict)
			#将 mos 和其参数一一对应并保存到 mos_replace_dict 之中
			for index, mos in enumerate(mos_list):
				mos_replace_dict[mos] = AD_AS_PD_PS_list[index]

		#对于给定的 mos_replace_dict 生成新的 sp 文件
		create_new_sp_file(mos_replace_dict, combination_num, group_pattern_list, CD_circuit_area, main_circuit)
		combination_num += 1

	'''
	#把 all_pattern_combination_list 的信息输出
	with open('all_pattern_combination_list.txt', 'w+') as output_file:
		i = 1
		for single_combination_list in all_pattern_combination_list:
			output_file.write('combination %s \n' %i)
			print('single_combination_list')
			for single_pattern_list in single_combination_list:
				for block_list in single_pattern_list:
					for block in block_list:
						print(block.number + '  ', end = '')
						output_file.write(block.number + '  ')
					print()
					output_file.write('\n')
				print()
				output_file.write('\n')
			print('\n'*5)
			output_file.write('\n'*5)
			i += 1
	'''

	'''
	#检查生成的文件共有多少行被修改了. 每个 Pipeline 有14个 mos, 所以应共有28处修改.
	#原文件结尾处的最后一行 .END 与 新生成的 sp 文件也不同, 所以共计29处.
	with open('3NAND_2_NP_errorall.sp') as file1:
		sp_file_1 = file1.readlines()
		for file in glob.glob('./sp_file_for_all_combination/*'):
			num = 0
			with open(file) as file2:
				sp_file_2 = file2.readlines()
				for index, line1 in enumerate(sp_file_1):
					if line1 != sp_file_2[index]:
						print(index, sp_file_2[index], end = '')
						num += 1
				print('\n'*2)		
			print('num of modification', num)
	#'''