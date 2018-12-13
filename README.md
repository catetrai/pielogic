### Install & run
1. Install Flask
`pip install Flask`

2. Clone and cd to repo

3. Run Flask server
`python json_io.py runserver -d`

4. Go to `http://127.0.0.1:8090/` on browser

### Problem formulation
#### Sliding
Least squares problem formulated as quadratic program with inequality and equality constraints.
Solver used: cvxopt.solvers.coneqp

minimize L2 norm of (Ax - b), subject to:

x >= PT_MIN

where:

* A selects the employee totals and project totals that should be fixed. _(Note: must *exclude* the slider selected by the user! That value is a constant, should be subtracted from vector b of totals.)_
* b is a vector of totals selected in A (subtracting the user-selected value, which we treat as a constant).

_NOTE: x >= PT_MIN means that employees who are in a project cannot be assigned fewer than that amount of PTs (e.g. 1). To remove the employee from the project, you must manually delete them. This also takes care of the non-negativity constraint.
_

#### One-shot optimizing
Linear program with equality and inequality constraints. The objective function to be minimized is the total cost of employees.

Solver used: cvxopt.solvers.lp

minimize F(x) = Cx, subject to:

Ax = b,

x >= 0

where:

* C is the vector of costs (€/d) for each employee in each project.
* A is the selector matrix for employee and project totals (set as equality constraints).
* b is the RHS for the totals constraint.
