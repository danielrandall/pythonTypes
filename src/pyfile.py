import ast

from src.preprocessing import Preprocessor
from src.traversers.ssatraverser import SSA_Traverser
from src.utils import Utils
import src.stcglobals as stcglobals

class PyFile(object):

    def __init__(self, name, relative_path, root):
        ast_source = PyFile.parse_file(root)
        utils = Utils()
        print(utils.dump_ast(ast_source))
        pp_source = PyFile.apply_preprocessing(root, ast_source)
        ssa_source = PyFile.apply_ssa(pp_source)
        
        self.source = ssa_source
        self.name = name
        self.path = relative_path
        self.typed = False
        self.global_vars = None
        
    def get_source(self):
        return self.source
    
    def get_name(self):
        return self.name
    
    def get_path(self):
        return self.name
    
    def has_been_typed(self):
        return self.typed
    
    def set_global_vars(self, global_vars):
        self.global_vars = global_vars
        
    def get_global_vars(self):
        return self.global_vars
    
    @staticmethod
    def extract_source(fn):
        '''Return the entire contents of the file whose name is given. '''
        fn = stcglobals.toUnicode(fn)
        f = open(fn,'r')
        s = f.read()
        f.close()
        return s

    @staticmethod
    def parse_file(file):
        s = PyFile.extract_source(file)
        return ast.parse(s, filename = file, mode = 'exec')
    
    @staticmethod
    def apply_ssa(source):
        ssa = SSA_Traverser()
        return ssa.run(source)
    
    @staticmethod
    def apply_preprocessing(root, source):
        pp = Preprocessor()
        return pp.run(root, source)