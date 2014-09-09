class Statistics():
    def __init__(self):
        self.num_modules = 0
        self.num_classes = 0
        self.num_funcs = 0
        self.num_func_calls = 0
        self.num_binops = 0
        
    def inc_num_modules(self):
        self.num_modules += 1
        
    def inc_num_classes(self):
        self.num_classes += 1 

    def inc_num_funcs(self):
        self.num_funcs += 1 
        
    def inc_num_func_calls(self):
        self.num_func_calls += 1 
    
    def inc_num_binops(self):
        self.num_binops += 1 
        
    def print_stats(self):
        print("Number of modules: " + str(self.num_modules))
        print("Number of classes: " + str(self.num_classes))
        print("Number of functions: " + str(self.num_funcs))
        print("Number of function calls: " + str(self.num_func_calls))
        print("Number of binops: " + str(self.num_binops))