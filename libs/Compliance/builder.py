import hierarchy, req_objects, tokenizer

'''
This is the object returned after a call to the build function.
It is populated with the given data structure, and ready to
evaluate against bugs. The current state of the model is cleared
before each bug run, so its state needs to be saved after each
bug using the get_messages (and get_errors?) functions.
'''
class Evaluator:
   def __init__(self, products):
      self.products = products
   
   def __repr__(self):
      return self.to_string()
   
   #New-line separate the calls to all products' to_string functions
   def to_string(self):
      build = ""
      for product in self.products:
         build += product.to_string() + "\n"
      return build.strip() + "\n"
   
   #Call the get-message method on all the products
   def get_messages(self):
      messages = []
      for product in self.products:
         messages += product.get_messages("root")
      return messages
   
   #Turns classes into more easily readable dictionaries
   def reduce(self):
      return [product.reduce() for product in self.products]
   
   #Returns an html-viewable version of the to_string method
   def html_string(self):
      build = self.to_string()
      build = build.replace("<", "&lt")
      build = build.replace(">", "&gt")
      build = build.replace("\n", "<br>")
      build = build.replace(" ", "&nbsp")
      return build
   
   #Evaluates a given bug against the built suite.
   #If testing is set to True, all module are run through, regardless
   #of the compilation/evaluation results of their parents.
   def evaluate(self, bug, testing = False):
      for product in self.products:
         product.clear()
         product.evaluate(bug, testing)
         

'''
Builds a single expression, with the option of adding some
variables. The expression can be evaluated against bugs, and
contains most of the same functions as the regular suite.
It is important to call .clear() on the expression before
each new bug evaluation because, unlike the full suit, the
single expression does not auto-clear before each call
to .evaluate()
'''
def build_expression(expression, variables = []):
   #If no expression, always evaluate to True
   condition = None
   if len(expression.strip()) == 0:
      condition = req_objects.AlwaysReturn(True)
      return condition
   
   #Handle exceptions created during expression compilation
   try:
      condition = tokenizer.tokenize(expression, variables)
   except Exception as e:
      #Expression can never evaluate to true if it did not compile
      condition = req_objects.AlwaysReturn(False)
      condition.error = e.args[0]

   return condition


#Creates the compliance suite from the DB products data structure
def build(data_structure):
   products = []
   for product in data_structure:
      products.append(make_group(product))
   return Evaluator(products)
   

#Used to recursively generate groups and their subgroups.
def make_group(data, variables = []):
   #Pass down variables from top-level groups to subgroups in the same scope
   if "variables" in data:
      #Variable over-write check
      problems = []
      for variable in data["variables"]:
         var_name = variable["name"]
         if any(var_name in old_var["name"] for old_var in variables):
            problem = "The variable @%s@ in the group %s overwrites another variable of the same name in a higher scope"
            problem = problem % (var_name, data["name"])
            problems.append(problem)
      
      #If variable overwrites were found
      if len(problems) > 0:
         #######Do something here?
         print problems
      
      #Now do the actual passing down
      variables += data["variables"]

   #Create the group object
   #(Expression evaluation occurs during __init__ of Group and Message objects)
   group = hierarchy.Group(data["name"], data["expression"], data["active"], data["description"], variables)
   
   #Populate its subgroups
   if "groups" in data:
      for sub in data["groups"]:
         group.groups.append(make_group(sub, variables))
         
   #Populate its messages
   if "messages" in data:
      for message in data["messages"]:
         group.messages.append(make_message(message, variables))
         
   #Return the created group to be added either in products,
   #Or as a subgroup of a group created by a previous call of this function.
   return group


#Creates and returns a Message object (Used to reduce screen clutter on the message append line)
def make_message(data, var_keys):
   return hierarchy.Message(data["name"], data["expression"], data["active"], data["description"], var_keys, data["message_type"])

