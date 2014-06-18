import ast
from astbasetraverser import AstBaseTraverser
class StatementTraverser(AstBaseTraverser):
        
    # def __init__(self):
        # AstBaseTraverser.__init__(self)

    #@+others
    #@+node:ekr.20130322134737.9553: *4* stat.run
    def run(self,node):

        # Only the top-level contexts visit their children.
        if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.Module)):
            for z in node.body:
                self.visit(z)
        elif isinstance(node,ast.Lamda):
            self.visit(node.body)
        else:
            assert False,'(Statement_Traverser) node must be a context'
    #@+node:ekr.20130317115148.9414: *4* stat.visit & default_visitor
    def visit(self,node):

        assert isinstance(node,ast.AST),node.__class__.__name__
        method_name = 'do_' + node.__class__.__name__
        method = getattr(self,method_name,self.default_visitor)
        return method(node)

    def default_visitor(self,node):
        pass
    #@+node:ekr.20130317115148.9416: *4* stat.visitors
    # There are no visitors for context nodes.
    #@+node:ekr.20130317115148.9394: *5* stat.ExceptHandler
    # ExceptHandler(expr? type, expr? name, stmt* body)

    def do_ExceptHandler(self,node):

        for z in node.body:
            self.visit(z)
    #@+node:ekr.20130317115148.9396: *5* stat.For
    # For(expr target, expr iter, stmt* body, stmt* orelse)

    def do_For (self,tree):

        for z in tree.body:
            self.visit(z)
        for z in tree.orelse:
            self.visit(z)

    #@+node:ekr.20130317115148.9399: *5* stat.If
    # If(expr test, stmt* body, stmt* orelse)

    def do_If(self,node):

        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
    #@+node:ekr.20130317115148.9406: *5* stat.TryExcept
    # TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)

    def do_TryExcept(self,node):
        
        for z in node.body:
            self.visit(z)
        for z in node.handlers:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
    #@+node:ekr.20130317115148.9407: *5* stat.TryFinally
    # TryFinally(stmt* body, stmt* finalbody)

    def do_TryFinally(self,node):

        for z in node.body:
            self.visit(z)
        for z in node.finalbody:
            self.visit(z)
    #@+node:ekr.20130317115148.9408: *5* stat.While
    # While(expr test, stmt* body, stmt* orelse)

    def do_While (self,node):

        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)

    def do_With (self,node):

        for z in node.body:
            self.visit(z)