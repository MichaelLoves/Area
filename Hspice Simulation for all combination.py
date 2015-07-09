#encoding:utf-8
import os, sys, getopt, operator, csv, glob, re
import math, time

#电源电压
VDD = float(1.8)

#查找一个元素的所有位置(完全符合)
def find_index(arr, search):
	return [index for index, item in enumerate(arr) if item == search]

#查找一个元素的所有位置(部分包含)
def find_index_2(arr, search):
	return [index for index, item in enumerate(arr) if search in item]

#从 .lis 文件中的单行中抽取信息
def extract_data(line):
	data_name, data = '', ''
	data_name = line.split('=')[0]
	raw_data = line.split('  ')[1]
	if 'e' in raw_data:
		data = float(raw_data.split('e')[0])/10**float(raw_data.split('e')[1].strip('-'))
	elif raw_data:
		#把原本的 string 类型转换为 float 类型, 好方便于之后的数值比较
		data = float(raw_data)
	else:
		#若在 .lis 文件中的结果为 failed (null)
		data = ''
	return(data_name, data)


############################## 判断波形的函数 ##############################

def is_Normal(single_result):
	#判断是否为正常波形
	#在n_and_3_timing3之后三个周期内的pulse_width与之前的测量结果n_and_3_pulse_width大致相同 且最大电压约为VDD
	#且cd_3, cd_4的波形也为正常

	#确定 cd_3 的 pulse_width
	if single_result['cd_3_pulse_width_after_pulse_in_period1_1'] > 0:
		cd_3_pulse_width_after_pulse_in_period1 = single_result['cd_3_pulse_width_after_pulse_in_period1_1']
	else:
		cd_3_pulse_width_after_pulse_in_period1 = single_result['cd_3_pulse_width_after_pulse_in_period1_2']

	#确定 cd_4 的 pulse_width
	if single_result['cd_4_pulse_width_after_pulse_in_period1_1'] > 0:
		cd_4_pulse_width_after_pulse_in_period1 = single_result['cd_4_pulse_width_after_pulse_in_period1_1']
	else:
		cd_4_pulse_width_after_pulse_in_period1 = single_result['cd_4_pulse_width_after_pulse_in_period1_2']

	#确定在injection timing之后三个周内各自的n_and_3_pulse_width_after_pulse
	if single_result['n_and_3_pulse_width_after_pulse_in_period1_1'] > 0:
		n_and_3_pulse_width_after_pulse_in_period1 = single_result['n_and_3_pulse_width_after_pulse_in_period1_1']
	else:
		n_and_3_pulse_width_after_pulse_in_period1 = single_result['n_and_3_pulse_width_after_pulse_in_period1_2']

	if single_result['n_and_3_pulse_width_after_pulse_in_period2_1'] > 0:
		n_and_3_pulse_width_after_pulse_in_period2 = single_result['n_and_3_pulse_width_after_pulse_in_period2_1']
	else:
		n_and_3_pulse_width_after_pulse_in_period2 = single_result['n_and_3_pulse_width_after_pulse_in_period2_2']
		
	if single_result['n_and_3_pulse_width_after_pulse_in_period3_1'] > 0:
		n_and_3_pulse_width_after_pulse_in_period3 = single_result['n_and_3_pulse_width_after_pulse_in_period3_1']
	else:
		n_and_3_pulse_width_after_pulse_in_period3 = single_result['n_and_3_pulse_width_after_pulse_in_period3_2']


	'''
	print('is normal')
	print('1', single_result['n_and_3_rise_timing_1'] < single_result['error_pulse_injection_timing'] + single_result['n_and_3_period'] ) 
	print('2', single_result['n_and_3_pulse_width']*0.7 < n_and_3_pulse_width_after_pulse_in_period1 and \
	n_and_3_pulse_width_after_pulse_in_period1 < single_result['n_and_3_pulse_width']*1.3 )
	print('3', single_result['n_and_3_pulse_width']*0.7 < n_and_3_pulse_width_after_pulse_in_period2 and \
	n_and_3_pulse_width_after_pulse_in_period2 < single_result['n_and_3_pulse_width']*1.3 ) 
	print('4', single_result['n_and_3_pulse_width']*0.7 < n_and_3_pulse_width_after_pulse_in_period3 and \
	n_and_3_pulse_width_after_pulse_in_period3 < single_result['n_and_3_pulse_width']*1.3 )
	print('5', VDD*0.8 < single_result['n_and_3_max_vol_after_pulse_in_period1'] and \
	single_result['n_and_3_max_vol_after_pulse_in_period1'] < VDD*1.2 ) 
	print('6', VDD*0.8 < single_result['n_and_3_max_vol_after_pulse_in_period2'] and \
	single_result['n_and_3_max_vol_after_pulse_in_period2'] < VDD*1.2 )
	print('7', VDD*0.8 < single_result['n_and_3_max_vol_after_pulse_in_period3'] and \
	single_result['n_and_3_max_vol_after_pulse_in_period3'] < VDD*1.2 )
	print('8', single_result['cd_3_pulse_width']*0.7 < cd_3_pulse_width_after_pulse_in_period1 and \
	cd_3_pulse_width_after_pulse_in_period1 < single_result['cd_3_pulse_width']*1.3 )
	print('9', single_result['cd_3_rise_timing_after_pulse_1'] <= single_result['error_pulse_injection_timing'] + single_result['cd_3_period'] )
	print('10', single_result['cd_4_pulse_width']*0.7 < cd_4_pulse_width_after_pulse_in_period1 and \
	cd_4_pulse_width_after_pulse_in_period1 < single_result['cd_4_pulse_width']*1.3 )
	print('11', (single_result['cd_4_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_4_period']) or (single_result['cd_4_period'] * 0.7 < single_result['cd_4_rise_timing_after_pulse_2'] - single_result['cd_4_rise_timing_after_pulse_1'] and single_result['cd_4_rise_timing_after_pulse_2'] - single_result['cd_4_rise_timing_after_pulse_1']  < single_result['cd_4_period'] * 1.3)  )
	#'''	

	#关于 n_and_3, cd_3, cd_4, n_nand_3, n_nand_4 的判断
	if ( single_result['n_and_3_rise_timing_1'] < single_result['error_pulse_injection_timing'] + single_result['n_and_3_period'] ) and \
	( single_result['n_and_3_pulse_width']*0.7 < n_and_3_pulse_width_after_pulse_in_period2 and \
	n_and_3_pulse_width_after_pulse_in_period2 < single_result['n_and_3_pulse_width']*1.3 ) and \
	( single_result['n_and_3_pulse_width']*0.7 < n_and_3_pulse_width_after_pulse_in_period3 and \
	n_and_3_pulse_width_after_pulse_in_period3 < single_result['n_and_3_pulse_width']*1.3 ) and \
	( VDD*0.8 < single_result['n_and_3_max_vol_after_pulse_in_period1'] and \
	single_result['n_and_3_max_vol_after_pulse_in_period1'] < VDD*1.2 ) and \
	(VDD*0.8 < single_result['n_and_3_max_vol_after_pulse_in_period2'] and \
	single_result['n_and_3_max_vol_after_pulse_in_period2'] < VDD*1.2 ) and \
	(VDD*0.8 < single_result['n_and_3_max_vol_after_pulse_in_period3'] and \
	single_result['n_and_3_max_vol_after_pulse_in_period3'] < VDD*1.2 ) and \
	(single_result['cd_3_pulse_width']*0.7 < cd_3_pulse_width_after_pulse_in_period1 and \
	cd_3_pulse_width_after_pulse_in_period1 < single_result['cd_3_pulse_width']*1.3 ) and \
	(single_result['cd_3_rise_timing_after_pulse_1'] <= single_result['error_pulse_injection_timing'] + single_result['cd_3_period'] ) and \
	(single_result['cd_4_pulse_width']*0.7 < cd_4_pulse_width_after_pulse_in_period1 and \
	cd_4_pulse_width_after_pulse_in_period1 < single_result['cd_4_pulse_width']*1.3 ) and \
	( (single_result['cd_4_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_4_period']) or (single_result['cd_4_period'] * 0.7 < single_result['cd_4_rise_timing_after_pulse_2'] - single_result['cd_4_rise_timing_after_pulse_1'] and single_result['cd_4_rise_timing_after_pulse_2'] - single_result['cd_4_rise_timing_after_pulse_1']  < single_result['cd_4_period'] * 1.3 ) ) :
		return(True)
	else:
		return(False)

def is_DeadlocK(single_result):
	#判断是否发生 deadlock 现象, 在注入 error pulse 之后, 没有出现第三个波的情况视为 deadlock
	if not single_result['n_and_3_rise_timing_3']:
		return(True)
	else:
		return(False)


def is_11_error(single_result):
	#在 normal operation 的情况下, n_nand_3 和 n_nand_4的输出为1
	#设置阈值为vdd*0.5的根据在Evernote笔记中有所记录
	
	'''
	print('is 11 error')
	print('1', single_result['n_and_3_max_vol_after_pulse_in_period1'] > VDD*0.5 )
	print('2', single_result['n_nand_3_max_vol_after_pulse'] > VDD*0.5 )
	print('3', single_result['n_nand_4_max_vol_after_pulse'] > VDD*0.5)
	#'''

	if single_result['n_and_3_max_vol_after_pulse_in_period1'] > VDD*0.5 and \
	single_result['n_nand_3_max_vol_after_pulse'] > VDD*0.5 and \
	single_result['n_nand_4_max_vol_after_pulse'] > VDD*0.5:
		return(True)


def is_Wrong_Output(single_result):
	#在cd信号正常的情况下(cd_3和cd_4波形正常)，应该有输出的n_and_3 和 n_and_4 为0, 且n_nand_3 和 n_nand_4 的输出为1, 则视为发生了出力的反转
	#cd信号正常:在injection timing+period之内rise, 且pulse width正常
	#波形特征 : n_and_3和 n_and_4的第一次 rise_timing 不在 injection timing+period 范围之内
 	#而 n_nand_3和 n_nand_4在 injection timing+period 范围内有波峰 


	#确定 n_and_3 在 injection timing 之后第二个周期内的 pulse_width
	if single_result['n_and_3_pulse_width_after_pulse_in_period2_1'] > 0:
		n_and_3_pulse_width_after_pulse_in_period2 = single_result['n_and_3_pulse_width_after_pulse_in_period2_1']
	else:
		n_and_3_pulse_width_after_pulse_in_period2 = single_result['n_and_3_pulse_width_after_pulse_in_period2_2']

	#确定 cd_3 的 pulse_width
	if single_result['cd_3_pulse_width_after_pulse_in_period1_1'] > 0:
		cd_3_pulse_width_after_pulse_in_period1 = single_result['cd_3_pulse_width_after_pulse_in_period1_1']
	else:
		cd_3_pulse_width_after_pulse_in_period1 = single_result['cd_3_pulse_width_after_pulse_in_period1_2']

	#确定 cd_4 的 pulse_width
	if single_result['cd_4_pulse_width_after_pulse_in_period1_1'] > 0:
		cd_4_pulse_width_after_pulse_in_period1 = single_result['cd_4_pulse_width_after_pulse_in_period1_1']
	else:
		cd_4_pulse_width_after_pulse_in_period1 = single_result['cd_4_pulse_width_after_pulse_in_period1_2']

	'''
	print('is_Wrong_Output')
	print('1', single_result['cd_3_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_3_period'] )
	print('2', cd_3_pulse_width_after_pulse_in_period1 > single_result['cd_3_pulse_width'] * 0.7 and cd_3_pulse_width_after_pulse_in_period1 < single_result['cd_3_pulse_width'] * 1.3 ) 
	print('3', single_result['cd_4_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_4_period'] ) 
	print('4', cd_4_pulse_width_after_pulse_in_period1 > single_result['cd_4_pulse_width'] * 0.7 and cd_4_pulse_width_after_pulse_in_period1 < single_result['cd_4_pulse_width'] * 1.3 )
	print('5', not ( ( single_result['n_and_3_rise_to_vdd_timing_after_pulse'] < single_result['error_pulse_injection_timing'] + single_result['n_and_3_period'] and \
	single_result['n_and_3_pulse_width']*0.7 < n_and_3_pulse_width_after_pulse_in_period2 and \
	n_and_3_pulse_width_after_pulse_in_period2 < single_result['n_and_3_pulse_width']*1.3 ) and \
	single_result['n_nand_3_max_vol_after_pulse'] < VDD*0.5 ) )
	print()
	#'''

	#关于cd_3, cd_4, n_and_3 的判断
	if ( (single_result['cd_3_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_3_period'] ) and \
	(single_result['cd_3_pulse_width'] * 0.7 < cd_3_pulse_width_after_pulse_in_period1 and cd_3_pulse_width_after_pulse_in_period1 < single_result['cd_3_pulse_width'] * 1.3 ) and \
	(single_result['cd_4_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_4_period'] ) and \
	(cd_4_pulse_width_after_pulse_in_period1 > single_result['cd_4_pulse_width'] * 0.7 and cd_4_pulse_width_after_pulse_in_period1 < single_result['cd_4_pulse_width'] * 1.3 ) and \
	not ( ( single_result['n_and_3_rise_to_vdd_timing_after_pulse'] < single_result['error_pulse_injection_timing'] + single_result['n_and_3_period'] and \
	single_result['n_and_3_pulse_width']*0.7 < n_and_3_pulse_width_after_pulse_in_period2 and n_and_3_pulse_width_after_pulse_in_period2 < single_result['n_and_3_pulse_width']*1.3 ) and \
	single_result['n_nand_3_max_vol_after_pulse'] < VDD*0.5 ) ):
		return(True)
	else:
		return(False)	


def is_Wrong_CD(single_result):

	#确定 cd_3 的 pulse_width
	if single_result['cd_3_pulse_width_after_pulse_in_period1_1'] > 0:
		cd_3_pulse_width_after_pulse_in_period1 = single_result['cd_3_pulse_width_after_pulse_in_period1_1']
	else:
		cd_3_pulse_width_after_pulse_in_period1 = single_result['cd_3_pulse_width_after_pulse_in_period1_2']

	#确定 cd_4 的 pulse_width
	if single_result['cd_4_pulse_width_after_pulse_in_period1_1'] > 0:
		cd_4_pulse_width_after_pulse_in_period1 = single_result['cd_4_pulse_width_after_pulse_in_period1_1']
	else:
		cd_4_pulse_width_after_pulse_in_period1 = single_result['cd_4_pulse_width_after_pulse_in_period1_2']

	'''
	print('is Wrong CD')
	print('1', single_result['cd_3_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_3_period'] )
	print('2', single_result['cd_3_pulse_width'] * 0.7 < cd_3_pulse_width_after_pulse_in_period1 and cd_3_pulse_width_after_pulse_in_period1 < single_result['cd_3_pulse_width'] * 1.3 )
	print('3', (single_result['cd_4_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_4_period']) or (single_result['cd_4_period'] * 0.7 < single_result['cd_4_rise_timing_after_pulse_2'] - single_result['cd_4_rise_timing_after_pulse_1'] and single_result['cd_4_rise_timing_after_pulse_2'] - single_result['cd_4_rise_timing_after_pulse_1']  < single_result['cd_4_period'] * 1.3) )
	print('4', cd_4_pulse_width_after_pulse_in_period1 > single_result['cd_4_pulse_width'] * 0.7 and cd_4_pulse_width_after_pulse_in_period1 < single_result['cd_4_pulse_width'] * 1.3 )
	#'''

	if ( (single_result['cd_3_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_3_period'] ) and \
	(single_result['cd_3_pulse_width'] * 0.7 < cd_3_pulse_width_after_pulse_in_period1 and cd_3_pulse_width_after_pulse_in_period1 < single_result['cd_3_pulse_width'] * 1.3 ) and \
	( (single_result['cd_4_rise_timing_after_pulse_1'] < single_result['error_pulse_injection_timing'] + single_result['cd_4_period']) or (single_result['cd_4_period'] * 0.7 < single_result['cd_4_rise_timing_after_pulse_2'] - single_result['cd_4_rise_timing_after_pulse_1'] and single_result['cd_4_rise_timing_after_pulse_2'] - single_result['cd_4_rise_timing_after_pulse_1']  < single_result['cd_4_period'] * 1.3)  ) and \
	(cd_4_pulse_width_after_pulse_in_period1 > single_result['cd_4_pulse_width'] * 0.7 and cd_4_pulse_width_after_pulse_in_period1 < single_result['cd_4_pulse_width'] * 1.3 )  ):
		return(False)
	else:
		return(True)	

############################## 判断波形的函数 ##############################

#从 output_file 文件夹中依照每一种combination来统计波形数据
def analyze_waveform(lis_file):
	#print('analyze waveform : lis file', lis_file)
	file = lis_file.readlines()
	result_list = []

	#先找到'transient analysis'所在行的行数, 用来确定每次模拟的结果在文件中所在的位置
	#以 'transient analysis'所在行作为截取上限
	for line in file:
		if re.findall(r'transient analysis', line):
			top_line_num = find_index(file, line)[0]

	#以 '100.0%time'所在行作为截取下限
	bottom_line_num = find_index_2(file, r'100.0% time =')[0]
	
	#根据截取上限和下限, 截取中间部分的参数数据, 并清楚空白行
	single_result = file[top_line_num + 2 : bottom_line_num]
	while ' \n' in single_result:
		single_result.remove(' \n')

	#将模拟结果保存在 single_result_dict 中, 不同的参数对应后面不同的数值
	single_result_dict = {}
	for item in single_result:
		data_name, data = extract_data(item)
		single_result_dict[data_name] = data

	#输出 single_result 内容
	#print('*'*40 + 'result_list' + '*'*40)
	#print(single_result_dict)

	#统计是否出现 deadlock
	if is_Normal(single_result_dict):
		if is_11_error(single_result_dict):
			return('11 error')
		else:
			return('normal')
	elif is_DeadlocK(single_result_dict):
		return('deadlock')
	elif is_Wrong_Output(single_result_dict):
		return('wrong output')
	elif is_Wrong_CD(single_result_dict):
		return('wrong cd')
	else:
		return('unknown')



'''
#进行模拟之前, 清空 input_file 和 output_file 文件夹中的所有文件
for file in glob.glob('./input_file/*'):
	os.remove(file)
for file in glob.glob('./output_file/*'):
	os.remove(file)
#'''


opts, args = getopt.getopt(sys.argv[1:], "i:")
injection_timing_csv_file = ''

def usage():
	#e.g. python Hspice Simulation for all combination.py -i timing.csv
	print('Usage: ' + sys.argv[0] + ' -i injection_timing_csv_file.csv')

for op, value in opts:
	if op == '-i':
		injection_timing_csv_file = value
	elif op == '-h':
		usage()
		sys.exit()


#用于测量程式运行时间
#程序开始时间
start_time = time.time()

'''
#对于每一种combination的sp文件进行 Hspice Simulation
for sp_file in sorted(glob.glob('./sp_file_for_all_combination/*'), key = lambda filename:int(filename.split('combination')[-1].strip('.sp')) ):
	os.system('python Hspice\ Simulation.py -i ' + sp_file +' -m 1 -c ' + injection_timing_csv_file)
	
#'''

'''
for sp_file in sorted(glob.glob('./sp_file_for_all_combination_exp/*')):
	os.system('python Hspice\ Simulation\ exp.py -i ' + sp_file +' -m 1 -c ' + injection_timing_csv_file)
#'''

#读取 output_file 文件夹中每个 .lis 文件并对其中的参数进行抽取和统计, 以便判断是否出现错误波形
#统计结果保存在 result.txt 文件之中
result_file = open('result.txt', 'w')
result_list = []

for file in sorted(glob.glob('./output_file/combination*.lis'), key = lambda file:int(file.split('combination')[-1].split('_')[0])):
	print('filename', file)
	lis_file = open(file, 'r')
	result = analyze_waveform(lis_file)
	result_list.extend([file.split('/')[-1] + ' '*3 + result + '\n'])
	lis_file.close()
result_file.writelines(result_list)
result_file.close()
#'''



########## 对于 result.txt 文件中的结果进行统计 #########
result_file = open('result.txt', 'r+')
result = result_file.readlines()

result_file.write('\n\nData Analysis\n')

#每一种 combination 对应不同 node 在不同 timing 的结果
combination_result_dict = {}

#初始化字典, key 为 combination 番号, value 为保存结果的列表
for line in result:
	#line = combination1_n1_100.0.lis  deadlock
	combination = line.split('_')[0]
	combination_result_dict[combination] = []

#每一种 combination 的 value 为 [injection_node, injection_timing, result] 的列表
for line in result:
	for combination in combination_result_dict:
		if line.split('_')[0] == combination:
			#line = combination1_n1_100.0.lis  deadlock\n
			injection_node = line.split('_', 2)[1]
			injection_timing = line.split('_', 2)[2].split(' ')[0].strip('.lis')
			result = line.split(' ', 1)[-1].strip('\n').strip(' ')
			combination_result_dict[combination].append([injection_node, injection_timing, result])

#获得 injection timing 的范围
node = combination_result_dict['combination1'][0][0]
injection_timing_list = []
for result_list in combination_result_dict['combination1']:
	if result_list[0] == node:
		injection_timing_list.append(result_list[1])
injection_timing_list.sort()
injection_timing_start = injection_timing_list[0]
injection_timing_end = injection_timing_list[-1]
result_file.write('injection timing : ' + injection_timing_start + ' -- ' + injection_timing_end + ' ns \n\n\n')

print(combination_result_dict)

for combination in sorted(combination_result_dict.keys(), key = lambda name:int(name.split('combination')[1]) ):
	
	result_file.write('*'*20 + '  ' + combination + '  ' + '*'*20 + '\n\n')

	#一个 combination 中所包含的 injection node
	injection_node_list = []
	for result_list in combination_result_dict[combination]:
		if result_list[0] not in injection_node_list:
			injection_node_list.append(result_list[0])

	#每种 combination 的总统计数据
	total_number_of_simulation = 0
	total_number_of_deadlock = 0
	total_number_of_normal = 0
	total_number_of_11_error = 0
	total_number_of_wrong_output = 0
	total_number_of_wrong_cd = 0
	total_number_of_unknown = 0

	#统计每个 node 的数据
	for injection_node in injection_node_list:
		#对于抽出的信息错误类型进行统计
		number_of_simulation = 0
		number_of_deadlock = 0
		number_of_normal = 0
		number_of_11_error = 0
		number_of_wrong_output = 0
		number_of_wrong_cd = 0
		number_of_unknown = 0

		for result_list in combination_result_dict[combination]:
			if result_list[0] == injection_node:
				number_of_simulation += 1
				total_number_of_simulation += 1
				if result_list[2] == 'normal':
					number_of_normal += 1
					total_number_of_normal += 1
				elif result_list[2] == 'deadlock':
					number_of_deadlock += 1
					total_number_of_deadlock += 1
				elif result_list[2] == '11 error':
					number_of_11_error += 1
					total_number_of_11_error += 1
				elif result_list[2] == 'wrong output':
					number_of_wrong_output += 1
					total_number_of_wrong_output += 1
				elif result_list[2] == 'wrong cd':
					number_of_wrong_cd += 1
					total_number_of_wrong_cd += 1
				else:
					number_of_unknown += 1	
					total_number_of_unknown += 1

		result_file.write('injection_node : ' + injection_node + '\n')
		result_file.write('number of simulation : %s \n' %number_of_simulation)
		result_file.write('number of normal : %s \n' %number_of_normal)
		result_file.write('number of deadlock : %s \n' %number_of_deadlock)
		result_file.write('number of 11 error : %s \n' %number_of_11_error)
		result_file.write('number of wrong output: %s \n' %number_of_wrong_output)
		result_file.write('number of wrong cd: %s \n' %number_of_wrong_cd)
		result_file.write('number of unknown : %s \n\n' %number_of_unknown)

	result_file.write('Total number\n')
	result_file.write('total number of simulation : %s \n' %total_number_of_simulation)
	result_file.write('total number of normal : %s \n' %total_number_of_normal)
	result_file.write('total number of deadlock : %s \n' %total_number_of_deadlock)
	result_file.write('total number of 11 error : %s \n' %total_number_of_11_error)
	result_file.write('total number of wrong output: %s \n' %total_number_of_wrong_output)
	result_file.write('total number of wrong cd: %s \n' %total_number_of_wrong_cd)
	result_file.write('total number of unknown : %s \n\n' %total_number_of_unknown)


	result_file.write('*'*20 + '  ' + combination + '  ' + '*'*20 + '\n'*3)


#程序结束时间
finish_time = time.time()
result_file.write('time used(s) : %s' %(finish_time - start_time))

result_file.close()
