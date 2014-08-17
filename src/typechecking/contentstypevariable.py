from src.typechecking.basictypevariable import BasicTypeVariable

class ContentsTypeVariable( BasicTypeVariable):
    
    def __init__(self, types = []):
        assert isinstance(types, list)
        types = self.extract_types(types)
        super().__init__(list(types))
        
    def extract_types(self, to_extract):
        ''' We want to extract the contents from each one. '''
        extracted = set()
        for types_class in to_extract:
            extracted |= types_class.get_contents_types()
        return extracted
    
    def update_types(self, other):
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types(other.get())
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return False
        self.types |= extracted
        return True
        