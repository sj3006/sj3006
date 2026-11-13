"""Instance-dependent lower bounds for the fixed-confidence problem.

Every bound here comes from the transportation inequality

    sum_y E_nu[N_y] KL(nu_y, nu'_y) >= kl(P_nu(E), P_nu'(E))           (*)

for an alternative instance nu' that also satisfies the structural
assumption, and an event E decided at the stopping time. Instances have
independent failure modes (the benchmark draws them that way), so KL adds
over modes.

Two facts about kl are used throughout. Let pi = P_nu(E).
- If P_nu'(E) <= alpha, then (*) gives at least g(pi) = kl(pi, alpha) when
  pi > alpha, and nothing otherwise.
- If P_nu'(E) >= 1 - beta, then (*) gives at least f(pi) = kl(pi, 1 - beta)
  when pi < 1 - beta, and nothing otherwise.

Ordered problem (Assumption A), as a linear program in n_y = E[N_y]:
(i)  target points. For each mode a and each riskiest point t of the target
     T (for a's order), raise mode a to eps on t's riskier cone. Then t is
     unsafe, so P'(T certified) <= alpha, while P(T certified) >= 1 - beta:
         sum_{y riskier than t, p_a(y) < eps} n_y KL(p_a(y) || eps) >= kl(1 - beta, alpha).
(ii) boundary points. For each mode a and each z outside T only because of
     mode a, with every strictly safer setting (for a) inside T for a,
     lower p_a(z) to q eps (keeps Assumption A). With pi = P(z certified):
         A_z = n_z KL(p_a(z) || q eps)                                  >= f(pi)
         B_z = sum_{y riskier than z, p_a(y) < eps} n_y KL(p_a(y)||eps) >= g(pi)
     for the same unknown pi. The feasible set of (A_z, B_z) is convex;
     we impose its supporting half-planes
         w A_z + (1 - w) B_z >= c(w) = min_pi [ w f(pi) + (1 - w) g(pi) ]
     for a grid of w. If p_a(z) >= eps then B_z = 0, pi <= alpha, and
     A_z >= kl(alpha, 1 - beta).
The bound is the LP minimum of sum_y n_y. (Earlier code added a
certification LP and a boundary sum computed separately, which can
double-count trials that serve both; this joint LP does not.)

Unordered problem (any instance): each setting is resolved on its own.
For x in T: n_x >= kl(1 - beta, alpha) / min_m KL(p_m(x) || eps).
For x outside T: lowering every mode above q eps at x puts x in T, and
raising one mode at x makes it unsafe, so
    n_x >= min_pi max( f(pi) / R_x , g(pi) / C_x ),
R_x = sum_{m: p_m > q eps} KL(p_m || q eps), C_x = min_m KL(p_m || eps)
(and n_x >= kl(alpha, 1 - beta) / R_x if x is unsafe).
"""

import numpy as np

from .cone import cone_sum

PI = np.linspace(0.0, 1.0, 20001)[1:-1]
W_GRID = (0.01, 0.03, 0.06, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99)


def kl_bern(a, b):
    a = np.clip(a, 1e-15, 1 - 1e-15)
    b = np.clip(b, 1e-15, 1 - 1e-15)
    return a * np.log(a / b) + (1 - a) * np.log((1 - a) / (1 - b))


def _fg(alpha, beta):
    f = np.where(PI < 1 - beta, kl_bern(PI, 1 - beta), 0.0)
    g = np.where(PI > alpha, kl_bern(PI, alpha), 0.0)
    return f, g


def cut_constants(alpha, beta, w_grid=W_GRID):
    f, g = _fg(alpha, beta)
    return {w: float(np.min(w * f + (1 - w) * g)) for w in w_grid}


def _arrays(sc):
    modes = sc.modes
    truth = np.stack([sc.truth[m] for m in modes])
    eps = np.array([sc.eps[m] for m in modes])[:, None, None]
    return modes, truth, eps


def ordered_lower_bound(sc, q=0.5, alpha=0.05, beta=0.05, boundary=True):
    """Joint LP bound for the fixed-confidence problem under Assumption A.

    Returns dict(lb, lb_target_only, n_target_pts, n_boundary_pts).
    """
    from scipy.optimize import linprog
    modes, truth, eps = _arrays(sc)
    M = len(modes)
    shape = truth.shape[1:]
    N = int(np.prod(shape))
    inT_m = truth <= q * eps                        # per mode
    T = inT_m.all(axis=0)
    k_cert = np.where(truth < eps, kl_bern(truth, eps), 0.0)
    K1 = float(kl_bern(1 - beta, alpha))
    rows, rhs = [], []

    def cone_row(a, z):
        zmask = np.zeros(shape)
        zmask[z] = 1.0
        riskier = cone_sum(zmask, sc.directions[modes[a]], riskier=False) > 0.5   # y with z in y's safer cone
        return np.where(riskier, k_cert[a], 0.0).ravel()

    n_t = 0
    for a, m in enumerate(modes):
        cnt = cone_sum(T.astype(float), sc.directions[m])
        for z in zip(*np.nonzero(T & (cnt < 1.5))):
            rows.append(cone_row(a, z))
            rhs.append(K1)
            n_t += 1
    n_target_rows = len(rows)

    n_b = 0
    if boundary:
        cuts = cut_constants(alpha, beta)
        K_unsafe = float(kl_bern(alpha, 1 - beta))
        for a, m in enumerate(modes):
            others = np.all([inT_m[b] for b in range(M) if b != a], axis=0) if M > 1 else np.ones(shape, bool)
            out_a = ~inT_m[a]
            # z such that no OTHER setting outside T for a is safer (for a) than z
            safer_out = cone_sum(out_a.astype(float), sc.directions[m], riskier=False)
            bnd = out_a & (safer_out < 1.5) & others
            qe = q * float(eps[a].ravel()[0])
            for z in zip(*np.nonzero(bnd)):
                n_b += 1
                arow = np.zeros(N)
                arow[np.ravel_multi_index(z, shape)] = float(kl_bern(truth[a][z], qe))
                brow = cone_row(a, z)
                if not brow.any():
                    rows.append(arow)
                    rhs.append(K_unsafe)
                    continue
                for w, c in cuts.items():
                    rows.append(w * arow + (1 - w) * brow)
                    rhs.append(c)

    A = np.array(rows)
    b = np.array(rhs)
    lp = linprog(np.ones(N), A_ub=-A, b_ub=-b, bounds=(0, None), method="highs")
    lp_t = linprog(np.ones(N), A_ub=-A[:n_target_rows], b_ub=-b[:n_target_rows], bounds=(0, None),
                   method="highs")
    return dict(lb=float(lp.fun), lb_target_only=float(lp_t.fun), n_target_pts=n_t, n_boundary_pts=n_b)


def unordered_lower_bound(sc, q=0.5, alpha=0.05, beta=0.05):
    modes, truth, eps = _arrays(sc)
    t = truth.reshape(len(modes), -1)
    e = eps.reshape(len(modes), 1)
    K1 = float(kl_bern(1 - beta, alpha))
    K_unsafe = float(kl_bern(alpha, 1 - beta))
    f, g = _fg(alpha, beta)
    inT = (t <= q * e).all(axis=0)
    safe = (t < e).all(axis=0)
    C = np.where(t < e, kl_bern(t, e), 0.0).min(axis=0)
    R = np.where(t > q * e, kl_bern(t, q * e), 0.0).sum(axis=0)
    total = 0.0
    for x in range(t.shape[1]):
        if inT[x]:
            total += K1 / C[x]
        elif not safe[x]:
            total += K_unsafe / R[x]
        else:
            total += float(np.min(np.maximum(f / R[x], g / C[x])))
    return total
