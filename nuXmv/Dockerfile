# Base image
FROM debian:bullseye-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/nuxmv

# Attempt to download nuXmv using the new link
RUN set -e; \
    echo "Attempting to download nuXmv..."; \
    wget "https://nuxmv.fbk.eu/theme/download.php?file=nuXmv-2.0.0-linux64.tar.gz" -O /tmp/nuxmv.tar.gz || { \
    echo "Failed to download nuXmv. Please manually place 'nuXmv-2.0.0-linux64.tar.gz' in the current directory."; \
    exit 1; \
    }

# Extract and install nuXmv
RUN tar -xvzf /tmp/nuxmv.tar.gz -C /opt/nuxmv --strip-components=1 \
    && rm /tmp/nuxmv.tar.gz

RUN ls -l /opt/nuxmv

# Add nuXmv to PATH
ENV PATH="/opt/nuxmv/bin:${PATH}"

# Default command for the container
CMD ["nuXmv"]