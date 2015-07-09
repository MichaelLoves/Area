import glob, sys, re


with open('node capacitance.txt', 'w+') as output_file:

	for sp_file in glob.glob('../sp_file_for_all_combination/*'):
		print(sp_file.split('/')[-1])
		file_name = sp_file.split('/')[-1]

		with open(sp_file) as input_file:
			file = input_file.readlines()
			node_capacitance_dict = {}
			net_to_node = {'net132':'n1', 'net0336':'n2', 'net0136':'n3', 'net284':'n4', 'net0330':'n5', 'net0342':'n6', 'net246':'n7', 'net0348':'n8', 'net105':'n9'}

			for line in file:
				if line[0] == 'c':
					net = line.split(' ')[1]
					node_capacitance = line.split(' ')[-2]

					if net in net_to_node.keys():
						node_capacitance_dict[net_to_node[net]] = node_capacitance

		sorted_dict = sorted(node_capacitance_dict.items(), key = lambda node_capacitance_dict:node_capacitance_dict[0])
		print(sorted_dict)

		output_file.write(file_name + '\n')
		for item in sorted_dict:
			output_file.write(item[0] + ' ')
			output_file.write(item[1] + '\n')
		output_file.write('\n'*2)