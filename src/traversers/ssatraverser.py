from src.traversers.astfulltraverser import AstFullTraverser
from src.typeclasses import *
from src.utils import Utils
import ast
import copy
from pprint import pprint

class SSA_Traverser(AstFullTraverser):
    ''' The SSA_Traverser class traverses the AST tree.
    
    Definitions of a symbol N kill previous definitions of N.
    
    Block processing is prioritised by ascending line numbers of the blocks.
    '''
    def __init__(self):
        AstFullTraverser.__init__(self)
        
    def run(self, root):
        self.global_variables = None
        self.global_var_edits = None
        self.local_variables = None
        self.function_ssa_tracker = {}
        self.func_global_stores = None
       # self.block_tracker = {}
        self.in_function = False
            # Keys are names, values are lists of a.values
            # where a is an assignment. 
        self.breaks = []
        self.continues = []
        self.blocks_to_process = []  # Block queue
        assert isinstance(root, ast.Module)
        self.visit(root)
        return root
    
    def process_block_list(self):
        while self.blocks_to_process:
            block, dict_to_pass = self.blocks_to_process.pop(0)
            self.process_block(block)
            if dict_to_pass:
                self.update_phis(block, dict_to_pass)
        
    def process_block(self, block):
        ''' TODO: Handle infinite loops '''
        if not self.in_function:
            return
        if block.ssa_mark:
            return
        block.ssa_mark = True
        if block.start_line_no == "Exit":
            return
        if not block.statements:
            return
        
        if block.start_line_no == 21:
            pass
        
        self.current_block = block
        # Update all but those created by phis
        self.current_block.tracker.update({k:v for k,v in self.function_ssa_tracker.items() if k not in self.current_block.tracker and k not in self.func_global_stores})
        for statement in block.statements:
            self.visit(statement)
        dict_to_pass = self.current_block.tracker.copy()
        
     #   print("Block " + str(block.start_line_no) + " to")
     #   print(block.exit_blocks)        
     #   print(block.statements)
        
        for an_exit in block.exit_blocks:
            self.add_to_list((an_exit, dict_to_pass))
            
    def add_to_list(self, item):
        if item[0].start_line_no == "Exit":
            return
        if not self.blocks_to_process:
            self.blocks_to_process.append(item)
            return
        insert_num = item[0].start_line_no
        i = 0
        test_num = self.blocks_to_process[i][0].start_line_no
        while insert_num > test_num and i < len(self.blocks_to_process) - 1:
            i += 1
            test_num = self.blocks_to_process[i][0].start_line_no
        self.blocks_to_process.insert(i, item)
        
    def add_all_phi_nodes(self, block, local_variables):
        if block.start_line_no == "Exit":
            return
        if not block.statements:
            return
        if block.has_phi_nodes:
            return
        global_phis = self.add_phi_nodes(block, local_variables)
        for an_exit in block.exit_blocks:
            self.add_all_phi_nodes(an_exit, local_variables | global_phis)
            
    def add_phi_nodes(self, block, local_variables):
        ''' Only add phi nodes with blocks with more than entry point. '''
        block.phi_nodes = {}
        block.tracker = {}
        block.statements[0].phi_nodes = []
        global_phis = block.global_phis - self.global_var_edits
        for ref_var in local_variables - global_phis:
            new_phi = self.create_new_phi_node(ref_var, block)
            block.phi_nodes[ref_var] = new_phi
            block.statements[0].phi_nodes.append(new_phi)
            print("Phi created for block " + str(block.start_line_no))
            print(block.phi_nodes)
        for ref_var in global_phis:
            new_phi = self.create_new_phi_node(ref_var, block)
            block.phi_nodes[ref_var] = new_phi
            block.statements[0].phi_nodes.append(new_phi)
            # Need to add un-labelled global
            new_phi.update_targets(ref_var)
            print("Phi created for block " + str(block.start_line_no))
            print(block.phi_nodes)
        block.has_phi_nodes = True
        return global_phis
            
    def update_phis(self, block, predecessor_dict):
        if block.start_line_no == "Exit":
            return
        for var, num in predecessor_dict.items():
                    # If it doesn't exist yet - can happen when transforming global to local -
                    # add it
                    if var not in block.phi_nodes:
                        new_phi = self.create_new_phi_node(var, block)
                        block.phi_nodes[var] = new_phi

                    # Don't add the var if it is itself!
                    if var + str(num) == block.phi_nodes[var].get_var():
                        continue
                    block.phi_nodes[var].update_targets(var + str(num))
                    print("Phis for: " + str(block.start_line_no))
                    print(block.phi_nodes)
                    
    def create_new_phi_node(self, var, block):
        if var in self.function_ssa_tracker:  # Needed for before when var may not yet exist
            self.function_ssa_tracker[var] += 1
        else:
            self.function_ssa_tracker[var] = 1
        block.tracker[var] = self.function_ssa_tracker[var]
        new_phi = Phi_Node(var + str(self.function_ssa_tracker[var]), set())
        new_phi.lineno = block.statements[0].lineno
        return new_phi
                    
    def visit(self, node):
        '''Compute the dictionary of assignments live at any point.'''
        method = getattr(self,'do_' + node.__class__.__name__)
        return method(node)
        
    def do_Name(self, node):
        # We don't SSA a global variable
        if node.id == "tag":
            pass
        if isinstance(node.stc_context, ast.Module) or isinstance(node.stc_context, ast.ClassDef):
            return
        if node.id == "self" or node.id == "cls":
            return
        # A load will refer to the global namespace if its not a local
        if node.id in self.global_variables and isinstance(node.ctx, ast.Load):
            return
        # In no way will we rename a node with combination
        if node.id in self.global_variables and node.id in self.global_var_edits:
            return
        if node.id in self.func_global_stores and node.id not in self.current_block.phi_nodes:
            return
        # Becomes local variable in this context
        if node.id in self.global_variables and node.id not in self.global_var_edits and isinstance(node.ctx, ast.Store):
            self.global_variables.remove(node.id)
        if not hasattr(node, 'originalId'):
            node.originalId = node.id
        # If the variable is being assigned a new value
        if isinstance(node.ctx, ast.Store):
            if node.originalId in self.function_ssa_tracker:
                self.function_ssa_tracker[node.originalId] += 1
            else:
                self.function_ssa_tracker[node.originalId] = 1
            self.current_block.tracker[node.originalId] = self.function_ssa_tracker[node.originalId]
        # If it's x.y attribute and a ast.Load then for now we assume that it's already present
        ''' TODO: Check all possible attributes. '''
        if isinstance(node.ctx, ast.Load) and isinstance(node, ast.Attribute):
            return
                
       # pprint(self.function_ssa_tracker)
        try:
            node.id = node.originalId + str(self.current_block.tracker[node.originalId])
        except:
            pass

    def do_ClassDef (self, node):
        ''' - We do not assign ssa numbers to class names as it's impossible
              to track order of execution.
            - We need the global variables. Do not start with an empty d '''    
        self.global_variables = node.global_variables | node.stc_context.global_variables
        old_tracker = self.function_ssa_tracker.copy()
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.function_ssa_tracker = old_tracker
            self.global_variables = node.stc_context.global_variables

    def do_FunctionDef (self, node):
        ''' Variables defined in function should not exist outside. '''
        # Store d so we can eradicate local variables
    #    old_args = self.fun_args.copy()
        old_globals = self.global_variables.copy()
        old_locals = self.local_variables
        self.global_var_edits = node.global_var_edits
        old_tracker = self.function_ssa_tracker.copy()
        old_in_function = self.in_function
        old_func_stores = self.func_global_stores
        self.func_global_stores = node.func_global_stores
        
        
        if node.name == "__init__":
            pass
    #    args = self.visit(node.args)
    #    self.fun_args += args
       # print(node.name)
       # self.visit(node.args)
    #    print("ssa-ing function: " + node.name)
        try:
            self.in_function = True
            self.local_variables = node.local_variables
            self.add_all_phi_nodes(node.initial_block, node.local_variables)
            self.blocks_to_process.append((node.initial_block, None))
            self.old_func_stores = old_func_stores
            self.process_block_list()
        finally:
            self.in_function = old_in_function
            self.function_ssa_tracker = old_tracker
            self.local_variables = old_locals
            self.global_variables = old_globals
     #   self.fun_args = old_args
        
    def do_arguments(self, node):
        args = []
        for z in node.args:
            args.extend(self.visit(z))
        return args
            
    def do_arg(self, node):
        return [node.arg]

    def do_Lambda(self, node):
        old_tracker = self.function_ssa_tracker.copy()
        self.visit(node.args)
        self.visit(node.body)
        self.function_ssa_tracker = old_tracker

    def do_Module (self, node):
   #     print("ssa-ing for Module code")
     #   self.blocks_to_process.append(node.initial_block)
     #   self.process_block_list()
        self.global_variables = node.global_variables
        for z in node.body:
            self.visit(z)

    def do_Assign(self, node):
        self.visit(node.value)
        for target in node.targets:
            self.visit(target)
            
    def do_While(self, node):
        ''' body and else are in their own blocks. '''
        self.visit(node.test)
        
    def do_For(self, node):
        ''' body and else are in their own blocks. '''
        self.visit(node.target)
        self.visit(node.iter)
        
    def do_If(self,node):
        ''' body and else are in their own blocks. '''
        self.visit(node.test)

    def do_Assert(self, node):
        self.visit(node.test)
        if node.msg:
            self.visit(node.msg)
            
    def do_Try(self, node):
        ''' body/finally/excepts are in their own blocks. '''
        pass
    
    def do_ExceptHandler(self,node):
        # We do NOT want to visit the body. These are in blocks.
        if node.type:
            self.visit(node.type)
        if node.name and isinstance(node.name,ast.Name):
            self.visit(node.name)
            
    def do_Call(self, node):
        self.visit(node.func)
        for z in node.args:
            self.visit(z)
        for z in node.keywords:
            self.visit(z)
        if getattr(node,'starargs',None):
            self.visit(node.starargs)
        if getattr(node,'kwargs',None):
            self.visit(node.kwargs)
            
    def do_ListComp(self, node):
        ''' Must visit generators first as they assign. '''
        for z in node.generators:
            self.visit(z)
        self.visit(node.elt)
    
    def do_DictComp(self, node):
        ''' Must visit generators first as they assign. '''
        for z in node.generators:
            self.visit(z)
        self.visit(node.key)
        self.visit(node.value)
    
    def do_GeneratorExp(self, node):
        ''' Must visit generators first as they assign. '''
        for z in node.generators:
            self.visit(z)
        self.visit(node.elt)
            
    def do_comprehension(self, node):
        ''' Must visit iters first as they assign. '''
        self.visit(node.iter)
        self.visit(node.target)
        for z in node.ifs:
            self.visit(z)
            
    def do_Pass(self, node):
        pass
        
class Phi_Node():
    ''' Class used to represent a phi node in the SSA. Allows us to represent
    a variable which is assigned to in more than one branch.
    
    The only real difference is that its values is a list of variables from
    which it can adopt its type from. '''
    
    TARGET_NOT_DECLARED = 0
    
    def __init__(self, var, targets):
        self.var = var
        self.targets = targets
        self.lineno = -1
        
    def _str__(self):
        self.__repr__()
        
    def __repr__(self):
        return self.var + ": " + str(self.targets)
    
    def get_var(self):
        return self.var
    
    def get_targets(self):
        return self.targets
        
    def update_targets(self, new_target):
        self.targets.add(new_target)