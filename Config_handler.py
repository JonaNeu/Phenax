import configparser

class Config_handler(): 

    def __init__(self, config_path):
        self.config_path = config_path

        self.parser = configparser.ConfigParser()
        self.parser.read(self.config_path)

     
    def get_max_runs(self):
        return self.parser.get('branchexp', 'max_runs')   

    def get_runner(self):
        return self.parser.get('branchexp', 'run_type') 

    def get_output_dir(self):
        return self.parser.get('branchexp', 'output_dir')

    def get_device_IP(self):
        return self.parser.get('branchexp', 'device')
        

    # new_may_runs has to be a string
    def set_max_runs(self, new_max_runs="5"):
        self.parser.set('branchexp', 'max_runs', new_max_runs)
        with open(self.config_path, 'w') as configfile:
            self.parser.write(configfile)

    def set_runner(self, new_runner="grodd"):
        self.parser.set('branchexp', 'run_type', new_runner)
        with open(self.config_path, 'w') as configfile:
            self.parser.write(configfile)

    def set_output_dir(self, new_output_dir):
        self.parser.set('branchexp', 'output_dir', new_output_dir)
        with open(self.config_path, 'w') as configfile:
            self.parser.write(configfile)

    def set_device_IP(self, IP):
        self.parser.set('branchexp', 'device', IP)
        with open(self.config_path, 'w') as configfile:
            self.parser.write(configfile)




#######################################
# Testing
# #####################################
# test = Config_handler("/Users/jonaneumeier/Dropbox/Uni/6. Semester/Bachelor-thesis/bachelor_code/grodd_new_version/BranchExplorer/branchexp/configTest.ini")

# print("FIRST")
# print(test.get_max_runs())
# test.set_max_runs('10')
# print(test.get_max_runs())

# print("SECOND")
# print(test.get_runner())
# test.set_runner('monkey')
# print(test.get_runner())

# print("THIRD")
# print(test.get_output_dir())
# test.set_output_dir('../test')
# print(test.get_output_dir())





