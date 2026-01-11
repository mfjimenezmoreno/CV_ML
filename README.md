# CV_ML - Cyclic Voltammetry Simulation with DOLFINx

This repository contains a complete setup for running cyclic voltammetry (CV) simulations using FEniCSx/DOLFINx with Butler-Volmer kinetics and diffusion-only transport.

## Features

- 🐬 **DOLFINx**: Uses the stable DOLFINx image for finite element simulations
- ⚡ **Butler-Volmer Kinetics**: Implements electrochemical kinetics at the electrode surface
- 🌊 **Diffusion Transport**: Solves the diffusion equation for mass transport
- 📊 **Comprehensive Visualization**: Uses matplotlib and seaborn for publication-quality plots
- 📓 **Interactive Notebook**: Fully documented Jupyter notebook with step-by-step analysis
- 🐋 **Docker Support**: Complete containerization with Docker and docker-compose
- 💻 **VS Code Integration**: DevContainer configuration for seamless development

## Quick Start

### Using Docker Compose (Recommended)

1. Build and start the container:
```bash
docker-compose up --build
```

2. Open your browser and navigate to:
```
http://localhost:8888
```

3. Open the `cyclic_voltammetry_demo.ipynb` notebook and run the cells!

### Using VS Code DevContainer

1. Open the repository in VS Code
2. Install the "Remote - Containers" extension
3. Press `F1` and select "Remote-Containers: Reopen in Container"
4. Wait for the container to build
5. Open `cyclic_voltammetry_demo.ipynb` and run it

### Using Docker Manually

```bash
# Build the image
docker build -t dolfinx-cv-ml .

# Run the container
docker run -it -p 8888:8888 -v $(pwd):/workspace dolfinx-cv-ml

# Access Jupyter Lab at http://localhost:8888
```

## Repository Structure

```
.
├── Dockerfile                      # DOLFINx container definition
├── docker-compose.yml             # Docker Compose configuration
├── .devcontainer/
│   └── devcontainer.json         # VS Code DevContainer settings
├── requirements.txt               # Python package dependencies
├── cyclic_voltammetry_demo.ipynb # Main demonstration notebook
└── README.md                      # This file
```

## Requirements

The following Python packages are included:
- `tqdm` - Progress bars for simulations
- `pandas` - Data manipulation and analysis
- `matplotlib` - Plotting and visualization
- `seaborn` - Statistical data visualization
- `scipy` - Scientific computing
- `numpy` - Numerical computing

DOLFINx and its dependencies (FEniCSx, PETSc, etc.) are included in the base Docker image.

## Simulation Details

The notebook demonstrates:
1. **1D diffusion problem** with a time-dependent boundary condition
2. **Butler-Volmer kinetics** describing electron transfer at the electrode
3. **Cyclic potential sweep** from starting potential to vertex and back
4. **Finite element method** using DOLFINx for solving the diffusion equation
5. **Comprehensive analysis** including peak currents, potentials, and reversibility

### Physical Parameters

- **Redox reaction**: O + e⁻ ⇌ R
- **Diffusion coefficients**: D = 1×10⁻⁹ m²/s
- **Standard rate constant**: k₀ = 1×10⁻² m/s
- **Transfer coefficient**: α = 0.5 (symmetric)
- **Scan rate**: 0.1 V/s
- **Temperature**: 298.15 K (25°C)

## Output

The notebook generates:
- 📈 **Cyclic voltammogram** (current vs. potential)
- 📊 **Time-series plots** (current, potential, concentration vs. time)
- 📉 **Analysis plots** (surface concentration behavior)
- 📁 **Data export** (CSV file with all results)
- 📝 **Summary report** (text file with key parameters)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

See LICENSE file for details.

## References

- FEniCSx/DOLFINx: https://fenicsproject.org/
- Cyclic Voltammetry: Bard, A. J., & Faulkner, L. R. (2001). Electrochemical Methods: Fundamentals and Applications.
- Butler-Volmer Equation: https://en.wikipedia.org/wiki/Butler–Volmer_equation
