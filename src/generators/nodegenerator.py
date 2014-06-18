import ast

class NodeGenerator:
    
    # def __init__(self):
        # pass
    
    # This "convenience" would be a big overhead!
    # def __call__(self,node):
        # for z in self.visit(node):
            # yield z
    
    #@+others
    #@+node:ekr.20130318065046.9310: *4* visit
    def visit(self,node):

        assert isinstance(node,ast.AST),node.__class__.__name__
        method_name = 'do_' + node.__class__.__name__
        method = getattr(self,method_name)
        yield node
        for node2 in method(node):
            yield node2
            
    # Avoid the overhead of an extra layer.
    run = visit

    if 0: # No longer used: all referenced visitors must exist.
        def default_visitor(self,node):
            '''yield all the children of a node without children.'''
            raise StopIteration
    #@+node:ekr.20130318065046.9372: *4* fg.operators
    #@+node:ekr.20130318065046.9426: *5* fg.do-nothings
    def do_Bytes(self,node): 
        raise StopIteration
            # Python 3.x only.
        
    def do_Ellipsis(self,node):
        raise StopIteration
        
    # Num(object n) # a number as a PyObject.
    def do_Num(self,node):
        raise StopIteration
           
    def do_Str (self,node):
        raise StopIteration
            # represents a string constant.
    #@+node:ekr.20130318065046.9374: *5* fg.arguments
    # arguments = (expr* args, identifier? vararg, identifier? kwarg, expr* defaults)

    def do_arguments(self,node):
        
        for z in node.args:
            for z2 in self.visit(z):
                yield z2
        for z in node.defaults:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9375: *5* fg.Attribute
    # Attribute(expr value, identifier attr, expr_context ctx)

    def do_Attribute(self,node):
        
        for z in self.visit(node.value):
            yield z
        # yield node.ctx
    #@+node:ekr.20130318065046.9376: *5* fg.BinOp
    # BinOp(expr left, operator op, expr right)

    def do_BinOp (self,node):
        
        for z in self.visit(node.left):
            yield z
        # yield node.op
        for z in self.visit(node.right):
            yield z
    #@+node:ekr.20130318065046.9377: *5* fg.BoolOp
    # BoolOp(boolop op, expr* values)

    def do_BoolOp (self,node):

        # yield node.op
        for z in node.values:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9378: *5* fg.Call
    # Call(expr func, expr* args, keyword* keywords, expr? starargs, expr? kwargs)

    def do_Call(self,node):
        
        for z in self.visit(node.func):
            yield z
        for z in node.args:
            for z2 in self.visit(z):
                yield z2
        for z in node.keywords:
            for z2 in self.visit(z):
                yield z2
        if getattr(node,'starargs',None):
            for z in self.visit(node.starargs):
                yield z
        if getattr(node,'kwargs',None):
            for z in self.visit(node.kwargs):
                yield z
    #@+node:ekr.20130318065046.9379: *5* fg.Compare
    # Compare(expr left, cmpop* ops, expr* comparators)

    def do_Compare(self,node):
        
        for z in self.visit(node.left):
            yield z
        # for z in node ops:
            # yield z
        for z in node.comparators:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9380: *5* fg.comprehension
    # comprehension (expr target, expr iter, expr* ifs)

    def do_comprehension(self,node):

        for z in self.visit(node.target): # a Name.
            yield z
        for z in self.visit(node.iter): # An Attribute.
            yield z
        for z in node.ifs: ### Does not appear in AstFullTraverser!
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9381: *5* fg.Dict
    # Dict(expr* keys, expr* values)

    def do_Dict(self,node):
        
        for z in node.keys:
            for z2 in self.visit(z):
                yield z2
        for z in node.values:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9382: *5* fg.Expr
    # Expr(expr value)

    def do_Expr(self,node):
        
        for z in self.visit(node.value):
            yield z
    #@+node:ekr.20130318065046.9383: *5* fg.Expression
    def do_Expression(self,node):
        
        '''An inner expression'''
        for z in self.visit(node.body):
            yield z
    #@+node:ekr.20130318065046.9384: *5* fg.ExtSlice
    # ExtSlice(slice* dims) 

    def do_ExtSlice (self,node):
        
        for z in node.dims:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9385: *5* fg.GeneratorExp
    # GeneratorExp(expr elt, comprehension* generators)

    def do_GeneratorExp(self,node):
        
        for z in self.visit(node.elt):
            yield z
        for z in node.generators:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9386: *5* fg.ifExp (ternary operator)
    # IfExp(expr test, expr body, expr orelse)

    def do_IfExp (self,node):

        for z in self.visit(node.body):
            yield z
        for z in self.visit(node.test):
            yield z
        for z in self.visit(node.orelse):
            yield z
    #@+node:ekr.20130318065046.9387: *5* fg.Index
    # Index(expr value)

    def do_Index (self,node):
        
        for z in self.visit(node.value):
            yield z
    #@+node:ekr.20130318065046.9388: *5* fg.keyword
    # keyword = (identifier arg, expr value)

    def do_keyword(self,node):

        # node.arg is a string.
        for z in self.visit(node.value):
            yield z
    #@+node:ekr.20130318065046.9389: *5* fg.Lambda
    # Lambda(arguments args, expr body)

    def do_Lambda(self,node):
        
        for z in self.visit(node.args):
            yield z
        for z in self.visit(node.body):
            yield z
    #@+node:ekr.20130318065046.9390: *5* fg.List & ListComp
    # List(expr* elts, expr_context ctx) 

    def do_List(self,node):
        
        for z in node.elts:
            for z2 in self.visit(z):
                yield z2
        # yield node.ctx

    # ListComp(expr elt, comprehension* generators)

    def do_ListComp(self,node):

        for z in self.visit(node.elt):
            yield z
        for z in node.generators:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9391: *5* fg.Name (revise)
    # Name(identifier id, expr_context ctx)

    def do_Name(self,node):
        # yield node.ctx
        raise StopIteration
    #@+node:ekr.20130318065046.9392: *5* fg.Repr
    # Python 2.x only
    # Repr(expr value)

    def do_Repr(self,node):

        for z in self.visit(node.value):
            yield z
    #@+node:ekr.20130318065046.9393: *5* fg.Slice
    def do_Slice (self,node):

        if getattr(node,'lower',None):
            for z in self.visit(node.lower):
                yield z            
        if getattr(node,'upper',None):
            for z in self.visit(node.upper):
                yield z
        if getattr(node,'step',None):
            for z in self.visit(node.step):
                yield z
    #@+node:ekr.20130318065046.9394: *5* fg.Subscript
    # Subscript(expr value, slice slice, expr_context ctx)

    def do_Subscript(self,node):
        
        for z in self.visit(node.value):
            yield z
        for z in self.visit(node.slice):
            yield z
        # yield node.ctx
    #@+node:ekr.20130318065046.9395: *5* fg.Tuple
    # Tuple(expr* elts, expr_context ctx)

    def do_Tuple(self,node):
        
        for z in node.elts:
            for z2 in self.visit(z):
                yield z2
        # yield node.ctx
    #@+node:ekr.20130318065046.9396: *5* fg.UnaryOp
    # UnaryOp(unaryop op, expr operand)

    def do_UnaryOp (self,node):
        
        # for z in self.visit(node.op):
            # yield z
        for z in self.visit(node.operand):
            yield z
    #@+node:ekr.20130318065046.9397: *4* fg.statements
    #@+node:ekr.20130318065046.9398: *5* fg.alias
    # identifier name, identifier? asname)

    def do_alias (self,node):
        raise StopIteration
    #@+node:ekr.20130318065046.9399: *5* fg.Assert
    # Assert(expr test, expr? msg)

    def do_Assert(self,node):

        for z in self.visit(node.test):
            yield z
        if node.msg:
            for z in self.visit(node.msg):
                yield z

    #@+node:ekr.20130318065046.9400: *5* fg.Assign
    # Assign(expr* targets, expr value)

    def do_Assign(self,node):

        for z in node.targets:
            for z2 in self.visit(z):
                yield z2
        for z in self.visit(node.value):
            yield z
            
    #@+node:ekr.20130318065046.9401: *5* fg.AugAssign
    # AugAssign(expr target, operator op, expr value)

    def do_AugAssign(self,node):
        
        for z in self.visit(node.target):
            yield z
        # yield node.op
        for z in self.visit(node.value):
            yield z
    #@+node:ekr.20130318065046.9402: *5* fg.Break
    def do_Break(self,node):

        raise StopIteration

    #@+node:ekr.20130318065046.9403: *5* fg.ClassDef
    # ClassDef(identifier name, expr* bases, stmt* body, expr* decorator_list)

    def do_ClassDef (self,node):

        for z in node.bases:
            for z2 in self.visit(z):
                yield z2
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.decorator_list:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9404: *5* fg.Continue
    def do_Continue(self,node):

        raise StopIteration

    #@+node:ekr.20130318065046.9405: *5* fg.Delete
    # Delete(expr* targets)

    def do_Delete(self,node):

        for z in node.targets:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9406: *5* fg.ExceptHandler
    # ExceptHandler(expr? type, expr? name, stmt* body)

    def do_ExceptHandler(self,node):
        
        if node.type:
            for z in self.visit(node.type):
                yield z
        if node.name:
            for z in self.visit(node.name):
                yield z
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9407: *5* fg.Exec
    # Python 2.x only
    # Exec(expr body, expr? globals, expr? locals)

    def do_Exec(self,node):

        for z in self.visit(node.body):
            yield z
        if getattr(node,'globals',None):
            for z in self.visit(node.globals):
                yield z
        if getattr(node,'locals',None):
            for z in self.visit(node.locals):
                yield z
    #@+node:ekr.20130318065046.9408: *5* fg.For
    # For(expr target, expr iter, stmt* body, stmt* orelse)

    def do_For (self,node):

        for z in self.visit(node.target):
            yield z
        for z in self.visit(node.iter):
            yield z
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.orelse:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9409: *5* fg.FunctionDef
    # FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list)

    def do_FunctionDef (self,node):
        
        for z in self.visit(node.args):
            yield z
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.decorator_list:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9410: *5* fg.Global
    # Global(identifier* names)

    def do_Global(self,node):

        raise StopIteration
    #@+node:ekr.20130318065046.9411: *5* fg.If
    # If(expr test, stmt* body, stmt* orelse)

    def do_If(self,node):
        
        for z in self.visit(node.test):
            yield z
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.orelse:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9412: *5* fg.Import & ImportFrom
    # Import(alias* names)

    def do_Import(self,node):

        raise StopIteration

    # ImportFrom(identifier? module, alias* names, int? level)

    def do_ImportFrom(self,node):
        
        for z in node.names:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9312: *5* fg.Module
    def do_Module(self,node):
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9414: *5* fg.Pass
    def do_Pass(self,node):

        raise StopIteration

    #@+node:ekr.20130318065046.9415: *5* fg.Print
    # Python 2.x only
    # Print(expr? dest, expr* values, bool nl)
    def do_Print(self,node):

        if getattr(node,'dest',None):
            for z in self.visit(node.dest):
                yield z
        for z in node.values:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9416: *5* fg.Raise
    # Raise(expr? type, expr? inst, expr? tback)

    def do_Raise(self,node):
        
        if getattr(node,'type',None):
            for z in self.visit(node.type):
                yield z
        if getattr(node,'inst',None):
            for z in self.visit(node.inst):
                yield z
        if getattr(node,'tback',None):
            for z in self.visit(node.tback):
                yield z
    #@+node:ekr.20130318065046.9417: *5* fg.Return
    # Return(expr? value)

    def do_Return(self,node):
        
        if node.value:
            for z in self.visit(node.value):
                yield z
    #@+node:ekr.20130318065046.9418: *5* fg.TryExcept
    # TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)

    def do_TryExcept(self,node):
        
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.handlers:
            for z2 in self.visit(z):
                yield z2
        for z in node.orelse:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9419: *5* fg.TryFinally
    # TryFinally(stmt* body, stmt* finalbody)

    def do_TryFinally(self,node):

        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.finalbody:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9420: *5* fg.While
    # While(expr test, stmt* body, stmt* orelse)

    def do_While (self,node):

        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.orelse:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9421: *5* fg.With
    # With(expr context_expr, expr? optional_vars, stmt* body)

    def do_With (self,node):
        
        for z in self.visit(node.context_expr):
            yield z
        if node.optional_vars:
            for z in self.visit(node.optional_vars):
                yield z
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130318065046.9422: *5* fg.Yield
    #  Yield(expr? value)

    def do_Yield(self,node):

        if node.value:
            for z in self.visit(node.value):
                yield z