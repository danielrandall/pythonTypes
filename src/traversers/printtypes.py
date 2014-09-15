from src.traversers.astfulltraverser import AstFullTraverser
from src.typeclasses import BUILTIN_TYPE_DICT

class Print_Types(AstFullTraverser):
    ''' Prints all variables in scope minus built-ins and variables from
        above scope. '''
    
    def run(self, file_tree):
        file_list = self.file_tree_to_list(file_tree)
        for file in file_list:
            self.print_file(file)
            
    def file_tree_to_list(self, file_tree):
        file_lists = []
        name_dicts = file_tree.values()
        for n_dict in name_dicts:
            file_lists.extend(n_dict.values())
        return file_lists
    
    def print_file(self, file):   
        ''' Runs the type_checking on an individual file. '''
        root = file.get_source()     
        self.module_name = file.get_path() + "/" + file.get_name()
        self.visit(root)
    
    def visit(self, node):
        '''Visit a single node.  Callers are responsible for visiting children.'''
        method = getattr(self,'do_' + node.__class__.__name__)
        return method(node)
    
    def print_all(self, to_print):
        for name, type_set in to_print.items():
            print(name + ": " + str(type_set))
        print()
    
    def do_Module(self, node):
        print("Types in module: " + self.module_name)
        to_print = {k:v for k,v in node.variableTypes.items() if k not in BUILTIN_TYPE_DICT}
        self.print_all(to_print)
        # Visit rest
        for z in node.body:
            self.visit(z)
    
    def do_ClassDef(self, node):
        print("Types in class: " + node.name)
        to_print = {k:v for k,v in node.variableTypes.items() if k not in node.stc_context.variableTypes}
        self.print_all(to_print)
        # Visit rest
        for z in node.body:
            self.visit(z)
        
    def do_FunctionDef(self, node):
        print("Types in function: " + node.name)
        print("Return types: " + str(node.return_types))
        to_print = {k:v for k,v in node.variableTypes.items() if k not in node.stc_context.variableTypes and k != "self"}
        self.print_all(to_print)
