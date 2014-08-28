class BasicTypeVariable:
    ''' This simulates a C style pointer to a set of types.
        This is a basic type variable. It is only capable of creating a simple
        subset constraint from variables '''
    
    def __init__(self, types = []):
        assert isinstance(types, list)
        self.types = set(types)
        self.constraint_dependents = set()

    def __str__(self):
        return self.types.__repr__()
    
    def __or__(self, other):
        ''' Implements self | other '''
        assert isinstance(other, BasicTypeVariable)
        return self.types | other.types
    
    def __ior__(self, other):
        ''' Implements self |= other '''
        assert isinstance(other, BasicTypeVariable)
        self.types |= other.types
        return self
        
    def __iter__(self):
        return iter(self.types)
    
    def __contains__(self, item):
        return item in self.types
    
    def get(self):
        return self.types
    
    def update_types(self, other):
        assert isinstance(other, BasicTypeVariable)
        if self.is_subset_of_self(other):
            return False
        self.types |= other.types
        return True
    
    def is_subset_of_self(self, other):
        assert isinstance(other, BasicTypeVariable)
        return other.types.issubset(self.types)
    
    def add_new_dependent(self, new_dependent):
        ''' Add the new dependent to the list and send it this variable's
            types. '''
        assert isinstance(new_dependent, BasicTypeVariable)
        self.constraint_dependents.add(new_dependent)
        self.update_dependent(new_dependent)
        
    def update_all_dependents(self):
        iterating_dependents = self.constraint_dependents.copy()
        for dependent in iterating_dependents:
            self.update_dependent(dependent)
        
    def update_dependent(self, dependent):
        dependent.receive_update(self)
    
    def receive_update(self, sender):
        ''' Receive the update and propagate it the dependents. '''
        assert isinstance(sender, BasicTypeVariable)
        any_change = self.update_types(sender)
        if any_change:
            self.update_all_dependents()
        
        
        
        
        
        
        
        
        