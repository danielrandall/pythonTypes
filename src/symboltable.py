class SymbolTable:
    
    def __init__ (self,cx):
        self.cx = cx
        self.attrs_d = {}
            # Keys are attribute names.
            # Values are sets of contexts having that name.
        self.d = {} # Keys are names, values are type lists.
        self.defined = set() # Set of defined names.
        self.defined_attrs = set() # Set of defined attributes.
        self.ssa_d = {} # Keys are names, values are reaching lists.
    
    def __repr__ (self):
        return 'Symbol Table for %s\n' % self.cx
    
    __str__ = __repr__
    