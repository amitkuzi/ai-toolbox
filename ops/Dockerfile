FROM python:3.12-slim

WORKDIR /workspace

# Install git and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY scripts/ ./scripts/
COPY catalog/ ./catalog/
COPY rules/ ./rules/
COPY profiles/ ./profiles/
COPY .git/ ./.git/

# Install Python dependencies
RUN pip install --no-cache-dir pyyaml python-ulid

# Configure git (required for commit author)
RUN git config --global user.email "curator@localhost" && \
    git config --global user.name "AI Toolbox Curator (Docker)"

# Default command: run daily refresh
CMD ["python", "scripts/store.py", "project"]
