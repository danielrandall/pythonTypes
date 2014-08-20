from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import *
import src.binopconstraints as binop_cons

class BinOpTypeVariable(BasicTypeVariable):
    ''' Represents a binary operation. The types must be given in the order
        left-right.
        self.types represents the types the binop can result in. '''
    def __init__(self, node, left, right, op):
        assert isinstance(left, BasicTypeVariable)
        assert isinstance(right, BasicTypeVariable)
        
        self.lineno = node.lineno
        self.left_types = left
        self.right_types = right
        self.op = op
        
        output_types = self.extract_types()
        super().__init__(list(output_types))
        
    def check_output(self):
        ''' We need the output types to not be empty.
            This signifies an acceptable combination. '''
        return self.types
        
    def extract_types(self):
        ''' Check all possible combinations. '''
        left_ts = self.left_types.get()
        right_ts = self.right_types.get()
        
        # If any or empty then we can't do anything
        if len(left_ts) == 0 or len(right_ts) == 0:
            return set()
        
        extracted = set()
        for left in left_ts:
            for right in right_ts:
                if isinstance(left, Any_Type) and isinstance(right, Any_Type):
                    extracted |= set([any_type])
                    continue
                if isinstance(left, Any_Type):
                    extracted |= binop_cons.get_right_return_types(self.op, right)
                    continue
                if isinstance(right, Any_Type):
                    extracted |= binop_cons.get_left_return_types(self.op, left)
                    continue
                extracted |= binop_cons.get_return_type(self.op, left, right)
        return extracted
    
    def update_types(self, other):
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types()
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return False
        self.types |= extracted
        return True
        