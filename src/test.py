'''
Created on 17 May 2014

@author: dr1810
'''
import src.statictypechecking as stc
import src.extractpysfromdirectory as file_extractor
from src.typechecking.typeinferrer import TypeInferrer
from src.typechecking.errorissuer import ErrorIssuer
from pprint import pprint


# Open source Python 3 projects to test on: https://pypi.python.org/pypi?%3Aaction=browse&c=533&show=all


if __name__ == '__main__':

  #  top_level = "/homes/dr1810/4thYear/individualProject/pythonTypes/"
    top_level = "/homes/dr1810/4thYear/individualProject/testFiles/realFiles/imdb-master"
    file_tree = file_extractor.get_pys(top_level)
    issuer = ErrorIssuer()
    ti = TypeInferrer(issuer)
    ti.run(file_tree) 
    issuer.check_for_errors()
    print("Finished type checking")