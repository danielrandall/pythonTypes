from src.typechecking.basictypevariable import BasicTypeVariable
from src.binopconstraints import *

class BinOpTypeVariable(BasicTypeVariable):
    ''' Represents a binary operation. The types must be given in the order
        left-right.
        self.types represents the types the binop can result in. '''
    def __init__(self, left, right, op):
        assert isinstance(left, BasicTypeVariable)
        assert isinstance(right, BasicTypeVariable)
        
        self.left_types = left
        self.right_types = right
        self.op = op
        
        output_types = self.extract_types()
        super().__init__(list(output_types))
        
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
                ''' TODO: do this better | check the type is acceptable
                    TODO: List types less explicitly'''
                if isinstance(left, Any_Type) and isinstance(right, Any_Type):
                    extracted.add(any_type)
                    continue
                if isinstance(left, Any_Type):
                    extracted |= set(BIN_OP_CONSTRAINTS[self.op][List_Type if isinstance(right, List_Type) else right])
                    continue
                if isinstance(right, Any_Type):
                    extracted |= set(BIN_OP_CONSTRAINTS[self.op][List_Type if isinstance(left, List_Type) else left])
                    continue

                if isinstance(left, Num_Type) and isinstance(right, Num_Type):
                    # Doesn't matter what the op is
                    if right <= float_type or left <= float_type:
                        extracted.add(float_type)
                        continue
                    else:
                        extracted.add(int_type)
                        continue
                    
                if isinstance(left, List_Type) and isinstance(right, List_Type) and self.op == 'Add':
                    extracted.add(List_Type())
                    continue
                
                if self.op == 'Mult' and isinstance(left, List_Type) and right <= int_type:
                    extracted.add(left)
                    continue
                
                if left <= string_type and right <= string_type and self.op == 'Add':
                    extracted.add(string_type)
                    continue
                
                if left <= string_type and self.op == 'Mod':
                    # String mod anything is a string, so long as there's stuff to format
                    extracted.add(string_type)
                    continue
                
                if self.op == 'Mult' and (
                        (left <= string_type and right <= int_type) or
                        (left <= int_type and right <= string_type)):
                    extracted.add(string_type)
                    continue
        return extracted
    
    def update_types(self, other):
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types()
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return False
        self.types |= extracted
        return True
        