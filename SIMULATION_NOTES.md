# Cyclic Voltammetry Simulation — Technical Notes

## Overview

This notebook simulates cyclic voltammetry (CV) for a simple one-electron redox couple
$O + e^- \leftrightarrow R$ using DOLFINx (FEniCSx) to solve the 1D diffusion equation
with Butler-Volmer kinetics at the electrode boundary.

---

## Critical Fix: Mass Conservation via Single-Species Formulation

### The Bug (original two-species Picard approach)

The original code solved **two separate nonlinear problems** — one for $C_O$ and one
for $C_R$ — coupled through the shared Butler-Volmer flux $J_{BV}$, using Picard
(fixed-point) iteration:

```
for each time step:
    for picard_iter in range(max_picard_iter):
        solve F_O(C_O; C_R_old) = 0   →  update C_O
        solve F_R(C_R; C_O_new) = 0   →  update C_R
        check convergence
```

**Why it failed:** At large overpotentials ($|\eta| \gg 0$), the Butler-Volmer
exponentials become extremely asymmetric. For example at $\eta = +0.5\text{ V}$:

- $e^{-\alpha f \eta} \approx 6 \times 10^{-5}$ (tiny — reduction suppressed)
- $e^{(1-\alpha) f \eta} \approx 1.7 \times 10^{4}$ (huge — oxidation dominant)

The sequential Picard solve evaluates $J_{BV}$ at **different states** for each species:
the O equation sees more flux (production) than the R equation loses (consumption)
because $C_R$ hasn't been updated yet when O is solved. Picard declares convergence
prematurely because the **O equation's Robin coefficient is negligible** at positive η
($k_0 e^{-\alpha f\eta} \approx 10^{-6}$), so $C_O$ barely changes between iterations.

**Result:** A cumulative mass conservation error that inflates $C_O$ far beyond the
physical limit of $C_{total} = C_O^{bulk} + C_R^{bulk}$.

### The Fix

Since $D_O = D_R$, the total concentration $C_{total}(x,t) = C_O(x,t) + C_R(x,t)$
satisfies a homogeneous diffusion equation with constant boundary conditions — meaning
$C_{total}$ is constant everywhere for all time:

$$C_R(x,t) = C_{total} - C_O(x,t)$$

We substitute this into the Butler-Volmer expression:

$$J_{BV} = k_0\left[C_O e^{-\alpha f\eta} - (C_{total} - C_O) e^{(1-\alpha)f\eta}\right]$$

and solve **a single nonlinear equation** for $C_O$. This:

1. **Guarantees mass conservation exactly** — by algebraic construction
2. **Eliminates Picard iteration** — no inter-species coupling to iterate on
3. **Is faster** — one Newton solve per time step instead of up to 20 × 2
4. **Is better conditioned** — the Robin-type BC coefficient
   $k_0[e^{-\alpha f\eta} + e^{(1-\alpha)f\eta}]$ is always positive

### When this simplification does NOT apply

If $D_O \neq D_R$, the conservation relation $C_R = C_{total} - C_O$ no longer holds
spatially. In that case, use a **monolithic mixed function space** approach where both
species are solved simultaneously in a single Newton system, ensuring the shared flux
is evaluated consistently.

---

## Sign Convention: US (Polarographic / American)

This simulation uses the **US (polarographic) sign convention**:

| Convention | Cathodic (reduction) | Anodic (oxidation) |
|------------|---------------------|--------------------|
| **US / Polarographic** | **Positive** current | **Negative** current |
| IUPAC | Negative current | Positive current |

### Why you see negative current at positive potentials

The Butler-Volmer flux is defined as:

$$J_{BV} = k_0\left[C_O e^{-\alpha f\eta} - C_R e^{(1-\alpha)f\eta}\right]$$

- **First term** = cathodic (reduction) component: $O + e^- \to R$
- **Second term** = anodic (oxidation) component: $R \to O + e^-$

At positive η (positive potentials): the anodic term dominates → $J_{BV} < 0$ →
current $I = nFAJ_{BV} < 0$. This means **oxidation gives negative current**.

**To switch to IUPAC convention**, flip the sign in the current calculation:

```python
# US convention (current code):
current = n * F * A_electrode * flux * 1e6

# IUPAC convention (flip sign):
current = -n * F * A_electrode * flux * 1e6
```

Or equivalently, redefine $J_{BV}$ with the anodic term first:

$$J_{BV}^{IUPAC} = k_0\left[C_R e^{(1-\alpha)f\eta} - C_O e^{-\alpha f\eta}\right]$$

---

## Cells Changed (from original → fixed)

| Cell # | Section | What Changed |
|--------|---------|-------------|
| 7 | Physical Parameters | Added `C_total = C_O_bulk + C_R_bulk` |
| 11 | Functions & IC | Removed `C_R`, `C_R_n`, `D_R_const`; only `C_O` solved |
| 15 | Butler-Volmer func | `C_R_surf = C_total - C_O_surf` instead of independent variable |
| 16 | Markdown (problem) | Updated math to show single-equation formulation |
| 18 | Markdown (form) | Updated description |
| 19 | Variational form | Single `F_O` with `(C_total_const - C_O)` in $J_{BV}$; no `F_R` |
| 20 | Markdown (BC) | Updated description |
| 21 | Solver setup | Single Newton solver; removed `problem_R`, `solver_R`, Picard params |
| 23 | Time loop | One `solver_O.solve()` per step; `C_R = C_total - C_O` derived; no Picard |
| 31 | Animation | Y-axis limit `C_total * 1.2` (was `5.5 * C_bulk`, nonsensical) |
| 32 | Save GIF | Same y-axis fix |
| 34 | Export | Added in-cell peak analysis (was referencing undefined variables) |

---

## Key Simulation Parameters

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Diffusion coefficient (both species) | $D$ | $10^{-9}$ | m²/s |
| Bulk concentration O | $C_O^{bulk}$ | 1.0 | mM |
| Bulk concentration R | $C_R^{bulk}$ | 1.0 | mM |
| Standard rate constant | $k_0$ | 0.1 | m/s |
| Transfer coefficient | $\alpha$ | 0.5 | — |
| Formal potential | $E^0$ | 0.0 | V |
| Scan rate | $\nu$ | 0.05 | V/s |
| Domain length | $L$ | 100 | μm |
| Mesh elements | $n_x$ | 1000 | — |
| Time steps | — | 1000 | — |

---

## Diagnostic Checklist

If results look wrong in the future, check:

1. **$C_O + C_R = C_{total}$ everywhere?** — If not, mass conservation is broken
2. **Max $C_O \leq C_{total}$?** — Overshoot signals flux inconsistency
3. **$\Delta E_p$ reasonable?** — For $k_0 = 0.1$ m/s (fast kinetics), expect near-Nernstian: ~59/n mV
4. **$|i_{pa}/i_{pc}| \approx 1$?** — For equal bulk concentrations and equal D
5. **Sign convention consistent?** — Check whether plots match US or IUPAC expectations

---

## Notebook Inventory

| File | Approach | When to use |
|------|----------|-------------|
| `cyclic_voltammetry_demo.ipynb` | Single-species ($C_R = C_{total} - C_O$) | $D_O = D_R$ — fast, simple, exact conservation by construction |
| `cyclic_voltammetry_monolithic.ipynb` | Monolithic mixed FE (coupled Newton) | **General case**: $D_O \neq D_R$, or when you want the full formulation |

### Monolithic approach — key ideas

The monolithic notebook uses a **mixed function space** `W = V × V` so that
`(C_O, C_R)` are solved **simultaneously** in a single Newton system:

```python
# Mixed element
elem = basix.ufl.element("Lagrange", "interval", 1)
mel = basix.ufl.mixed_element([elem, elem])
W = fem.functionspace(domain, mel)

# Single combined solution
u = fem.Function(W)
C_O, C_R = ufl.split(u)

# Single combined residual
F = (O_equation_terms) + (R_equation_terms)  # one form, two species

# One Newton solve per time step
problem = NonlinearProblem(F, u, bcs=[bc_O, bc_R])
solver = NewtonSolver(MPI.COMM_WORLD, problem)
```

**Why this works:** Newton sees the full Jacobian including cross-derivatives
$\partial F_O / \partial C_R$ and $\partial F_R / \partial C_O$ from the shared
$J_{BV}$ term. Both species are updated simultaneously — no splitting error,
no Picard lag, no conservation assumption.

**Trade-off:** The linear system is 2× larger (2N DOFs vs N), but with a direct
LU solver this is negligible for 1D problems. For 2D/3D, consider iterative
solvers with block preconditioners.
