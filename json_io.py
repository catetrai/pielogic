from flask import Flask, render_template, request, jsonify, json
from constropt_py import constropt, solve_linear_system

app = Flask(__name__)

# Set globals (TODO: integrate as class properties)
costs = [[1, 1, 1], [1, 1, 1], [1, 10, 1], [1, 1, 1]]
skills = [[1, 1, 1], [0, 1, 1], [1, 1, 1], [1, 1, 1]]

# Construct projEmplMap as list of dicts
# !!! TODO !!! each dict must be sorted alphabetically by empl username!
def get_init_data():
	projEmplDict = [
	{
		"0449": {
			"backend.jud": 10,
			"consult.jan": 0,
			"develop.joh": 120,
			"workstu.jil": 100
		}
	},
	{
		"0584": {
			"backend.jud": 0,
			"consult.jan": 100,
			"develop.joh": 100,
			"workstu.jil": 80
		}
	},
	{
		"9999": {
			"backend.jud": 50,
			"consult.jan": 100,
			"develop.joh": 70,
			"workstu.jil": 50
		}
	}]
	return projEmplDict


# Methods for dict <-> list conversion
def update_dict_from_list(mydict, mylist):
	proj = 0
	for obj in mydict:
		emp = 0
		for key in sorted(obj.values()[0].keys()):
			obj.values()[0][key] = mylist[emp][proj]
			emp += 1
		proj += 1
	return mydict

def create_list_from_dict(mydict):
	# List will be size (nEmpl,nProj)
	mylist = []
	for obj in mydict:
		mylist.append(obj.values()[0].values())
	return transpose_list(mylist)

def transpose_list(mylist):
	# Python FTW!!
	newlist = map(list, zip(*mylist))
	return newlist

def get_totals(mydict):
	# 'totals' is a list of lists with emplTotals and projTotals.
	mylist = create_list_from_dict(mydict)
	totals_empl = []
	for i in mylist:
		totals_empl.append(sum(i))
	totals_proj = []
	for j in transpose_list(mylist):
		totals_proj.append(sum(j))
	return [totals_empl, totals_proj]


# Create dataDict variable
dataDict = get_init_data()
totals = get_totals(dataDict)
print totals


# Render the HTML page
@app.route("/")
def output():
	projEmplDict = get_init_data()
	return render_template('index.html', initdata=projEmplDict)

# Send original data
@app.route("/reset_data", methods=['GET'])
def reset_data():
	projEmplDict = get_init_data()
	return json.dumps(projEmplDict)

# Get slided data and send solved linear system
@app.route('/slide_data', methods=['GET', 'POST'])
def slide_data():
	if request.method == 'POST':
		# Get current dict
		out = request.get_json()
		arrNew = out['arrNew']
		idx_selected = out['idx_selected']
		if skills[idx_selected[0]][idx_selected[1]]:
			dataList = solve_linear_system(transpose_list(arrNew), costs, skills, idx_selected, totals)
			# Update dict with new values from constropt
			print dataDict
			update_dict_from_list(dataDict, dataList)
			print dataDict
			return json.dumps(dataDict)
		else:
			return json.dumps([])



# Send optimized data
@app.route('/optimize_data', methods=['GET'])
def optimize_data():
	# Get current dict
	dataDict = get_init_data()
	# Convert dict to list to feed it to constropt
	emplproj = create_list_from_dict(dataDict)
	dataList = constropt(emplproj, costs, skills)
	# Update dict with new values from constropt
	update_dict_from_list(dataDict, dataList)
	print dataDict
	return json.dumps(dataDict)


if __name__ == "__main__":
	app.run(host='127.0.0.1', port=8090)