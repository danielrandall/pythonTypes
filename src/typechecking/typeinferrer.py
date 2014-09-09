import ast
from pprint import pprint

from src.traversers.astfulltraverser import AstFullTraverser
from src.typechecking.errorissuer import *
from src.typechecking.basictypevariable import BasicTypeVariable
from src.typechecking.calltypevariable import CallTypeVariable
from src.typechecking.contentstypevariable import ContentsTypeVariable
from src.typechecking.itertypevariable import IterTypeVariable
from src.typechecking.indextypevariable import IndexTypeVariable
from src.typechecking.binoptypevariable import BinOpTypeVariable
from src.typechecking.classtypevariable import ClassTypeVariable
from src.typechecking.getattrtypevariable import GetAttrTypeVariable
from src.typechecking.setattrtypevariable import SetAttrTypeVariable
from src.typeclasses import *
from src.traversers.astfulltraverser import AstFullTraverser
from src.importdependent import ImportDependent
from src.binopconstraints import get_op_types
from src.pyfile import PyFile

class TypeInferrer(AstFullTraverser):
    
    def __init__(self, error_issuer, stats):
        self.error_issuer = error_issuer
        self.stats = stats
    
    def initialise(self):
        self.currently_assigning = False
        # Motions whether the param has an assignment  param -> bool
        self.fun_params = {}
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
            if key not in BUILTIN_TYPE_DICT:
                print(key + ": " + str(value.get()))
            
    def check_dependents(self, file, file_tree):
        ''' Extracts all of the type variables for the imports.
            TODO: Detect circular references?
            TODO: Wildcard imports '''
        dependent_vars = {}
        root = file.get_source()
        #print(file_tree)
     #   print("dependents for " + file.path_and_name)
     #   if file.get_name() == "glances_monitor_list":
     #       pass
        for dependent in root.import_dependents:
            new_vars = dependent.find(file_tree, file.get_path())
    #        print(new_vars)
            assert isinstance(new_vars, list)
            for name, var in new_vars:
                dependent_vars[name] = var
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
    #    print()
    #    print("Printing module: |||||||||||||||||||||||||||||||||||************************ " + file.get_path() + " " + file.get_name() + " *******************|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")   
    #    print()
        self.module_name = file.get_path() + " " + file.get_name()
        self.variableTypes = root.variableTypes
        self.initialise()
   #     print("-DEPENDENTS-")
   #     pprint(dependents)
        self.link_imports(dependents)
        self.visit(root)
        file.typed = True
        
    def link_imports(self, imports):
        for name, value in imports.items():
            # Due to wildcards there may be names not yet definied
            if name not in self.variableTypes:
                self.variableTypes[name] = BasicTypeVariable()
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
            return [BasicTypeVariable([Bool_Type()])]
        if node.id == "None":
            return [BasicTypeVariable([None_Type()])]
        if node.id == "self"  or node.id == "cls":
            if self.current_class:
                return [self.current_class]
            else:
                # Then we have to treat this like a regular parameter. Make sure it's a function parameter
                return [BasicTypeVariable([Any_Type()])]
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
        targets = []
        self.currently_assigning = True
        try:
            for z in node.targets:
                targets.extend(self.visit(z))
        finally:
            self.currently_assigning = False
            
    #    if len(node.targets) > 1:
            # x = y = 5
    #        value_types = self.visit(node.value)
    #        assert len(value_types) == 1
    #        value_types = [value_types[0]] * len(targets)
        
        if isinstance(node.targets[0], ast.List) or isinstance(node.targets[0], ast.Tuple):
            if isinstance(node.value, ast.List) or isinstance(node.value, ast.Tuple):
                # [x, y] = [5, 2]
                self.currently_assigning = True
                value_types = self.visit(node.value)
                self.currently_assigning = False
            else:
                value_types = self.visit(node.value)
        else:
            value_types = self.visit(node.value)

        self.conduct_assignment(targets, value_types, node)
        
    def conduct_assignment(self, targets, value_types, node):
        ''' Updates the type variables with the new types. '''
   #     print()
    #    if hasattr(node, "lineno:
    #        print(node.lineno)
   #     print("targets")
   #     print(targets)
   #     print("values")
   #     print(value_types)
   #     print()
   
        # Special case list or double assignment
        # x = y = 6 
       # if node:
       #     print(node.lineno)
        if len(targets) != len(value_types):
          #  print(node.lineno)
          #  print("targets")
          #  print(targets)
          #  print("values")
          #  print(value_types)
            # Makes sure it's a single element
            assert len(value_types) == 1
            # Create a contentstypevariable for each target
            value_types = value_types[0]
            # Hack
            container = ContentsTypeVariable([])
            self.conduct_assignment([container], [value_types], node)
            value_types = [container] * len(targets)
            
        for target, value in zip(targets, value_types):
            assert isinstance(value, BasicTypeVariable)
            assert isinstance(target, BasicTypeVariable)
            value.add_new_dependent(target)
      #  print()
      #  print("Conduct")
      #  self.print_types()
            
    def do_Call(self, node):
        ''' Link the indentifier to a callvariable. '''
        self.stats.inc_num_func_calls()
        func_indentifier = self.visit(node.func)[0]
        given_args = []
        for z in node.args:
            given_args.extend(self.visit(z))
      #  if node.lineno == 427:
      #      pass
        return_type = CallTypeVariable(given_args, node, func_indentifier)
        # Set up a constraint between the call and the identifier
        self.conduct_assignment([return_type], [func_indentifier], node)
        # Do args as well
        self.conduct_assignment([return_type]*len(given_args), given_args, node)
        # Create a call issue
        self.error_issuer.add_issue(CallIssue(node, return_type, self.module_name))
        return [return_type]
    
    def do_Attribute(self, node):
        return_type = None
        value = self.visit(node.value)[0]
   #    if node.attr == "getKey":
   #         pass
        if isinstance(node.ctx, ast.Store):
            return_type = SetAttrTypeVariable(value, node.attr, node)
            # Create constraint between value and setattr
            self.conduct_assignment([return_type], [value], node)
        elif isinstance(node.ctx, ast.Load):
            return_type = GetAttrTypeVariable(value, node.attr, node)
            # Create constraint between value and getattr
            self.conduct_assignment([return_type], [value], node)
            # Add an output constraint to the error issuer
            self.error_issuer.add_issue(GetAttrIssue(node, return_type, self.module_name, node.attr))
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
        self.stats.inc_num_funcs()
        self.variableTypes = node.variableTypes
        old_return = self.return_variable
        old_params = self.fun_params
        try:
            params = self.visit(node.args)
            self.fun_params = {}
            self.fun_params.update({self.variableTypes[param] : False for param in params})

            self.return_variable = BasicTypeVariable()
            for z in node.body:
                self.visit(z)
            for z in node.decorator_list:
                self.visit(z)
                
        #    if node.name == "__init__":
        #        pass    
                
            # Add Any_Type() to args if we can't infer them
            for param, assigned in self.fun_params.items():
                if not assigned:
                    self.conduct_assignment([param], [BasicTypeVariable([Any_Type()])], node)
                    
            # Create error issue for init. Should only return None
            if node.name == "__init__":
                self.error_issuer.add_issue(InitNoneIssue(node, self.return_variable, self.module_name))
                
            if node.name == "f":
                print()
                print("Final types")
                print(node.lineno)
                self.print_types()
                print("Param types")
                print([self.variableTypes[param].get() for param in params])
                print("Return types")
                print(self.return_variable.get())
        finally:
            
            # Add the new function type
            param_types = [self.variableTypes[param] for param in params]
            has_kwarg_vararg = self.check_has_kwarg_or_vararg(node.args)
            defaults_length = self.get_defaults_length(node.args)
            # Check to see whether function is a generator
            return_types = None
            if node.generator_function:
                return_types = BasicTypeVariable([Generator_Type()])
            else:
                return_types = self.return_variable
            # Create the function type
            fun_type = BasicTypeVariable([Def_Type(param_types, return_types, defaults_length, has_kwarg_vararg)])
            
            # Restore parent variables
            self.variableTypes = node.stc_context.variableTypes
            self.conduct_assignment([self.variableTypes[node.name]], [fun_type], node)
            self.fun_params = old_params
            
    def get_defaults_length(self, arguments):
        return len(arguments.defaults)
            
    def check_has_kwarg_or_vararg(self, arguments):
        return arguments.vararg or arguments.kwarg
        
            
    def do_arguments(self, node):
        ''' Defaults are also in args. '''
        args = []
        for z in node.args:
            args.extend(self.visit(z))
        # Always a tuple
        if node.vararg:
            self.conduct_assignment([self.variableTypes[node.vararg]], [BasicTypeVariable([Tuple_Type()])], node)
        # Always a dict
        if node.kwarg:
            self.conduct_assignment([self.variableTypes[node.kwarg]], [BasicTypeVariable([Dict_Type()])], node)
        return args
            
    def do_arg(self, node):
        if node.arg == "self" or node.arg == "cls":
            return []
        return [node.arg]
        
    def do_Return(self, node):
        value = None
        if not node.value:
            value = BasicTypeVariable([None_Type()])
        else:
            value = self.visit(node.value)[0]
        self.conduct_assignment([self.return_variable], [value], node)                
        
    def do_ClassDef(self, node):
        self.stats.inc_num_classes()
        
        self.variableTypes = node.variableTypes

        parent_class = self.current_class
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
    #        print("Class " + node.name + " vars")
    #        self.print_types()
    
            # Restore parents variables            
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
        self.stats.inc_num_binops()
        op = self.kind(node.op)
        left_types = self.visit(node.left)[0]
        right_types = self.visit(node.right)[0]
        
   #     if node.lineno == 81:
   #         pass
        
        # Add constraints if they are function parameters
        if left_types in self.fun_params:
            self.conduct_assignment([left_types], [get_op_types(op)], node)
            self.fun_params[left_types] = True
        if right_types in self.fun_params:
            self.conduct_assignment([right_types], [get_op_types(op)], node)
            self.fun_params[right_types] = True
        
        binop_var = BinOpTypeVariable(node, left_types, right_types, op)
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
        
        for it in iters:
            if it in self.fun_params:
                # Assign param to any in iter types
                self.conduct_assignment([it], [ITERATOR_TYPES], node)
                self.fun_params[it] = True
        
        # Assign to the iter target#
        iter_contents = [IterTypeVariable() for x in iters]
        self.conduct_assignment(iter_contents, iters, node)
        self.conduct_assignment(targets, iter_contents, node)
        
        for iter_typevar in iter_contents:
            self.error_issuer.add_issue(IteratorIssue(node, iter_typevar, self.module_name))
        
        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
  
    def do_Tuple(self, node):
        names = []
        for z in node.elts:
            # We only want to go one deep
            if self.currently_assigning and (isinstance(z, ast.List) or isinstance(z, ast.Tuple)):
                self.currently_assigning = False
                try:
                    names.extend(self.visit(z))
                finally:
                    self.currently_assigning = True
            else:
                names.extend(self.visit(z))
        if self.currently_assigning and names:
            return names
        else:
            new_tuple = Tuple_Type()
            return [BasicTypeVariable([new_tuple])]   
    
    def do_List(self, node):
        names = []
        for z in node.elts:
            # We only want to go one deep
            if self.currently_assigning and (isinstance(z, ast.List) or isinstance(z, ast.Tuple)):
                self.currently_assigning = False
                try:
                    names.extend(self.visit(z))
                finally:
                    self.currently_assigning = True
            else:
                names.extend(self.visit(z))
        # Only return if there's something there otherwise it's probably
        # a list_type
        if self.currently_assigning and names:
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
       # self.visit(node.args)
       # self.visit(node.body)
        return [BasicTypeVariable([Any_Type()])]
    
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
        return [BasicTypeVariable([Any_Type()])]

    def do_Subscript(self, node):
        ''' You can have slice assignment. e.g. x[0:2] = [1, 2]
            TODO: Allow user-defined types to index/slice. '''
        value_types = self.visit(node.value)
        self.visit(node.slice)
        
        # Will return something in the container if index
        if isinstance(node.slice, ast.Index):
            # Update function parameters if used as an index
            if value_types[0] in self.fun_params:
                self.conduct_assignment(value_types, [INDEX_TYPES], node)
                self.fun_params[value_types[0]] = True
            
            index_var = IndexTypeVariable()
            self.conduct_assignment([index_var], value_types, node)
            self.error_issuer.add_issue(IndexIssue(node, index_var, self.module_name))
            return [index_var]
        # Will return portion of the list. We don't know which
        if isinstance(node.slice, ast.Slice):
            return value_types
        # I don't know what an extended slice is...
        if isinstance(node.slice, ast.ExtSlice):
            return [BasicTypeVariable([Any_Type()])]
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
        iters = self.visit(node.iter)
        # Assign to the iter target
        iter_contents = [IterTypeVariable() for x in iters]
        self.conduct_assignment(iter_contents, iters, node)
        self.conduct_assignment(targets, iter_contents, node)
        
     #   self.conduct_assignment(targets, value_types, node)
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
            return [BasicTypeVariable([Bool_Type()])]
      #  for a_type in op_types:
      #      if a_type == int_type or a_type == float_type:
      #          return [set([a_type])]
        return [BasicTypeVariable([Any_Type()])]
    
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
        comparators = []
        for z in node.comparators:
            comparators.extend(self.visit(z))
        # Only check if its, say, if x in something
        # Can't be doing with the complications of all the possible combinations
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.In):
            comp = comparators[0]
            # if comp is a parameter then constrain types
            if comp in self.fun_params:
                self.conduct_assignment([comp], [CONTAINS_TYPES], node)
                self.fun_params[comp] = True
            self.error_issuer.add_issue(ContainsIssue(node, comp, self.module_name))
            
        return [BasicTypeVariable([Bool_Type()])]
    
    def do_Num(self, node):
        ''' node.n is the number in the num. '''
        ''' Returns int or float. '''
        t_num = None
        if isinstance(node.n, int):
            t_num = Int_Type()
        if isinstance(node.n, float):
            t_num = Float_Type()
        return [BasicTypeVariable([t_num])]
    
    def do_ExceptHandler(self, node):
        if node.type and node.name and node.name:
            except_type = self.visit(node.type)
            target = self.visit(node.name)
            self.conduct_assignment(target, except_type, node)
        for z in node.body:
            self.visit(z)
    
    def do_Bytes(self, node):
        return [BasicTypeVariable([Bytes_Type()])]

    def do_Str(self, node):
        '''This represents a string constant.'''
        return [BasicTypeVariable([String_Type()])]
    
    def do_Module (self,node):
        self.stats.inc_num_modules()
        for z in node.body:
            self.visit(z)