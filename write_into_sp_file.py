import re, os, sys, getopt, operator, csv
from copy import deepcopy

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

def create_AD_AS_PD_PS_list(pipeline, pipeline_group_pattern_name_list, main_circuit):
	#对于读入的 pipeline, 结合 main_circuit 中详细的 block 信息, 计算 AD AS PD PS
	pipeline_AD_AS_PD_PS_list = []
	for group_pattern_name_list in pipeline_group_pattern_name_list:
		for single_pattern_name in group_pattern_name_list:
			block_AD_AS_PD_PS_dict = {}
			for block_name in main_circuit.list_of_block_info_in_every_single_pattern.keys():
				if block_name == single_pattern_name:
					mos_AD_AS_PD_PS_list = []
					for block_index, block in enumerate(main_circuit.list_of_block_info_in_every_single_pattern[block_name]):
						# 以 gate block 为中心, 利用左右两侧的 block (可能是 net, 可能是 gate_gate_sw) 来计算 AD AS PD PS
						if block.block_name == 'gate':
							mos_AD_AS_PD_PS_list.append(calculate_area_and_periphery_for_block(main_circuit.list_of_block_info_in_every_single_pattern[block_name][block_index-1], block, main_circuit.list_of_block_info_in_every_single_pattern[block_name][block_index+1]))
					block_AD_AS_PD_PS_dict[block_name] = mos_AD_AS_PD_PS_list
			#只有在 dict 包含元素的时候才进行填加
			if block_AD_AS_PD_PS_dict:
				pipeline_AD_AS_PD_PS_list.append(block_AD_AS_PD_PS_dict)
	return(pipeline_AD_AS_PD_PS_list)

def search_AS_PS_PD_PS(single_pattern_list, AD_AS_PD_PS_list):
	mos_list = []
	for block_list in single_pattern_list:
		block_list_name = []
		for block in block_list:
			block_list_name.append(block.number)
		#print(block_list_name)
		#print('block_list_name', block_list_name)
		for single_pattern_dict in AD_AS_PD_PS_list:
			if ' '.join(block_list_name) in single_pattern_dict:
				print(single_pattern_dict)


def write_into_file(pipeline1, pipeline2, main_circuit, sp_file):
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
	pipeline1_AD_AS_PD_PS_list = create_AD_AS_PD_PS_list(pipeline1, pipeline1_all_pattern_combination_list, main_circuit)
	pipeline2_AD_AS_PD_PS_list = create_AD_AS_PD_PS_list(pipeline2, pipeline1_all_pattern_combination_list, main_circuit)

	print('吃饭')

	'''
	for single_pattern in pipeline1_AD_AS_PD_PS_list:
		print(single_pattern)
	print()			
	#'''


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
