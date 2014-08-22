import ast
import copy
from pprint import pprint

from src.typeclasses import BUILTIN_TYPE_DICT
from src.symboltable import SymbolTable
from src.utils import Utils
from src.traversers.astfulltraverser import AstFullTraverser
from src.importdependent import ImportDependent, Import, ImportFrom

class Preprocessor(AstFullTraverser):
    '''
    '''
    def __init__(self):
        AstFullTraverser.__init__(self)
            # A hack: True if visiting the target of an AugAssign node.
        self.u = Utils()

    class Dummy_Node:
        def __init__(self):
            # Use stc_ prefix to ensure no conflicts with ast.AST node field names.
            self.stc_parent = None
            self.stc_context = None
            self.stc_child_nodes = [] # Testing only.

    def run(self,fn,root):
        '''Run the prepass: init, then visit the root.'''
        # Init all ivars.
        self.context = None
        self.parent = self.Dummy_Node()
        self.import_dependents = None
        self.visit(root)
        self.current_body = None
        # Undo references to Dummy_Node objects.
        root.stc_parent = None
        root.stc_context = None
        return root
        
    def visit(self,node):
        '''Inject node references in all nodes.'''
        assert isinstance(node,ast.AST),node.__class__.__name__
        # Save the previous context & parent & inject references.
        # Injecting these two references is cheap.
        node.stc_context = self.context
        node.stc_parent = self.parent
        # Visit the children with the new parent.
        self.parent = node
        method = getattr(self,'do_' + node.__class__.__name__)
        result = method(node)
        # Restore the context & parent.
        self.context = node.stc_context
        self.parent = node.stc_parent
        return result
        
    def define_name(self,cx,name,defined=True):
        '''
        Fix the scope of the given name to cx.
        Set the bit in stc_defined_table if defined is True.
        '''
        st = cx.stc_symbol_table
        d = st.d
        if name not in d.keys():
            d[name] = [] # The type list.
        if defined:
            st.defined.add(name)

    def do_Attribute(self,node):
        name = self.visit(node.value)
        cx = node.stc_context
        st = cx.stc_symbol_table
        d = st.attrs_d
        key = node.attr
        val = node.value
        node.variable = isinstance(node.value, ast.Name)
        # Check if leftside is self
        if name == "self":
            parent_class = self.find_parent_class_def(node)
            if parent_class:
                parent_class.self_variables.add(node.attr)
            else:
                print("Error: self outside of class. ")
        # The following lines are expensive!
        # For Leo P1: 2.0 sec -> 2.5 sec.
    #    if d.has_key(key):
    #        d.get(key).add(val)
    #    else:
    #        aSet = set()
    #        aSet.add(val)
    #        d[key] = aSet
        # self.visit(node.ctx)
        if isinstance(node.ctx,(ast.Param,ast.Store)):
            st.defined_attrs.add(key)
            
    def find_parent_class_def(self, node):
        if not node:
            return None
        if isinstance(node, ast.ClassDef):
            return node
        return self.find_parent_class_def(node.stc_context)

    def do_AugAssign(self, node):
        ''' We need to store the previous iteration of the target variable name
            so we know what to load in the type inference.
            TODO: Assign prev_name a bit more elegantly.
            TODO: Allow this to work with Expressions such as self.x += 4'''
        if not hasattr(node, "transformed"):
            op = node.op
            target = node.target
            value = node.value
            copy_target = copy.deepcopy(target)
            # New value needs to be loaded, not stored
            copy_target.ctx = ast.Load()
            node.value = ast.BinOp(copy_target, op, value)
            node.value.lineno = node.lineno
            node.targets = [node.target]
            node.transformed = True
        self.do_Assign(node)
            

    def do_ClassDef(self, node):
        old_globals = self.global_variables     
        node.global_variables = set()
        node.global_variables |= self.global_variables
        self.global_variables = node.global_variables
        
        parent_cx = self.context
        assert parent_cx == node.stc_context
        # Add this function to its parents contents dict
        parent_cx.contents_dict[node.name] = node
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(parent_cx)
        # The contents of this module to which children add themselves.
        node.contents_dict = {}
        # Holds whether the node is callable and the relevant func node
        node.callable = False, None
        node.self_variables = set()
        # Define the function name itself in the enclosing context.
        self.define_name(parent_cx,node.name)
        # Visit the children in a new context.
        self.context = node
        for z in node.bases:
            self.visit(z)
            
        old_body = self.current_body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.global_variables = old_globals
            self.current_body = old_body
        for z in node.decorator_list:
            self.visit(z)
        self.context = parent_cx
       # print("CLASS CONTENTS")
       # pprint(node.contents_dict)
        
        # Add self variables to the starting list. Initially empty
       # print("SELF VARS")
       # for self_var in node.self_variables:
       #     print(self_var)

    def do_FunctionDef(self, node):
        ''' Doesn't need global variables. Use parent's. '''
        
        parent_cx = self.context
        assert parent_cx == node.stc_context
        # Add this function to its parents contents dict
        parent_cx.contents_dict[node.name] = node
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(parent_cx)
        # The contents of this module to which children add themselves.
        node.contents_dict = {}
        # Add a list of all returns
        node.stc_symbol_table.returns = []
        node.generator_function = False
        # Check special functions
        if isinstance(parent_cx, ast.ClassDef):
            parent_cx.self_variables.add(node.name)
            if node.name == "__call__":
                parent_cx.callable = (True, node)
        # Define the function name itself in the enclosing context.
        self.define_name(parent_cx,node.name)
        # Visit the children in a new context.
        self.context = node
        
        node.args.lineno = node.lineno
        self.visit(node.args)
        
        old_body = self.current_body
        self.current_body = node.body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.current_body = old_body
        for z in node.decorator_list:
            self.visit(z)
        self.context = parent_cx
        
    def do_Call(self, node):
        self.visit(node.func)
        for z in node.args:
            z.lineno = node.lineno
            self.visit(z)
        for z in node.keywords:
            z.lineno = node.lineno
            self.visit(z)
        if getattr(node,'starargs',None):
            self.visit(node.starargs)
        if getattr(node,'kwargs',None):
            self.visit(node.kwargs)
        
    def do_Return(self,node):
        assert hasattr(self.context.stc_symbol_table, 'returns'), "Return outside of function"
        self.context.stc_symbol_table.returns.append(node)
        if node.value:
            self.visit(node.value)

    def do_Global(self,node):
        cx = self.u.compute_module_cx(node)
        assert hasattr(cx,'stc_symbol_table'),cx
        node.stc_scope = cx
        for name in node.names:
            self.define_name(cx,name)
            
    def do_Import(self, node):
        ''' Import(names=[alias(name='ast')])
            Import(names=[alias(name='os',asname='ossy')]) '''
        for alias in node.names:
            as_name = alias.asname if alias.asname else None
            new_import = Import(alias.name, as_name)
            self.import_dependents.append(new_import)
    #    self.alias_helper(node, None)
                
    def do_ImportFrom(self,node):
        ''' ImportFrom(module='b',names=[alias(name='*')],level=0)])'''
        for alias in node.names:
            as_name = alias.asname if alias.asname else None
            new_import = ImportFrom(alias.name, node.module, as_name, node.level)
            self.import_dependents.append(new_import)
    #    self.alias_helper(node, node.module)

    def alias_helper(self, node, import_from):
        ''' alias.name contains import name e.g. a.b.c.filename
            alias.asname contains the obvious asname e.g. import filename as asname
            TODO: Allow imports outside of start ''' 
        #assert self.import_dependents
        for alias in node.names:
            as_name = alias.asname if alias.asname else None
            import_dependent = ImportDependent(alias.name, import_from, as_name)
            self.import_dependents.append(import_dependent)
            
            self.global_variables.add(import_dependent.get_as_name())
            

    def do_Lambda(self, node):
        parent_cx = self.context
        assert parent_cx == node.stc_context
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(parent_cx)
        # There is no lambda name.
        # Handle the lambda args.
        for arg in node.args.args:
            if isinstance(arg,ast.Name):
                # Python 2.x.
                assert isinstance(arg.ctx,ast.Param),arg.ctx
                # Define the arg in the lambda context.
                self.define_name(node,arg.id)
            else:
                # Python 3.x.
                assert isinstance(arg,ast.arg),arg
                assert isinstance(arg,ast.arg),arg
                self.define_name(node,arg.arg)
            arg.stc_scope = node
        # Visit the children in the new context.
        self.context = node
        
        node.args.lineno = node.lineno
        self.visit(node.args)
        self.visit(node.body)
        self.context = parent_cx

    def do_Module (self,node):
        node.global_variables = set()
        self.global_variables = node.global_variables
        # Add builtins
        self.global_variables |= set(BUILTIN_TYPE_DICT.keys())
        
        assert self.context is None
        assert node.stc_context is None
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(node)
        # The contents of this module to which children add themselves.
        node.contents_dict = {}
        node.import_dependents = []
        self.import_dependents = node.import_dependents
        # Visit the children in the new context.
        self.context = node
        
        self.current_body = node.body
        for z in node.body:
            self.visit(z)
        self.context = None
        
    def do_arguments(self, node):
        for z in node.args:
            z.lineno = node.lineno
            self.visit(z)
        for z in node.defaults:
            z.lineno = node.lineno
            self.visit(z)
        
    def do_Subscript(self, node):
        node.slice.lineno = node.lineno
        self.visit(node.slice)
        self.visit(node.value)
        
    def do_ExtSlice (self, node):
        for z in node.dims:
            z.lineno = node.lineno
            self.visit(z)
        
    def do_ListComp(self, node):
        self.visit(node.elt)
        for z in node.generators:
            z.lineno = node.lineno
            self.visit(z)
            
    def do_SetComp(self, node):
        self.visit(node.elt)
        for z in node.generators:
            z.lineno = node.lineno
            self.visit(z)
            
    def do_GeneratorExp(self, node):
        self.visit(node.elt)
        for z in node.generators:
            z.lineno = node.lineno
            self.visit(z)
            
    def do_DictComp(self, node):
        self.visit(node.key)
        self.visit(node.value)
        for z in node.generators:
            z.lineno = node.lineno
            self.visit(z)
            
    def do_With(self, node):
        ''' withs offer nothing to type inference. Replace all occurences in
            code with equivalent, nicer, stuff. '''
        transformed_items = self.convert_with_items(node.items, node.lineno)
        current_index = self.current_body.index(node)
        del self.current_body[current_index]
        insert_list = transformed_items + node.body
        for elem in reversed(insert_list):
            self.current_body.insert(current_index, elem)
        for z in insert_list:
            self.visit(z)
       # for z in node.items:
       #     z.lineno = node.lineno
       #     self.visit(z)
       # for z in node.body:
       #     z.lineno = node.lineno
       #     self.visit(z)
            
    def convert_with_items(self, items, lineno):
        return_list = []
        for item in items:
            new_node = None
            if item.optional_vars:
                # Create an assignment
                new_node = ast.Assign()
                new_node.lineno = lineno
                new_node.targets = [item.optional_vars]
                new_node.value = item.context_expr
            else:
                new_node = item.context_expr
            return_list.append(new_node)
        return return_list
                
                

    def do_Name(self, node):
        # If node is a global variable, add it to the globals
        if isinstance(node.ctx, ast.Store) and isinstance(node.stc_context, ast.Module) or isinstance(node.stc_context, ast.ClassDef):
            self.global_variables.add(node.id)
        
        cx = node.stc_context
        if isinstance(node.ctx,(ast.Param,ast.Store)):
            # The scope is unambigously cx, **even for AugAssign**.
            # If there is no binding, we will get an UnboundLocalError at run time.
            # However, AugAssigns do not actually assign to the var.
            assert hasattr(cx,'stc_symbol_table'),cx
            node.stc_scope = cx
        else:
            # ast.Store does *not* necessarily define the scope.
            # For example, a += 1 generates a Store, but does not defined the symbol.
            # Instead, only ast.Assign nodes really define a symbol.
            node.stc_scope = None
        return node.id     
    
    def do_Yield(self, node):
        ''' If a yield is found anywhere in a function then it is a generator
            function. '''
        assert isinstance(self.context, ast.FunctionDef)
        self.context.generator_function = True
        #self.visit(node.expr)
        if node.value:
            self.visit(node.value)
            
    # The following functions are only here to track the current body.
            
    def do_Try(self, node):
        # body
        old_body = self.current_body
        self.current_body = node.body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.current_body = old_body
        for z in node.handlers:
            self.visit(z)
        # orelse
        old_body = self.current_body
        self.current_body = node.orelse
        try:
            for z in node.orelse:
                self.visit(z)
        finally:
            self.current_body = old_body
        # final body
        old_body = self.current_body
        self.current_body = node.finalbody
        try:
            for z in node.finalbody:
                self.visit(z)
        finally:
            self.current_body = old_body

    def do_TryExcept(self, node):
        old_body = self.current_body
        self.current_body = node.body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.current_body = old_body
        for z in node.handlers:
            self.visit(z)
        # orelse
        old_body = self.current_body
        self.current_body = node.orelse
        try:
            for z in node.orelse:
                self.visit(z)
        finally:
            self.current_body = old_body

    def do_TryFinally(self, node):
        # body
        old_body = self.current_body
        self.current_body = node.body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.current_body = old_body
        # final body
        old_body = self.current_body
        self.current_body = node.finalbody
        try:
            for z in node.finalbody:
                self.visit(z)
        finally:
            self.current_body = old_body

    def do_While (self, node):
        self.visit(node.test)
        
        old_body = self.current_body
        self.current_body = node.body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.current_body = old_body
            
        # orelse
        old_body = self.current_body
        self.current_body = node.orelse
        try:
            for z in node.orelse:
                self.visit(z)
        finally:
            self.current_body = old_body
            
    def do_If(self,node):
        self.visit(node.test)
        
        old_body = self.current_body
        self.current_body = node.body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.current_body = old_body
            
        # orelse
        old_body = self.current_body
        self.current_body = node.orelse
        try:
            for z in node.orelse:
                self.visit(z)
        finally:
            self.current_body = old_body
            
    def do_For (self,node):
        self.visit(node.target)
        self.visit(node.iter)
        
        old_body = self.current_body
        self.current_body = node.body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.current_body = old_body
            
        # orelse
        old_body = self.current_body
        self.current_body = node.orelse
        try:
            for z in node.orelse:
                self.visit(z)
        finally:
            self.current_body = old_body
            
    def do_ExceptHandler(self,node):
        if node.type:
            self.visit(node.type)
        if node.name and isinstance(node.name,ast.Name):
            self.visit(node.name)
        # body
        old_body = self.current_body
        self.current_body = node.body
        try:
            for z in node.body:
                self.visit(z)
        finally:
            self.current_body = old_body