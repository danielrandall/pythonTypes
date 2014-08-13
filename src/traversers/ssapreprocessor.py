from pprint import pprint
import ast

from src.traversers.astfulltraverser import AstFullTraverser

class SSA_Pre_Processor(AstFullTraverser):
    '''
    Takes a CFG and for each block notes which variables are referenced.
    '''

    def __init__(self):
        self.built_in_classes = ["list", "set", "tuple", "float", "int"]  
        self.current_block = None
        self.in_loop_test = False
        
    def run(self, source):
        self.visit(source)
        return source
        
    def visit(self, node):
        '''Visit a single node. Callers are responsible for visiting children.'''
        method = getattr(self, 'do_' + node.__class__.__name__)
        return method(node)
    
    def do_Module(self, node):
        print("CFG for Module code")
        self.process_blocks(node.initial_block)
        for z in node.body:
            self.visit(z)
    
    def do_FunctionDef(self, node):
        print("CFG for " + node.name)
        print(node.lineno)
        self.process_blocks(node.initial_block)
        
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
        
    def do_Name(self, node):
        if isinstance(node.stc_context, ast.Module):
            return
        if node.id == "True" or node.id == "False":
            return
        if node.id == "None":
            return
        if node.id == "self":
            return
        if node.id in self.built_in_classes:
            return
        if node.id in self.built_in_classes:
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
        pprint("Block starting at: " + str(block.start_line_no) + " to " + str(exit_nos))
        pprint("Block starting at: " + str(block.start_line_no) + " preceded by " + str(pred_nos))
        print(block.statements)
        if block.start_line_no == 4:
            pass
        for statement in block.statements:
            self.visit(statement)
            block.ssa_prepro_mark = True
        print("Variables referenced: " + str(block.referenced_vars))
        for an_exit in block.exit_blocks:
            self.process_blocks(an_exit)
        if block.next_block:
            self.process_blocks(block.next_block)