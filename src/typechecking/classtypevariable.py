from src.typechecking.basictypevariable import BasicTypeVariable
from src.typechecking.setattrtypevariable import SetAttrTypeVariable
from src.binopconstraints import *
from src.typeclasses import Class_Type

class ClassTypeVariable(BasicTypeVariable):
    
    def __init__(self, base_classes, self_variables, name):
        ''' Base classes must be given in the correct order. '''
        self.base_classes = base_classes
        self.class_variables = {}
        # Contains all of the base classes which have a class type
        self.acceptable_base_classes = set()
        self.any_base_class = False
        
        self.initialise_vars(self_variables)
        self.class_type = Class_Type(name, self.class_variables)
        if self.any_base_class:
            self.class_type.set_any_base()
        
        super().__init__([self.class_type])
        
    def check_base_classes(self):
        return [base for base in self.base_classes if base not in self.acceptable_base_classes]
        
    def initialise_vars(self, self_variables):
        ''' Add the variables from the base classes in the correct order. '''
        for base_class in self.base_classes:
            assert isinstance(base_class, BasicTypeVariable)
            for possible_type in base_class:
                if possible_type == any_type:
                    # What the hell do I do here?
                    self.acceptable_base_classes.add(base_class)
                    self.any_base_class = True
                if isinstance(possible_type, Class_Type):
                    # If there is a clash, the first instance will be used
                    self.class_variables.update({k:v for k,v in possible_type.get_vars().items() if k not in self.class_variables})
                    self.acceptable_base_classes.add(base_class)
        # Add the self variables
        self.class_variables.update(self_variables)
                
    def check_new_vars(self, base_class):
         ''' Add any new global variables. '''
         assert isinstance(base_class, BasicTypeVariable)
         change = False
         for possible_type in base_class:
            if possible_type == any_type:
                    # What the hell do I do here?
                    self.acceptable_base_classes.add(base_class)
                    self.class_type.set_any_base()
                    # Only update change if we've not already seen a any
                    change = True if not self.any_base_class else change
                    self.any_base_class = True
            if isinstance(possible_type, Class_Type):
                # If there is a clash, the first instance will be used
                new_vars = {k:v for k,v in possible_type.get_vars().items() if k not in self.class_variables}
                if new_vars:
                    change = True
                self.class_variables.update(new_vars)
                self.acceptable_base_classes.add(base_class)
         return change
    
    def receive_update(self, other):
        ''' Can be updated by a base class. '''
        assert isinstance(other, BasicTypeVariable)
        if other in self.base_classes:
            new_vars = self.check_new_vars(other)
            if new_vars:
                self.update_all_dependents()