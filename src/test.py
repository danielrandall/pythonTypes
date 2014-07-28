'''
Created on 17 May 2014

@author: dr1810
'''
import src.stcglobals as stcglobals
import src.statictypechecking as stc
import src.extractpysfromdirectory as file_extractor
from src.traversers.ssatraverser import SSA_Traverser

import ast
from pprint import pprint


# Open source Python 3 projects to test on: https://pypi.python.org/pypi?%3Aaction=browse&c=533&show=all

'''Return the entire contents of the file whose name is given.
   Almost most entirely copied from stc. '''
def get_source(fn):
        try:
            fn = stcglobals.toUnicode(fn)
            # g.trace(g.os_path_exists(fn),fn)
            f = open(fn,'r')
            s = f.read()
            f.close()
            return s
        except IOError:
            return ''

def parseFile(file):
    s = get_source(file)
    return ast.parse(s, filename = file, mode = 'exec')

def printSymbolTable(source):
    pprint(source.stc_symbol_table.cx)
    pprint(source.stc_symbol_table.attrs_d)
    pprint(source.stc_symbol_table.defined)
    pprint(source.stc_symbol_table.defined_attrs)
    pprint(source.stc_symbol_table.ssa_d)

if __name__ == '__main__':
  #  top_level = "/homes/dr1810/4thYear/individualProject/pythonTypes/"
    top_level = "/homes/dr1810/4thYear/individualProject/pythonTypes/testFiles/realFiles/a"
    file_tree = file_extractor.get_pys(top_level)
    print(file_tree)
   # fn = "/homes/dr1810/4thYear/individualProject/pythonTypes/testFiles/test.py"
  #  fn = "/homes/dr1810/4thYear/individualProject/pythonTypes/src/statictypechecking.py"
  
    ti = stc.TypeInferrer()
    ti.run(file_tree)