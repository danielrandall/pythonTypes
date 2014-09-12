from src.typechecking.basictypevariable import BasicTypeVariable
from src.typechecking.setattrtypevariable import SetAttrTypeVariable
from src.binopconstraints import *
from src.typeclasses import Class_Type, ITERATOR_TYPES

class ClassTypeVariable(BasicTypeVariable):
    
    ''' TODO: Combine two functions into one. '''
    
    def __init__(self, base_classes, self_variables, name):
        ''' Base classes must be given in the correct order. '''
        self.base_classes = base_classes
        self.class_variables = {}
        # Contains all of the base classes which have a class type
        self.acceptable_base_classes = set()
        self.any_base_class = False
        self.found_special_methods = set()
        
        self.initialise_vars(self_variables)
        self.class_type = Class_Type(name, self.class_variables)
        if self.any_base_class:
            self.class_type.set_any_base()
        
        super().__init__([self.class_type])
        
        self.add_special_class_types()
        
    def check_base_classes(self):
        return [base for base in self.base_classes if base not in self.acceptable_base_classes]
        
    def initialise_vars(self, self_variables):
        ''' Add the variables from the base classes in the correct order. '''
        for base_class in self.base_classes:
            assert isinstance(base_class, BasicTypeVariable)
            for possible_type in base_class:
                if isinstance(possible_type, Any_Type):
                    # What the hell do I do here?
                    self.acceptable_base_classes.add(base_class)
                    self.any_base_class = True
                if isinstance(possible_type, Class_Base):
                    # If base class has any_base then so do we
                    if possible_type.has_any_base():
                        self.any_base_class = True
                        change = True
                    
                    # If there is a clash, the first instance will be used
                    self.class_variables.update({k:v for k,v in possible_type.get_vars().items() if k not in self.class_variables})
                    self.acceptable_base_classes.add(base_class)
        # Add the self variables
        self.class_variables.update(self_variables)
                
    def check_new_vars(self, base_class):
         ''' Add any new global variables.
             The __init__ function is not inherited. '''
         assert isinstance(base_class, BasicTypeVariable)
         change = False
         for possible_type in base_class:
            if isinstance(possible_type, Any_Type):
                    # What the hell do I do here?
                    self.acceptable_base_classes.add(base_class)
                    self.class_type.set_any_base()
                    # Only update change if we've not already seen a any
                    change = True if not self.any_base_class else change
                    self.any_base_class = True
            if isinstance(possible_type, Class_Base):
                # If base class has any_base then so do we
                if possible_type.has_any_base():
                    self.any_base_class = True
                    change = True
                    
                # If there is a clash, the first instance will be used
                new_vars = {k:v for k,v in possible_type.get_vars().items() if k not in self.class_variables}
                
                # If there's a clash, share the types except for __init__!
                shared_keys = [k for k,_ in possible_type.get_vars().items() if k in self.class_variables and k != "__init__"]
                for k in shared_keys:
                    their_shared_var = possible_type.get_vars()[k]
                    this_shared_var = self.class_variables[k]
                    their_shared_var.add_new_dependent(this_shared_var)
                    this_shared_var.add_new_dependent(their_shared_var)
                
                if new_vars:
                    change = True
                self.class_variables.update(new_vars)
                self.acceptable_base_classes.add(base_class)
         return change
     
    def add_special_class_types(self):
        ''' For things like __iter__ '''
        if self.class_type.get_global_var("__iter__") and "__iter__" not in self.found_special_methods:
            # send type to iterators
            self.add_new_dependent(ITERATOR_TYPES)
            self.found_special_methods.add("__iter__")
        # Add it to set of all index types
        if self.class_type.get_global_var("__getitem__") and "__getitem__" not in self.found_special_methods:
            self.add_new_dependent(INDEX_TYPES)
            self.found_special_methods.add("__getitem__")
        # contains
        if self.class_type.get_global_var("__contains__") and "__contains__" not in self.found_special_methods:
            self.add_new_dependent(INDEX_TYPES)
            self.found_special_methods.add("__contains__")
    
    def receive_update(self, other):
        ''' Can be updated by a base class. '''
        assert isinstance(other, BasicTypeVariable)
        if other in self.base_classes:
            new_vars = self.check_new_vars(other)
            if new_vars:
                self.update_all_dependents()
                # Add special stuff for magic methods
                self.add_special_class_types()