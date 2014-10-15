import re

class Circuit:
	"""保存 netlist 中各部分 circuit 的 cell name 和 netlist"""
	def __init__(self, name, netlist):
		self.name = name         #circuit 的 cell name
		self.netlist = netlist   #circuit 的 netlist

	def m_list(self):
		list = []
		for part in self.netlist:
			if re.findall(r'\bm\w*\b', part):
				list.append(part)
		return(list)


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
	print(temp)
	return(temp)	


#把 netlist 以 break_point 为分割点 分割为几部分 返回一个各部分为 class Circuit 的 list
def break_into_part(filename, break_point):
	try:
		with open(filename) as file:
			file_list = list(file)
			splitter = find_all_index(file_list, break_point)
			splitter_list = iterate(splitter)
			temp = []
			list_of_circuits = []
			for i in range(len(splitter)):
				#print(splitter_list[i][0], splitter_list[i][1])
				list_of_circuits.append('circuit%d' %i)   	#把列表填满 circuit1, circuit2... 之后用每一项去创建 class Circuit 的 instance
				#temp.append(file_list[splitter_list[i][0]:splitter_list[i][1]])
				list_of_circuits[i] = Circuit(file_list[splitter_list[i][0]+1].replace('** Cell name: ', ''), file_list[splitter_list[i][0]+4:splitter_list[i][1]]) #填加各 subcircuit 的 name 和 netlist
			#temp.append(file_list[splitter_list[i][1]+1:])	
			list_of_circuits.append(Circuit(file_list[splitter_list[i][1]+2].replace('** Cell name: ', ''), file_list[splitter_list[i][1]+1:]))

			for part in list_of_circuits:
				print(part.name)
				print(part.m_list())
				#print(part.netlist)
				print()

	except IOError as err:
			print("File error: " + str(err))
			return(None)



break_into_part('netlist_lvs_3NAND_2_NP.txt', '** End of subcircuit definition.\n')
#list = [10, 100, 1000, 10000]
#iterate(list)