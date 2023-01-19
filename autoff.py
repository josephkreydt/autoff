'''
- Read a file that lays out the fields/format of a plaintext flat file and CSV file fields that should map to each
- Then automatically generate a flat file based on the mapping file
'''
#### Handle outputJustify and outputPadCharacter in map file and in set_field function
#### Add ability to name file based on JSON map, and ability to use variables like MMDDYYYY in the filename

import csv
import json
import logging
from datetime import datetime
import sys
from pathlib import Path

# variables
json_map_file_path = '1098.json'
output_file_path = 'corrected_1098s.dat'
current_datetime = datetime.now()
current_date = current_datetime.strftime("%Y-%m-%d")
current_time = current_datetime.strftime("%H:%M:%S")

logging.basicConfig(filename='auto_ff_error_log_{}.txt'.format(current_date), level=logging.DEBUG)

# figure out length of string
# if string length is greater than field length, then trim string
# if string length is less than field length, then pad string
def set_field(data, field_length, justify, pad_char):
	formatted_field = ''
	string_length = len(data)
	#logging.info('set_field function. length of data string passed in: {}'.format(string_length))
	#logging.info('set_field function. length of output field: {}'.format(field_length))
	#logging.info('set_field function. output field justification: {}'.format(justify))
	if string_length < field_length:
		#logging.info('set_field function. string will be padded because it is shorter than output field length')
		if justify == "left":
			formatted_field = data.ljust(field_length, pad_char)
			#logging.info('set_field function. padding character: {}'.format(pad_char))
		elif justify == "right":
			formatted_field = data.rjust(field_length, pad_char)
			#logging.info('set_field function. padding character: {}'.format(pad_char))
		else:
			logging.error('set_field function. field must either be left or right justified')
			formatted_field = ''
	else:
		formatted_field = data[:field_length]
		#logging.warning('set_field function. string will be trimmed because it is longer than output field length')
	#logging.info('set_field function. formatted field: {}'.format(formatted_field))
	if formatted_field == '':
		logging.error('set_field function. problem trimming/padding the field')
		logging.info('set_field function. length of data string passed in: {}'.format(string_length))
		logging.info('set_field function. length of output field: {}'.format(field_length))
		logging.info('set_field function. output field justification: {}'.format(justify))
		logging.info('set_field function. padding character: {}'.format(pad_char))
	return formatted_field

# function to get a map field's value based on it's outputColumnStart value in map file
def get_field_value(output_column_start_value, field_to_get_value_of, map_json, output_record_row_number):
	final_field_value = ''
	map_json_row_number = 'row' + str(output_record_row_number)
	#logging.info('get_field_value function. getting value based on outputColumnStart: {}'.format(output_column_start_value))
	#logging.info('get_field_value function. getting value of this field: {}'.format(field_to_get_value_of))
	#logging.info('get_field_value function. getting value from this row: {}'.format(map_json_row_number))
	for field_value in map_json[map_json_row_number]:
		if output_column_start_value == field_value['outputColumnStart']:
			final_field_value = field_value[field_to_get_value_of]
		#logging.info('get_field_value function. found {0} value of: {1}'.format(field_to_get_value_of, final_field_value))
	if final_field_value == '':
		logging.error('get_field_value function. no field/value found in JSON map file')
		logging.info('get_field_value function. getting value based on outputColumnStart: {}'.format(output_column_start_value))
		logging.info('get_field_value function. getting value of this field: {}'.format(field_to_get_value_of))
		logging.info('get_field_value function. getting value from JSON map file, this row: {}'.format(map_json_row_number))
	return final_field_value

# create array that contains the proper order of each column based on start position
# uses values of outputColumnStart in the map file because outputColumnStart always has to be unique, so it's a unique identifier 
def get_field_write_order(map_json, output_record_row_number):
	tracker_list = []
	field_write_order = []
	map_json_row_number = 'row' + str(output_record_row_number)
	for each in map_json[map_json_row_number]:
		tracker_list.append(each['outputColumnStart'])
	tracker_list.sort()
	field_write_order = tracker_list

	if not field_write_order:
		logging.error('get_field_write_order function. no fields found')
		logging.info('get_field_write_order function. checked for fields in JSON map file in this row: {}'.format(map_json_row_number))

	return field_write_order

# check the map file to get the length that a field should be in the output file
def get_field_length(map_json, field_output_column_start_value, output_record_row_number):
	field_length = 0
	map_json_row_number = 'row' + str(output_record_row_number)
	for field_value in map_json[map_json_row_number]:
		if field_output_column_start_value == field_value['outputColumnStart']:
			field_length = field_value['outputColumnLength']

	if field_length == 0:
		logging.error('get_field_length function. field length is 0, or unable to determine field length')
		logging.info('get_field_length function. checked for field length in JSON map file in this row: {}'.format(map_json_row_number))
		logging.info('get_field_length function. checked for field length in item with outputColumnStart value of: {}'.format(field_output_column_start_value))

	return field_length

# get the default output value for this output field, given in the map file
def get_default_value(map_json, field_output_column_start_value, output_record_row_number):
	default_value = ''
	map_json_row_number = 'row' + str(output_record_row_number)
	for field_value in map_json[map_json_row_number]:
		if field_output_column_start_value == field_value['outputColumnStart']:
			default_value = field_value['outputDefaultValue']
	if default_value is None:
		return ''
	else:
		return default_value

def get_justify_value(map_json, field_output_column_start_value, output_record_row_number):
	justify_value = 'left'
	map_json_row_number = 'row' + str(output_record_row_number)
	for field_value in map_json[map_json_row_number]:
		if field_output_column_start_value == field_value['outputColumnStart']:
			justify_value = field_value['outputJustify']
	if justify_value is None:
		return 'left'
	else:
		return justify_value

def get_pad_value(map_json, field_output_column_start_value, output_record_row_number):
	pad_value = ' '
	map_json_row_number = 'row' + str(output_record_row_number)
	for field_value in map_json[map_json_row_number]:
		if field_output_column_start_value == field_value['outputColumnStart']:
			pad_value = field_value['outputPadCharacter']
	if pad_value is None:
		return ''
	else:
		return pad_value

def create_json_map_template():
	map_template = {
		"dataFile": "filename.csv",
		"numberOfHeaderRows": 1,
		"numberOfRowsPerOutputRecord": 2,
		"_notes": [
			{
				"csvFieldNumber": "Starts with 0, so first column in CSV is field 0."
			}
		],
		"row1": [
			{
				"csvFieldNumber": None,
				"outputColumnName": "Record ID",
				"outputColumnStart": 1,
				"outputColumnLength": 2,
				"outputDefaultValue": "OW",
				"outputJustify": "left",
				"outputPadCharacter": " "
			},
			{
				"csvFieldNumber": 0,
				"outputColumnName": "First Name",
				"outputColumnStart": 3,
				"outputColumnLength": 50,
				"outputDefaultValue": "",
				"outputJustify": "left",
				"outputPadCharacter": " "
			},
			{
				"csvFieldNumber": 2,
				"outputColumnName": "Last Name",
				"outputColumnStart": 53,
				"outputColumnLength": 50,
				"outputDefaultValue": "",
				"outputJustify": "left",
				"outputPadCharacter": " "
			}
		],
		"row2": [
			{
				"csvFieldNumber": 4,
				"outputColumnName": "DOB",
				"outputColumnStart": 1,
				"outputColumnLength": 10,
				"outputDefaultValue": "",
				"outputJustify": "left",
				"outputPadCharacter": " "
			},
			{
				"csvFieldNumber": 3,
				"outputColumnName": "Phone",
				"outputColumnStart": 11,
				"outputColumnLength": 14,
				"outputDefaultValue": "",
				"outputJustify": "left",
				"outputPadCharacter": " "
			}
		]
	}

	map_template_json_object = json.dumps(map_template, indent=4)

	# make sure map_file_template.json doesn't already exist
	map_file_template = Path('map_file_template.json')
	if map_file_template.exists():
		logging.error('cannot create map_file_template.json because it already exists. use that template to create your own json map file. make sure its name/path matches the name/path you put in the json_map_file_path variable at the top of this script')
	else:
		try:
			with open('map_file_template.json', 'w') as map_output:
				map_output.write(map_template_json_object)
				sys.exit('script ended due to error')
		except:
			logging.error('unable to create map_file_template.json')
			sys.exit('script ended due to error')

# check if json map file exists
json_map_file = Path(json_map_file_path)
map_json = ''
if json_map_file.exists():
	# read the map file, keep in map_json variable
	try:
		with open(json_map_file_path, 'r') as map_file:
			try:
				map_json = json.load(map_file)
			except json.decoder.JSONDecodeError as e:
				logging.error('error loading json from map file: {}'.format(e))
				sys.exit()
	except IOError as e:
		logging.error('error opening map file: {}'.format(e))
		sys.exit('script ended due to error')
	except:
		logging.error('error opening map file')
		sys.exit('script ended due to error')
else:
	create_json_map_template()

# this is to know how many rows to write to the file for each record
if 'numberOfRowsPerOutputRecord' not in map_json:
	logging.error('numberOfRowsPerOutputRecord field not found in JSON map file. assuming 1')
	number_of_rows_per_output_record = 1
else:
	if map_json['numberOfRowsPerOutputRecord'] <= 0:
		logging.error('invalid value for numberOfRowsPerOutputRecord field in JSON map file. needs to be 1 or more')
		sys.exit('script ended due to error')
	else:
		number_of_rows_per_output_record = map_json['numberOfRowsPerOutputRecord']
		#logging.info('number of row per output record: {}'.format(number_of_rows_per_output_record))

# check to make sure no column start values are duplicated in the map file
def duplicate_column_start_values_check(map_json):
	i = 0
	j = 1
	match_found = True

	while i < number_of_rows_per_output_record:
		column_start_value_list = []
		map_json_row_number = 'row' + str(j)
		for field_value in map_json[map_json_row_number]:
			column_start_value_list.append(field_value['outputColumnStart'])

		if len(column_start_value_list) == len(set(column_start_value_list)):
			match_found = False
		else:
			match_found = True
			return match_found
		i += 1
		j += 1
	return match_found

if duplicate_column_start_values_check(map_json) == True:
	logging.error('multiple columns have same outputColumnStart value in JSON map file. output column start values must be unique to each row of output')
	sys.exit('script ended due to error')

# open the file that contains the data that will need to be formatted
try:
	with open(map_json['dataFile'], 'r') as data_file:
		if 'numberOfHeaderRows' not in map_json:
			# assume 0 header rows
			data = csv.reader(data_file, delimiter=',', quotechar='"')
		else:
			if map_json['numberOfHeaderRows'] == 1:
				data = csv.reader(data_file, delimiter=',', quotechar='"')
				next(data)
			elif map_json['numberOfHeaderRows'] > 1:
				logging.error('script cannot currently handle more than 1 header row. please manually remove header rows from input file and try again')
				sys.exit('script ended due to error')
			else:
				data = csv.reader(data_file, delimiter=',', quotechar='"')

		# create the output file where the newly formatted data will be written
		try:
			with open(output_file_path, 'w') as output_file:
				# format the data and write it to the file
				for row_of_csv_data in data:
					# handle each row of the output record
					output_record_row_number = 1
					while output_record_row_number <= number_of_rows_per_output_record:
						field_write_order = get_field_write_order(map_json, output_record_row_number)
						if not field_write_order:
							logging.error('field write order indeterminable')
							sys.exit('script ended due to error')
						output_row = ''
						for output_column_start_value in field_write_order:
							column_to_grab_from_csv_data = get_field_value(output_column_start_value=output_column_start_value, field_to_get_value_of='csvFieldNumber', map_json=map_json, output_record_row_number=output_record_row_number)
							if column_to_grab_from_csv_data is None:
								# if no csvFieldNumber is given in the map file, write default value to output file
								field_length = get_field_length(map_json=map_json, field_output_column_start_value=output_column_start_value, output_record_row_number=output_record_row_number)
								if field_length == 0:
									logging.error('field length invalid')
									sys.exit('script ended due to error')
								default_value = get_default_value(map_json, output_column_start_value, output_record_row_number=output_record_row_number)
								justify_value = get_justify_value(map_json, output_column_start_value, output_record_row_number=output_record_row_number)
								pad_value = get_pad_value(map_json, output_column_start_value, output_record_row_number=output_record_row_number)
								#if default_value == '':
									#logging.warning('no csvFieldNumber listed, and no default value given for record with outputColumnStart value of: {}. field will be blank'.format(output_column_start_value))
								output_field = set_field(default_value, field_length, justify_value, pad_value)
								if output_field == '':
									logging.error('issue getting value that will be written to output file. issue in record with outputColumnStart value of: {}'.format(output_column_start_value))
									sys.exit('script ended due to error')
								output_row = output_row + output_field
							elif column_to_grab_from_csv_data == 'None' or column_to_grab_from_csv_data == '':
								# if no csvFieldNumber is given in the map file, write default value to output file
								field_length = get_field_length(map_json=map_json, field_output_column_start_value=output_column_start_value, output_record_row_number=output_record_row_number)
								if field_length == 0:
									logging.error('field length invalid')
									sys.exit('script ended due to error')
								default_value = get_default_value(map_json, output_column_start_value, output_record_row_number=output_record_row_number)
								justify_value = get_justify_value(map_json, output_column_start_value, output_record_row_number=output_record_row_number)
								pad_value = get_pad_value(map_json, output_column_start_value, output_record_row_number=output_record_row_number)
								#if default_value == '':
									#logging.warning('no csvFieldNumber listed, and no default value given for record with outputColumnStart value of: {}. field will be blank'.format(output_column_start_value))
								output_field = set_field(default_value, field_length, justify_value, pad_value)
								if output_field == '':
									logging.error('issue getting value that will be written to output file. issue related to record with outputColumnStart value of: {}'.format(output_column_start_value))
									sys.exit('script ended due to error')
								output_row = output_row + output_field
							else:
								# get correct csv column based on output_field
								# format csv field data to spec in map file
								field_length = get_field_length(map_json=map_json, field_output_column_start_value=output_column_start_value, output_record_row_number=output_record_row_number)
								if field_length == 0:
									logging.error('field length invalid')
									sys.exit('script ended due to error')
								justify_value = get_justify_value(map_json, output_column_start_value, output_record_row_number=output_record_row_number)
								pad_value = get_pad_value(map_json, output_column_start_value, output_record_row_number=output_record_row_number)
								output_field = set_field(row_of_csv_data[column_to_grab_from_csv_data], field_length, justify_value, pad_value)
								if output_field == '':
									logging.error('issue getting value that will be written to output file. issue related to record with outputColumnStart value of: {}'.format(output_column_start_value))
									sys.exit('script ended due to error')
								output_row = output_row + output_field
						output_file.write(output_row)
						output_file.write("\r\n")
						output_record_row_number = output_record_row_number + 1

		except IOError as e:
			logging.error('error opening output file: {}'.format(e))
			sys.exit('script ended due to error')
		
except IOError as e:
	logging.error("error opening data file: {}. please make sure CSV file exists".format(e))
	sys.exit('script ended due to error')

# Kreydt
