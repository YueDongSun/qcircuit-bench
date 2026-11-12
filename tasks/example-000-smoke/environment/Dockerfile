FROM python:3.11.11-slim-bookworm

# Build from the repository root:
#   docker build -f tasks/example-000-smoke/environment/Dockerfile .
# Packages are installed at image build. Do not use the network at test time.

RUN pip install --no-cache-dir \
    "cirq==1.7.0" \
    "numpy==2.4.6" \
    "qiskit==2.6.2" \
    "qiskit-aer==0.18.2" \
    "pytest==9.2.0" \
    "hatchling==1.33.0"

COPY pyproject.toml README.md LICENSE /opt/qcbench/
COPY src /opt/qcbench/src
RUN pip install --no-cache-dir --no-build-isolation --no-deps /opt/qcbench

WORKDIR /workspace
