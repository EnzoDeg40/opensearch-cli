# opensearch-cli

CLI to inspect OpenSearch without the dashboard.

## Installation

```bash
pip install opensearch-cli
```

## Usage

```bash
# List all indices
os-cli --list

# Show documents from an index
os-cli my_index --limit 20

# Show documents with embedding vectors
os-cli my_index --show-embedding
```

## Configuration

Set environment variables or use a `.env` file:

```bash
# Option 1: JSON config
OPENSEARCH_URL='{"endpoint": "https://...", "username": "admin", "password": "..."}'

# Option 2: URL
OPENSEARCH_URL=https://localhost:9200

# Option 3: Separate vars
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
```

## License

MIT
