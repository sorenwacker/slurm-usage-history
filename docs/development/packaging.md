# Packaging Guide

This guide explains how to build and publish the slurm-dashboard package to PyPI.

## Package Structure

The package includes both Python backend and pre-built React frontend:

```
slurm-dashboard/
├── src/slurm_usage_history/     # Python source
├── backend/                      # FastAPI application
│   └── app/
│       └── static/              # Pre-built frontend (included in wheel)
├── frontend/                    # React source (not included in wheel)
│   └── dist/                   # Built frontend (copied to backend/app/static)
└── pyproject.toml
```

## Building the Package

### 1. Build Frontend

The frontend must be built before packaging:

```bash
./build_frontend.sh
```

This creates `frontend/dist/` which will be included in the wheel at `backend/app/static/`.

### 2. Build Python Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
python -m build

# Or with uv
uv build
```

This creates:
- `dist/slurm_dashboard-X.Y.Z-py3-none-any.whl` - Wheel with frontend included
- `dist/slurm-dashboard-X.Y.Z.tar.gz` - Source distribution

### 3. Verify Package Contents

```bash
# Check wheel contents
unzip -l dist/slurm_dashboard-*.whl | grep static

# Should show:
# backend/app/static/index.html
# backend/app/static/assets/...
```

## Publishing to PyPI

### Test PyPI (Recommended First)

```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Install from Test PyPI to verify
pip install --index-url https://test.pypi.org/simple/ slurm-dashboard[web]
```

### Production PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# Verify installation
pip install slurm-dashboard[web]
```

## Version Management

Version is managed by `hatch-vcs` from git tags:

```bash
# Create new version tag
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0

# Version will be automatically set from tag
```

## Configuration Files

### pyproject.toml

Key sections for packaging:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/slurm_usage_history"]
artifacts = ["backend/app/static"]

[tool.hatch.build.targets.wheel.force-include]
"frontend/dist" = "backend/app/static"
```

This ensures `frontend/dist/` is copied to `backend/app/static/` in the wheel.

### MANIFEST.in

Includes additional files in source distribution:

```
include README.md
include LICENSE
include CHANGELOG.md
recursive-include frontend/dist *
recursive-include backend/app/static *
```

## Frontend Serving

The backend serves static frontend files from two possible locations:

1. **Development**: `frontend/dist/` (relative to repository root)
2. **Packaged**: `backend/app/static/` (included in wheel)

See `backend/app/main.py` for implementation.

## Troubleshooting

### Frontend not found after pip install

Check if static files are in the wheel:

```bash
unzip -l dist/slurm_dashboard-*.whl | grep static
```

If missing, ensure:
1. Frontend was built: `./build_frontend.sh`
2. `frontend/dist/` directory exists
3. `pyproject.toml` has correct `force-include` configuration

### Import errors after pip install

Check installed package structure:

```bash
pip show -f slurm-dashboard | grep static
```

### Version not updating

Ensure git tag is created and pushed:

```bash
git describe --tags
git push origin v0.3.0
```

## Complete Release Workflow

```bash
# 1. Update CHANGELOG.md
vim CHANGELOG.md

# 2. Commit changes
git add -A
git commit -m "Prepare release v0.3.0"

# 3. Create and push tag
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin main
git push origin v0.3.0

# 4. Build frontend
./build_frontend.sh

# 5. Build package
python -m build

# 6. Test locally
pip install dist/slurm_dashboard-0.3.0-py3-none-any.whl[web]
uvicorn backend.app.main:app --port 8100

# 7. Test on Test PyPI
twine upload --repository testpypi dist/*

# 8. Upload to PyPI
twine upload dist/*
```
