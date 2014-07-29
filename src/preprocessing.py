import ast
from pprint import pprint

from src.symboltable import SymbolTable
from src.utils import Utils
from src.traversers.astfulltraverser import AstFullTraverser
from src.importdependent import ImportDependent

class Preprocessor(AstFullTraverser):
    '''
    Unified pre-pass does two things simultaneously:
    1. Injects ivars into nodes. Only this pass should do this!
       For all nodes::
            node.stc_context = self.context
            node.stc_parent = self.parent
       For all context nodes::
            node.stc_symbol_table = {} # Expensive!
       For all Name nodes.
            node.stc_scope = None.
    2. Calls define_name() for all defined names:
       - class and function names,
       - all names defined in import statements.
       - all paramater names (ctx is 'Param')
       - all assigned-to names (ctx is 'Store'):
       This has the effect of setting::
           node.stc_scope = self.context.
           
    **Important**: Injecting empty lists, dicts or sets causes gc problems.
    This code now injects empty dicts only in context nodes, which does
    not cause significant problems.
    
    TODO: Edit this and make it more useful
    '''
    def __init__(self):
        AstFullTraverser.__init__(self)
        self.in_aug_assign = False
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
        self.fn = fn
        self.n_attributes = 0
        self.n_contexts = 0
        self.n_defined = 0
        self.n_nodes = 0
        self.parent = self.Dummy_Node()
        self.visit(root)
        # Undo references to Dummy_Node objects.
        root.stc_parent = None
        root.stc_context = None
        return root
        
    def visit(self,node):
        '''Inject node references in all nodes.'''
        assert isinstance(node,ast.AST),node.__class__.__name__
        self.n_nodes += 1
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
            self.n_defined += 1
            d[name] = [] # The type list.
        if defined:
            st.defined.add(name)

    def do_Attribute(self,node):
        self.n_attributes += 1
        name = self.visit(node.value)
        cx = node.stc_context
        st = cx.stc_symbol_table
        d = st.attrs_d
        key = node.attr
        val = node.value
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

    def do_AugAssign(self,node):
        # g.trace('FT',self.u.format(node),g.callers())
        assert not self.in_aug_assign
        try:
            self.in_aug_assign = True
            self.visit(node.target)
        finally:
            self.in_aug_assign = False
        self.visit(node.value)

    def do_ClassDef (self,node):
        self.n_contexts += 1
        parent_cx = self.context
        assert parent_cx == node.stc_context
        # Add this function to its parents contents dict
        parent_cx.contents_dict[node.name] = node
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(parent_cx)
        # The contents of this module to which children add themselves.
        node.contents_dict = {}
        # Holds whether the node is callable and the relevent func node
        node.callable = False, None
        node.self_variables = set()
        # Define the function name itself in the enclosing context.
        self.define_name(parent_cx,node.name)
        # Visit the children in a new context.
        self.context = node
        for z in node.bases:
            self.visit(z)
        for z in node.body:
            self.visit(z)
        for z in node.decorator_list:
            self.visit(z)
        self.context = parent_cx
        print("CLASS CONTENTS")
        pprint(node.contents_dict)

    def do_FunctionDef (self,node):
        self.n_contexts += 1
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
        pprint(self.context.stc_symbol_table.returns)
        self.visit(node.args)
        for z in node.body:
            self.visit(z)
        for z in node.decorator_list:
            self.visit(z)
        self.context = parent_cx
        
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
            
    def do_Import(self,node):
        ''' Import(names=[alias(name='ast')])
            Import(names=[alias(name='os',asname='ossy')]) '''
        self.alias_helper(node, None)
                
    def do_ImportFrom(self,node):
        ''' ImportFrom(module='b',names=[alias(name='*')],level=0)])'''
        self.alias_helper(node, node.module)

    def alias_helper(self, node, import_from):
        ''' alias.name contains import name e.g. a.b.c.filename
            alias.asname contains the obvious asname e.g. import filename as asname
            TODO: Deal with asname
            TODO: Allow imports outside of start ''' 
        assert isinstance(node.stc_context, ast.Module)
        for alias in node.names:
            as_name = alias.asname if alias.asname else None
            import_dependent = ImportDependent(alias.name, import_from, as_name)
            node.stc_context.import_dependents.append(import_dependent)

    def do_Lambda(self,node):
        self.n_contexts += 1
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
        # self.visit(node.args)
        self.visit(node.body)
        self.context = parent_cx

    def do_Module (self,node):
        self.n_contexts += 1
        assert self.context is None
        assert node.stc_context is None
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(node)
        # The contents of this module to which children add themselves.
        node.contents_dict = {}
        node.import_dependents = []
        # Visit the children in the new context.
        self.context = node
        for z in node.body:
            self.visit(z)
        self.context = None

    def do_Name(self,node):
        # g.trace('P1',node.id)
        
        # self.visit(node.ctx)
        cx = node.stc_context
        if isinstance(node.ctx,(ast.Param,ast.Store)):
            # The scope is unambigously cx, **even for AugAssign**.
            # If there is no binding, we will get an UnboundLocalError at run time.
            # However, AugAssigns do not actually assign to the var.
            assert hasattr(cx,'stc_symbol_table'),cx
            self.define_name(cx,node.id,defined = not self.in_aug_assign)
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