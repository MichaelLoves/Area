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

def calculate_area_ratio_of_node_in_single_pattern_list(node, single_pattern_list, list_of_block_info_in_every_single_pattern):
	#计算给定的 node 在其 pattern 中的面积比例
	for

def create_new_sp_file(mos_replace_dict, combinaiton_num, group_pattern_list):
	#用最上面的 n 和 p pipeline 的对应表来生成另一个需要替换的 mos_replace_dict
	mos_list = []
	for mos in mos_replace_dict.keys():
		if mos in n_pipeline_to_p_pipeline_dict:
			#print(mos, n_pipeline_to_p_pipeline_dict[mos])
			mos_list.append(n_pipeline_to_p_pipeline_dict[mos])
		#若 mos 不在 n_pipeline_to_p_pipeline_dict 中, 说明读入的为 p pipeline 生成的 replace ditc, 这时候用 p_pipeline_to_n_pipeline_dict
		else:
			mos_list.append(p_pipeline_to_n_pipeline_dict[mos])


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

	with open('./sp file for all combination/combinaiton%s.sp' %combinaiton_num ,'w+') as new_file:
		new_file.writelines(old_file[:-1])
		new_file.write('\n' + '*'*20 + ' pattern list ' + '*'*20 + '\n')

		for single_pattern_list in group_pattern_list:
			mos_list = []
			for part in single_pattern_list:
				if 'm' in part:
					mos_list.append(part)
			new_file.write(' '.join(mos_list) + '\n')

			for mos in mos_list:
				print(calculate_area_and_periphery_for_block(mos, single_pattern_list, main_circuit.list_of_block_info_in_every_single_pattern))

		new_file.write('*'*20 + ' pattern list ' + '*'*20 + '\n \n \n')
		new_file.write(old_file[-1].strip('\n'))

def write_into_file(pipeline1, pipeline2, main_circuit, sp_file):
	#先清除同目录下的 sp file for all combination 文件夹
	for file in glob.glob('./sp file for all combination/*'):
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
		create_new_sp_file(mos_replace_dict, combinaiton_num, group_pattern_list)
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
		for file in glob.glob('./sp file for all combination/*'):
		#with open('./sp file for all combination/combinaiton1.sp') as file2:
			num = 0
			with open(file) as file2:
				sp_file_2 = file2.readlines()
				for index, line1 in enumerate(sp_file_1):
					if line1 != sp_file_2[index]:
						num += 1

			print('num of modification', num)
	'''