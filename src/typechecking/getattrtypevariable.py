from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import Class_Base, Any_Type, any_type

class GetAttrTypeVariable(BasicTypeVariable):
    ''' Must work for modules and classes.
        self.types represents the types the attribute can take '''
    def __init__(self, value, attr, node):
        assert isinstance(value, BasicTypeVariable)
        
        self.value = value
        self.attr = attr
        
        self.found_attributes = set()
        super().__init__()
        
        output_types = self.extract_class_attrs()
        
    def check_output(self):
        ''' We need the output types to not be empty.
            This signifies an acceptable combination. '''
        return self.types
        
    def extract_class_attrs(self):
        any_base = False
        extracted = set()
        new_dependents = set()
        for possible_type in self.value:
            if isinstance(possible_type, Any_Type):
                extracted.add(any_type)
                continue
            has_attr = possible_type.get_global_var(self.attr)
            if has_attr:
                # Need to add it in case this attribute updates as the
                # class will not update when a member changes
                self.found_attributes.add(has_attr)
                new_dependents.add(has_attr)
                #has_attr.add_new_dependent(self)
                extracted |= has_attr.types
            else:
                any_base = True if possible_type.has_any_base() else any_base
        for new_dep in new_dependents:
            new_dep.add_new_dependent(self)
        # If the attr hasn't been found but has any base then
        # it might be there but we can't see it! any_type
        if not extracted and any_base:
            extracted.add(any_type)
        return extracted
    
    def extract_from_attrs(self, other):
        extracted = other.types
        return extracted
    
    def receive_update(self, other):
        ''' Can only receive updates from its identifier.
            i.e. x in x.f '''
        assert isinstance(other, BasicTypeVariable)
        if other in self.found_attributes:
            extracted = self.extract_from_attrs(other)
        else:
            # From the class
            extracted = self.extract_class_attrs()
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return
        self.types |= extracted
        self.update_all_dependents()