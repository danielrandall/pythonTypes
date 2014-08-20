import ast
from pprint import pprint

from src.traversers.astfulltraverser import AstFullTraverser
from src.typechecking.errorissuer import *
from src.typechecking.basictypevariable import BasicTypeVariable
from src.typechecking.contentstypevariable import ContentsTypeVariable
from src.typechecking.binoptypevariable import BinOpTypeVariable
from src.typechecking.classtypevariable import ClassTypeVariable
from src.typechecking.getattrtypevariable import GetAttrTypeVariable
from src.typechecking.setattrtypevariable import SetAttrTypeVariable
from src.typeclasses import *
from src.traversers.astfulltraverser import AstFullTraverser
from src.importdependent import ImportDependent
from src.pyfile import PyFile

class TypeInferrer(AstFullTraverser):
    
    def __init__(self, error_issuer):
        self.error_issuer = error_issuer
    
    def initialise(self):
        self.currently_assigning = False
        self.fun_params = []
        # The class definition we are currently under
        self.current_class = None
        self.return_variable = None
        
        # Detecting circular inferences
        self.call_stack = [] # Detects recursive calls
        self.assign_stack = [] # Detects circular assignments.
        
       
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
        print()
        print("Printing module: |||||||||||||||||||||||||||||||||||************************ " + file.path + " " + file.get_name() + " *******************|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")   
        print()
        self.module_name = file.path + " " + file.get_name()
        self.variableTypes = root.variableTypes
        self.initialise()
   #     print("-DEPENDENTS-")
   #     pprint(dependents)
        self.link_imports(dependents)
        self.visit(root)
        file.typed = True
        
    def link_imports(self, imports):
        for name, value in imports.items():
            self.conduct_assignment([self.variableTypes[name]], [value], None)
    
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
        if node.id == "True" or node.id == "False":
            return [BasicTypeVariable([bool_type])]
        if node.id == "None":
            return [BasicTypeVariable([none_type])]
        if node.id == "self":
            if self.current_class:
                return [self.current_class]
            else:
                # Then we have to treat this like a regular parameter. Make sure it's a function parameter
                return [BasicTypeVariable([any_type])]
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
   #     print()
   #     print(node.lineno)
   #     print("targets")
   #     print(targets)
   #     print("values")
   #     print(value_types)
   #     print()
   
        # Special case list or double assignment
        # x = y = 6 
        if len(targets) != len(value_types):
            # Makes sure it's a single element
            assert len(value_types) == 1
            # Create a contentstypevariable for each target
            value_types = value_types[0]
            # Hack
            if isinstance(list(value_types.get())[0], Container_Type):
                value_types = ContentsTypeVariable(list(value_types.get()))
            value_types = [value_types] * len(targets)
            
        for target, value in zip(targets, value_types):
            assert isinstance(value, BasicTypeVariable)
            assert isinstance(target, BasicTypeVariable)
            value.add_new_dependent(target)
    #    print("Conduct")
    #    self.print_types()
            
    def do_Call(self, node):
        return [BasicTypeVariable([any_type])]
    
    def do_Attribute(self, node):
        return_type = None
        value = self.visit(node.value)[0]
        if isinstance(node.ctx, ast.Store):
            return_type = SetAttrTypeVariable(value, node.attr, node)
            # Create constraint between value and setattr
            self.conduct_assignment([return_type], [value], node)
        elif isinstance(node.ctx, ast.Load):
            return_type = GetAttrTypeVariable(value, node.attr, node)
            # Create constraint between value and getattr
            self.conduct_assignment([return_type], [value], node)
            # Add an output constraint to the error issuer
            self.error_issuer.add_issue(GetAttrIssue(node, return_type, self.module_name))
        elif isinstance(node.ctx, ast.Del):
            # This is like del x.f . Do we care? Don't think so
            return
        else:
            print("CONTEXXXXXXXXXX")
            print(node.ctx)
            assert(False)
        return [return_type]
        
    def do_FunctionDef(self, node):
        ''' Find all args and return values.
        
            TODO: Find out possible types in *karg dict. '''
        self.variableTypes = node.variableTypes
        old_return = self.return_variable
        try:
            self.fun_params = self.visit(node.args)
            # Add any_type to args
            for param in self.fun_params:
                self.conduct_assignment([self.variableTypes[param]], [BasicTypeVariable([any_type])], node)
                
            self.return_variable = BasicTypeVariable()
            for z in node.body:
                self.visit(z)
            for z in node.decorator_list:
                self.visit(z)

     #       print("Final types")
     #       self.print_types()
        finally:
            # Restore parent variables
            self.variableTypes = node.stc_context.variableTypes
            # Add the new function type
            fun_type = BasicTypeVariable([any_type])
            self.conduct_assignment([self.variableTypes[node.name]], [fun_type], node)
            
    def do_arguments(self, node):
        ''' We need to begin checking what types the args can take.
            We can check stuff like 'self' here. '''
        args = []
        for z in node.args:
            args.extend(self.visit(z))
        return args
            
    def do_arg(self, node):
        return [node.arg]
        
    def do_Return(self, node):
        value = None
        if not node.value:
            value = BasicTypeVariable([none_type])
        else:
            value = self.visit(node.value)[0]
        self.conduct_assignment([self.return_variable], [value], node)                
        
    def do_ClassDef(self, node):
        self.variableTypes = node.variableTypes

        parent_class = self.current_class
        # Deal with inheritance.
        inherited_vars = {}
        base_classes = []
        for base in node.bases:
            base_classes.append(self.visit(base)[0])
        
        new_class = ClassTypeVariable(base_classes, node.variableTypes, node.name)
        # Set up constraints between the classes
        self.conduct_assignment([new_class] * len(base_classes), base_classes, node)
            
        # Add the definition to the context of this class
        self.conduct_assignment([self.variableTypes[node.name]], [new_class], node)
        
        # Add an base class constraint to the issuer
        self.error_issuer.add_issue(BaseClassIssue(node, new_class, self.module_name))
        
        # Type the class body
        self.current_class = new_class
        try:
            self.move_init_to_top(node.body, node)
            for z in node.body:
                self.visit(z)
        finally:
            # Restore parents variables
    #        print("Class " + node.name + " vars")
    #        self.print_types()
            self.variableTypes = node.stc_context.variableTypes
            self.current_class = parent_class 
            
    def move_init_to_top(self, body, node):
        assert isinstance(body, list), "Body needs to be a list."
        for i in range(len(body)):
            elem = body[i]
            if isinstance(elem, ast.FunctionDef):
                if elem.name == "__init__":
                    body.insert(0, body.pop(i))
                    return
  
    def do_BinOp (self, node):
        ''' Adding the dependents causes it to update 3 times initially.
            TODO: find a way to stop this. '''
        left_types = self.visit(node.left)[0]
        right_types = self.visit(node.right)[0]
        binop_var = BinOpTypeVariable(node, left_types, right_types, self.kind(node.op))
        # Create the dependents
        self.conduct_assignment([binop_var] * 2, [left_types, right_types], node)
        
        # Add an output constraint to the issuer
        self.error_issuer.add_issue(BinOpIssue(node, binop_var, self.module_name))
        return [binop_var]
    
    def do_For(self, node):
        ''' Here we need to assign the target the contents of the list.
            TODO: Ensure all iters are iterable. '''
        self.currently_assigning = True
        try:
            targets = self.visit(node.target)
        finally:
            self.currently_assigning = False
            
        iters = self.visit(node.iter)
        # Assign to the iter target#
     #   contents_var = ContentsTypeVariable(list(iter.get()))
        self.conduct_assignment(targets, iters, node)
        
        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
  
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
    
    def do_Lambda(self, node):
        self.visit(node.args)
        self.visit(node.body)
        return [BasicTypeVariable([any_type])]
    
   # def do_Slice(self, node):
        ''' No need to return anything here.
            TODO: Do better with awaiting_type '''
    #   pass
    
    def do_Index(self, node):
        ''' Lists can only index with ints, but dicts can be anything.
            No need to return anything here.
            TODO: Distinguish what can be indexed with. '''
        value_types = self.visit(node.value)[0]
        
    def do_Ellipsis(self, node):
        ''' Not 100% what to do with this. '''
        return [BasicTypeVariable([any_type])]

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
        # I don't know what an extended slice is...
        if isinstance(node.slice, ast.ExtSlice):
            return [BasicTypeVariable([any_type])]
        assert False
    
    def do_ListComp(self, node):
        ''' A list comp can edit values inside of comp. 
            TODO: Tuple in node.elt should result in List(Tuple(type)). '''
        for z in node.generators:
            self.visit(z)
        t = self.visit(node.elt)
        return [BasicTypeVariable([List_Type()])]
    
    def do_DictComp(self, node):
        self.visit(node.key)
        self.visit(node.value)
        for z in node.generators:
            self.visit(z)
        return [BasicTypeVariable([Dict_Type()])]
    
    def do_comprehension(self, node):
        ''' Can check whether node.iter has __iter__ function.
            The target is assigned the contents. '''
        self.currently_assigning = True
        try:
            targets = self.visit(node.target)
        finally:
            self.currently_assigning = False 
        value_types = self.visit(node.iter)
        self.conduct_assignment(targets, value_types, node)
        for z in node.ifs:
            self.visit(z)
    
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
    
    def do_IfExp (self, node):
        ''' For stuff like x = a if b else c.
            Can return the type of a or c. '''
        self.visit(node.test)
        body_types = self.visit(node.body)[0]
        else_types = self.visit(node.orelse)[0]
        return_types = BasicTypeVariable()
        self.conduct_assignment([return_types] * 2, [body_types, else_types], node)
        return [return_types]
    
    def do_GeneratorExp(self,node):
        for z in node.generators:
            self.visit(z)
        self.visit(node.elt)
        return [BasicTypeVariable([Generator_Type()])]

    def do_Compare(self, node):
        ''' A comparison will always return a boolean type.
            TODO: Check if errors can occur as a result of a comparison. '''
        self.visit(node.left)
        for z in node.comparators:
            self.visit(z)
        return [BasicTypeVariable([bool_type])]
    
    def do_Num(self, node):
        ''' node.n is the number in the num. '''
        ''' Returns int or float. '''
        t_num = None
        if isinstance(node.n, int):
            t_num = int_type
        if isinstance(node.n, float):
            t_num = float_type
        return [BasicTypeVariable([t_num])]
    
    def do_Bytes(self, node):
        return [BasicTypeVariable([bytes_type])]

    def do_Str(self, node):
        '''This represents a string constant.'''
        return [BasicTypeVariable([string_type])]