from src.traversers.astfulltraverser import AstFullTraverser
from src.utils import Utils
import ast
import copy
from pprint import pprint

class SSA_Traverser(AstFullTraverser):
    ''' The SSA_Traverser class traverses the AST tree.
    
    Definitions of a symbol N kill previous definitions of N.
    
    Phi nodes are implemented by adding a list to the if and case nodes. This
    was seen as simpler than modifying the AST. 
    '''
    def __init__(self):
        AstFullTraverser.__init__(self)
            
    def changed_dicts(self, newDict, oldDict):
        ''' The order of the parameters is important.
            Adds keys in newDict but in oldDict to oldDict with value 0. A 
            bit of a hack but makes it easier. '''
        newKeys = set(newDict.keys())
        oldKeys = set(oldDict.keys())
        intersection = newKeys.intersection(oldKeys)
        added = newKeys - oldKeys
        return set(o for o in intersection if oldDict[o] != newDict[o]) | added

    def run(self, root):
        self.u = Utils()
        self.d = {}
            # Keys are names, values are lists of a.values
            # where a is an assignment. 
        self.breaks = []
        self.continues = []
        self.built_in_classes = ["list", "set", "tuple", "float", "int"]  
        assert isinstance(root, ast.Module)
        self.visit(root)
        return root
        
    def process_blocks(self, block):
        ''' TODO: Handle infinite loops '''
        if block.ssa_mark:
            return
        if block.start_line_no == "Exit":
            return
        if not block.statements:
            return
        if block.start_line_no == 4:
            pass
        self.add_phi_nodes(block)
        for statement in block.statements:
            self.visit(statement)
        block.ssa_mark = True
        #block.
        exit_nos = [block.start_line_no for block in block.exit_blocks]
        pprint("Block starting at: " + str(block.start_line_no) + " to " + str(exit_nos))
        print(block.statements)
        dict_to_pass = self.d.copy()
        for an_exit in block.exit_blocks:
            self.process_blocks(an_exit)
            self.update_phis(an_exit, dict_to_pass)
            
    def add_phi_nodes(self, block):
        ''' Only add phi nodes with blocks with more than entry point. '''
        block.phi_nodes = {}
        block.statements[0].phi_nodes = []
        for ref_var in block.referenced_vars:
            if ref_var in self.d:  # Needed for before when var may not yet exist
                self.d[ref_var] += 1
            else:
                self.d[ref_var] = 1
            new_phi = Phi_Node(ref_var + str(self.d[ref_var]), set())
            block.phi_nodes[ref_var] = new_phi
            block.statements[0].phi_nodes.append(new_phi)
            
    def update_phis(self, block, predecessor_dict):
        for var, num in predecessor_dict.items():
            if var in block.referenced_vars:
                    # Don't add the var if it is itself!
                    if var + str(num) == block.phi_nodes[var].get_var():
                        continue
                    block.phi_nodes[var].update_targets(var + str(num))
                    print(block.start_line_no)
                    print(block.phi_nodes)
                    
    def visit(self,node):
        '''Compute the dictionary of assignments live at any point.'''
        method = getattr(self,'do_' + node.__class__.__name__)
        method(node)
    
    def buildPhiList(self, nameList, dictList, node, before):
        ''' name_list is the list of names to add phi nodes for.
            dict_list is the list of dicts to extract the instance of the variable
        '''
        phiList = []
        for name in nameList:
            if name in self.d:  # Needed for before when var may not yet exist
                self.d[name] += 1
            else:
                self.d[name] = 1
            targets = []
            for nameDict in dictList:
                # Check if the variables had not been previously
                #  initialised
                if name not in nameDict:
                    targets.append(Phi_Node.TARGET_NOT_DECLARED)
                else:
                    if (before):
                        targets.append(name + str(nameDict[name]))
                    else:
                        targets.append(name + str(nameDict[name]))
            newPhi = Phi_Node(name + str(self.d[name]), targets)
            phiList.append(newPhi)
        return phiList

    def do_ClassDef (self, node):
        ''' - We do not assign ssa numbers to class names as it's impossible
              to track order of execution.
            - We need the global variables. Do not start with an empty d
            TODO: Check for classes defined after. '''    
        old_d = self.d.copy()
        for z in node.body:
            self.visit(z)
        self.d = old_d

    def do_FunctionDef (self, node):
        ''' Variables defined in function should not exist outside. '''
        # Store d so we can eradicate local variables
        old_d = self.d.copy()
       # print(node.name)
       # self.visit(node.args)
        print("ssa-ing function: " + node.name)
        self.process_blocks(node.initial_block)
        self.d = old_d

    def do_Lambda(self, node):
        old_d = self.d
        self.visit(node.args)
        self.visit(node.body)
        self.d = old_d

    def do_Module (self, node):
        print("ssa-ing for Module code")
        self.process_blocks(node.initial_block)
        for z in node.body:
            self.visit(z)

    def do_Assign(self, node):
        self.visit(node.value)
        for target in node.targets:
            self.visit(target)
            
    def do_While(self, node):
        self.visit(node.test)
        
    def do_For(self, node):
        self.visit(node.target)
        self.visit(node.iter)
        
    def do_If(self,node):
        self.visit(node.test)

    def do_Assert(self, node):
        self.visit(node.test)
        if node.msg:
            self.visit(node.msg)
    
    def do_Name(self, node):
        ''' If the id is True or false then ignore. WHY ARE TRUE AND FALSE
            IDENTIFIED THE SAME WAY AS VARIABLES. GAH. '''
      #  print(node.id)
        # We don't SSA a global variable
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
        if not hasattr(node, 'originalId'):
            node.originalId = node.id
        # If the variable is being assigned a new value
        if isinstance(node.ctx, ast.Store):
            if node.originalId in self.d:
                self.d[node.originalId] += 1
            else:
                self.d[node.originalId] = 1
        # If it's x.y attribute and a ast.Load then for now we assume that it's already present
        ''' TODO: Check all possible attributes. '''
        if isinstance(node.ctx, ast.Load) and isinstance(node, ast.Attribute):
            return
                
       # pprint(self.d)
        try:
            node.id = node.originalId + str(self.d[node.originalId])
        except:
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