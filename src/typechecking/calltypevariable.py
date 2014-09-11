from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import Any_Type, Class_Type, Def_Type
from itertools import product

class CallTypeVariable(BasicTypeVariable):
    ''' Must work for modules and classes.
        self.types represents the types the function call can return.
        
        If type is a class def then check __init__
        If function - obvious
        If class instance - call '''
    def __init__(self, args, node, function_ident, fun_args):
        self.lineno = node.lineno
        self.has_callable_type = False
        self.args = args
        self.function_ident = function_ident
        self.fun_args = fun_args
        
        super().__init__()
        
    def check_callable(self):
        return self.has_callable_type
        
    def extract_types(self):
        value = self.function_ident
        extracted = set()
        for possible_type in value:
            if possible_type.is_callable():
                # Check all given types match the necessary arg types
                if isinstance(possible_type, Class_Type):
                    self.has_callable_type = True
                    extracted |= possible_type.get_return_types().types
                    continue
                if self.check_parameter_types(possible_type):
                    self.has_callable_type = True
                    extracted |= possible_type.get_return_types().types
        return extracted
    
    def check_parameter_types(self, candidate_function):
        ''' Returns whether there is an acceptable combination of arguments. '''
        if isinstance(candidate_function, Any_Type):
            return True
        if not isinstance(candidate_function, Def_Type):
            return True
        # We do not check the parameter types for kwarg/vaarg
        if candidate_function.get_is_kwarg():
            return True
        
        default_length = candidate_function.get_default_length()
        parameter_types = candidate_function.get_parameter_types()
        
        # Not enough args or too many args
        if len(self.args) < len(parameter_types) - default_length or \
        len(self.args) > len(parameter_types):
            return False
        
        given_params_and_types = []
        for i in range(len(self.args)):
            # Check if given arg is a function parameter
            if self.args[i] in self.fun_args:
                given_params_and_types.append((self.args[i], parameter_types[i]))
                continue
            given_arg = self.args[i].get()
            accepted_types = parameter_types[i].get()
            # If either are any_type then it succeeds
            if any([isinstance(arg, Any_Type) for arg in given_arg | accepted_types]):
                continue
            if any([x <= y for x, y in product(given_arg, accepted_types)]):
                continue
            return False
        # All other arguments are acceptable so assign types to any function parameters
        for given_param, accepted_types in given_params_and_types:
            accepted_types.add_new_dependent(given_param)
        return True
                
        
    
    def receive_update(self, other):
        ''' Can receive updates from its identifier as well as the arg types. Doesn't matter which '''
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types()
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return
        self.types |= extracted
        self.update_all_dependents()