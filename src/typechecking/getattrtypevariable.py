from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import Class_Type, Any_Type, any_type

class GetAttrTypeVariable(BasicTypeVariable):
    ''' Must work for modules and classes.
        self.types represents the types the attribute can take '''
    def __init__(self, value, attr, node):
        try:
            assert isinstance(value, BasicTypeVariable)
        except:
            print(value)
            print(node.lineno)
        
        self.value = value
        self.attr = attr
        
        output_types = self.extract_types()
        super().__init__(list(output_types))
        
    def extract_types(self):
        extracted = set()
        for possible_type in self.value:
            if isinstance(possible_type, Any_Type):
                extracted.add(any_type)
            
            if isinstance(possible_type, Class_Type):
                has_attr = possible_type.get_global_var(self.attr)
                if has_attr:
                    extracted |= has_attr.types
        return extracted
    
    def receive_update(self, other):
        ''' Can only receive updates from its identifier.
            i.e. x in x.f '''
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types()
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return
        self.types |= extracted
        self.update_all_dependents()