import re, os, sys, glob, math

#查找一个元素的所有位置(部分包含)
def find_index(arr, search):
	return [index for index, item in enumerate(arr) if search in item]


net_dict = {'net10':0, 'net14':0, 'net15':0, 'net16':0, 'net24':0, 'net35':0, 'net36':0, 'net38':0, 'net5':0, 'net8':0}

for sp_file in glob.glob('./sp_file_for_all_combination/*'):
	with open(sp_file) as input_file:
		file = input_file.readlines()
		line_index = find_index(file, 'area ratio list')
		area_ratio_list = file[line_index[0]: line_index[1]]

		for part in area_ratio_list:
			if 'net' in part:
				net_num = part.strip('*').split(':')[0].strip(' ')
				area_ratio = float(part.strip('*').split(':')[1].strip('\n'))
				net_dict[net_num] += area_ratio

for key in net_dict:
	net_dict[key] = round(net_dict[key]/32, 5)

print(net_dict)
