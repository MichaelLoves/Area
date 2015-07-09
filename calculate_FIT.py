import glob, sys, math, re

net_to_node_dict = {'net38':'n1', 'net35':'n2', 'net36':'n3', 'net24':'n4', 'net14':'n5', 'net15':'n6', 'net8':'n7', 'net10':'n8', 'net5':'n9'}

combination_FIT_dict = {}

for sp_file in glob.glob('./sp_file_for_all_combination/*'):
	combination_num = sp_file.split('/')[-1].strip('.sp')

	with open(sp_file) as input_file:
		file = input_file.readlines()
		node_area_ratio_dict = {}
		node_area_dict = {}
		node_upset_per_hour_dict = {}
		node_timing_error_probability_dict = {}
		node_FIT_dict = {}

		#确定 standard cell area
		for line in file:
			if 'standard cell area' in line:
				standard_cell_area = float(line.split(':')[-1])

		#计算每个 node 的面积
		for line in file:
			if re.findall(r'\bnet\d{1,2}\b :', line):
				net_num = line.strip('*').split(':')[0].strip(' ')
				net_area_ratio = float(line.strip('*').split(':')[1].strip(' ').strip('\n'))
				#出去 pipeline 最下面的 net
				if net_num != 'net16':
					node_area_ratio_dict[net_to_node_dict[net_num]] = net_area_ratio

		for node, node_area_ratio in node_area_ratio_dict.items():
			node_area_dict[node] = node_area_ratio * standard_cell_area * pow(10, -12)

		for node, node_area in node_area_dict.items():
			#FIT 的定义是每平方厘米, 而 node_area 的单位为平方米, 所以需要除以 pow(10, -4)
			node_upset_per_hour_dict[node] = 10 * node_area / pow(10, -4)


	with open('result.txt') as result_file:
		result = result_file.readlines()

		#截取 combination 所对应的统计结果
		line_index_list = []
		for line_index, line in enumerate(result):
			if combination_num in line and '*' in line:
				line_index_list.append(line_index)
		all_node_result = result[line_index_list[0]:line_index_list[1]+1]

	#初始化字典
	for key in node_upset_per_hour_dict:
		node_FIT_dict[key] = 0.
		node_timing_error_probability_dict[key] = 0.


	for node in node_upset_per_hour_dict:
		total_simulation_number = 0
		total_error_number = 0

		for line_index, line in enumerate(all_node_result):
			if 'injection_node' in line and node in line:
				#总模拟次数
				total_simulation_number = float(all_node_result[line_index + 1].split(':')[1].strip(' \n'))

				#总错误次数
				for line in all_node_result[line_index + 3 : line_index + 8]:
					total_error_number += float(line.split(':')[1].strip(' \n'))
		
				node_timing_error_probability_dict[node] = total_error_number / total_simulation_number

	for node in node_FIT_dict:
		node_FIT_dict[node] = int(node_upset_per_hour_dict[node] * node_timing_error_probability_dict[node] * pow(10, 9))
	
	combination_FIT_dict[combination_num] = 0
	for node_FIT in node_FIT_dict.values():
		combination_FIT_dict[combination_num] += node_FIT


with open('combination_FIT.txt', 'w+') as output_file:
	for part in sorted(combination_FIT_dict.items(), key = lambda item:int(item[0].split('n')[-1])):
		output_file.write(part[0] + ' ' + str(part[1]) + '\n')













