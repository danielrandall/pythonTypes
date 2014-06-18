import ast

class LocalStatementGenerator:
    
    def run(self,node):
        if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.Module)):
            # g.trace(node,node.body)
            for z in node.body:
                for z2 in self.visit(z):
                    yield z2
        else:
            assert isinstance(node,ast.Lambda),node.__class__.__name__
            for z in self.visit(node.body):
                yield z
                
    def default(self,node):
        raise StopIteration
            
    def visit(self,node):
        if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.Lambda)):
            yield node # These *are* part of the local statements.
            for z in node.body:
                for z2 in self.visit(z):
                    yield z2
        else:
            yield node
            method = getattr(self,'do_'+node.__class__.__name__,self.default)
            for z in method(node):
                yield z


    def do_ExceptHandler(self,node):

        for z in node.body:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130325220703.9738: *4* sg.For
    # For(expr target, expr iter, stmt* body, stmt* orelse)

    def do_For (self,node):

        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.orelse:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130325220703.9741: *4* sg.If
    # If(expr test, stmt* body, stmt* orelse)

    def do_If(self,node):
        
        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.orelse:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130325220703.9748: *4* sg.TryExcept
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
    #@+node:ekr.20130325220703.9749: *4* sg.TryFinally
    # TryFinally(stmt* body, stmt* finalbody)

    def do_TryFinally(self,node):

        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.finalbody:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130325220703.9750: *4* sg.While
    # While(expr test, stmt* body, stmt* orelse)

    def do_While (self,node):

        for z in node.body:
            for z2 in self.visit(z):
                yield z2
        for z in node.orelse:
            for z2 in self.visit(z):
                yield z2
    #@+node:ekr.20130325220703.9751: *4* sg.With
    # With(expr context_expr, expr? optional_vars, stmt* body)

    def do_With (self,node):

        for z in node.body:
            for z2 in self.visit(z):
                yield z2