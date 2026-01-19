cat > data/README.md << 'EOF'

# Data policy

This public repository does not include any real library data.

- `data/raw/`, `data/interim/`, and `data/processed/` are intentionally gitignored.
- Only small simulated datasets may be stored under `data/simulated/` for reproducibility.

When real data becomes available, it should be placed locally in `data/raw/` and processed through the pipeline.
EOF
