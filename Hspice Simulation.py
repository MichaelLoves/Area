#encoding:utf-8
import os, sys, getopt, operator, csv, re, glob
import math, time
from copy import deepcopy

#电源电压
VDD = float(1.8)

#查找一个元素的所有位置(完全符合)
def find_index(arr, search):
	return [index for index, item in enumerate(arr) if item == search]

#查找一个元素的所有位置(部分包含)
def find_index_2(arr, search):
	return [index for index, item in enumerate(arr) if search in item]

def hspice_simulation(start_timing, end_timing, current_height, injection_node, output_node, input_file):

	injection_timing = float(start_timing)
	stop_timing = float(end_timing)
	#在 injection timing 的开始时间和结束时间之间进行间隔为 0.1ns 的循环
	while injection_timing <= stop_timing:
		injection_timing = round(injection_timing, 2)
		read_file = open(input_file, 'r')
		temp_file = read_file.readlines()

		#在原 sp 文件中查找定义 current height 的命令行
		injection_current_height_line_index = find_index_2(temp_file, '.param current_height ')
		line = temp_file[injection_current_height_line_index[0]]
		new_line = ''.join([line.split('current_height = ')[0] + 'current_height = ' + current_height + 'e-6' + line.split('current_height = ')[1].split(' ', 1)[1] ])
		temp_file[injection_current_height_line_index[0]] = new_line	

		#在原 sp 文件中查找定义 injection timing 的命令行并 comment out 掉
		injection_timing_line_index = find_index_2(temp_file, 'injection timing delay')
		for line_index, line in enumerate(temp_file[injection_timing_line_index[0]+1 : injection_timing_line_index[1]]):
			#初始化原 sp 文件中的命令行, 去掉之前行开头可能有的'*'符号
			line.strip('*')
			if '.param injection_timing_' + injection_node in line:
				#comment out 注入 node 所在行的命令
				temp_file[injection_timing_line_index[0] + line_index + 1] = '*' + line
				#并把本行命令保存下来, 在下面的部分使用
				injection_timing_option = line.split(' ')

		#通过替换 .param currentdelay = **n 这行命令中的 ** 来定义不同的 injection timing
		for line_number, line in enumerate(temp_file):
			if '.TRAN 1p simtime' in line and '*' not in line:
				injection_timing_option[3] = str(injection_timing) + 'n'
				temp_file[line_number+1] = ' '.join(injection_timing_option)

		#替换 .MEASURE command 中的有关 injection node 的参数部分
		for line_number, line in enumerate(temp_file):
			if '.MEASURE' in line and 'injection_timing' in line:
				measure_command = line.split(' ')
				for part_num, part in enumerate(measure_command):
					if 'injection_timing_' in part:
						old_part = part.split('injection_timing_')
						temp = injection_node + old_part[-1][2:]
						new_part = old_part[0] + 'injection_timing_' + temp
						measure_command[part_num] = new_part
				temp_file[line_number] = ' '.join(measure_command)


		#输出入力文件时, 以 combination 和 injection node 和 injection timing 作为文件名保存
		combination_num = input_file.split('/')[2].strip('.sp')
		write_file = open('./input_file/'  + combination_num +  '_' + injection_node + '_' + str(injection_timing) + '.sp', 'w+')
		for item in temp_file:
			write_file.write(item)

		write_file.close()
		read_file.close()

		#injection timing 每次 shift 的间隔为 0.1ns
		injection_timing = round(injection_timing + 0.1, 2)
		#injection_timing = round(injection_timing + 0.3, 2)		

	#调用 input_file 文件夹中的每个 sp 文件进行一次 hspice 模拟, 输出文件的文件名与输入文件保持一致并保持在 output_file 文件夹中
	for sp_file in sorted(glob.glob('./input_file/' + combination_num + '_' + injection_node + '*.sp')):
		#进行 Hspice Simulation
		os.system('hspice64 -hpp -mt 4 -i ' + sp_file + ' -o output_file/' + combination_num + '_' + injection_node + '_' + sp_file[-8:-3] + '.lis')
		




#从命令行中获取 CSV 文件
#可以是储存了不同 current height 的, 也可以是储存了不同 injection timing 的 CSV 文件
#simulation_mode = 1 : fixed current height, shift injection timing
#simulation_mode = 2 : fixed injection timing, shift current height
opts, args = getopt.getopt(sys.argv[1:], "hi:c:m:")
input_file, simulation_mode, input_csv_file = '', '', ''

def usage():
	#比如 python Hspice Simulation.py -i 3NAND_2_NP_errorall.sp -m 1 -c timing.csv
	print('Usage: ' + sys.argv[0] + ' -i input_file.sp -m simulation_mode -c input_csv_file')

for op, value in opts:
	if op == '-i':
		input_file = value
	if op == '-c':
		input_csv_file = value
	if op == '-m':
		simulation_mode = value
	elif op == '-h':
		usage()
		sys.exit()


#读取 CSV 文件
CSV_file = csv.reader(open(input_csv_file, 'rU'))

#保存 CSV 文件中的输入数据
input_data = []
for line in CSV_file:
	if re.findall(r"\bstart\w*\b", ' '.join(line)):
		pass
	else:
		single_data = line[0].split(';')
		input_data.append(single_data)

print('input_data')
print(input_data)


#'''
########## 进行 hspice simulation ##########
for data in input_data:
	hspice_simulation(data[0], data[1], data[2], data[3], data[4], input_file)
#'''

