from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import Any_Type

class ArgTypeVariable(BasicTypeVariable):
    ''' Takes the intersection of the types in all possible uses. The type is
        any if the intersection is empty.
        self.types holds the argument type. '''
    def __init__(self):
        # Holds the types legal in each use case of the arg
        # We need to hold them to take the intersection
        self.arg_uses = set()
        
        super().__init__()
        # Needed in case it's never used
        self.types.add(Any_Type())
        
    def extract_types(self):
        ''' Take the intersection of type variables in arg_uses. '''
        uses_in_list = list(self.arg_uses)
        extracted = set()
        first_use = uses_in_list.pop()
        extracted |= first_use.get()
        for possible_use in uses_in_list:
            new_extracted = set()
            for possible_type in possible_use.get():
                intersection = any([x.kind == possible_type.kind for x in extracted])
                if intersection:
                    new_extracted.add(possible_type)
            extracted = new_extracted
        # Add any if intersection is empty
        if not extracted:
            extracted.add(Any_Type())
        return extracted
    
    def is_same_as_self(self, other):
        for possible_type in self.types:
            if not any([x.kind == possible_type.kind for x in other.get()]):
                return False
        for possible_type in other.get():
            if not any([x.kind == possible_type.kind for x in self.types]):
                return False
        return True
    
    def receive_update(self, other):
        ''' Can receive updates from its use cases.
             We don't want to check extracted is a subset of current types,
             but has changes since it can get smaller. '''
        assert isinstance(other, BasicTypeVariable)
        # Add it to the possible uses
        self.arg_uses.add(other)
        extracted = self.extract_types()
        if self.is_same_as_self(BasicTypeVariable(list(extracted))):
            return
        # Replace contents with extracted
        self.types.clear()
        self.types |= extracted
        self.update_all_dependents()
        
