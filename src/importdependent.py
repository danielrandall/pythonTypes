class ImportDependent(object):

    def __init__(self, name, import_from, as_name):
        self.name = name
        self.import_from = import_from
        self.as_name = as_name
        
    def convert_to_directories(self):
        return self.name.replace('.', '/')
        
    def get_module_name(self):
        ''' Returns only the module name in a string.
            e.g. "a.b.c" -> "c" '''
        split_string = self.name.split('.')
        return split_string.pop()
    
    def get_as_name(self):
        ''' If no asname is specified then it is just the name '''
        return self.as_name if self.as_name else self.name
    
    def get_directory_no_name(self):
        converted = self.convert_to_directories()
        name = self.get_module_name()
        # We want to remove the last '/' as well
        return converted[:converted.rfind(name) - 1]        