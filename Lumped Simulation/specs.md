# EIS Biosensor — Lumped Circuit Applet
## Specification for GitHub Copilot / Claude Opus

---

## 1. Device Context

A **Metal-Insulator-Semiconductor (MIS) capacitor** contacted through electrolyte,
used as a DNA biosensor. The instrument (potentiostat / impedance analyser) applies
a small AC voltage between two terminals and measures the resulting current:

- **WE (working electrode):** Au top surface
- **CE (counter electrode):** Si++ substrate, bottom

### Layer stack

```
Si++       heavily doped silicon     conductor   CE / ground
t-SiO₂    500 nm   ε_r = 3.9        dielectric  PRIMARY TRANSDUCER
e-SiO₂    400 nm   ε_r = 3.7        dielectric  spacer / pore walls
Cr          15 nm                    conductor   adhesion
Au         100 nm                    conductor   WE
electrolyte  aqueous buffer          ionic       above Au, inside pores
```

### Pore array

The e-SiO₂/Cr/Au stack is patterned by **liftoff**, leaving circular openings
(micropores) where the t-SiO₂ floor is exposed directly to the electrolyte.
DNA primers are immobilised on t-SiO₂ inside the pores. Upon target DNA
amplification, surface charge (σ_DNA) and local dielectric (c_DNA) change at
that interface, modifying the impedance.

```
Top view — one unit cell:

  ┌─────────────────────────┐  pitch × pitch
  │   Au / e-SiO₂ (field)  │
  │         ┌───┐           │
  │         │ ∅ │  r_pore   │  ← t-SiO₂ exposed, DNA here
  │         └───┘           │
  └─────────────────────────┘

  A_pore  = π · r²
  A_field = pitch² − A_pore
```

---

## 2. Equivalent Circuit — Three Paths

Every path closes between Au (WE) and Si++ (CE).
The instrument measures Z_total = 1 / (Y₁ + Y₂ + Y₃).

### Path 1 — Field solid (spurious background)
```
Au → C_dl_Au → e-SiO₂ → t-SiO₂ → Si++
```
Pure series dielectric stack. No electrolyte in the vertical column.
C_dl_Au sits at the Au/electrolyte interface on the field surface —
it charges from the electrolyte but the circuit closes through the
oxide stack to Si++. Since C_dl_Au >> C_eox >> C_tox, the series
combination is dominated by t-SiO₂.

### Path 2 — Open pore (signal)
```
Au → C_dl_Au(rim) → electrolyte/R_access → C_dl_SiO₂(σ_DNA) → C_DNA_layer(c_DNA) → t-SiO₂ → Si++
```
The electrolyte fills the pore lumen and acts as an ionic conductor.
R_access is the hemispherical spreading resistance at the pore mouth —
it is the geometric resistance of the electrolyte path, not a separate
physical element. DNA grows at the t-SiO₂ surface and modifies this
path in two ways (see Section 3).
This path repeated N_open times in parallel.

### Path 3 — Closed pore (spurious, negligible)
```
Au → C_PR → t-SiO₂ → Si++
```
Photoresist remains in the pore. C_PR is so large in impedance
(thick, low-ε film) that this path is electrically invisible.
Included for completeness. Repeated N_closed times in parallel.

---

## 3. DNA Signal — Two Mechanisms, Both Modelled

DNA grows at the t-SiO₂ / electrolyte interface, inside the Debye layer.

### Mechanism A — Fixed surface charge σ_DNA (dominant effect)
Each dsDNA molecule contributes negative charge to the SiO₂ surface.
This shifts the surface potential φ_s via the **Grahame equation**:

```
σ_DNA = √(8 ε₀ ε_w R T I) · sinh(F φ_s / 2RT)
```

φ_s in turn changes the double layer capacitance (Gouy-Chapman):

```
C_dl(σ_DNA) = ε₀ · ε_w · A_pore / λ_D · cosh(F φ_s / 2RT)
```

So σ_DNA modifies C_dl_SiO₂ — it is not a new circuit element but
shifts an existing one through the nonlinear C(V) relationship.

### Mechanism B — Dielectric displacement c_DNA (secondary effect)
DNA (ε_r = 8) displaces water (ε_r = 78.5) in the Debye layer.
Modelled as a thin slab capacitor in series:

```
C_DNA_layer = ε₀ · ε_DNA · A_pore / δ_DNA
δ_DNA = c_DNA · λ_D      (DNA occupies fraction c_DNA of Debye layer)
```

Effect is small (ΔC/C ≈ −0.9% for full displacement) but included.

### Full Path 2 series chain
```
C_dl_Au(rim)  →  R_access  →  C_dl_SiO₂(σ_DNA)  →  C_DNA_layer(c_DNA)  →  C_tox
```
All in series. t-SiO₂ still dominates the impedance magnitude.
DNA effects are visible as shifts in the spectrum shape and phase.

---

## 4. All Derived Quantities — Physics Formulae

No R or C value is entered directly. All are computed from physical parameters.

```python
# Geometry
A_pore  = pi * r_pore**2
A_field = pitch**2 - A_pore

# Electrolyte
lambda_D = sqrt(eps0 * eps_w * R * T / (2 * F**2 * I))   # I in mol/m³ = mM
rho      = 0.1 / sqrt(I_mM / 10)                          # Ω·m, empirical
R_access = rho / (4 * r_pore)                             # spreading resistance

# Capacitors — parallel plate: C = eps0 * eps_r * A / t
C_tox_pore   = eps0 * 3.9 * A_pore  / t_tox
C_tox_field  = eps0 * 3.9 * A_field / t_tox
C_eox_field  = eps0 * 3.7 * A_field / t_eox
C_PR         = eps0 * 3.5 * A_pore  / t_PR

# Double layers — Gouy-Chapman
C_dl_Au      = eps0 * eps_w * A_field / lambda_D          # field surface
C_dl_SiO2_0  = eps0 * eps_w * A_pore  / lambda_D          # pore floor, no DNA

# DNA — Mechanism A: shift C_dl via Grahame equation
phi_s     = (2*R*T/F) * arcsinh(sigma_DNA / sqrt(8*eps0*eps_w*R*T*I))
C_dl_SiO2 = C_dl_SiO2_0 * cosh(F * phi_s / (2*R*T))      # modified by σ_DNA

# DNA — Mechanism B: dielectric slab
delta_DNA    = c_DNA * lambda_D
C_DNA_layer  = eps0 * 8.0 * A_pore / delta_DNA            # only if delta_DNA > 0

# Series combination for Path 2 (single pore)
# C_eff = series(C_dl_Au_rim, C_dl_SiO2, C_DNA_layer, C_tox_pore)
# For Path 1: series(C_dl_Au, C_eox_field, C_tox_field)

# Characteristic frequencies (for reference lines on plots)
f_lateral = D_ion / (pi * r_pore**2)     # ~212 Hz at r=1.5µm
f_RC_pore = 1 / (2*pi * R_access * C_tox_pore)  # ~19 GHz — never reached
```

---

## 5. Ultimate Objective and Why the Applet

### Objective
Generate a large synthetic dataset `{θ, Z(ω)}` to train a probabilistic
inverse model p(θ | Z_obs) that infers DNA concentration and device state
from a measured impedance spectrum. The production simulator will be a
**FEM solution of the full Poisson–Nernst–Planck equations** (DOLFINx),
which captures Warburg diffusion, nonlinear electrostatics, and spatial
DNA distribution without any lumped approximations.

### Why the applet first
The FEM is slow (~10–60 s per simulation) and requires a compute cluster
for the full parameter sweep. Before building it, we need to:

1. Verify the circuit topology is physically correct
2. Understand which parameters shift the spectrum and in which direction
3. Identify the frequency regions that carry the most DNA information
4. Catch conceptual errors cheaply, before they propagate into FEM code

The lumped applet runs in milliseconds, is interactive, and gives immediate
physical intuition. It is a **sanity check and design tool**, not the final model.

### Known limitations of the lumped model
| Omitted physics | Consequence |
|----------------|-------------|
| Warburg diffusion | Phase error below ~200 Hz |
| Stern layer correction | C_dl overestimated ~20% |
| CPE / surface roughness | Nyquist arcs too perfect |
| Pore-pore interaction | Invalid below ~10 Hz |
| Spatial DNA distribution | DNA treated as uniform layer |

---

## 6. Applet Specification

### Technology
**Python + Dash (Plotly)**. Physics in pure Python/NumPy. No JavaScript.

### Input parameters (sliders)

| Group | Parameter | Default | Range | Units |
|-------|-----------|---------|-------|-------|
| Geometry | r_pore | 1.5 | 0.5 – 2.5 | µm |
| Geometry | pitch | 20 | 5 – 50 | µm |
| Geometry | t_tox | 500 | 50 – 1000 | nm |
| Geometry | t_eox | 400 | 100 – 800 | nm |
| Electrolyte | I | 10 | 1 – 150 | mM |
| Electrolyte | T | 298 | 273 – 320 | K |
| DNA signal | σ_DNA | 0 | 0 – 5 | mC/m² |
| DNA signal | c_DNA | 0 | 0 – 1 | — |
| Array | N_total | 100 | 10 – 500 | — |
| Array | f_open | 0.7 | 0.05 – 1.0 | — |

### Output plots (live update)

1. **Bode magnitude** — log₁₀|Z| vs log₁₀ f
   - Traces: Z_total, Z_path1, Z_path2_array, Z_path3
   - Reference lines: f_lateral (dashed)

2. **Bode phase** — φ [degrees] vs log₁₀ f
   - Reference line at −90° (ideal capacitor)

3. **Nyquist** — −Im(Z) vs Re(Z)
   - Two panels: raw Z_total | background-subtracted (Z_total − Z_path1)
   - Frequency markers at 10 Hz, 1 kHz, 100 kHz

### Derived values panel
Display after each slider update:
`λ_D`, `C_tox`, `C_dl_SiO₂(σ_DNA)`, `C_DNA_layer`, `R_access`,
`φ_s` (surface potential), `N_open`, `f_lateral`

### File structure
```
eis_applet/
  physics.py     # all derive_components(), calc_Z() functions
  app.py         # Dash layout and callbacks
  run.py         # entry point: python run.py → opens on localhost:8050
```

### Code conventions
- All internal quantities in SI units; variable names carry units (e.g. `r_pore_m`)
- Complex impedance: Python `complex` type
- `calc_Z(omega, components) -> complex` — one function, one frequency point
- `frequency_sweep(params) -> dict` — returns arrays for all plot quantities
- Every function has a docstring with Args, Returns, and a Physics note