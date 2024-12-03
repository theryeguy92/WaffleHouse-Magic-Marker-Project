# Base image
FROM debian:bullseye-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/nuxmv

# Download and extract the Linux version of nuXmv
RUN wget "https://nuxmv.fbk.eu/theme/download.php?file=nuXmv-2.0.0-linux64.tar.gz" -O /tmp/nuxmv.tar.gz \
    && tar -xvzf /tmp/nuxmv.tar.gz -C /opt/nuxmv --strip-components=1 \
    && chmod +x /opt/nuxmv/bin/nuXmv \
    && rm /tmp/nuxmv.tar.gz

# Add /opt/nuxmv/bin to PATH
ENV PATH="/opt/nuxmv/bin:${PATH}"

# Default command
CMD ["nuXmv"]
