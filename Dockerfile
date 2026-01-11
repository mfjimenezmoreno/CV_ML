# Use the stable DOLFINx image from FEniCS project
FROM dolfinx/dolfinx:stable

# Set working directory
WORKDIR /workspace

# Install additional Python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Jupyter Lab for running notebooks
RUN pip3 install --no-cache-dir jupyterlab

# Expose Jupyter Lab port
EXPOSE 8888

# Set up environment
ENV PYTHONUNBUFFERED=1

# Default command to start Jupyter Lab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]
