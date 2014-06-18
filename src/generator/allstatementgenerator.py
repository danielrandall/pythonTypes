from allstatementstraverser import AllStatementsTraverser
import ast
class AllStatementsPseudoGenerator(AllStatementsTraverser):
    
    # def __init__(self,node):
        # Statement_Traverser.__init__(self)
        
    def __call__(self,node):
        return self.run(node)
       
    def run(self,node):
        self.result = []
        if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.Module)):
            for z in node.body:
                self.visit(z)
            return self.result
        elif isinstance(node,ast.Lambda):
            self.result = []
            self.visit(node.body)
        else:
            assert False,node
        return self.result
        
    def default_visitor(self,node):
        pass

    def visit(self,node):
        assert isinstance(node,ast.AST),node.__class__.__name__
        method_name = 'do_' + node.__class__.__name__
        method = getattr(self,method_name,self.default_visitor)
        self.result.append(node)
        method(node)