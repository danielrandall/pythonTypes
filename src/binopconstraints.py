from src.typeclasses import *

BASE_ADD_TYPES = [List_Type(), int_type, float_type, string_type, bytes_type]
BASE_MOD_TYPES = [List_Type(), int_type, float_type, string_type]
BASE_POW_TYPES = [int_type, float_type]
BASE_BITAND_TYPES = [Set_Type(), int_type, bool_type]
BASE_BITOR_TYPES = [Set_Type(), int_type, bool_type]
BASE_RSHIFT = [int_type]
BASE_LSHIFT = [int_type]
BASE_FLOOR_DIV = [int_type, bool_type, float_type]
        
OP_TYPES = {
                'Add' : BASE_ADD_TYPES,
                'Mod' : BASE_MOD_TYPES
}
    
# Used when we have a concrete type and a parameter. It shows us which
# types can used in conjunction.
BIN_OP_CONSTRAINTS = {
        'Add' : { float_type : [float_type, int_type],
                  int_type  : [float_type, int_type],
                   List_Type : [List_Type()],
                  string_type : [string_type],
                  bytes_type : [bytes_type],
                  any_type: BASE_ADD_TYPES }, 
        'Mult' : { float_type : [float_type, int_type],
                   int_type : [float_type, int_type, List_Type(), string_type],
                   List_Type: [List_Type(), int_type],
                   bytes_type: [int_type],
                   string_type: [string_type, int_type] },
        'Sub' : { float_type : [float_type, int_type],
                  int_type : [float_type, int_type],
                  List_Type: [List_Type()],
                  string_type : [string_type] },   
        'Mod' : { float_type : [float_type, int_type],
                  int_type : [float_type, int_type],
                  List_Type: [List_Type()],
                  any_type: BASE_MOD_TYPES,
                  string_type: [any_type] },
        'Pow' : { float_type : [float_type, int_type],
                  int_type : [float_type, int_type],
                  any_type: BASE_POW_TYPES },
        'Div' : { float_type : [float_type, int_type],
                  int_type : [float_type, int_type],
                  List_Type: [List_Type()] },
                  string_type : [string_type],
        'BitAnd' : { int_type : [int_type],
                  bool_type : [bool_type],
                  Set_Type: [Set_Type()] ,
                  bool_type : [bool_type] },         
        'BitOr' : { int_type : [int_type],
                  bool_type : [bool_type],
                  Set_Type: [Set_Type()] ,
                  bool_type : [bool_type] },    
        'BitXor' : { int_type : [int_type],
                  bool_type : [bool_type],
                  Set_Type: [Set_Type()] ,
                  bool_type : [bool_type] },    
        'RShift' : { int_type : [int_type] },
        'LShift' : { int_type : [int_type] },
        'FloorDiv' : {bool_type: [bool_type, int_type, float_type],
                      int_type: [bool_type, int_type, float_type],
                      float_type: [bool_type, int_type, float_type] }
                      
        
}
