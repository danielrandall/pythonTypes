import ast
from pprint import pprint

from src.traversers.astfulltraverser import AstFullTraverser
from src.importdependent import ImportDependent
from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import *
from src.traversers.ssatraverser import Phi_Node

class PreprocessorSecond(AstFullTraverser):
    '''
    Creates a BasicTypeVariable for every variable in the correct scope.
    '''
    def __init__(self):
        AstFullTraverser.__init__(self)

    def run(self, file, root):
        self.source_file = file
        self.variableTypes = None
        self.visit(root)
        return root
        
    def visit(self,node):
        if hasattr(node, "phi_nodes"):
            phis = node.phi_nodes
            for phi in phis:
                self.visit(phi)
        method = getattr(self,'do_' + node.__class__.__name__)
        result = method(node)
        return result
    
    def do_Phi_Node(self, node):
        if node.get_var() not in self.variableTypes:
            self.variableTypes[node.var] = BasicTypeVariable()
        
    def do_ClassDef(self, node):
        # Update parent dict
        if node.name not in self.variableTypes:
            self.variableTypes[node.name] = BasicTypeVariable()  
            
        old_types = self.variableTypes 
        node.variableTypes = {}
        node.variableTypes.update(self.variableTypes)
        self.variableTypes = node.variableTypes
        self.variableTypes.update({name : BasicTypeVariable() for name in node.global_variables if name not in self.variableTypes})
        self.variableTypes.update({name : BasicTypeVariable() for name in node.self_variables if name not in self.variableTypes})
        
        try:
            for z in node.bases:
                self.visit(z)
            for z in node.body:
                self.visit(z)
            for z in node.decorator_list:
                self.visit(z)
        finally:
            # Restore
       #     print("class vars " + node.name)
       #     pprint(node.variableTypes)
            self.variableTypes = old_types
            
    def do_arg(self, node):
        self.variableTypes[node.arg] = BasicTypeVariable()
        
    def do_arguments(self,node):
        for z in node.args:
            self.visit(z)
        for z in node.defaults:
            self.visit(z)
        if node.kwarg:
            self.variableTypes[node.kwarg] = BasicTypeVariable()

    def do_FunctionDef(self, node):    
        if node.name not in self.variableTypes:
            self.variableTypes[node.name] = BasicTypeVariable()
            
        old_types = self.variableTypes 
        node.variableTypes = {}
        node.variableTypes.update(self.variableTypes)
        self.variableTypes = node.variableTypes
        try:
            self.visit(node.args)
            for z in node.body:
                self.visit(z)
            for z in node.decorator_list:
                self.visit(z)
        finally:
            # Restore
      #      print("functions vars " + node.name)
      #      pprint(node.variableTypes)
            self.variableTypes = old_types

    def do_Lambda(self, node):
        self.visit(node.args)
        self.visit(node.body)

    def do_Module (self,node):
        node.variableTypes = {}
        self.variableTypes = node.variableTypes
        # Add the builtin_types to the variable dict
        self.variableTypes.update(BUILTIN_TYPE_DICT)
        self.variableTypes.update({name : BasicTypeVariable() for name in node.global_variables if name not in self.variableTypes})
        
        # Add names for imports
        for dependent in node.import_dependents:
            as_name = dependent.get_as_name()
            # Don't include wildcard
            if as_name not in self.variableTypes and as_name != "*":
                self.variableTypes[as_name] = BasicTypeVariable() 
        for z in node.body:
            self.visit(z)
     #   print("Module vars")
     #   pprint(node.variableTypes)
        module_type = Module_Type(node.variableTypes)
        self.source_file.set_module_type(module_type)
        

    def do_Name(self, node):
        ''' Create a entry into the type dict if necessary. '''
        if node.id == "True" or node.id == "False":
            return
        if node.id == "None":
            return
        if node.id == "self":
            return
        if node.id in BUILTIN_TYPE_DICT:
            return
        if node.id not in self.variableTypes:
                self.variableTypes[node.id] = BasicTypeVariable() 
            
