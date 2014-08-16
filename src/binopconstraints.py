from src.typeclasses import *

BASE_ADD_TYPES = [List_Type(None, [], set()), int_type, float_type, string_type]
BASE_MOD_TYPES = [List_Type(None, [], set()), int_type, float_type, string_type]
        
OP_TYPES = {
                'Add' : BASE_ADD_TYPES,
                'Mod' : BASE_MOD_TYPES
}
    
# Used when we have a concrete type and a parameter. It shows us which
# types can used in conjunction.
BIN_OP_CONSTRAINTS = {
        'Add' : { float_type : [float_type, int_type],
                  int_type  : [float_type, int_type],
                   List_Type : [List_Type(None, [], set())],
                  string_type : [string_type],
                  any_type: BASE_ADD_TYPES}, 
        'Mult' : { float_type : [float_type, int_type],
                   int_type : [float_type, int_type, List_Type(None, [], set()), string_type],
                   List_Type: [List_Type(None, [], set()), int_type],
                   string_type: [string_type, int_type] },
        'Sub' : { float_type : [float_type, int_type],
                  int_type : [float_type, int_type],
                  List_Type: [List_Type(None, [], set())],
                  string_type : [string_type] },   
        'Mod' : { float_type : [float_type, int_type],
                  int_type : [float_type, int_type],
                  List_Type: [List_Type(None, [], set())],
                  any_type: BASE_MOD_TYPES,
                  string_type: [any_type]},
        'Div' : { float_type : [float_type, int_type],
                  int_type : [float_type, int_type],
                  List_Type: [List_Type(None, [], set())],
                  string_type : [string_type] }                            
}