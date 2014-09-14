from src.typechecking.basictypevariable import BasicTypeVariable
from src.typeclasses import *
import src.binopconstraints as binop_cons

class BinOpTypeVariable(BasicTypeVariable):
    ''' Represents a binary operation. The types must be given in the order
        left-right.
        self.types represents the types the binop can result in. '''
    def __init__(self, node, left, right, op, left_param, right_param):
        assert isinstance(left, BasicTypeVariable)
        assert isinstance(right, BasicTypeVariable)
        
        self.lineno = node.lineno
        self.left_types = left
        self.right_types = right
        self.op = op
        self.left_param = left_param
        self.right_param = right_param
        
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
                  
        self.infer_arguments()
        
        extracted = set()
        for left in left_ts:
            for right in right_ts:
                if isinstance(left, Any_Type) and isinstance(right, Any_Type):
                    extracted.add(Any_Type())
                    continue
                if isinstance(left, Any_Type):
                    extracted |= binop_cons.get_right_return_types(self.op, right)
                    continue
                if isinstance(right, Any_Type):
                    extracted |= binop_cons.get_left_return_types(self.op, left)
                    continue
                extracted |= binop_cons.get_return_type(self.op, left, right)
        return extracted
    
    def infer_arguments(self):
        ''' If function arguments are used in a binop then infer their possible
            types. '''
        # In this case the op dictates the types
        if self.left_types is self.right_types:
            binop_cons.get_symmetrical_types(self.op).add_new_dependent(self.left_types)
            return
        
        if self.left_param and self.right_param:
            binop_cons.get_op_types(self.op).add_new_dependent(self.left_types)
            binop_cons.get_op_types(self.op).add_new_dependent(self.right_types)
            return
        
        # Check there's one
        if self.right_param:
            binop_cons.get_all_right_types(self.op, self.left_types).add_new_dependent(self.right_types)
            return
        
        if self.left_param:
            binop_cons.get_all_left_types(self.op, self.right_types).add_new_dependent(self.left_types)
            return
    
    def update_types(self, other):
        assert isinstance(other, BasicTypeVariable)
        extracted = self.extract_types()
        if self.is_subset_of_self(BasicTypeVariable(list(extracted))):
            return False
        self.types |= extracted
        return True
        