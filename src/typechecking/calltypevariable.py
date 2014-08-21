from src.typechecking.basictypevariable import BasicTypeVariable

class CallTypeVariable(BasicTypeVariable):
    ''' Must work for modules and classes.
        self.types represents the types the attribute can take '''
    def __init__(self, args, node):
        self.lineno = node.lineno
        self.has_callable_type = False
        self.args = args
        
        super().__init__()
        
    def check_callable(self):
        return self.has_callable_type
        
    def extract_types(self, value):
        extracted = set()
        for possible_type in value:
            if possible_type.is_callable():
                # Check all type match the necessary arg types
                self.has_callable_type = True
                extracted |= possible_type.get_return_types().types
        return extracted
    
    def receive_update(self, other):
        ''' Can receive updates from its identifier as well as the arg types. '''
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types(other.get())
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return
        self.types |= extracted
        self.update_all_dependents()