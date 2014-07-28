from src.generators.nodegenerator import NodeGenerator
import ast
class LocalNodeGenerator(NodeGenerator):
    
    '''Same as NodeGenerator, but don't enter context nodes.'''
    
    def run(self,node):
        if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.Module)):
            for z in node.body:
                for z2 in self.visit(z):
                    yield z2
        elif isinstance(node,ast.Lambda):
            for z in self.visit(node.body):
                yield z
        else:
            # It *is* valid to visit the nodes of a non-context statement.
            for z in self.visit(node):
                yield z
    
    def do_ClassDef(self,node):
        raise StopIteration
    
    def do_FunctionDef(self,node):
        raise StopIteration
        
    def do_Lambda(self,node):
        raise StopIteration

    def do_Module(self,node):
        assert False,node
