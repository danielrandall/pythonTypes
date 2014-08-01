from src.traversers.astbasetraverser import AstBaseTraverser
import ast
class AllStatementsTraverser(AstBaseTraverser):
        
    # def __init__(self):
        # AstBaseTraverser.__init__(self)

    #@+others
    #@+node:ekr.20130323113653.9641: *4* stat.run
    def run(self,node):

        # Only the top-level contexts visit their children.
        if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.Module)):
            for z in node.body:
                self.visit(z)
        elif isinstance(node,ast.Lamda):
            self.visit(node.body)
        else:
            g.trace(node)
            assert False,'(Statement_Traverser) node must be a context'
    #@+node:ekr.20130323113653.9642: *4* stat.visit & default_visitor
    def visit(self,node):

        assert isinstance(node,ast.AST),node.__class__.__name__
        method_name = 'do_' + node.__class__.__name__
        method = getattr(self,method_name,self.default_visitor)
        return method(node)

    def default_visitor(self,node):
        pass
    #@+node:ekr.20130323113653.9643: *4* stat.visitors
    # There are no visitors for context nodes.
    #@+node:ekr.20130323113653.9654: *5* stat.ClassDef
    # ClassDef(identifier name, expr* bases, stmt* body, expr* decorator_list)

    def do_ClassDef (self,node):

        # for z in node.bases:
            # self.visit(z)
        for z in node.body:
            self.visit(z)
        # for z in node.decorator_list:
            # self.visit(z)
    #@+node:ekr.20130323113653.9644: *5* stat.ExceptHandler
    # ExceptHandler(expr? type, expr? name, stmt* body)

    def do_ExceptHandler(self,node):

        for z in node.body:
            self.visit(z)
    #@+node:ekr.20130323113653.9645: *5* stat.For
    # For(expr target, expr iter, stmt* body, stmt* orelse)

    def do_For (self,tree):

        for z in tree.body:
            self.visit(z)
        for z in tree.orelse:
            self.visit(z)

    #@+node:ekr.20130323113653.9656: *5* stat.FunctionDef
    # FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list)

    def do_FunctionDef (self,node):
        
        # self.visit(node.args)
        for z in node.body:
            self.visit(z)
        # for z in node.decorator_list:
            # self.visit(z)

       
    #@+node:ekr.20130323113653.9647: *5* stat.If
    # If(expr test, stmt* body, stmt* orelse)

    def do_If(self,node):

        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
    #@+node:ekr.20130323113653.9660: *5* stat.Lambda
    # Lambda(arguments args, expr body)

    # Lambda is a statement for the purpose of contexts.

    def do_Lambda(self,node):
        pass
        # self.visit(node.args)
        # self.visit(node.body)
    #@+node:ekr.20130323113653.9658: *5* stat.Module
    def do_Module (self,node):
        
        for z in node.body:
            self.visit(z)
    #@+node:ekr.20130323113653.9648: *5* stat.TryExcept
    # TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)

    def do_TryExcept(self,node):
        
        for z in node.body:
            self.visit(z)
        for z in node.handlers:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
    #@+node:ekr.20130323113653.9649: *5* stat.TryFinally
    # TryFinally(stmt* body, stmt* finalbody)

    def do_TryFinally(self,node):

        for z in node.body:
            self.visit(z)
        for z in node.finalbody:
            self.visit(z)
    #@+node:ekr.20130323113653.9650: *5* stat.While
    # While(expr test, stmt* body, stmt* orelse)

    def do_While (self,node):

        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
    #@+node:ekr.20130323113653.9651: *5* stat.With
    # With(expr context_expr, expr? optional_vars, stmt* body)

    def do_With (self,node):

        for z in node.body:
            self.visit(z)
