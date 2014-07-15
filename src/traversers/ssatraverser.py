from src.traversers.astfulltraverser import AstFullTraverser
from src.utils import Utils
import ast
from pprint import pprint

class SSA_Traverser(AstFullTraverser):
    ''' The SSA_Traverser class traverses the AST tree,
    computing reaching sets for ast.Name and other nodes.
    
    Definitions of a symbol N kill previous definitions of N. 'if' and
    'while' statement add entries to reaching sets.
    
    Phi nodes are implemented by adding a list to the if and case nodes. This
    was seen as simpler than modifying the AST. 
    '''
    def __init__(self):
        AstFullTraverser.__init__(self)
        
    def __call__(self,node):
        return self.run(node)

    def dump_dict (self,aDict,tag=''):
        g.trace(tag)
        for key in sorted(aDict.keys()):
            print('  %s = [%s]' % (key,self.u.format(aDict.get(key,[]))))

    # Similar to p1.lookup, but node can be any node.
    def lookup(self,node,key):
        '''Return the symbol table for key, starting the search at node cx.'''
        trace = False and not g.app.runningAllUnitTests
        if isinstance(node,(ast.Module,ast.ClassDef,ast.FunctionDef)):
            cx = node
        else:
            cx = node.stc_context
        while cx:
            # d = getattr(cx,'stc_symbol_table',{})
            d = cx.stc_symbol_table.d
            if key in d.keys():
                if trace: g.trace('found',key,self.u.format(cx))
                return d
            else:
                cx = cx.stc_context
        g.trace(' not found',key,self.u.format(node))
        return None
        
        # for d in (self.builtins_d,self.special_methods_d):
            # if key in d.keys():
                # return d
        # else:
            # g.trace(node,key)
            # return None

    def merge_dicts(self,aDict,aDict2):
        '''Merge the lists in aDict2 into aDict.'''
        for key in aDict2.keys():
            aList = aDict.get(key,[])
            aList2 = aDict2.get(key)
            for val in aList2:
                if val not in aList:
                    aList.append(val)
            aDict[key] = aList
            
    def changed_dicts(self, newDict, oldDict):
        ''' The order of the parameters is important.
            Adds keys in newDict but in oldDict to oldDict with value 0. A 
            bit of a hack but makes it easier. '''
        newKeys = set(newDict.keys())
        oldKeys = set(oldDict.keys())
        intersection = newKeys.intersection(oldKeys)
        added = newKeys - oldKeys
        return set(o for o in intersection if oldDict[o] != newDict[o]) | added

    def run(self,root):
        self.u = Utils()
        self.d = {}
            # Keys are names, values are lists of a.values
            # where a is an assignment. 
        self.built_in_classes = ["list", "set", "tuple", "float", "int"]  
        self.breaks = []
        self.continues = []
        assert isinstance(root,ast.Module)
        self.visit(root)
        
    def add_intial_module_names(self):
        ''' Add names which exist from the start '''
        self.d["__name__"] = 1
        self.d["__file__"] = 1
        
    def add_intial_class_names(self):
        ''' Add names which exist from the start '''
        self.d["__str__"] = 1
        self.d["__repr__"] = 1    

    def visit(self,node):
        '''Compute the dictionary of assignments live at any point.'''
        method = getattr(self,'do_' + node.__class__.__name__)
        method(node)

    def do_ExceptHandler(self,node):
        for z in node.body:
            self.visit(z)
            
    def do_Call(self,node):
        #  self.visit(node.func)    Not necessary to look here...
        for z in node.args:
            self.visit(z)
        for z in node.keywords:
            self.visit(z)
        if getattr(node,'starargs',None):
            self.visit(node.starargs)
        if getattr(node,'kwargs',None):
            self.visit(node.kwargs)
        self.visit(node.func)

    def do_For(self,node):
        ''' if loop, for now, is the same as the while loop. '''
        self.visit(node.target)
        self.visit(node.iter)
        self.loop_helper(node)

    def do_While (self,node):
        ''' - The else branch is only executed if the test evaluates to false,
              not when you break or an exception is raised.
            - Should not have to care about returns as the values of variables
              will be lost
            TODO: Try to optimise. '''
        self.visit(node.test)
        self.loop_helper(node)
        
    def loop_helper(self, node):
        node.beforePhis = []
        node.afterPhis = []
        
        beforeD = self.d.copy()
        # Keep track of breaks and continues
        old_breaks = self.breaks.copy()
        old_continues = self.continues.copy()
        
        for z in node.body:
            self.visit(z)
        pprint(self.breaks)
        # Check for variable values after loop
        ifD = self.d.copy()
        ifChanged = self.changed_dicts(ifD, beforeD)
        # Create before phis for all variables changed in the loop
        self.d = beforeD.copy()       # Reset the dict so new var has correct #
         # All of #'s we want will be behind by 1
        for key in ifD.keys():
            ifD[key] += 1    
        for cont in self.continues:
            for key in cont.keys():
                cont[key] += 1          
        self.editBeforePhiList(ifChanged, [beforeD, ifD] + self.continues, node)
       
        self.breaks = []
        self.continues = []
        for z in node.body:
            self.visit(z)      # Vist nodes again so future vars have correct #
        ifD = self.d.copy()
        
        if (node.orelse):
            for z in node.orelse:
                self.visit(z)
            elseD = self.d.copy()
            elseChanged = self.changed_dicts(elseD, ifD)
            elseIfChanged = set(ifChanged) & set(elseChanged)
            self.editAfterPhiList(elseIfChanged, [elseD, ifD] + self.breaks, node)
            changedOnceElse = set(elseChanged) - elseIfChanged
            self.editAfterPhiList(changedOnceElse, [elseD, beforeD], node)
            ifChangedOnly = set(ifChanged) - elseIfChanged
        else:
            ifChangedOnly = ifChanged
        self.editAfterPhiList(ifChangedOnly, [ifD, beforeD] + self.breaks, node)
        
        # Restore the breaks and continues for outer loops
        self.breaks = old_breaks
        self.continues = old_continues
        
        print("Before")
        for phi in node.beforePhis:
            pprint(phi.var)
            pprint(phi.targets)
        print("After")
        for phi in node.afterPhis:
            pprint(phi.var)
            pprint(phi.targets)
    
    def increment_dict(self, dict):
        for key in dict.keys():
            dict[key] += 1   
            
    def do_Break(self, node):
        ''' Values present at a break can be present after a loop.
            Needs to be included in after-phis. '''
        self.breaks.append(self.d.copy())
    
    def do_Continue(self, node):
        ''' Values present at a break can be present at the beggining of loop
            iterations. Needs to be included in before-phis. '''
        self.continues.append(self.d.copy())

    def do_If (self,node):
        ''' Checks whether if and else branches use the same name. If they do
            then we must create a phi node which uses both.
            TODO: Optimise this function. 
            TODO: Functions defined inside of an if '''
        node.afterPhis = [] # All ifs have an empty list.
        
        self.visit(node.test)
        beforeD = self.d.copy()
        for z in node.body:
            self.visit(z)
        ifD = self.d.copy()
        ifChanged = self.changed_dicts(ifD, beforeD)
        
        if node.orelse:
            for z in node.orelse:
                self.visit(z)
            elseD = self.d.copy()
            elseChanged = self.changed_dicts(elseD, ifD)
            # vars changed in both branches
            elseIfChanged = set(ifChanged) & set(elseChanged)
            self.editAfterPhiList(elseIfChanged, [elseD, ifD], node)
            changedOnceElse = set(elseChanged) - elseIfChanged
            self.editAfterPhiList(changedOnceElse, [elseD, beforeD], node)
            ifChangedOnly = set(ifChanged) - elseIfChanged
        else:
            ifChangedOnly = ifChanged
        self.editAfterPhiList(ifChangedOnly, [ifD, beforeD], node)
        for phi in node.afterPhis:
            pprint(phi.var)
            pprint(phi.targets)
            
    def editAfterPhiList(self, nameList, dictList, node):
        phiList = self.buildPhiList(nameList, dictList, node, False)
        node.afterPhis.extend(phiList)
    
    def editBeforePhiList(self, nameList, dictList, node):
        phiList = self.buildPhiList(nameList, dictList, node, True)
        node.beforePhis.extend(phiList)
            
    def buildPhiList(self, nameList, dictList, node, before):
        ''' name_list is the list of names to add phi nodes for.
            dict_list is the list of dicts to extract the instance the variable
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
    
    def do_ListComp(self, node):
        ''' The inside of a comprehension can not assign anything. Ignore
            it for now. '''
        for z in node.generators:
            self.visit(z)
            
    def do_comprehension(self, node):
        ''' We want to ssa any named lists. '''
        self.visit(node.iter)
        
    def do_GeneratorExp(self,node):
        ''' We need not be interest in anything here. '''
        pass
    
    def do_Try(self,node):
        for z in node.body:
            self.visit(z)
        for z in node.handlers:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
        for z in node.finalbody:
            self.visit(z)

    def do_TryExcept(self,node):
        ''' TODO: Treat this as an if. '''
        for z in node.body:
            self.visit(z)
            # self.merge_dicts(aDict,aDict2)
        for z in node.handlers:
            self.visit(z)
            # self.merge_dicts(aDict,aDict2)
        for z in node.orelse:
            self.visit(z)
            # self.merge_dicts(aDict,aDict2)

    def do_TryFinally(self,node):
        for z in node.body:
            self.visit(z)
        for z in node.finalbody:
            self.visit(z)

    def do_ClassDef (self,node):
        ''' We need the global variables. Do not start with an empty d
            TODO: Check for classes defined after. '''
        # Class becomes a sort variable when defined
        if node.name in self.d:
            self.d[node.name] += 1
        else:
            self.d[node.name] = 1
        node.originalId = node.name
        node.id = node.originalId + str(self.d[node.originalId])
        old_d = self.d
        self.add_intial_class_names()
        for z in node.bases:
            self.visit(z)
        for z in node.body:
            self.visit(z)
        self.d = old_d

    def do_FunctionDef (self,node):
        ''' Variables defined in function should not exist outside. '''
        # Function becomes a sort variable when defined
        if node.name in self.d:
            self.d[node.name] += 1
        else:
            self.d[node.name] = 1
        node.originalId = node.name
        node.id = node.originalId + str(self.d[node.originalId])
        # Store d so we can eradicate local variables
        old_d = self.d
        print(node.name)
        self.visit(node.args)
        for z in node.body:
            self.visit(z)
        self.d = old_d

    def do_Lambda(self,node):
        old_d = self.d
        self.d = {}
        self.visit(node.args)
        self.visit(node.body)
        self.d = old_d

    def do_Module (self,node):
        old_d = self.d
        self.d = {}
        self.add_intial_module_names()
        self.body = node.body
        for z in node.body:
            self.visit(z)
        self.d = old_d

    def do_arguments(self,node):
        assert isinstance(node,ast.AST),node
        
        for arg in node.args:
            self.visit(arg)
            
    def do_arg(self, node):
        if node.arg == "self":
            node.id = node.arg
            return
        node.originalId = node.arg
        self.d[node.arg] = 1
        node.id = node.originalId + str(self.d[node.originalId])

    def do_Assign(self,node):
        self.visit(node.value)
        for target in node.targets:
            self.visit(target)

    def do_AugAssign(self,node):
        ''' We need to store the previous iteration of the target variable name
            so we know what to load in the type inference.
            TODO: Assign prev_name a bit more elegantly.
            TODO: Allow this to work with Expressions such as self.x += 4'''
        self.visit(node.value)
   #     pprint(node.target.attr)
        # We to create a node.target.id but no need to visit it again
        if isinstance(node.target, ast.Attribute):
            self.visit(node.target)
            node.prev_name = node.target
            return
        assert hasattr(node.target, 'id'), "Error: Target is not a variable."
        
        prev_name = ast.Name()
        prev_name.ctx = ast.Load()
        prev_name.id = node.target.id
        node.prev_name = node.target.id
        node.prev_name = prev_name
        self.visit(prev_name)
        self.visit(node.target)
        print("Target")      
        print(node.target.id)
        print("Prev name")
        print(node.prev_name.id)  
        
    def do_Attribute(self,node):
        ''' Add a new variable of the form x.y if it's a variable.
            SSA not currently performed '''
        if isinstance(node.value, ast.Name):
            node.id = node.value.id + '.' + node.attr
            node.variable = True
            self.do_Name(node)
            self.visit(node.value)
        else:
            self.visit(node.attr)
            self.visit(node.value)
            node.variable = False

    def do_Import(self,node):        
        for z in node.names:
            self.visit(z)

    def do_ImportFrom(self,node):
        for z in node.names:
            self.visit(z)
            
    def do_alias (self,node):
        ''' Entered after imports.
            Store the module name. Add name to the variable list. Imports are
            essentially assigned to variables. '''
        node.module_name = node.name  
        if getattr(node,'asname'):
            self.d[node.asname] = 1
            node.id = node.asname + str(self.d[node.asname])
        else:
            self.d[node.name] = 1
            node.id = node.name + str(self.d[node.name])
    
    def do_Name(self,node):
        ''' If the id is True or false then ignore. WHY ARE TRUE AND FALSE
            IDENTIFIED THE SAME WAY AS VARIABLES. GAH. '''
       # print(node.id)
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