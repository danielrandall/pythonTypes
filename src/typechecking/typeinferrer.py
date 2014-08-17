import ast
from pprint import pprint

from src.traversers.astfulltraverser import AstFullTraverser
from src.typechecking.basictypevariable import BasicTypeVariable
from src.typechecking.contentstypevariable import ContentsTypeVariable
from src.typechecking.binoptypevariable import BinOpTypeVariable
from src.typeclasses import *
from src.traversers.astfulltraverser import AstFullTraverser
from src.importdependent import ImportDependent
from src.pyfile import PyFile

class TypeInferrer(AstFullTraverser):
    def init(self):   
        self.currently_assigning = False
        self.fun_params = []
        # The class definition we are currently under
        self.current_class = None
        
        # Detecting circular inferences
        self.call_stack = [] # Detects recursive calls
        self.assign_stack = [] # Detects circular assignments.

        # Add the builtin_types to the variable dict
    #    self.variableTypes.update(BUILTIN_TYPE_DICT)
        
       
    def run(self, file_tree):
        ''' file_tree is a list of pyfiles.
            TODO: Do this file find outside of this module... '''
        # Keys are module name, values their typed dicts
        file_list = self.file_tree_to_list(file_tree)
        for file in file_list:
            assert isinstance(file, PyFile), "Error: Not a Python file"
            dependents = self.check_dependents(file, file_tree)
            self.type_file(file, dependents) 
            
    def print_types(self):
        for key, value in self.variableTypes.items():
          #  print(key)
          #  print(value)
            print(key + ": " + str(value.get()))
            
    def check_dependents(self, file, file_tree):
        ''' Extracts all of the type variables for the imports.
            TODO: Detect circular references?
            TODO: Wildcard imports '''
        dependent_vars = {}
        root = file.get_source()
        for dependent in root.import_dependents:
                assert isinstance(dependent, ImportDependent)
                name = dependent.get_module_name()
                as_name = dependent.get_as_name()
                directory = dependent.get_directory_no_name()
               # assert(directory in file_tree), "File not found"
               
                # If can't find it then just set it to any   
                if not directory in file_tree or name not in file_tree[directory]:
                    dependent_vars[as_name] = BasicTypeVariable([any_type])
                    continue
                
                dependent_file = file_tree[directory][name]
                # Check if a specific global_var is imported from the module
                dependent_module = dependent_file.get_module_type()
                if dependent.is_import_from():
                    value = dependent_module.get_global_var(dependent.get_class_name())
                else:
                    value = BasicTypeVariable([dependent_module])
                dependent_vars[as_name] = value
        return dependent_vars 
            
    def file_tree_to_list(self, file_tree):
        file_lists = []
        name_dicts = file_tree.values()
        for n_dict in name_dicts:
            file_lists.extend(n_dict.values())
        return file_lists
            
    def type_file(self, file, dependents):   
        ''' Runs the type_checking on an individual file. '''
        root = file.get_source()     
        print("Printing module: ----------------------------- " + file.get_name() + " ------------------------------")   
        self.variableTypes = root.variableTypes
        self.init()
        print("-DEPENDENTS-")
        pprint(dependents)
        self.variableTypes.update(dependents)
        self.visit(root)
        file.typed = True
    
    def visit(self, node):
        '''Visit a single node.  Callers are responsible for visiting children.'''
        if hasattr(node, "phi_nodes"):
            phis = node.phi_nodes
            for phi in phis:
                self.visit(phi)
        method = getattr(self,'do_' + node.__class__.__name__)
        return method(node)
    
    def do_Name(self, node):
        ''' TODO: Add True/False/None to builtins. '''
        print(node.id)
        if (node.id == "True" or node.id == "False"):
            return [BasicTypeVariable([bool_type])]
        if (node.id == "None"):
            return [BasicTypeVariable([none_type])]
        return [self.variableTypes[node.id]]
    
    def do_Phi_Node(self, node):
        ''' We can treat this as multiple assignments to the target variable.
        '''
        if not node.get_targets():
            return
        var = self.variableTypes[node.get_var()]
        targets = []
        values = []
        for target in node.get_targets():
            targets.append(var)
            values.append(self.variableTypes[target])
        self.conduct_assignment(targets, values, node)
    
    def do_Assign(self, node):
        ''' Set all target variables to have the type of the value of the
            assignment. '''
        print(node.lineno)
        value_types = self.visit(node.value)
    
        targets = []
        self.currently_assigning = True
        try:
            for z in node.targets:
                targets.extend(self.visit(z))
        finally:
            self.currently_assigning = False  
        self.conduct_assignment(targets, value_types, node)
        
    def conduct_assignment(self, targets, value_types, node):
        ''' Updates the type variables with the new types. '''
#        print(node.lineno)
        print(targets)
        print(value_types)
        # Special case list assignment
        if len(targets) != len(value_types):
            # Makes sure it's a single list
            assert len(value_types) == 1
            # Create a contentstypevariable for each target
            contents_var = ContentsTypeVariable(list(value_types[0].get()))
            value_types = [contents_var] * len(targets)
            
        for target, value in zip(targets, value_types):
            assert isinstance(value, BasicTypeVariable)
            assert isinstance(target, BasicTypeVariable)
            value.add_new_dependent(target)
            
    def do_Call(self, node):
        return [BasicTypeVariable([any_type])]
    
    def do_Attribute(self,node):
        return [BasicTypeVariable([any_type])]
        
    def do_FunctionDef(self, node):
        ''' Find all args and return values.
        
            TODO: Find out possible types in *karg dict. '''
        self.variableTypes = node.variableTypes
        self.variableTypes.update(node.stc_context.variableTypes)

        for z in node.body:
            self.visit(z)
        for z in node.decorator_list:
            self.visit(z)

        print("Final types")
        self.print_types()
        
        # Restore parent variables
        self.variableTypes = node.stc_context.variableTypes
        
        # Add the new function type
        fun_type = BasicTypeVariable([any_type])
        self.conduct_assignment([self.variableTypes[node.name]], [fun_type], node)

    def do_ClassDef(self, node):
        self.variableTypes = node.variableTypes
        self.variableTypes.update(node.stc_context.variableTypes)

        parent_class = self.current_class
        # Deal with inheritence.
        inherited_vars = {}
        for base in node.bases:
            base_class = self.visit(base)[0]
            acceptable_type = False
            for possible_type in base_class:
                if possible_type == any_type:
                    # What the hell do I do here?
                    acceptable_type = True
                if isinstance(possible_type, Class_Type):
                    # If there is a clash, the first instance will be used
                    inherited_vars.update({k:v for k,v in possible_type.get_vars().items() if k not in inherited_vars})
                    acceptable_type = True
            assert acceptable_type, "Line " + str(node.lineno) + ": " + base.id + " is not a class. "
        # Add the self variables found
   #     for self_var in node.self_variables:
   #         if self_var not in inherited_vars:
   #             inherited_vars[self_var] = set()
        self.current_class = Class_Type(node.name, inherited_vars, node.callable)
        self.move_init_to_top(node.body, node)
        
        for z in node.body:
            self.visit(z)
        # We need to set the parameters for init
     #   init_def = list(self.variableTypes["__init__"])[0]
        
        # Set the call if possible
        is_callable, call_node = node.callable
        if is_callable:
            fun = list(self.variableTypes[call_node.name])
            # Should be a list of size 1
            assert len(fun) == 1, "__call__ multiply defined. "
            self.current_class.set_callable_params(fun[0].get_parameter_types(), fun[0].get_return_types())
        
        pprint("class globals")
        pprint(node.self_variables)
        
        # Restore parents variables
        self.variableTypes = node.stc_context.variableTypes
        self.variableTypes[node.name] = set([self.current_class])
        self.current_class = parent_class 
  
    def do_BinOp (self, node):
        ''' Adding the dependents causes it to update 3 times initially.
            TODO: find a way to stop this. '''
        left_types = self.visit(node.left)[0]
        right_types = self.visit(node.right)[0]
        binop_var = BinOpTypeVariable(left_types, right_types, self.kind(node.op))
        # Create the dependents
        self.conduct_assignment([binop_var] * 2, [left_types, right_types], node)
        return [binop_var]
  
    def do_Tuple(self, node):
        names = []
        for z in node.elts:
            names.extend(self.visit(z))
        if self.currently_assigning:
            return names
        else:
            new_tuple = Tuple_Type()
            return [BasicTypeVariable([new_tuple])]   
    
    def do_List(self, node):
        names = []
        for z in node.elts:
            names.extend(self.visit(z))
        if self.currently_assigning:
            return names
        else:
            new_list = List_Type()
            return [BasicTypeVariable([new_list])]    
        
    def do_Dict(self, node):
        for z in node.keys:
            self.visit(z)
        for z in node.values:
            self.visit(z)
        return [BasicTypeVariable([Dict_Type()])]
    
   # def do_Slice(self, node):
        ''' No need to return anything here.
            TODO: Do better with awaiting_type '''
    #   pass
    
    def do_Index(self, node):
        ''' Lists can only index with ints, but dicts can be anything.
            No need to return anythin here.
            TODO: Distinguish what can be indexed with. '''
        value_types = self.visit(node.value)[0]

    def do_Subscript(self, node):
        ''' You can have slice assignment. e.g. x[0:2] = [1, 2]
            TODO: Allow user-defined types to index/slice. '''
        value_types = self.visit(node.value)[0]
        self.visit(node.slice)
        
        # Will return something in the container if index
        if isinstance(node.slice, ast.Index):
            contents_var = ContentsTypeVariable(list(value_types.get()))
            return [contents_var]
        # Will return portion of the list. We don't know which
        if isinstance(node.slice, ast.Slice):
            return [value_types]
        assert False
    
    def do_ListComp(self, node):
        ''' A list comp can edit values inside of comp. Therefore must reset the
            variable types.
            TODO: Tuple in node.elt should result in List(Tuple(type)). '''
        old_type_list = self.variableTypes.copy()
        
        for node2 in node.generators:
            self.visit(node2)
        t = self.visit(node.elt)
        # Reset types
        self.variableTypes = old_type_list
        return [BasicTypeVariable([List_Type()])]
    
    def do_BoolOp(self, node):
        ''' For and/or
            Never fails.
            Boolean operators can return any types used in its values.
            ie. len(x) or [] can return Int or List.
            We create a subset constraint between the parameters. '''
        all_types = []
        for z in node.values:
            types = self.visit(z)[0]
            all_types.append(types)
        bool_op_var = BasicTypeVariable()
        self.conduct_assignment([bool_op_var] * len(all_types), all_types, node)
        return [bool_op_var]
    
    def do_UnaryOp(self,node):
        ''' TODO: Check this. Should be able to return more than one type.
            Must create an end constraint of containing an int or float for
            ops other than 'Not'. '''
        op_types = self.visit(node.operand)[0] # Will only have 1 element
        op_kind = self.kind(node.op)
        if op_kind == 'Not':    # All types are valid
            return [BasicTypeVariable([bool_type])]
      #  for a_type in op_types:
      #      if a_type == int_type or a_type == float_type:
      #          return [set([a_type])]
        return [BasicTypeVariable([any_type])]

    def do_Compare(self, node):
        ''' A comparison will always return a boolean type.
            TODO: Check if errors can occur as a result of a comparison. '''
        self.visit(node.left)
        for z in node.comparators:
            self.visit(z)
        return [BasicTypeVariable([bool_type])]
    
    def do_Num(self, node):
        ''' Returns int or float. '''
        t_num = Num_Type(node.n.__class__)
        return [BasicTypeVariable([t_num])]
    
    def do_Bytes(self, node):
        return [BasicTypeVariable([bytes_type])]

    def do_Str(self, node):
        '''This represents a string constant.'''
        return [BasicTypeVariable([string_type])]