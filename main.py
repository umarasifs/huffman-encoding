from collections import Counter
import click
import sys
import heapq
from functools import total_ordering
from bitarray import bitarray
import re

@total_ordering
class Node:
    def __init__(self,freq=0,char=None,left=None,right=None):
        self.freq=freq
        self.char=char
        self.left=left
        self.right=right

    def __lt__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.freq < other.freq

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.freq == other.freq

def get_frequency(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        contents = file.read()
        return sorted([Node(num,char) for char,num in Counter(contents).items()]),Counter(contents)

def generate_tree(frequency):
    if len(frequency) == 1:
        return Node(frequency[0].freq,None,left=frequency[0])
    while len(frequency) > 1:
        bottom1, bottom2 = heapq.heappop(frequency),heapq.heappop(frequency)
        heapq.heappush(frequency,Node(bottom1.freq+bottom2.freq,None,left=bottom1,right=bottom2))
    return frequency[0]
    
def generate_table(tree):
    table = {}
    def dfs(root,prefix):
        if root is None:
            return
        if root.char is not None:
            table[root.char] = prefix
        else:
            dfs(root.left,prefix+'0')
            dfs(root.right,prefix+'1')
    dfs(tree,'')
    return table

def generate_header(table,size):
    header=''
    for char in table:
        freq = table[char]
        if char == "'":
            char = "\\'"
        header += f"'{char}':{freq},\n"
    header+='HEADER\n'
    header+=str(size)
    header+='\nSIZE\n'
    return header

def write_output(input, output, table,frequency):
    size = 0
    for char, count in frequency.items():
        size += count * len(table[char])
    try:
        
        with open(output, 'wb') as output_file:
            output_file.write(generate_header(table,size).encode())
        with open(output, 'ab') as output_file:
            size = 0
            with open(input, 'r', encoding='utf-8') as input_file:
                chunk = input_file.read()

                bit_str = ''
                for char in chunk:
                    bit_str+=table[char]
                bits = bitarray(bit_str)
                packed_bytes = bits.tobytes()
                output_file.write(packed_bytes)
                size += len(bit_str)
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

def find_header_and_size(filename):
    with open(filename,'rb') as file:
        text = file.read()

        header = text.find('HEADER'.encode('utf-8'))
        end = text.find('\nSIZE\n'.encode('utf-8'))
        size = int(text[header+7:end].decode())
        return header,end+6,size

def string_parse(data):
    data = data[1:]
    if len(data) > 3 and data[:3] == "\\''":
        return ("'",data[3:].strip())
    idx = data.find("'")
    value = data[:idx]
    return (value, data[idx+1:].strip())

def number_parse(data):
    number_regex = r'^\d+'
    match = re.search(number_regex,data)
    raw_value = match.group(0)
    
    return (raw_value, data[len(raw_value):].strip())

def parse(data):
    table = {}
    while data:
        string, data = string_parse(data)
        data=data[1:]
        number,data = number_parse(data)
        data=data[1:].strip()
        table[number]=string
    return table

def build_table(filename, header_pos):

    with open(filename,'rb') as file:
        text = file.read(header_pos)
        return parse(text.decode('utf-8'))

def write_decoded(compressed,output,header_pos,size,table):
    with open(compressed,'rb') as input_file:
        with open(output,'a',encoding='utf-8') as out:
            input_file.seek(header_pos)
            data = input_file.read()
            bit_array = bitarray()
            bit_array.frombytes(data)
            curr_prefix = ''
            for i in range(size):
                bit = bit_array[i]
                if bit:
                    curr_prefix += '1'
                else:
                    curr_prefix += '0'
                if curr_prefix in table:
                    out.write(table[curr_prefix])
                    curr_prefix = ''
            


@click.command()
@click.argument("filename", nargs=1, type=click.Path(exists=True))
@click.argument("output", nargs=1)
def encode(filename,output):
    try:
        frequency_nodes, frequency = get_frequency(filename)
        tree = generate_tree(frequency_nodes)
        table = generate_table(tree)
        write_output(filename,output,table, frequency)

    except Exception as e:
        print(f"Error opening file: {e}")
        sys.exit(1)
    sys.exit(0)

@click.command()
@click.argument("filename", nargs=1, type=click.Path(exists=True))
@click.argument("output", nargs=1)
def decode(filename,output):
    try:
        header_pos, compress_start, size = find_header_and_size(filename)
        table = build_table(filename,header_pos)
        write_decoded(filename,output,compress_start,size,table)
    except Exception as e:
        print(f"Error opening file: {e}")
        sys.exit(1)
    sys.exit(0)