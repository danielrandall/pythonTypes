class ErrorChecker(object):
    '''
    Checks whether the types are correct.
    Normally this boils down to checking that the node outputs a type.
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.types_to_check = []
             
    def add_type(self, new_type):
        self.types_to_check.append(new_type)   
        
    def check_types(self):
        pass
        