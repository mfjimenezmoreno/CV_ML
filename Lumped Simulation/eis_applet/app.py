"""
EIS Biosensor — Dash Application
==================================

Interactive applet for exploring the lumped-circuit impedance model
of a Metal-Insulator-Semiconductor (MIS) capacitor DNA biosensor.

Provides:
  - Bode magnitude and phase plots
  - Nyquist plots (raw & background-subtracted)
  - Live-updating derived values panel
  - Sliders for all physical parameters
"""

import numpy as np
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from physics import (
    DeviceParams, derive_components, frequency_sweep, format_eng,
    EPS0, EPS_W, F_CONST, R_GAS,
)

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    title="EIS Biosensor — Lumped Circuit",
    update_title="Calculating…",
)

# ---------------------------------------------------------------------------
# Slider definitions
# ---------------------------------------------------------------------------
SLIDER_DEFS = [
    # (id, label, min, max, default, step, unit, group)
    ("r_pore", "r_pore", 0.5, 2.5, 1.5, 0.1, "µm", "Geometry"),
    ("pitch", "pitch", 5, 50, 20, 1, "µm", "Geometry"),
    ("t_tox", "t_tox", 50, 1000, 500, 10, "nm", "Geometry"),
    ("t_eox", "t_eox", 100, 800, 400, 10, "nm", "Geometry"),
    ("I_mM", "I (ionic str.)", 1, 150, 10, 1, "mM", "Electrolyte"),
    ("T_K", "T", 273, 320, 298, 1, "K", "Electrolyte"),
    ("sigma_DNA", "σ_DNA", 0, 5, 0, 0.1, "mC/m²", "DNA signal"),
    ("c_DNA", "c_DNA", 0, 1, 0, 0.01, "—", "DNA signal"),
    ("N_total", "N_total", 10, 500, 100, 10, "—", "Array"),
    ("f_open", "f_open", 0.05, 1.0, 0.7, 0.05, "—", "Array"),
]


def _make_slider(sid, label, vmin, vmax, default, step, unit):
    """Build a single slider row with label displaying current value."""
    marks_count = 5
    mark_values = np.linspace(vmin, vmax, marks_count)
    marks = {float(v): f"{v:g}" for v in mark_values}

    return html.Div([
        html.Label(
            id=f"{sid}-label",
            children=f"{label} = {default} {unit}",
            style={"fontWeight": "bold", "fontSize": "13px"},
        ),
        dcc.Slider(
            id=sid,
            min=vmin,
            max=vmax,
            value=default,
            step=step,
            marks=marks,
            tooltip={"placement": "bottom", "always_visible": False},
            updatemode="mouseup",
        ),
    ], style={"marginBottom": "10px"})


def _build_slider_groups():
    """Organise sliders by group into labelled sections."""
    groups = {}
    for sid, label, vmin, vmax, default, step, unit, group in SLIDER_DEFS:
        groups.setdefault(group, []).append(
            _make_slider(sid, label, vmin, vmax, default, step, unit)
        )

    sections = []
    for group_name, sliders in groups.items():
        sections.append(html.Div([
            html.H4(group_name,
                     style={"marginTop": "16px", "marginBottom": "6px",
                            "color": "#2c3e50", "borderBottom": "1px solid #bdc3c7",
                            "paddingBottom": "4px"}),
            *sliders,
        ]))
    return sections


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
app.layout = html.Div([
    # Header
    html.Div([
        html.H2("EIS Biosensor — Lumped Circuit Model",
                 style={"margin": "0", "color": "#ecf0f1"}),
        html.P("Interactive impedance explorer for MIS capacitor DNA biosensor",
               style={"margin": "2px 0 0 0", "color": "#bdc3c7", "fontSize": "14px"}),
    ], style={
        "background": "#2c3e50", "padding": "14px 24px",
        "marginBottom": "16px", "borderRadius": "4px",
    }),

    # Main grid: sliders | plots
    html.Div([
        # Left panel — sliders + derived values
        html.Div([
            html.Div(
                _build_slider_groups(),
                style={"maxHeight": "55vh", "overflowY": "auto",
                       "paddingRight": "8px"},
            ),
            html.Hr(),
            html.H4("Derived Values",
                     style={"marginTop": "8px", "color": "#2c3e50"}),
            html.Div(id="derived-values",
                     style={"fontSize": "13px", "fontFamily": "monospace",
                            "lineHeight": "1.7"}),
        ], style={
            "width": "320px", "minWidth": "280px",
            "padding": "12px", "background": "#f8f9fa",
            "borderRadius": "4px", "border": "1px solid #dee2e6",
            "marginRight": "16px", "overflowY": "auto",
            "maxHeight": "92vh",
        }),

        # Right panel — plots
        html.Div([
            dcc.Graph(id="bode-plot", style={"height": "44vh"}),
            html.Div([
                dcc.Graph(id="nyquist-raw", style={"height": "42vh", "width": "50%"}),
                dcc.Graph(id="nyquist-sub", style={"height": "42vh", "width": "50%"}),
            ], style={"display": "flex"}),
        ], style={"flex": "1", "minWidth": "0"}),

    ], style={"display": "flex", "padding": "0 16px"}),

], style={"fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"})


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
SLIDER_INPUTS = [Input(sid, "value") for sid, *_ in SLIDER_DEFS]


@app.callback(
    Output("bode-plot", "figure"),
    Output("nyquist-raw", "figure"),
    Output("nyquist-sub", "figure"),
    Output("derived-values", "children"),
    *[Output(f"{sid}-label", "children") for sid, *_ in SLIDER_DEFS],
    SLIDER_INPUTS,
)
def update_all(*slider_values):
    """
    Master callback — recomputes physics and updates all plots + derived panel.

    Args:
        *slider_values: Current values from all sliders, in SLIDER_DEFS order.

    Returns:
        Tuple of (bode_fig, nyquist_raw_fig, nyquist_sub_fig, derived_div,
                  *slider_labels).
    """
    # Unpack slider values
    r_pore, pitch, t_tox, t_eox, I_mM, T_K, sigma_DNA, c_DNA, N_total, f_open = slider_values

    # Build params
    params = DeviceParams(
        r_pore_um=r_pore,
        pitch_um=pitch,
        t_tox_nm=t_tox,
        t_eox_nm=t_eox,
        I_mM=I_mM,
        T_K=T_K,
        sigma_DNA_mCm2=sigma_DNA,
        c_DNA=c_DNA,
        N_total=int(N_total),
        f_open=f_open,
    )

    # Run sweep
    result = frequency_sweep(params, f_min=1.0, f_max=1e6, n_points=300)
    comp = result['components']
    f = result['f']

    # === BODE PLOT ===
    bode_fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        subplot_titles=("Bode Magnitude", "Bode Phase"),
        vertical_spacing=0.08,
    )

    # Magnitude traces
    for label, key, color, dash_style in [
        ("Z_total", "Z_total", "#2c3e50", "solid"),
        ("Z_path1 (field)", "Z_path1", "#e74c3c", "dash"),
        ("Z_path2 (pore array)", "Z_path2_arr", "#27ae60", "dot"),
        ("Z_path3 (closed)", "Z_path3_arr", "#3498db", "dashdot"),
    ]:
        Z = result[key]
        mag = np.abs(Z)
        # Skip if all infinite
        if np.all(np.isinf(mag)):
            continue
        bode_fig.add_trace(go.Scatter(
            x=f, y=mag, name=label, mode="lines",
            line=dict(color=color, dash=dash_style, width=2),
            legendgroup=label,
        ), row=1, col=1)

    # f_lateral reference line
    if comp.f_lateral > 0 and comp.f_lateral < 1e6:
        for row in [1, 2]:
            bode_fig.add_vline(
                x=comp.f_lateral, row=row, col=1,
                line=dict(color="orange", dash="dash", width=1),
                annotation_text="f_lat" if row == 1 else None,
                annotation_position="top right" if row == 1 else None,
            )

    # Phase trace
    phase = np.angle(result['Z_total'], deg=True)
    bode_fig.add_trace(go.Scatter(
        x=f, y=phase, name="Phase (Z_total)", mode="lines",
        line=dict(color="#2c3e50", width=2),
        showlegend=False,
    ), row=2, col=1)

    # −90° reference
    bode_fig.add_hline(
        y=-90, row=2, col=1,
        line=dict(color="grey", dash="dot", width=1),
        annotation_text="−90° (ideal C)",
        annotation_position="bottom right",
    )

    # Compute magnitude y-range from finite data, snapped to nearest decade
    all_mag = np.concatenate([
        np.abs(result['Z_total']), np.abs(result['Z_path1']),
        np.abs(result['Z_path2_arr']), np.abs(result['Z_path3_arr']),
    ])
    finite_mag = all_mag[np.isfinite(all_mag) & (all_mag > 0)]
    if len(finite_mag) > 0:
        log_min = np.floor(np.log10(np.percentile(finite_mag, 1))) - 0.5
        log_max = np.ceil(np.log10(np.percentile(finite_mag, 99))) + 0.5
    else:
        log_min, log_max = 4, 14

    bode_fig.update_xaxes(type="log", title_text="Frequency (Hz)",
                           range=[0, 6], row=2, col=1)
    bode_fig.update_xaxes(type="log", range=[0, 6], row=1, col=1)
    bode_fig.update_yaxes(type="log", title_text="|Z| (Ω)",
                           range=[log_min, log_max], row=1, col=1)
    bode_fig.update_yaxes(title_text="Phase (°)", range=[-95, 5], row=2, col=1)
    bode_fig.update_layout(
        margin=dict(l=60, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        uirevision="bode",
    )

    # === NYQUIST — RAW ===
    Z_t = result['Z_total']
    nyq_raw = go.Figure()
    nyq_raw.add_trace(go.Scatter(
        x=Z_t.real, y=-Z_t.imag, mode="lines",
        name="Z_total", line=dict(color="#2c3e50", width=2),
    ))

    # Frequency markers
    for f_mark, marker_label in [(10, "10 Hz"), (1e3, "1 kHz"), (1e5, "100 kHz")]:
        idx = np.argmin(np.abs(f - f_mark))
        nyq_raw.add_trace(go.Scatter(
            x=[Z_t[idx].real], y=[-Z_t[idx].imag],
            mode="markers+text", text=[marker_label],
            textposition="top right",
            marker=dict(size=8, color="#e74c3c"),
            showlegend=False,
        ))

    nyq_raw.update_layout(
        title="Nyquist — Z_total",
        xaxis_title="Re(Z) (Ω)", yaxis_title="−Im(Z) (Ω)",
        yaxis_scaleanchor="x", yaxis_scaleratio=1,
        margin=dict(l=60, r=20, t=40, b=40),
        template="plotly_white",
    )

    # === NYQUIST — BACKGROUND SUBTRACTED ===
    Z_sub = Z_t - result['Z_path1']  # remove field contribution (Path 1)
    nyq_sub = go.Figure()
    nyq_sub.add_trace(go.Scatter(
        x=Z_sub.real, y=-Z_sub.imag, mode="lines",
        name="Z_total − Z_path1", line=dict(color="#27ae60", width=2),
    ))

    for f_mark, marker_label in [(10, "10 Hz"), (1e3, "1 kHz"), (1e5, "100 kHz")]:
        idx = np.argmin(np.abs(f - f_mark))
        nyq_sub.add_trace(go.Scatter(
            x=[Z_sub[idx].real], y=[-Z_sub[idx].imag],
            mode="markers+text", text=[marker_label],
            textposition="top right",
            marker=dict(size=8, color="#e74c3c"),
            showlegend=False,
        ))

    nyq_sub.update_layout(
        title="Nyquist — Background Subtracted",
        xaxis_title="Re(Z) (Ω)", yaxis_title="−Im(Z) (Ω)",
        yaxis_scaleanchor="x", yaxis_scaleratio=1,
        margin=dict(l=60, r=20, t=40, b=40),
        template="plotly_white",
    )

    # === DERIVED VALUES PANEL ===
    derived = html.Div([
        html.Table([
            html.Tr([html.Td("λ_D"), html.Td(format_eng(comp.lambda_D_m, "m"))]),
            html.Tr([html.Td("C_tox (pore)"), html.Td(format_eng(comp.C_tox_pore, "F"))]),
            html.Tr([html.Td("C_dl_SiO₂(σ)"), html.Td(format_eng(comp.C_dl_SiO2, "F"))]),
            html.Tr([html.Td("C_DNA_layer"),
                      html.Td(format_eng(comp.C_DNA_layer, "F")
                              if not np.isinf(comp.C_DNA_layer)
                              else "∞ (no DNA)")]),
            html.Tr([html.Td("R_access"), html.Td(format_eng(comp.R_access, "Ω"))]),
            html.Tr([html.Td("φ_s"), html.Td(f"{comp.phi_s_V * 1e3:.2f} mV")]),
            html.Tr([html.Td("N_open"), html.Td(str(comp.N_open))]),
            html.Tr([html.Td("f_lateral"), html.Td(format_eng(comp.f_lateral, "Hz"))]),
            html.Tr([html.Td("f_RC_pore"), html.Td(format_eng(comp.f_RC_pore, "Hz"))]),
        ], style={"width": "100%", "borderCollapse": "collapse"}),
    ])

    # === SLIDER LABELS ===
    labels = []
    for sid, label, vmin, vmax, default, step, unit, group in SLIDER_DEFS:
        idx = [s[0] for s in SLIDER_DEFS].index(sid)
        val = slider_values[idx]
        labels.append(f"{label} = {val} {unit}")

    return (bode_fig, nyq_raw, nyq_sub, derived, *labels)


# ---------------------------------------------------------------------------
# Export for run.py
# ---------------------------------------------------------------------------
server = app.server  # for production WSGI if needed
