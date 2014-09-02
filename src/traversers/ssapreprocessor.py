from pprint import pprint
import ast

from src.traversers.astfulltraverser import AstFullTraverser
from src.typeclasses import *

class SSA_Pre_Processor(AstFullTraverser):
    '''
    Takes a CFG and for each block notes which variables are referenced.
    '''

    def __init__(self):
        self.current_block = None
        self.in_loop_test = False
        self.ssa_exempts = set()
        self.local_variables = None
        self.global_variables = None
        self.func_global_stores = None
        
    def run(self, source):
        self.visit(source)
        return source
        
    def visit(self, node):
        '''Visit a single node. Callers are responsible for visiting children.'''
        method = getattr(self, 'do_' + node.__class__.__name__)
        return method(node)
    
    def do_Module(self, node):
        self.global_variables = node.global_variables
        for dependent in node.import_dependents:
            self.ssa_exempts.add(dependent.get_as_name())
            
        self.process_blocks(node.initial_block)
        for z in node.body:
            self.visit(z)
            
    def do_ClassDef(self, node):
        
        self.ssa_exempts.add(node.name)
        old_globals = self.global_variables
        self.global_variables = node.global_variables
        old_ssa_exempts = self.ssa_exempts.copy()
        try:
            for z in node.bases:
                self.visit(z)
            for z in node.body:
                self.visit(z)
            for z in node.decorator_list:
                self.visit(z)
        finally:
            self.global_variables = old_globals
            self.ssa_exempts = old_ssa_exempts 
        
    
    def do_FunctionDef(self, node):
        node.global_var_edits = set()
        old_locals = self.local_variables
        node.local_variables = set()
        self.local_variables = node.local_variables
        old_func_store = self.func_global_stores
        node.func_global_stores = set()
        self.func_global_stores = node.func_global_stores
        
        self.ssa_exempts.add(node.name)
        old_ssa_exempts = self.ssa_exempts.copy()
        try:
            # Visit args to exempts them
            self.visit(node.args)
            self.process_blocks(node.initial_block)
        finally:
            self.local_variables -= node.global_var_edits
           # print("Local variables for " + node.name)
           # print(self.local_variables)
            self.local_variables = old_locals
            self.func_global_stores = old_func_store
            self.ssa_exempts = old_ssa_exempts 
            
    def do_arguments(self,node):
        for z in node.args:
            self.visit(z)
        for z in node.defaults:
            self.visit(z)
        if node.vararg:
            self.ssa_exempts.add(node.vararg)
        if node.kwarg:
            self.ssa_exempts.add(node.kwarg)
        
    def do_arg(self, node):
        self.ssa_exempts.add(node.arg)
        
    def do_While(self, node):
        self.visit(node.test)
        old_ilt = self.in_loop_test
        self.in_loop_test = True
        for z in node.body:
            self.visit(z)
        self.in_loop_test = old_ilt
        
    def do_For(self, node):
        self.visit(node.target)
        self.visit(node.iter)
        old_ilt = self.in_loop_test
        self.in_loop_test = True
        for z in node.body:
            self.visit(z)
        self.in_loop_test = old_ilt
        
    def do_If(self,node):
        self.visit(node.test)
        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
                
    def do_ListComp(self, node):
        ''' Must visit generators first as they assign. '''
        for z in node.generators:
            self.visit(z)
        self.visit(node.elt)
    
    def do_DictComp(self, node):
        for z in node.generators:
            self.visit(z)
        self.visit(node.key)
        self.visit(node.value)
        
    
    def do_GeneratorExp(self, node):
        for z in node.generators:
            self.visit(z)
        self.visit(node.elt)
            
    def do_comprehension(self, node):
        self.visit(node.iter)
        self.visit(node.target)
        for z in node.ifs:
            self.visit(z)
            
    def do_Global(self, node):
        assert isinstance(node.stc_context, ast.FunctionDef), "Global can't be outside of function"
        for identifier in node.names:
            assert isinstance(identifier, str)
            node.stc_context.global_var_edits.add(identifier)
        
    def do_Name(self, node):
        # Global variable
   #     if node.id == "bytes_":
   #         pass
        if isinstance(node.ctx, ast.Store) and (isinstance(node.stc_context, ast.Module) or isinstance(node.stc_context, ast.ClassDef)):
            self.ssa_exempts.add(node.id)
        if isinstance(node.stc_context, ast.Module):
            return
        if isinstance(node.stc_context, ast.ClassDef):
            return
        if node.id == "self" or node.id == "cls":
            return
        # Calculate local variables
        if isinstance(node.ctx, ast.Store) and isinstance(node.stc_context, ast.FunctionDef) and node.id not in self.ssa_exempts:
            self.local_variables.add(node.id)
            
        if node.id in self.ssa_exempts and isinstance(node.ctx, ast.Store):
            self.global_phis.add(node.id)      
            self.func_global_stores.add(node.id)     
            
        if node.id in BUILTIN_TYPE_DICT:
            return
        
        self.current_block.referenced_vars.add(node.id)
        
        
    def process_blocks(self, block):
        if block.ssa_prepro_mark:
            return
        if block.start_line_no == "Exit":
            return
        self.current_block = block
        block.global_phis = set()
        self.global_phis = block.global_phis
        pred_nos = [block.start_line_no for block in block.predecessors]
        exit_nos = [block.start_line_no for block in block.exit_blocks]
   #     pprint("Block starting at: " + str(block.start_line_no) + " to " + str(exit_nos))
   #     pprint("Block starting at: " + str(block.start_line_no) + " preceded by " + str(pred_nos))
   #     print(block.statements)
    #    if block.start_line_no == 4:
    #        pass
        for statement in block.statements:
            self.visit(statement)
            block.ssa_prepro_mark = True
   #     print("Variables referenced: " + str(block.referenced_vars))
        for an_exit in block.exit_blocks:
            self.process_blocks(an_exit)
      #  if block.next_block:
      #      self.process_blocks(block.next_block)