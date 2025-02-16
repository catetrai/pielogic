import numpy as np
from cvxopt import matrix, spmatrix, solvers
from scipy import stats, optimize


def put_solution(mat, vec, ind):
	mat = np.zeros(mat.shape)
	np.put(mat, ind, vec)
	return mat


def solve_linear_system(emplproj_list, cost_list, skills_list, idx_selected, totals):
	'''
	'idx_selected' is a tuple with row and column index of selected (empl,proj).
	'totals' is a tuple constaining two tuples, one for emplTotals and one for projTotals.
	'''

	# Check that employee has skill
	if not skills_list[idx_selected[0]][idx_selected[1]]:
		status_msg = "NO_SKILL"
		return status_msg

	# User-supplied data in array form (#empl x #proj)
	emplproj_arr = np.array(emplproj_list, np.dtype('d'))
	nEmpl, nProj = emplproj_arr.shape
	N = nEmpl*nProj
	cost_arr = np.array(cost_list, np.dtype('d'))
	skills_mask = np.array(skills_list, np.dtype('?'))

	# Flatten arrays into vectors, taking only allowed values based on skills_mask
	emplproj_vec = emplproj_arr[skills_mask]
	cost_vec = cost_arr[skills_mask]
	skills_mask_ind = np.nonzero(skills_mask.flatten())[0]

	# Adjust index of selected [empl,proj] after flattening and skill filtering
	idx_mat = np.arange(N).reshape(nEmpl,nProj)
	idx_selec_mat = idx_mat[idx_selected[0]][idx_selected[1]]
	idx_vec	= idx_mat[skills_mask]
	idx_selec_flat = np.where(np.isin(idx_vec, idx_selec_mat))[0][0]

	# Create design matrix for fixed marginal totals, excluding user-selected element
	A = create_design_matrix(emplproj_arr, skills_mask, excluded_elem=[idx_selected])
	m, n = A.shape

	# Create right-hand-side vector.
	# Must subtract the user-supplied value (constant) from the totals!
	selec_value = emplproj_vec[idx_selec_flat]
	tot_empl = list(totals[0])
	tot_empl[idx_selected[0]] = totals[0][idx_selected[0]] - selec_value
	tot_proj = list(totals[1])
	tot_proj[idx_selected[1]] = totals[1][idx_selected[1]] - selec_value
	b = tot_empl + tot_proj[:-1]

	# Compute least-squares solution of linear matrix equation
	print(A)
	print(b)
	lb = np.ones(n)
	ub = np.full(n, np.inf)
	x = optimize.lsq_linear(A, b, bounds=(lb, ub))['x']

	# Check that solution satisfies equations
	if not np.allclose(np.dot(A, x), b):
		status_msg = "NO_SOLUTION"
		return status_msg

	# Add user-selected element back to x vector
	x = np.insert(x, idx_selec_flat, selec_value)

	# Put all values back in matrix
	new_mat = put_solution(emplproj_arr, x, skills_mask_ind)
	return new_mat.tolist()



def create_design_matrix(emplproj_arr, skills_mask, excluded_elem=[]):
	'''
	'excluded_elem' (optional argument) is a tuple of 1-by-2 tuples with the row and column
		indexes of (empl,proj) that should not be included as variables
		(analogous to what happens to elements with skills_mask(i) = 0).
	'''
	# Exclude additional optional elements (by masking them in the 'skills_mask' matrix)
	if excluded_elem:
		for i in range(0, len(excluded_elem)):
			e, p = excluded_elem[i]
			skills_mask[e,p] = 0

	emplproj_vec = emplproj_arr[skills_mask]
	skills_mask_ind = np.nonzero(skills_mask.flatten())[0]
	nEmpl, nProj = emplproj_arr.shape
	N = nEmpl*nProj

	# Enforce fixed employee and project totals (equality constraints matrix for LP)
	n = len(emplproj_vec)
	m = nEmpl + nProj - 1	# -1 so that constraint matrix is full rank

	A = np.zeros((m, n))
	mat_ind = np.arange(N).reshape(nEmpl,nProj)
	# Employee totals
	for i in range(0,nEmpl):
		temp = np.zeros(N)
		np.put(temp, mat_ind[i,:], 1)
		A[i,:] = temp[skills_mask_ind]
	# Project totals
	for i in range(0,nProj-1):
		temp = np.zeros(N)
		np.put(temp, mat_ind[:,i], 1)
		A[i+nEmpl,:] = temp[skills_mask_ind]
	return A


def constropt(emplproj_list, cost_list, skills_list):

	# User-supplied data in array form (#empl x #proj)
	emplproj_arr = np.array(emplproj_list, np.dtype('d'))
	# cost_arr = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], np.dtype('d'))
	cost_arr = np.array(cost_list, np.dtype('d'))
	skills_mask = np.array(skills_list, np.dtype('?'))

	# Flatten arrays into vectors, taking only allowed values based on skills_mask
	emplproj_vec = emplproj_arr[skills_mask]
	cost_vec = cost_arr[skills_mask]
	skills_mask_ind = np.nonzero(skills_mask.flatten())[0]

	A = create_design_matrix(emplproj_arr, skills_mask)
	tot_proj = np.sum(emplproj_arr, axis=0)
	tot_empl = np.sum(emplproj_arr, axis=1)
	b = np.concatenate((tot_empl, tot_proj[:-1]), axis=None)

	def solve_lp(coeff, A_0, b_0, initvals, solver):

		n = len(coeff)
		m = len(b_0)
		assert A_0.shape == (m, n)

		# Coefficients for cost function to be minimized
		c = matrix(coeff)

		# Equality constraints (marginal totals)
		A = matrix(A_0)
		b = matrix(b_0)

		# If using default cvxopt solver, set inequality constraints (x >= 0)
		if solver is None or solver == 'cvxopt':
			solver = None
			G = spmatrix(-1., range(n), range(n))
			h = matrix(0., (n,1))
		elif solver == 'glpk' or solver == 'simplex':
			solver = 'glpk'
			G = matrix(0., (1,n))
			h = matrix(0., (1,1))
		else:
			raise ValueError("Invalid solver name. 'solver' must be None for cvxopt method or 'glpk' for simplex method.")

		# Sei initial values
		primalstart = None
		# GLPK solver (simplex method) can't do much with initial values
		# (must be *basic* feasible solution, which has at least n-m zero values)
		# (therefore, tends to make the vector sparser, i.e. kick out employees)
		if initvals is not None and solver != 'glpk':
			assert len(initvals) == len(coeff)
			primalstart = {
				'x': matrix(initvals),
				's': matrix(1e-10, (n,1))
			}

		# Solve LP
		sol = solvers.lp(c=c, G=G, h=h, A=A, b=b, solver=solver, primalstart=primalstart)
		if sol['status'] is 'optimal':
			res = []
			for i in range(0,n):
				res.append(sol['x'][i])
			# Check that constraints are satisfied
			tol = 1e-5
			new_totals = A * sol['x'] - b
			for i in range(0,m):
				assert new_totals[i] < tol
			# Return solution vector
			return res
		else:
			print('No optimal solution found!')
			return None

	DEBUG = False
	if not DEBUG:
		res = solve_lp(cost_vec, A, b, None, None)
		if res is not None:
			new_mat = put_solution(emplproj_arr, res, skills_mask_ind)
			print('Original data:')
			print(emplproj_arr)
			print('\nEmployee costs:')
			print(cost_arr)
			print('\nSkills mask:')
			print(skills_mask)
			print('\nConstrained optimization:')
			np.set_printoptions(precision=0, suppress=True)
			print(new_mat)
			return new_mat.tolist()
