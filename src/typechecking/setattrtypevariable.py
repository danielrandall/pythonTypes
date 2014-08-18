from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import Class_Type

class SetAttrTypeVariable(BasicTypeVariable):
    ''' Must work for modules and classes.
        self.types represents the types the attribute assigns.
        
        This class adds its own dependents '''
    def __init__(self, value, attr):
        assert isinstance(value, BasicTypeVariable)
        
        self.value = value
        self.attr = attr
        super().__init__()
        
    def find_new_dependents(self):
        dependents = set()
        for possible_type in self.value:
            if isinstance(possible_type, Class_Type):
                # Doesn't have the var yet, create a new type var for it
                if self.attr not in possible_type.get_vars():
                    new_dependent = BasicTypeVariable()
                    possible_type.set_var(self.attr, new_dependent)
                else:
                    new_dependent = possible_type.get_var(self.attr)
                if new_dependent not in self.constraint_dependents:
                    dependents.add(new_dependent)
        return dependents
    
    def get_attr(self):
        return self.attr
        
    def receive_update(self, sender):
        ''' Can receive updates from the types it receives and the class
            identifier '''
        assert isinstance(sender, BasicTypeVariable)
        # Receiving from class identifier - find new classes it can be
        if sender == self.value:
            new_dependents = self.find_new_dependents()
            self.constraint_dependents |= new_dependents
            for new_dep in new_dependents:
                self.update_dependent(new_dep)
            return 
        # Otherwise from types
        any_change = self.update_types(sender)
        if any_change:
            self.update_all_dependents()