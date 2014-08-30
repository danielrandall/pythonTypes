from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import Any_Type

class IterTypeVariable(BasicTypeVariable):
    
    def __init__(self, types = []):
        assert isinstance(types, list)

        super().__init__(list(types))
        
    def check_iter(self):
        return self.types
        
    def extract_types(self, to_extract):
        ''' We want to extract the contents from each one. '''
        assert isinstance(to_extract, BasicTypeVariable)
        extracted = set()
        for possible_type in to_extract.get():
                if possible_type.get_global_var("__iter__") or isinstance(possible_type, Any_Type):
                    extracted |= possible_type.get_contents_types()
        return extracted
    
    def update_types(self, other):
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types(other)
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return False
        self.types |= extracted
        return True
        
