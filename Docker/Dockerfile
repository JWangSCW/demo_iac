FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Copy code
COPY . /app

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8080

ENV SCW_ACCESS_KEY=SCWXNVMDB4K8FT13Q4JJ
ENV SCW_SECRET_KEY=c87f18df-2c0c-4d6c-aa31-141effce4948
ENV SCW_DEFAULT_PROJECT_ID=8cfcea18-2aa9-4eb4-8754-4e32a034abec
ENV SCW_DEFAULT_REGION=fr-par
ENV SCW_DEFAULT_ORGANIZATION_ID=e97e853d-3cce-4ebf-acda-ec5d6abc8fa8

# Install Scaleway CLI (platform-aware)
RUN curl -sL https://github.com/scaleway/scaleway-cli/releases/download/v2.39.0/scaleway-cli_2.39.0_linux_amd64 \
    -o /usr/local/bin/scw && chmod +x /usr/local/bin/scw



# CMD ["sh", "-c", "printenv | grep SCW && scw instance server list --output json"]

# Launch FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
