import simplejson, builder, pprint, os


f = open("suite.txt")
data_structure = simplejson.loads("\n".join(f.readlines()))
f.close()

f = open("results.txt")
bug = simplejson.loads("\n".join(f.readlines()))["bugs"][0]
f.close()

suite = builder.build(data_structure)
suite.evaluate(bug, True)

print suite
#print suite
#pprint.pprint(suite.get_messages())
