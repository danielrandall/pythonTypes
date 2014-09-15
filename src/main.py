import src.extractpysfromdirectory as file_extractor
from src.typechecking.typeinferrer import TypeInferrer
from src.typechecking.errorissuer import ErrorIssuer
from src.stats import Statistics
from src.traversers.printtypes import Print_Types
from src.typechecking.basictypevariable import BasicTypeVariable
from src.typechecking.argtypevariable import ArgTypeVariable
from src.typeclasses import Int_Type, Float_Type, String_Type

import timeit
import sys

# Open source Python 3 projects to test on: https://pypi.python.org/pypi?%3Aaction=browse&c=533&show=all


if __name__ == '__main__':
    
  #  arg_type = ArgTypeVariable()
  #  arg_type.arg_uses.add(BasicTypeVariable([Int_Type(), Float_Type(), String_Type()]))
  #  arg_type.arg_uses.add(BasicTypeVariable([Int_Type(), String_Type()]))
  #  extracted = arg_type.extract_types()
  #  arg_type.is_same_as_self(BasicTypeVariable(list(extracted)))
  #  arg_type.types |= extracted
  #  arg_type.arg_uses.add(BasicTypeVariable([Int_Type()]))

   # extracted = arg_type.extract_types()
   # arg_type.is_same_as_self(BasicTypeVariable(list(extracted)))
   # assert(False)
   
    print(sys.argv)
    assert len(sys.argv) == 2, "Enter only one directory."
    top_level = sys.argv[1]

    
    #top_level = "/homes/dr1810/4thYear/individualProject/demos/demo4"
 #   top_level = "/homes/dr1810/4thYear/individualProject/testFiles/realFiles/a"
    
    start = timeit.default_timer()
    
    file_tree = file_extractor.get_pys(top_level)
    issuer = ErrorIssuer()
    stats  = Statistics()
    ti = TypeInferrer(issuer, stats)
    ti.run(file_tree)
    print("Statistics:")
    stats.print_stats() 
    print()
    print("Inferred Types:")
    type_printer = Print_Types()
    type_printer.run(file_tree)
    print()
    print("Errors:")
    issuer.check_for_errors()
    
    print()
    print("Finished type checking")
    
    stop = timeit.default_timer()

    print(stop - start) 