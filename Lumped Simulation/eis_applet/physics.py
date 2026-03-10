"""
EIS Biosensor — Lumped Circuit Physics Module
==============================================

All impedance calculations for the Metal-Insulator-Semiconductor (MIS)
capacitor DNA biosensor. Every R and C value is derived from physical
parameters (geometry, material properties, electrolyte conditions, DNA state).

No component value is entered directly — all are computed from first principles.

Units: All internal quantities are in SI units.
       Variable names carry unit suffixes where helpful (e.g. r_pore_m).
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Tuple

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
EPS0 = 8.854187817e-12   # F/m   vacuum permittivity
F_CONST = 96485.33212     # C/mol Faraday constant
R_GAS = 8.314462618       # J/(mol·K)  gas constant
D_ION = 1.5e-9            # m²/s  typical ion diffusivity (KCl-like)

# Material permittivities (relative)
EPS_W = 78.5              # water at ~25 °C
EPS_TSIO2 = 3.9           # thermal SiO₂
EPS_ESIO2 = 3.7           # evaporated SiO₂
EPS_PR = 3.5              # photoresist
EPS_DNA = 8.0             # DNA dielectric constant

# Oxide conduction parameters (SiO₂)
PHI_B_SIO2 = 3.1                        # eV     barrier height SiO₂→Si
ALPHA_FN = 1.54e-6                       # A/V²   Fowler-Nordheim prefactor
BETA_FN = 2.35e10                        # V/m    FN exponential constant
M_EFF_SIO2 = 0.42 * 9.1093837015e-31    # kg     effective electron mass in SiO₂
Q_ELECTRON = 1.602176634e-19             # C      electron charge
HBAR = 1.054571817e-34                   # J·s    reduced Planck constant
KAPPA_DT = np.sqrt(2 * M_EFF_SIO2 * PHI_B_SIO2 * Q_ELECTRON) / HBAR  # m⁻¹
T_OX_DT_LIMIT = 4e-9                    # m      direct-tunnelling thickness limit


@dataclass
class DeviceParams:
    """
    All user-adjustable parameters for the EIS biosensor simulation.

    Args:
        r_pore_um: Pore radius in micrometres (0.5–2.5 µm).
        pitch_um: Unit cell pitch in micrometres (5–50 µm).
        t_tox_nm: Thermal oxide thickness in nanometres (5–1000 nm).
                  5–4 nm: direct tunnelling regime; 5–25 nm: Fowler-Nordheim regime at max V_dc.
        t_eox_nm: Evaporated oxide thickness in nanometres (100–800 nm).
        I_mM: Ionic strength in millimolar (1–150 mM).
        T_K: Temperature in kelvin (273–320 K).
        sigma_DNA_mCm2: DNA surface charge density in mC/m² (0–5 mC/m²).
        c_DNA: DNA fractional coverage of Debye layer (0–1, dimensionless).
        N_total: Total number of pores in the array (10–500).
        f_open: Fraction of pores that are open (0.05–1.0).
        V_dc_V: DC bias voltage in volts (−0.6 – +1.2 V).
    """
    r_pore_um: float = 1.5
    pitch_um: float = 20.0
    t_tox_nm: float = 500.0
    t_eox_nm: float = 400.0
    I_mM: float = 10.0
    T_K: float = 298.0
    sigma_DNA_mCm2: float = 0.0
    c_DNA: float = 0.0
    N_total: int = 100
    f_open: float = 0.7
    V_dc_V: float = 0.0


@dataclass
class DerivedComponents:
    """
    All derived physical quantities and circuit components.

    Physics note:
        Every value here is computed from DeviceParams using the formulae
        in the specification (Gouy-Chapman, Grahame, parallel-plate, etc.).
    """
    # Geometry (SI)
    r_pore_m: float = 0.0
    pitch_m: float = 0.0
    t_tox_m: float = 0.0
    t_eox_m: float = 0.0
    A_pore_m2: float = 0.0
    A_field_m2: float = 0.0

    # Electrolyte
    I_molm3: float = 0.0
    lambda_D_m: float = 0.0
    rho_elec: float = 0.0       # Ω·m

    # Capacitors (F)
    C_tox_pore: float = 0.0
    C_tox_field: float = 0.0
    C_eox_field: float = 0.0
    C_PR: float = 0.0
    C_dl_Au: float = 0.0
    C_dl_SiO2_0: float = 0.0    # bare, no DNA
    C_dl_SiO2: float = 0.0      # modified by σ_DNA
    C_DNA_layer: float = 0.0    # dielectric displacement

    # Resistance (Ω)
    R_access: float = 0.0

    # DNA state
    phi_s_V: float = 0.0        # surface potential from Grahame
    delta_DNA_m: float = 0.0    # effective DNA layer thickness

    # Array
    N_open: int = 0
    N_closed: int = 0

    # Characteristic frequencies (Hz)
    f_lateral: float = 0.0
    f_RC_pore: float = 0.0

    # Photoresist thickness (for closed pores)
    t_PR_m: float = 0.0

    # DC bias
    V_dc_V: float = 0.0
    oxide_regime: str = "Capacitive"


def derive_components(params: DeviceParams) -> DerivedComponents:
    """
    Compute all circuit components from physical parameters.

    Args:
        params: DeviceParams with user-set values.

    Returns:
        DerivedComponents with every R, C, frequency, etc. populated.

    Physics note:
        - Capacitors use parallel-plate formula: C = ε₀·εᵣ·A / t
        - Double layers use Gouy-Chapman: C_dl = ε₀·ε_w·A / λ_D · cosh(…)
        - σ_DNA → φ_s via Grahame equation (inverse sinh)
        - R_access is hemispherical spreading resistance: ρ / (4·r)
    """
    c = DerivedComponents()

    # --- Unit conversions ---
    c.r_pore_m = params.r_pore_um * 1e-6
    c.pitch_m = params.pitch_um * 1e-6
    c.t_tox_m = params.t_tox_nm * 1e-9
    c.t_eox_m = params.t_eox_nm * 1e-9
    c.I_molm3 = params.I_mM  # 1 mM = 1 mol/m³
    T = params.T_K

    # Photoresist thickness — same as e-SiO₂ for closed pores
    c.t_PR_m = c.t_eox_m

    # --- Geometry ---
    c.A_pore_m2 = np.pi * c.r_pore_m ** 2
    c.A_field_m2 = c.pitch_m ** 2 - c.A_pore_m2

    # --- Electrolyte ---
    c.lambda_D_m = np.sqrt(
        EPS0 * EPS_W * R_GAS * T / (2.0 * F_CONST ** 2 * c.I_molm3)
    )
    # Empirical resistivity: ρ ≈ 0.1 / √(I_mM / 10)  [Ω·m]
    c.rho_elec = 0.1 / np.sqrt(params.I_mM / 10.0)
    c.R_access = c.rho_elec / (4.0 * c.r_pore_m)

    # --- Capacitors (parallel-plate) ---
    c.C_tox_pore = EPS0 * EPS_TSIO2 * c.A_pore_m2 / c.t_tox_m
    c.C_tox_field = EPS0 * EPS_TSIO2 * c.A_field_m2 / c.t_tox_m
    c.C_eox_field = EPS0 * EPS_ESIO2 * c.A_field_m2 / c.t_eox_m
    c.C_PR = EPS0 * EPS_PR * c.A_pore_m2 / c.t_PR_m

    # --- Double layers (Gouy-Chapman) ---
    c.C_dl_Au = EPS0 * EPS_W * c.A_field_m2 / c.lambda_D_m
    c.C_dl_SiO2_0 = EPS0 * EPS_W * c.A_pore_m2 / c.lambda_D_m

    # --- DNA Mechanism A: σ_DNA → φ_s → modified C_dl ---
    sigma_DNA_SI = params.sigma_DNA_mCm2 * 1e-3  # mC/m² → C/m²
    if abs(sigma_DNA_SI) > 0:
        arg = sigma_DNA_SI / np.sqrt(
            8.0 * EPS0 * EPS_W * R_GAS * T * c.I_molm3
        )
        c.phi_s_V = (2.0 * R_GAS * T / F_CONST) * np.arcsinh(arg)
        c.C_dl_SiO2 = c.C_dl_SiO2_0 * np.cosh(
            F_CONST * c.phi_s_V / (2.0 * R_GAS * T)
        )
    else:
        c.phi_s_V = 0.0
        c.C_dl_SiO2 = c.C_dl_SiO2_0

    # --- DNA Mechanism B: dielectric displacement ---
    if params.c_DNA > 0:
        c.delta_DNA_m = params.c_DNA * c.lambda_D_m
        c.C_DNA_layer = EPS0 * EPS_DNA * c.A_pore_m2 / c.delta_DNA_m
    else:
        c.delta_DNA_m = 0.0
        c.C_DNA_layer = np.inf  # no DNA layer → short circuit (infinite C)

    # --- Array ---
    c.N_open = int(round(params.N_total * params.f_open))
    c.N_closed = params.N_total - c.N_open

    # --- Characteristic frequencies ---
    c.f_lateral = D_ION / (np.pi * c.r_pore_m ** 2)
    if c.R_access > 0 and c.C_tox_pore > 0:
        c.f_RC_pore = 1.0 / (2.0 * np.pi * c.R_access * c.C_tox_pore)
    else:
        c.f_RC_pore = np.inf

    # --- DC bias & oxide conduction regime ---
    c.V_dc_V = params.V_dc_V
    c.oxide_regime = oxide_regime_label(c.t_tox_m, params.V_dc_V)

    # Voltage-dependent double layer (Gouy-Chapman with V_dc contribution)
    if abs(params.V_dc_V) > 1e-9 and c.C_tox_pore > 0 and c.C_dl_SiO2 > 0:
        V_dl = params.V_dc_V * c.C_tox_pore / (c.C_tox_pore + c.C_dl_SiO2)
        phi_eff = c.phi_s_V + V_dl
        c.C_dl_SiO2 = c.C_dl_SiO2_0 * np.cosh(
            F_CONST * phi_eff / (2.0 * R_GAS * T)
        )

    return c


# ---------------------------------------------------------------------------
# Impedance calculations
# ---------------------------------------------------------------------------

def _series_impedance(*Z_list) -> complex:
    """
    Series combination of impedances.

    Args:
        *Z_list: Variable number of complex impedances.

    Returns:
        Total series impedance (sum).

    Physics note:
        Z_series = Z₁ + Z₂ + … (simply additive for series elements).
    """
    return sum(Z_list)


def _cap_impedance(C: float, omega: float) -> complex:
    """
    Impedance of an ideal capacitor.

    Args:
        C: Capacitance in farads.
        omega: Angular frequency in rad/s.

    Returns:
        Complex impedance Z = 1 / (jωC).

    Physics note:
        For C = ∞ (short circuit), returns 0+0j.
    """
    if np.isinf(C) or C <= 0:
        return 0 + 0j
    return 1.0 / (1j * omega * C)


def oxide_regime_label(t_ox_m: float, V_dc_V: float) -> str:
    """
    Return a human-readable label for the oxide conduction regime.

    Args:
        t_ox_m: Oxide thickness in metres.
        V_dc_V: DC bias voltage in volts.

    Returns:
        One of 'Capacitive', 'Fowler-Nordheim', or 'Direct tunnelling'.
    """
    V = abs(V_dc_V)
    if V < 1e-9:
        return "Capacitive"
    if t_ox_m <= T_OX_DT_LIMIT:
        return "Direct tunnelling"
    E_ox = V / t_ox_m
    exp_arg = BETA_FN / E_ox
    if exp_arg < 50:
        return "Fowler-Nordheim"
    return "Capacitive"


def Z_oxide(t_ox_m: float, A_m2: float, eps_r: float,
            V_dc_V: float, omega: float) -> complex:
    """
    Oxide impedance with automatic conduction-regime selection.

    Selects between:
      - Capacitive (thick oxide, low field)
      - Fowler-Nordheim tunnelling (t_ox > 4 nm, high field)
      - Direct tunnelling (t_ox ≤ 4 nm)

    Returns Z_cap ∥ R_leak.

    Args:
        t_ox_m:  Oxide thickness [m].
        A_m2:    Oxide area [m²].
        eps_r:   Relative permittivity of the oxide.
        V_dc_V:  DC voltage across the oxide [V].
        omega:   Angular frequency [rad/s].

    Returns:
        Complex impedance of the oxide layer.
    """
    C_ox = EPS0 * eps_r * A_m2 / t_ox_m
    Z_cap = _cap_impedance(C_ox, omega)

    V = abs(V_dc_V)
    if V < 1e-9:
        return Z_cap  # no DC bias → pure capacitive

    E_ox = V / t_ox_m

    if t_ox_m <= T_OX_DT_LIMIT:
        # Direct tunnelling (Simmons-like WKB)
        v_ratio = min(V / PHI_B_SIO2, 0.999)
        exp_arg = 2.0 * KAPPA_DT * t_ox_m * np.sqrt(1.0 - v_ratio)
    else:
        # Fowler-Nordheim tunnelling
        exp_arg = BETA_FN / E_ox

    if exp_arg > 500:
        return Z_cap  # negligible leakage

    J_leak = ALPHA_FN * E_ox ** 2 * np.exp(-exp_arg)
    I_leak = J_leak * A_m2

    if I_leak < 1e-30:
        return Z_cap

    R_leak = V / I_leak
    # Parallel combination: Z_cap ∥ R_leak
    return (Z_cap * R_leak) / (Z_cap + R_leak)


def calc_Z_path1(omega: float, comp: DerivedComponents) -> complex:
    """
    Path 1 — Field solid (spurious background).

    Circuit: Au → C_dl_Au → e-SiO₂ → t-SiO₂ → Si++
    All in series.

    Args:
        omega: Angular frequency in rad/s.
        comp: DerivedComponents from derive_components().

    Returns:
        Complex impedance of Path 1 for one unit cell.

    Physics note:
        Pure dielectric path through oxide stack. C_dl_Au >> C_eox >> C_tox,
        so series is dominated by t-SiO₂. Scales with A_field.
    """
    Z_dl = _cap_impedance(comp.C_dl_Au, omega)
    Z_eox = Z_oxide(comp.t_eox_m, comp.A_field_m2, EPS_ESIO2, comp.V_dc_V, omega)
    Z_tox = Z_oxide(comp.t_tox_m, comp.A_field_m2, EPS_TSIO2, comp.V_dc_V, omega)
    return _series_impedance(Z_dl, Z_eox, Z_tox)


def calc_Z_path2_single(omega: float, comp: DerivedComponents) -> complex:
    """
    Path 2 — Single open pore (signal path).

    Circuit: C_dl_Au(rim) → R_access → C_dl_SiO₂(σ_DNA) → C_DNA_layer → C_tox_pore
    All in series.

    Args:
        omega: Angular frequency in rad/s.
        comp: DerivedComponents from derive_components().

    Returns:
        Complex impedance of a single open pore.

    Physics note:
        The rim double-layer capacitance is approximated as the pore-area
        fraction of C_dl_Au. R_access is the spreading resistance at the
        pore mouth. DNA modifies C_dl_SiO₂ (Mechanism A) and adds
        C_DNA_layer in series (Mechanism B).
    """
    # Rim C_dl_Au: approximate as pore-area proportional fraction
    # In reality it's at the rim perimeter; we use A_pore as proxy area
    C_dl_Au_rim = EPS0 * EPS_W * comp.A_pore_m2 / comp.lambda_D_m

    Z_dl_rim = _cap_impedance(C_dl_Au_rim, omega)
    Z_R = comp.R_access + 0j
    Z_dl_sio2 = _cap_impedance(comp.C_dl_SiO2, omega)
    Z_dna = _cap_impedance(comp.C_DNA_layer, omega)
    Z_tox = Z_oxide(comp.t_tox_m, comp.A_pore_m2, EPS_TSIO2, comp.V_dc_V, omega)

    return _series_impedance(Z_dl_rim, Z_R, Z_dl_sio2, Z_dna, Z_tox)


def calc_Z_path3_single(omega: float, comp: DerivedComponents) -> complex:
    """
    Path 3 — Single closed pore (photoresist-filled, negligible).

    Circuit: Au → C_PR → t-SiO₂ → Si++
    All in series.

    Args:
        omega: Angular frequency in rad/s.
        comp: DerivedComponents from derive_components().

    Returns:
        Complex impedance of a single closed pore.

    Physics note:
        Photoresist is thick and low-ε, making this path electrically
        invisible. Included for completeness.
    """
    Z_pr = _cap_impedance(comp.C_PR, omega)
    Z_tox = Z_oxide(comp.t_tox_m, comp.A_pore_m2, EPS_TSIO2, comp.V_dc_V, omega)
    return _series_impedance(Z_pr, Z_tox)


def calc_Z_total(omega: float, comp: DerivedComponents) -> complex:
    """
    Total device impedance at angular frequency omega.

    Z_total = 1 / (Y₁ + Y₂_array + Y₃_array)

    where Y = 1/Z is admittance, and path 2 & 3 are repeated N times.

    Args:
        omega: Angular frequency in rad/s.
        comp: DerivedComponents from derive_components().

    Returns:
        Complex total impedance.

    Physics note:
        Three parallel paths between Au (WE) and Si++ (CE).
        The instrument measures Z_total.
    """
    # Path 1 — field (one unit cell, but there's one field region)
    Y1 = 1.0 / calc_Z_path1(omega, comp) if calc_Z_path1(omega, comp) != 0 else 0

    # Path 2 — open pores (N_open in parallel)
    Z2_single = calc_Z_path2_single(omega, comp)
    Y2 = comp.N_open / Z2_single if Z2_single != 0 and comp.N_open > 0 else 0

    # Path 3 — closed pores (N_closed in parallel)
    Z3_single = calc_Z_path3_single(omega, comp)
    Y3 = comp.N_closed / Z3_single if Z3_single != 0 and comp.N_closed > 0 else 0

    Y_total = Y1 + Y2 + Y3
    if Y_total == 0:
        return complex(np.inf, 0)
    return 1.0 / Y_total


# ---------------------------------------------------------------------------
# Frequency sweep — vectorised
# ---------------------------------------------------------------------------

def frequency_sweep(params: DeviceParams,
                    f_min: float = 1.0,
                    f_max: float = 1e7,
                    n_points: int = 200) -> Dict[str, np.ndarray]:
    """
    Compute impedance spectra over a logarithmic frequency range.

    Args:
        params: DeviceParams with user-set values.
        f_min: Minimum frequency in Hz (default 1 Hz).
        f_max: Maximum frequency in Hz (default 10 MHz).
        n_points: Number of frequency points (default 200).

    Returns:
        Dictionary with keys:
            'f'           : frequency array (Hz)
            'omega'       : angular frequency array (rad/s)
            'Z_total'     : complex impedance array (total)
            'Z_path1'     : complex impedance array (path 1)
            'Z_path2_arr' : complex impedance array (path 2 array, N_open pores)
            'Z_path3_arr' : complex impedance array (path 3 array, N_closed pores)
            'Z_mag'       : |Z_total| array
            'Z_phase_deg' : phase of Z_total in degrees
            'components'  : DerivedComponents object

    Physics note:
        All paths are computed independently and combined via admittance
        addition (parallel). The sweep is logarithmically spaced to cover
        the wide frequency range typical of EIS measurements.
    """
    comp = derive_components(params)
    f = np.logspace(np.log10(f_min), np.log10(f_max), n_points)
    omega = 2.0 * np.pi * f

    Z_total = np.zeros(n_points, dtype=complex)
    Z_path1 = np.zeros(n_points, dtype=complex)
    Z_path2_arr = np.zeros(n_points, dtype=complex)
    Z_path3_arr = np.zeros(n_points, dtype=complex)

    for i, w in enumerate(omega):
        # Path 1 — field
        Z_p1 = calc_Z_path1(w, comp)
        Z_path1[i] = Z_p1

        # Path 2 — open pore array
        Z_p2_single = calc_Z_path2_single(w, comp)
        if comp.N_open > 0:
            Z_path2_arr[i] = Z_p2_single / comp.N_open
        else:
            Z_path2_arr[i] = complex(np.inf, 0)

        # Path 3 — closed pore array
        Z_p3_single = calc_Z_path3_single(w, comp)
        if comp.N_closed > 0:
            Z_path3_arr[i] = Z_p3_single / comp.N_closed
        else:
            Z_path3_arr[i] = complex(np.inf, 0)

        # Total
        Z_total[i] = calc_Z_total(w, comp)

    return {
        'f': f,
        'omega': omega,
        'Z_total': Z_total,
        'Z_path1': Z_path1,
        'Z_path2_arr': Z_path2_arr,
        'Z_path3_arr': Z_path3_arr,
        'Z_mag': np.abs(Z_total),
        'Z_phase_deg': np.angle(Z_total, deg=True),
        'components': comp,
    }


def format_eng(value: float, unit: str = '') -> str:
    """
    Format a value in engineering notation with SI prefix.

    Args:
        value: Numeric value to format.
        unit: Unit string to append.

    Returns:
        Formatted string like '1.50 µm' or '34.5 pF'.
    """
    if value == 0:
        return f"0 {unit}".strip()
    if np.isinf(value):
        return f"∞ {unit}".strip()

    prefixes = [
        (1e-15, 'f'), (1e-12, 'p'), (1e-9, 'n'), (1e-6, 'µ'),
        (1e-3, 'm'), (1e0, ''), (1e3, 'k'), (1e6, 'M'), (1e9, 'G'),
        (1e12, 'T'),
    ]
    abs_val = abs(value)
    for scale, prefix in prefixes:
        if abs_val < scale * 1000:
            return f"{value / scale:.3g} {prefix}{unit}".strip()
    return f"{value:.3g} {unit}".strip()
