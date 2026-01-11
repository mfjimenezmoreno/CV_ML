# Usage Examples

This document provides examples of how to use the DOLFINx CV/ML environment.

## Starting the Environment

### Method 1: Using the Quick Start Script (Easiest)

```bash
./start.sh
```

This will build and start the container, then provide you with a URL to access Jupyter Lab.

### Method 2: Using Docker Compose

```bash
# Start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Method 3: Using Docker Directly

```bash
# Build the image
docker build -t dolfinx-cv-ml .

# Run the container
docker run -it -p 8888:8888 -v $(pwd):/workspace dolfinx-cv-ml

# Or run interactively with bash
docker run -it -p 8888:8888 -v $(pwd):/workspace dolfinx-cv-ml /bin/bash
```

### Method 4: Using VS Code DevContainer

1. Install the "Remote - Containers" extension in VS Code
2. Open the repository folder in VS Code
3. Press `F1` and select "Remote-Containers: Reopen in Container"
4. Wait for the container to build
5. Open `cyclic_voltammetry_demo.ipynb`

## Running the Notebook

Once Jupyter Lab is running:

1. Navigate to `http://localhost:8888` in your browser
2. Open `cyclic_voltammetry_demo.ipynb`
3. Run all cells: Click "Run" → "Run All Cells" or press `Shift+Enter` on each cell

## Customizing the Simulation

You can modify the physical parameters in the notebook:

### Electrochemical Parameters

```python
# Change scan rate (V/s)
scan_rate = 0.05  # Slower scan rate

# Change potential window
E_start = -0.5  # Starting potential (V)
E_vertex = 0.5  # Vertex potential (V)

# Change kinetics
k0 = 1e-3  # Slower electron transfer
alpha = 0.3  # Asymmetric transfer coefficient
```

### Transport Parameters

```python
# Change diffusion coefficient
D_O = 5e-10  # Slower diffusion (m^2/s)

# Change bulk concentration
C_O_bulk = 2.0  # Higher concentration (mM)
```

### Numerical Parameters

```python
# Increase mesh resolution
nx = 200  # More elements

# Change time step
dt = t_total / 500  # Smaller time steps
```

## Exporting Results

The notebook automatically saves:
- `cv_results.csv` - Full time series data
- `cv_summary.txt` - Summary statistics
- `cyclic_voltammogram.png` - Main CV plot
- `cv_analysis_plots.png` - Additional analysis plots

## Troubleshooting

### Port 8888 Already in Use

If port 8888 is already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8889:8888"  # Change host port to 8889
```

Then access at `http://localhost:8889`

### Container Build Fails

Try pulling the base image manually:

```bash
docker pull dolfinx/dolfinx:stable
```

### Notebook Kernel Dies

This may happen with large simulations. Increase container resources in Docker Desktop settings:
- Memory: At least 4 GB
- CPUs: At least 2 cores

### Permission Issues

If you encounter permission issues with mounted volumes:

```bash
# On Linux, you may need to add your user to the docker group
sudo usermod -aG docker $USER
# Then log out and back in
```

## Running from Command Line

You can also run Python scripts directly:

```bash
# Enter the running container
docker exec -it dolfinx-cv-ml /bin/bash

# Or run a command directly
docker exec -it dolfinx-cv-ml python3 your_script.py
```

## Stopping and Cleaning Up

```bash
# Stop the container
docker-compose down

# Remove all containers and images
docker-compose down --rmi all

# Remove volumes as well
docker-compose down -v
```

## Advanced: Running in Production

For production use, consider:

1. Remove the empty token/password settings
2. Use environment variables for configuration
3. Set up proper authentication
4. Use a reverse proxy (nginx, traefik)
5. Enable HTTPS

Example with authentication:

```bash
docker run -it -p 8888:8888 \
  -e JUPYTER_TOKEN=your-secret-token \
  -v $(pwd):/workspace \
  dolfinx-cv-ml
```

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify Docker is running: `docker ps`
3. Check container status: `docker-compose ps`
4. Open an issue on GitHub with error details
