import src.extractpysfromdirectory as file_extractor
from src.typechecking.typeinferrer import TypeInferrer
from src.typechecking.errorissuer import ErrorIssuer
from src.stats import Statistics
import timeit


# Open source Python 3 projects to test on: https://pypi.python.org/pypi?%3Aaction=browse&c=533&show=all


if __name__ == '__main__':

    top_level = "/homes/dr1810/4thYear/individualProject/testFiles/realFiles/Glances-2.0.1"
    
    start = timeit.default_timer()
    
    file_tree = file_extractor.get_pys(top_level)
    issuer = ErrorIssuer()
    stats  = Statistics()
    ti = TypeInferrer(issuer, stats)
    ti.run(file_tree)
    print("Statistics:")
    stats.print_stats() 
    print()
    print("Errors:")
    issuer.check_for_errors()
    
    print()
    print("Finished type checking")
    
    stop = timeit.default_timer()

    print(stop - start) 