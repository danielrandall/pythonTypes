'''
Created on 17 May 2014

@author: dr1810
'''
import src.stcglobals as stcglobals
import src.statictypechecking as stc
import ast
from pprint import pprint


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
    fn = "/homes/dr1810/4thYear/individualProject/pythonTypes/testFiles/test.py"
    sourceAst = parseFile(fn)
    
    utils = stc.Utils()
   # print(utils.dump_ast(sourceAst, True, None, False, 2))
    
    p1 = stc.P1()
    p1(fn, sourceAst)
   # printSymbolTable(sourceAst)
   # print(utils.dump_ast(sourceAst))

    ssa = stc.SSA_Traverser()
    ssa(sourceAst)
 #   printSymbolTable(sourceAst)
    print(utils.dump_ast(sourceAst, True))
    
  #  print(utils.dump_ivars_dict(sourceAst))
  
    ti = stc.TypeInferrer()
    ti(sourceAst)