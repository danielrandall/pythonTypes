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
        
    def run(self, source):
        self.visit(source)
        return source
        
    def visit(self, node):
        '''Visit a single node. Callers are responsible for visiting children.'''
        method = getattr(self, 'do_' + node.__class__.__name__)
        return method(node)
    
    def do_Module(self, node):
        for dependent in node.import_dependents:
            self.ssa_exempts.add(dependent.get_as_name())
            
        self.process_blocks(node.initial_block)
        for z in node.body:
            self.visit(z)
        pass
            
    def do_ClassDef(self, node):
        
        self.ssa_exempts.add(node.name)
        old_ssa_exempts = self.ssa_exempts.copy()
        try:
            for z in node.bases:
                self.visit(z)
            for z in node.body:
                self.visit(z)
            for z in node.decorator_list:
                self.visit(z)
        finally:
            self.ssa_exempts = old_ssa_exempts 
        
    
    def do_FunctionDef(self, node):
        node.global_var_edits = set()
        
        self.ssa_exempts.add(node.name)
        old_ssa_exempts = self.ssa_exempts.copy()
        try:
            # Visit args to exempts them
            self.visit(node.args)
            self.process_blocks(node.initial_block)
        finally:
            self.ssa_exempts = old_ssa_exempts 
            
    def do_arguments(self,node):
        for z in node.args:
            self.visit(z)
        for z in node.defaults:
            self.visit(z)
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
        if self.in_loop_test:
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
        assert isinstance(node.stc_context, ast.FunctionDef), "Global can be outside of function"
        for identifier in node.names:
            assert isinstance(identifier, str)
            node.stc_context.global_var_edits.add(identifier)
        
    def do_Name(self, node):
        # Global variable
        
        if isinstance(node.ctx, ast.Store) and (isinstance(node.stc_context, ast.Module) or isinstance(node.stc_context, ast.ClassDef)):
            self.ssa_exempts.add(node.id)
        if isinstance(node.stc_context, ast.Module):
            return
        if isinstance(node.stc_context, ast.ClassDef):
            return
        if node.id == "_":
            return
        if node.id == "True" or node.id == "False":
            return
        if node.id == "None":
            return
        if node.id == "self":
            return
        if node.id in BUILTIN_TYPE_DICT:
            return
        if node.id in self.ssa_exempts:
            return
        self.current_block.referenced_vars.add(node.id)
        
        
    def process_blocks(self, block):
        if block.ssa_prepro_mark:
            return
        if block.start_line_no == "Exit":
            return
        self.current_block = block
        pred_nos = [block.start_line_no for block in block.predecessors]
        exit_nos = [block.start_line_no for block in block.exit_blocks]
   #     pprint("Block starting at: " + str(block.start_line_no) + " to " + str(exit_nos))
   #     pprint("Block starting at: " + str(block.start_line_no) + " preceded by " + str(pred_nos))
   #     print(block.statements)
        if block.start_line_no == 4:
            pass
        for statement in block.statements:
            self.visit(statement)
            block.ssa_prepro_mark = True
   #     print("Variables referenced: " + str(block.referenced_vars))
        for an_exit in block.exit_blocks:
            self.process_blocks(an_exit)
      #  if block.next_block:
      #      self.process_blocks(block.next_block)