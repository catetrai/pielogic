Playground for Flask, D3.js, and optimization problems

### Installation
#### Run in Python virtual environment
1. Install the python3-venv package: sudo apt-get install python3-venv
2. Clone and cd to this repo
3. Create a virtual environment: `python3 -m venv .`
4. Activate the virtual environment: `source ./bin/activate`
5. Install dependencies: `pip install -r requirements.txt` 
6. Set environment variable with name of app file: `export FLASK_APP=main.py`
7. Run Flask development server: `flask run`
8. Go to `http://localhost:5000/`

#### Run in Docker container
1. Clone and cd to this repo
2. Build image from Dockerfile (warning: it's 1.2GB): `docker build -t pielogic ./`
3. Run container: `sudo docker run -d --name pielogic -p 5000:5000 -e PORT="5000" pielogic`
4. Go to `http://<docker-host>:5000/`

### Problem formulation
The data consists of units of work (mandays/Persontage, PT) assigned to each employee in each project. We can represent this as a 2-d matrix of size #employees x #projects, which includes all employees and all projects (values will be 0 for employees not working in a project). We'll call this the EP matrix.

Two user operations are supported:

* Sliding: the user changes the value of one employee's PT in one project (i.e. an element in the EP matrix) by using the range slider. Because the employee's total available mandays are fixed, other values of the matrix should be automatically scaled to accommodate the change.
* Optimizing: the EP matrix is recalculated from scratch to satisfy an optimality criterion, defined by the user (e.g. minimize total costs). This is a one-shot operation performed by the user with a button click.

All operations obey the following constraints:

* EP matrix values must be non-negative: 0 where the employee is not working the project, and strictly >0 where the employee is working in the project.
* Both marginal totals of the matrix are fixed. This enforces the constraint that employees have a set capacity, and that a project requires a set amount of work. To change the totals, the user must change the original dataset.

Below are the implementation details of the two methods.

#### Sliding
When the user sets the PT value for an employee in a given project, the other values should be changed to compensate accordingly, while keeping fixed employee and project marginal totals.

In this scenario, the following elements of the matrix are _constants_: the user-supplied value, and the zero-values of employees not working in a project. All other _n_ elements are our actual variables, which define an _n_-dimensional space of solutions.

Given _I_ employees and _J_ projects, we can describe the variables and their constraints as a linear system of _n_ equations, such as:

```
x(e1,p1) + x(e1,p2) + ... + x(e1,pJ) = sum(x(e1,:))    # marginal total for employee 1

x(e1,p1) + x(e2,p1) + ... + x(eI,p1) = sum(x(:,p1))    # marginal total for project 1

...
```

We can then express the linear system in matrix form (_Ax = b_), and find x by solving the matrix. However, because the problem is under-determined (there is no unique solution to the matrix), we must define a criterion for choosing a solution. The simplest criterion is just to minimize the deviation from the "exact" solution _Ax = b_.

This effectively becomes a *linear least-squares problem* with bounds on the variables:

```
minimize L2 norm of (Ax - b), subject to:

x >= PT_MIN
```

where:

* _A_ selects the employee totals and project totals that should be fixed.
* _b_ is the vector of totals selected in A.
* _x >= PT_MIN_ means that employees who are in a project cannot be assigned fewer than that amount of PTs (e.g. 1). To remove the employee from the project (set the value to zero), the user must manually delete them.
* Note that, because the user-supplied value is a constant (and is therefore not included as a variable in the least-squares formulation), it is subtracted from the marginal totals _b_.
* Solver used: `scipy.optimize.lsq_linear`


#### Optimizing
In this scenario, the following values are _constants_: the user-supplied value, and the zero-values of employees who do not have the skills for a particular project. Importantly, the optimizer _may_ add employees to new projects to which they were originally not assigned, or remove employees from projects they were originally working in -- provided that the skills match.

The problem is formulated as a *linear program* with equality and inequality constraints. The objective function to be minimized is, for example, the total cost of employees.

```
minimize F(x) = Cx, subject to:

Ax = b,

x >= 0
```

where:

* C is the vector of costs (€/work unit) for each [employee,project] combination in _x_.
* A is the design matrix for employee and project marginal totals (set as equality constraints).
* b is the RHS for the equality constraint.
* Solver used: `cvxopt.solvers.lp`

### TODOs
* Visualize skills mask
* Implement project roles (project lead, technical lead)
* Possible modes of the game: core-team/conservative (tend to keep existing resources in a project) vs. distributed/volatile (tend to change project members)
