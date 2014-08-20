from src.typechecking.basictypevariable import BasicTypeVariable

class CallTypeVariable(BasicTypeVariable):
    ''' Must work for modules and classes.
        self.types represents the types the attribute can take '''
    def __init__(self, args):
        self.has_callable_type = False
        self.args = args
        super().__init__(list(output_types))
        
    def extract_types(self):
        extracted = set()
        for possible_type in self.value:
            if possible_type.is_callable():
                # Check all type match the necessary arg types
                self.callable_type = True
                extracted |= possible_type.get_return_types().types
        return extracted
    
    def receive_update(self, other):
        ''' Can receive updates from its identifier as well as the arg types. '''
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types()
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return
        self.types |= extracted
        self.update_all_dependents()