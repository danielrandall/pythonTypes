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
        
    def check_output(self):
        ''' We need the output types to not be empty.
            This signifies an acceptable combination. '''
        return self.types
        
    def extract_types(self):
        any_base = False
        extracted = set()
        for possible_type in self.value:
            if isinstance(possible_type, Any_Type):
                extracted.add(any_type)
            if isinstance(possible_type, Class_Type):
                has_attr = possible_type.get_global_var(self.attr)
                if has_attr:
                    extracted |= has_attr.types
                else:
                    any_base = True if possible_type.has_any_base() else any_base
        # If the attr hasn't been found but has any base then
        # it might be there but we can't see it! any_type
        if not extracted and any_base:
            extracted.add(any_type)
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