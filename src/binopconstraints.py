from src.typeclasses import *

BASE_ADD_TYPES = [List_Type(), int_type, float_type, string_type, bytes_type]
BASE_MOD_TYPES = [List_Type(), int_type, float_type, string_type]
BASE_POW_TYPES = [int_type, float_type]
BASE_BITAND_TYPES = [Set_Type(), int_type, bool_type]
BASE_BITOR_TYPES = [Set_Type(), int_type, bool_type]
BASE_RSHIFT = [int_type]
BASE_LSHIFT = [int_type]
BASE_FLOOR_DIV = [int_type, bool_type, float_type]
        

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
             (List_Type, List_Type) : List_Type,
             (Bool_Type, Int_Type) : Int_Type,
             (Bool_Type, Float_Type) : Float_Type,
             (Bool_Type, Bool_Type) : Int_Type,
            }
MULT_DICT = { (Int_Type, Int_Type) : Int_Type,
             (Int_Type, Float_Type) : Float_Type,
             (Int_Type, List_Type) : List_Type,
             (Int_Type, String_Type) : String_Type,
             (Int_Type, Bool_Type) : Int_Type,
             (Float_Type, Int_Type) : Float_Type,
             (Float_Type, Float_Type) : Float_Type,
             (Float_Type, Bool_Type) : Float_Type,
             (String_Type, String_Type) : String_Type,
             (String_Type, Int_Type) : String_Type,
             (Bytes_Type, Int_Type) : Bytes_Type,
             (List_Type, List_Type) : List_Type,
             (List_Type, Int_Type) : List_Type,
             (Bool_Type, Int_Type) : Int_Type,
             (Bool_Type, Float_Type) : Float_Type,
             (Bool_Type, Bool_Type) : Int_Type,
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

def get_left_return_types(op, left_type):
    op_dict = OP_DICTS[op]
    possible_combos = [(x, y) for (x, y) in op_dict if x == left_type.__class__ or x == Any_Type]
    return_types = [op_dict[x]() for x in possible_combos]
    return set(return_types)

def get_right_return_types(op, right_type):
    op_dict = OP_DICTS[op]
    possible_combos = [(x, y) for (x, y) in op_dict if y == right_type.__class__ or y == Any_Type]
    return_types = [op_dict[x]() for x in possible_combos]
    return set(return_types)

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
    pass

print(get_return_type('Add', int_type, float_type))
