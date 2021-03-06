from src.typeclasses import *
from src.typechecking.basictypevariable import BasicTypeVariable

BASE_ADD_TYPES = BasicTypeVariable([List_Type(), Int_Type(), Float_Type(), String_Type(), Bytes_Type(), Bool_Type()])
BASE_SUB_TYPES = BasicTypeVariable([Int_Type(), Float_Type(), String_Type(), Bytes_Type(), Bool_Type()])
BASE_MULT_TYPES = BasicTypeVariable([List_Type(), Tuple_Type(), Int_Type(), Float_Type(), String_Type(), Bytes_Type(), Bool_Type()])
BASE_DIV_TYPES = BasicTypeVariable([List_Type(), Int_Type(), Float_Type(), String_Type(), Bool_Type()])
BASE_MOD_TYPES = BasicTypeVariable([List_Type(), Int_Type(), Float_Type(), String_Type(), Bool_Type()])
BASE_POW_TYPES = BasicTypeVariable([Int_Type(), Float_Type(), Bool_Type()])
BASE_BITAND_TYPES = BasicTypeVariable([Set_Type(), Int_Type(), Bool_Type()])
BASE_BITOR_TYPES = BasicTypeVariable([Set_Type(), Int_Type(), Bool_Type()])
BASE_BITXOR_TYPES = BasicTypeVariable([Set_Type(), Int_Type(), Bool_Type()])
BASE_RSHIFT_TYPES = BasicTypeVariable([Int_Type(), Bool_Type()])
BASE_LSHIFT_TYPES = BasicTypeVariable([Int_Type(), Bool_Type()])
BASE_FLOORDIV_TYPES = BasicTypeVariable([Int_Type(), Bool_Type(), Float_Type(), Bool_Type()])
        

# (left_type, right_type) -> return_type


ADD_DICT = { (Int_Type, Int_Type) : Int_Type,
             (Int_Type, Float_Type) : Float_Type,
             (Int_Type, Bool_Type) : Int_Type,
             (Float_Type, Int_Type) : Float_Type,
             (Float_Type, Float_Type) : Float_Type,
             (Float_Type, Bool_Type) : Float_Type,
             (String_Type, String_Type) : String_Type,
             (Bytes_Type, Bytes_Type) : Bytes_Type,
             (List_Type, List_Type) : List_Type,
             (Bool_Type, Int_Type) : Int_Type,
             (Bool_Type, Float_Type) : Float_Type,
             (Bool_Type, Bool_Type) : Int_Type,
            }
SUB_DICT = { (Int_Type, Int_Type) : Int_Type,
             (Int_Type, Float_Type) : Float_Type,
             (Int_Type, Bool_Type) : Int_Type,
             (Float_Type, Int_Type) : Float_Type,
             (Float_Type, Float_Type) : Float_Type,
             (Float_Type, Bool_Type) : Float_Type,
             (String_Type, String_Type) : String_Type,
             (Bytes_Type, Bytes_Type) : Bytes_Type,
             (Bool_Type, Int_Type) : Int_Type,
             (Bool_Type, Float_Type) : Float_Type,
             (Bool_Type, Bool_Type) : Int_Type,
            }
MULT_DICT = { (Int_Type, Int_Type) : Int_Type,
             (Int_Type, Float_Type) : Float_Type,
             (Int_Type, List_Type) : List_Type,
             (Int_Type, String_Type) : String_Type,
             (Int_Type, Tuple_Type) : Tuple_Type,
             (Int_Type, Bool_Type) : Int_Type,
             (Float_Type, Int_Type) : Float_Type,
             (Float_Type, Float_Type) : Float_Type,
             (Float_Type, Bool_Type) : Float_Type,
             (String_Type, Int_Type) : String_Type,
             (String_Type, Bool_Type) : String_Type,
             (Bytes_Type, Int_Type) : Bytes_Type,
             (List_Type, Int_Type) : List_Type,
             (List_Type, Bool_Type) : List_Type,
             (Tuple_Type, Int_Type) : Tuple_Type,
             (Tuple_Type, Bool_Type) : Tuple_Type,
             (Bool_Type, Int_Type) : Int_Type,
             (Bool_Type, Float_Type) : Float_Type,
             (Bool_Type, Bool_Type) : Int_Type,
             (Bool_Type, List_Type) : List_Type,
             (Bool_Type, String_Type) : String_Type,
             (Bool_Type, Tuple_Type) : Tuple_Type,
            }

DIV_DICT = { (Int_Type, Int_Type) : Int_Type,
             (Int_Type, Float_Type) : Float_Type,
             (Int_Type, List_Type) : List_Type,
             (Int_Type, String_Type) : String_Type,
             (Int_Type, Bool_Type) : Int_Type,
             (Float_Type, Int_Type) : Float_Type,
             (Float_Type, Float_Type) : Float_Type,
             (Float_Type, Bool_Type) : Float_Type,
             (List_Type, List_Type) : List_Type,
             (Bool_Type, Int_Type) : Int_Type,
             (Bool_Type, Float_Type) : Float_Type,
             (Bool_Type, Bool_Type) : Int_Type,
            }

MOD_DICT = { (Int_Type, Int_Type) : Int_Type,
             (Int_Type, Float_Type) : Float_Type,
             (Int_Type, Bool_Type) : Int_Type,
             (Float_Type, Int_Type) : Float_Type,
             (Float_Type, Float_Type) : Float_Type,
             (String_Type, Any_Type) : String_Type,
             (Bool_Type, Int_Type) : Int_Type,
             (Bool_Type, Float_Type) : Float_Type,
             (Bool_Type, Bool_Type) : Int_Type,
            }

POW_DICT = { (Int_Type, Int_Type) : Int_Type,
             (Int_Type, Float_Type) : Float_Type,
             (Int_Type, Bool_Type) : Int_Type,
             (Float_Type, Int_Type) : Float_Type,
             (Float_Type, Float_Type) : Float_Type,
             (Bool_Type, Int_Type) : Int_Type,
             (Bool_Type, Float_Type) : Float_Type,
             (Bool_Type, Bool_Type) : Int_Type,
            }

BITAND_DICT = { (Int_Type, Int_Type) : Int_Type,
                (Int_Type, Bool_Type) : Int_Type,
                (Bool_Type, Bool_Type) : Bool_Type,
                (Bool_Type, Int_Type) : Int_Type,
                (Set_Type, Set_Type) : Set_Type,
              }

BITOR_DICT = { (Int_Type, Int_Type) : Int_Type,
               (Int_Type, Bool_Type) : Int_Type,
               (Bool_Type, Bool_Type) : Bool_Type,
               (Bool_Type, Int_Type) : Int_Type,
               (Set_Type, Set_Type) : Set_Type,
             }
 
BITXOR_DICT = { (Int_Type, Int_Type) : Int_Type,
                (Int_Type, Bool_Type) : Int_Type,
                (Bool_Type, Bool_Type) : Bool_Type,
                (Bool_Type, Int_Type) : Int_Type,
                (Set_Type, Set_Type) : Set_Type,
              }

RSHIFT_DICT = { (Int_Type, Int_Type) : Int_Type,
                (Int_Type, Bool_Type) : Int_Type,
                (Bool_Type, Int_Type) : Int_Type,
                (Bool_Type, Bool_Type) : Int_Type,
              }

LSHIFT_DICT = { (Int_Type, Int_Type) : Int_Type,
                (Int_Type, Bool_Type) : Int_Type,
                (Bool_Type, Int_Type) : Int_Type,
                (Bool_Type, Bool_Type) : Int_Type,
              }

FLOORDIV_DICT = { (Int_Type, Int_Type) : Int_Type,
                  (Int_Type, Float_Type) : Float_Type,
                  (Int_Type, Bool_Type) : Int_Type,
                  (Float_Type, Int_Type) : Float_Type,
                  (Float_Type, Float_Type) : Float_Type,
                  (Float_Type, Bool_Type) : Float_Type,
                  (Bool_Type, Int_Type) : Int_Type,
                  (Bool_Type, Float_Type) : Float_Type,
                  (Bool_Type, Bool_Type) : Int_Type,
                }

OP_DICTS = {'Add' : ADD_DICT,
            'Sub' : SUB_DICT,
            'Mult' : MULT_DICT,
            'Div' : DIV_DICT,
            'Mod' : MOD_DICT,
            'Pow' : POW_DICT,
            'BitAnd' : BITAND_DICT,
            'BitOr' : BITOR_DICT,
            'BitXor' : BITXOR_DICT,
            'RShift' : RSHIFT_DICT,
            'LShift' : LSHIFT_DICT,
            'FloorDiv' : FLOORDIV_DICT
           }

OP_BASES = {'Add' : BASE_ADD_TYPES,
            'Sub' : BASE_SUB_TYPES,
            'Mult' : BASE_MULT_TYPES,
            'Div' : BASE_DIV_TYPES,
            'Mod' : BASE_MOD_TYPES,
            'Pow' : BASE_POW_TYPES,
            'BitAnd' : BASE_BITAND_TYPES,
            'BitOr' : BASE_BITOR_TYPES,
            'BitXor' : BASE_BITXOR_TYPES,
            'RShift' : BASE_RSHIFT_TYPES,
            'LShift' : BASE_LSHIFT_TYPES,
            'FloorDiv' : BASE_FLOORDIV_TYPES
           }

def get_left_return_types(op, left_type):
    ''' Takes a single left type and an op and returns all possible return types '''
    op_dict = OP_DICTS[op]
    possible_combos = [(x, y) for (x, y) in op_dict if x == left_type.__class__ or x == Any_Type]
    return_types = [op_dict[x]() for x in possible_combos]
    return set(return_types)

def get_right_return_types(op, right_type):
    ''' Takes a single right type and an op and returns all possible return
        types. '''
    op_dict = OP_DICTS[op]
    possible_combos = [(x, y) for (x, y) in op_dict if y == right_type.__class__ or y == Any_Type]
    return_types = [op_dict[x]() for x in possible_combos]
    return set(return_types)

def get_possible_right_types(op, left_type):
    op_dict = OP_DICTS[op]
    possible_rights = [y for (x, y) in op_dict if x == left_type.__class__ or x == Any_Type]
    return_types = [x() for x in possible_rights]
    return set(return_types)

def get_possible_left_types(op, right_type):
    op_dict = OP_DICTS[op]
    possible_lefts = [x for (x, y) in op_dict if y == right_type.__class__ or y == Any_Type]
    return_types = [x() for x in possible_lefts]
    return set(return_types)

def get_symmetrical_types(op):
    op_dict = OP_DICTS[op]
    possible_types = [x for (x, y) in op_dict if y == x or y == Any_Type or x == Any_Type]
    return_types = [x() for x in possible_types]
    return BasicTypeVariable(return_types)

def get_all_right_types(op, left_types):
    ''' Takes a number of left types and returns all possible right types. '''
    assert isinstance(left_types, BasicTypeVariable)
    return_types = set()
    for possible_type in left_types.get():
        return_types |= get_possible_right_types(op, possible_type)
    return BasicTypeVariable(list(return_types))
    
def get_all_left_types(op, right_types):
    ''' Takes a number of left types and returns all possible right types. '''
    assert isinstance(right_types, BasicTypeVariable)
    return_types = set()
    for possible_type in right_types.get():
        return_types |= get_possible_left_types(op, possible_type)
    return BasicTypeVariable(list(return_types))

def get_return_type(op, left_type, right_type):
    return_type = set()
    op_dict = OP_DICTS[op]
    if (left_type.__class__, right_type.__class__) in op_dict:
        r_type = op_dict[(left_type.__class__, right_type.__class__)]
        return_type.add(r_type())
    if (Any_Type, right_type.__class__) in op_dict:
        r_type = op_dict[(Any_Type, right_type.__class__)]
        return_type.add(r_type())
    if (left_type.__class__, Any_Type) in op_dict:
        r_type = op_dict[(left_type.__class__, Any_Type)]
        return_type.add(r_type())
    return return_type

def get_op_types(op):
    return OP_BASES[op]


print(get_all_left_types('Add', BasicTypeVariable([Int_Type(), Float_Type()])))