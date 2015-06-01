import re, os, sys, getopt, operator, glob
from copy import deepcopy

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

def calculate_area_and_periphery_for_block(source, gate, drain):
	#对于读入的block 计算其 AD(Drain diffusion area), AS(Source diffusion area), PD(Drain diffusion periphery), PS(Source diffusion periphery)
	AD = str(round(drain.W * drain.L, 2)) + 'p'
	AS = str(round(source.W * source.L, 2)) + 'p'
	PD = str(round(drain.W * 2 + drain.L * 2, 2)) + 'u'
	PS = str(round(source.W * 2 + source.L * 2, 2)) + 'u'

	#print('source gate drain', source.block_name, gate.block_name, drain.block_name)
	#print('AD AS PD PS', AD, AS, PD, PS)
	return([AD, AS, PD, PS])

def create_AD_AS_PD_PS_dict(pipeline, list_of_group_pattern_list, main_circuit):
	#对于读入的 pipeline, 结合 main_circuit 中详细的 block 信息, 计算 AD AS PD PS
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

def calculate_area_in_single_pattern_list(part, single_pattern_list, list_of_block_info_in_every_single_pattern):
	#计算读入的 single pattern list 中的给定 part 的面积和所有部分的面积, 进而可以求得整个 pattern list 的总面积
	#给定部分的面积
	part_area = 0

	#先找出所给定的 pattern list 对应的 block list 的详细信息
	for key in list_of_block_info_in_every_single_pattern:
		if ' '.join(single_pattern_list) == key:
			single_pattern_list_block = list_of_block_info_in_every_single_pattern[key]

	#整个 pattern list 的总面积
	single_pattern_list_block_area = 0
	for block in single_pattern_list_block:
		single_pattern_list_block_area += block.W * block.L

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
	#如果 part 为 net 
	else:
		part_position = single_pattern_list.index(part)
		#若为 block list 中最左侧的 net
		if part_position == 0:
			part_area = single_pattern_list_block[0].W * single_pattern_list_block[0].L
		#若为 block list 中最右侧的 net
		elif part_position == (len(single_pattern_list) - 1):
			#因为 single_pattern_list_block[-1] 最后一个元素为 diff_space, 倒数第二个采薇 edge_contact
			part_area = single_pattern_list_block[-2].W * single_pattern_list_block[-2].L
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

			for block in part_block_list:
				part_area += block.W * block.L

	return(part_area, single_pattern_list_block_area)

def create_new_sp_file(mos_replace_dict, combinaiton_num, group_pattern_list, main_circuit):
	#用最上面的 n 和 p pipeline 的对应表来生成另一个需要替换的 mos_replace_dict
	mos_list = []
	for mos in mos_replace_dict.keys():
		if mos in n_pipeline_to_p_pipeline_dict:
			#print(mos, n_pipeline_to_p_pipeline_dict[mos])
			mos_list.append(n_pipeline_to_p_pipeline_dict[mos])
		#若 mos 不在 n_pipeline_to_p_pipeline_dict 中, 说明读入的为 p pipeline 生成的 replace ditc, 这时候用 p_pipeline_to_n_pipeline_dict
		else:
			mos_list.append(p_pipeline_to_n_pipeline_dict[mos])

	#以现有的 3NAND_2_NP_errorall.sp 为源文件, 对于其中的特定部分进行替换, 并生成新的 sp 文件
	with open('3NAND_2_NP_errorall.sp', 'r') as source_file:
		old_file = source_file.readlines()
		for mos in mos_replace_dict.keys():
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

	#将替换后的临时文件写入新的 sp 文件
	with open('./sp_file_for_all_combination/combinaiton%s.sp' %combinaiton_num ,'w+') as new_file:
		new_file.writelines(old_file[:-1])
		#电路的总面积, 现在暂且以两个 pipeline 的面积为准, 但日后应该修改为 standard cell 的总面积
		two_pipeline_area = 0

		new_file.write('\n' + '*'*20 + ' pattern list ' + '*'*20 + '\n')
		for single_pattern_list in group_pattern_list:
			for part in single_pattern_list:
				new_file.write(part + '  ')
			new_file.write('\n')
		new_file.write('*'*20 + ' pattern list ' + '*'*20 + '\n \n \n')

		#保存每一个 single pattern 的内容, 之后统计里面每个 node 的面积
		area_ratio_dict_list = []

		#计算每部分的每个 pattern 的面积和电路的总面积(standard cell 的总面积)
		for single_pattern_list in group_pattern_list:
			#保存 single pattern 中每一个 block 的面积
			single_pattern_area_dict = {}

			#用 calculate_area_in_single_pattern_list() 函数计算每个小 block 和整个 pattern 的面积
			for part in single_pattern_list:
				part_area, pattern_area = calculate_area_in_single_pattern_list(part, single_pattern_list, main_circuit.list_of_block_info_in_every_single_pattern)
				single_pattern_area_dict[part] = part_area 

			two_pipeline_area += pattern_area

			area_ratio_dict_list.append(single_pattern_area_dict)

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
			final_area_ratio_dict[key] = round(final_area_ratio_dict[key]/two_pipeline_area, 4)

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
	#先清除同目录下的 sp_file_for_all_combination 文件夹
	for file in glob.glob('./sp_file_for_all_combination/*'):
		os.remove(file)

	#根据生产的 layout block 的面积, 来替换 sp 文件中的AD, AS, PD, PS参数
	main_circuit_mos_list = []
	for line in main_circuit.netlist:
		if re.findall(r'\bm\d{2,3}\b.*\b', line):
			main_circuit_mos_list.append(line)

	#因为每个 pipeline 中共有三个部分, 所以循环三次, 但其实这样的做法欠缺通用性
	pipeline1_all_pattern_combination_list = []
	for group_1 in pipeline1.list_of_group_pattern_list[0]:
		for group_2 in pipeline1.list_of_group_pattern_list[1]:
			for group_3 in pipeline1.list_of_group_pattern_list[2]:
				pipeline1_all_pattern_combination_list.append([group_1, group_2, group_3])

	pipeline2_all_pattern_combination_list = []
	for group_1 in pipeline2.list_of_group_pattern_list[0]:
		for group_2 in pipeline2.list_of_group_pattern_list[1]:
			for group_3 in pipeline2.list_of_group_pattern_list[2]:
				pipeline2_all_pattern_combination_list.append([group_1, group_2, group_3])

	#先生成每个 pipeline 的 group_pattern_name_list 之后依次在 list_of_block_info 中找到对应的具体信息
	#pipeline 的 list_of_group_pattern_list 中的分层方法
	#group_pattern_list - single_pattern_list - block_list - block
	pipeline1_all_pattern_combination_list = create_all_pattern_combination_list(pipeline1_all_pattern_combination_list)
	pipeline2_all_pattern_combination_list = create_all_pattern_combination_list(pipeline2_all_pattern_combination_list)


	#对于每个 mos 计算其 AD AS PD PS, 之后插入到 sp 文件之中
	pipeline1_AD_AS_PD_PS_dict = create_AD_AS_PD_PS_dict(pipeline1, pipeline1.list_of_group_pattern_list, main_circuit)
	pipeline2_AD_AS_PD_PS_dict = create_AD_AS_PD_PS_dict(pipeline2, pipeline2.list_of_group_pattern_list, main_circuit)

	combinaiton_num = 1
	for group_pattern_list in pipeline1_all_pattern_combination_list:
		#对于 group pattern list 中包含的所有 mos, 替换其后面的 AD AS PD PS 参数
		mos_replace_dict = {}

		#对于一个特定的 single_pattern_list, 找出其中所包含的 mos 并计算其 AD AS PD PS 信息
		for single_pattern_list in group_pattern_list:
			mos_list, AD_AS_PD_PS_list = search_AS_PS_PD_PS(single_pattern_list, pipeline1_AD_AS_PD_PS_dict)
			#将 mos 和其参数一一对应并保存到 mos_replace_dict 之中
			for index, mos in enumerate(mos_list):
				mos_replace_dict[mos] = AD_AS_PD_PS_list[index]

		#print('mos_replace_dict', combinaiton_num)
		#对于给定的 mos_replace_dict 生成新的 sp 文件
		create_new_sp_file(mos_replace_dict, combinaiton_num, group_pattern_list, main_circuit)
		combinaiton_num += 1


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
	with open('3NAND_2_NP_errorall.sp') as file1:
		sp_file_1 = file1.readlines()
		for file in glob.glob('./sp_file_for_all_combination/*'):
		#with open('./sp_file_for_all_combination/combinaiton1.sp') as file2:
			num = 0
			with open(file) as file2:
				sp_file_2 = file2.readlines()
				for index, line1 in enumerate(sp_file_1):
					if line1 != sp_file_2[index]:
						num += 1

			print('num of modification', num)
	'''