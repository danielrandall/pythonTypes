from src.typeclasses import None_Type, Any_Type, Int_Type

class ErrorIssuer():
    def __init__(self):
        self.issues = []
        
    def add_issue(self, issue):
        self.issues.append(issue)    
        
    def check_for_errors(self):
        for iss in self.issues:
            assert isinstance(iss, BaseIssue)
            iss.check()
    
    
class BaseIssue():
    def __init__(self, node, var, module_name):
        self.var_to_check = var
        self.node = node
        self.lineno = node.lineno
        self.module_name = module_name
        
    def check(self):
        ''' Override this. '''
        pass
    
class DefinedIssue(BaseIssue):
    ''' Ensure a variable has been initilised. '''
    pass
    
class CallIssue(BaseIssue):
    ''' Checks there is an acceptable call. '''
    def __init__(self, node, var, module_name):
        super().__init__(node, var, module_name)
    
    def check(self):
        if not self.var_to_check.check_callable():
            self.print_error()
            
    def print_error(self):
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": Cannot call variable: ")
    
class BaseClassIssue(BaseIssue):
    ''' Checks acceptable base classes. '''
    def __init__(self, node, var, module_name):
        super().__init__(node, var, module_name)
    
    def check(self):
        for base_class in self.var_to_check.check_base_classes():
            self.print_error(base_class)
        
    def print_error(self, base_class):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": Unacceptable base class: " + str(base_class))

class BinOpIssue(BaseIssue):
    ''' Checks acceptable binop combination. '''
    def __init__(self, node, var, module_name):
        super().__init__(node, var, module_name)
    
    def check(self):
        if not self.var_to_check.check_output():
            self.print_error()
        
    def print_error(self):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": Incompatible types for binary operation.")


class GetAttrIssue(BaseIssue):
    ''' Checks whether an attribute exists. '''
    def __init__(self, node, var, module_name, attr):
        super().__init__(node, var, module_name)
        self.attr = attr
    
    def check(self):
        if not self.var_to_check.check_output():
            self.print_error()
        
    def print_error(self):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": Cannot find attribute: " + self.attr)
        
class IteratorIssue(BaseIssue):
    ''' Checks whether the given type is an iterator. '''
    def __init__(self, node, var, module_name):
        super().__init__(node, var, module_name)
    
    def check(self):
        if not self.var_to_check.check_iter():
            self.print_error()
        
    def print_error(self):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": Not an iterator")
        
class IndexIssue(BaseIssue):
    ''' Checks whether the given type is an iterator. '''
    def __init__(self, node, var, module_name):
        super().__init__(node, var, module_name)
    
    def check(self):
        if not self.var_to_check.check_iter():
            self.print_error()
        
    def print_error(self):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": cannot be indexed")

class ContainsIssue(BaseIssue):
    ''' Checks whether the given type is an iterator. '''
    def __init__(self, node, var, module_name):
        super().__init__(node, var, module_name)
    
    def check(self):
        ''' This should be done in a type variable. '''
        for possible_type in self.var_to_check.get():
            if possible_type.get_global_var("__contains__") or isinstance(possible_type, Any_Type):
                return
        self.print_error()
        
    def print_error(self):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": cannot be searched for contents")
        
class UnaryIssue(BaseIssue):
    ''' Checks whether the given type is an int or a float. '''
    def __init__(self, node, var, module_name, op_kind):
        super().__init__(node, var, module_name)
        self.op_kind = op_kind
    
    def check(self):
        ''' This should be done in a type variable. '''
        if not self.var_to_check.check_output():
            self.print_error()
        
    def print_error(self):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": variable cannot be used with unary operator " + self.op_kind + ". Must be int or float.")
        
class SliceIssue(BaseIssue):
    def __init__(self, node, var, module_name):
        super().__init__(node, var, module_name)
    
    def check(self):
        ''' This should be done in a type variable. '''
        for possible_type in self.var_to_check.get():
            if isinstance(possible_type, Int_Type) or isinstance(possible_type, Any_Type):
                return
        self.print_error()
        
    def print_error(self):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": variable cannot be used in a slice. Must be int type")
        
class MustContainTypeIssue(BaseIssue):
    pass

class InitNoneIssue(BaseIssue):
    def __init__(self, node, var, module_name):
        super().__init__(node, var, module_name)
    
    def check(self):
        for possible_type in self.var_to_check.get():
            if not isinstance(possible_type, None_Type):
                self.print_error()
        
        
    def print_error(self):        
        print(self.module_name + ": " + "Line " + str(self.lineno) + ": __init__ should only return None")

