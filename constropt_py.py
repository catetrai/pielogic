import numpy as np
from cvxopt import matrix, spmatrix, solvers
from scipy import stats, optimize
# import time

# start = time.time()


def put_solution(mat, vec, ind):
	mat = np.zeros(mat.shape)
	np.put(mat, ind, vec)
	return mat


def solve_linear_system(emplproj_list, cost_list, skills_list, idx_selected, totals):
	'''
	'idx_selected' is a 1-by-2 list with row and column index of selected [empl,proj].
	'totals' is a list of lists with emplTotals and projTotals.
	'''
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
	print idx_mat
	idx_selec_mat = idx_mat[idx_selected[0]][idx_selected[1]]
	print idx_selec_mat
	idx_vec	= idx_mat[skills_mask]
	print idx_vec
	idx_selec = np.where(np.isin(idx_vec, idx_selec_mat))[0][0]
	print idx_selec

	# Create first row block of coefficient matrix for fixed marginal totals
	A = create_coeff_matrix(emplproj_arr, skills_mask)

	# Append rows for fixed pairwise proportions between employees in same project
	# (careful about degrees of freedom -> linear system should not get overdetermined!)
	# nrows_prop = nProj + 

	# Solve constropt problem to minimize KL divergence
	# slid_mat = solve_lp(coeff, A_0, b_0, initvals, solver)


	# Last row is for setting user-supplied x
	last_row = np.zeros(A.shape[1])
	last_row[idx_selec] = 1
	A = np.concatenate((A, [last_row]), axis=0)

	# Create right-hand-side vector
	tot_empl = totals[0]
	tot_proj = totals[1]
	# tot_proj = np.sum(emplproj_arr, axis=0)
	# tot_empl = np.sum(emplproj_arr, axis=1)
	b = np.concatenate((tot_empl, tot_proj[:-1], emplproj_vec[idx_selec]), axis=None)

	# Compute solution of linear matrix equation
	print A
	print b
	x = np.linalg.lstsq(A, b)[0]
	# x = optimize.nnls(A, b)[0]

	# Check that solution satisfies equations
	assert np.allclose(np.dot(A, x), b)

	# Put values back in matrix
	new_mat = put_solution(emplproj_arr, x, skills_mask_ind)
	return new_mat.tolist()



def create_coeff_matrix(emplproj_arr, skills_mask):
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

	A = create_coeff_matrix(emplproj_arr, skills_mask)
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
			print 'No optimal solution found!'
			return None

	DEBUG = False
	if not DEBUG:
		res = solve_lp(cost_vec, A, b, None, None)
		if res is not None:
			new_mat = put_solution(emplproj_arr, res, skills_mask_ind)
			print 'Original data:'
			print emplproj_arr
			print '\nEmployee costs:'
			print cost_arr
			print '\nSkills mask:'
			print skills_mask
			print '\nConstrained optimization:'
			np.set_printoptions(precision=0, suppress=True)
			print new_mat
			return new_mat.tolist()


# end = time.time()
# print('Elapsed time: %.5fs' % (end - start))


# c = matrix([1., 1., 1., 1., 1.])
# 's': matrix(1e-100, (5,1))
# 100:  4.7000e+02  7.9013e+04  3e-20  2e+02  2e+02  1e+02
# Terminated (maximum number of iterations reached).
# [[ 120.]
#  [ 100.]
#  [ 100.]
#  [ 100.]
#  [  50.]]

# c = matrix([1., 1., 1., 1., 1.])
# 's': matrix(1., (5,1))
# 7:    4.7000e+02  4.7000e+02  5e-09  5e-09  2e-11  5e-09
# Optimal solution found.
# [[ 134.08629067]
#  [  85.91370933]
#  [  85.91370933]
#  [ 100.        ]
#  [  64.08629067]]

# c = matrix([1., 1., 1., 1., 1.])
# no primalstart
# 4:  4.7000e+02  4.7000e+02  5e-06  5e-14  1e-08  1e-08
# Optimal solution found.
# [[ 127.5]
#  [  92.5]
#  [  92.5]
#  [ 100. ]
#  [  57.5]]







  
# a = np.random.randint(20, 30, size=5)
# target1 = 30
# target2 = 0.60
# K = 26

# A = matrix(np.vstack([np.ones(5), a, np.array([max(x-K,x*x) for x in a])]))
# A = np.vstack([np.ones(5), a, np.array([max(x-K,x*x) for x in a])])
# b = matrix([1.0, target1, target2])
# print A


#---------------------------------------------

# from scipy.optimize import linprog, minimize

# guess = [120,100,100,100,50]
# # costs = [10,5,1,100,50]
# costs = [90,100,50,70,80]

# fun = lambda x: costs[0]*x[0] + costs[1]*x[1] + costs[2]*x[2] + costs[3]*x[3] + costs[4]*x[4]
# cons = ({'type': 'ineq', 'fun': lambda x:  x[0] + x[2] - 220},
#          {'type': 'ineq', 'fun': lambda x: x[1] + x[4] -150},
#          {'type': 'ineq', 'fun': lambda x: x[0] + x[1] -220},
#          {'type': 'ineq', 'fun': lambda x: x[2] + x[3] + x[4] -250})
# bnds = ((0, None), (0, None), (0, None), (0, None), (0, None))

# A_eq = [[1,0,1,0,0],
# 		[0,1,0,0,1],
# 		[1,1,0,0,0],
# 		[0,0,1,1,1]]

# # A_eq = [[1,1,0,0,0],
# # 		[0,0,1,1,1]]

# b_eq = [220,150,220,250]
# # b_eq = [220,250]

# # c = [1,1,1,1,1]
# c = costs

# # x = linprog(c=c, A_eq=A_eq, b_eq=b_eq, method='simplex')
# res = minimize(fun, guess, method='trust-constr', bounds=bnds, constraints=cons)
# print res