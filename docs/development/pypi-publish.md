# PyPI Publishing Guide

Quick reference for publishing slurm-dashboard to PyPI.

## Prerequisites

```bash
# Install build tools
pip install build twine

# Verify PyPI credentials
# Username: soerendip
# API token stored in ~/.pypirc or use prompt
```

## Publishing Workflow

### 1. Prepare Release

```bash
# Update version in git (hatch-vcs reads from tags)
git tag -a v0.3.0 -m "Release v0.3.0"

# Update CHANGELOG.md with release notes
vim CHANGELOG.md

# Commit changes
git add CHANGELOG.md
git commit -m "Prepare release v0.3.0"
git push origin main
git push origin v0.3.0
```

### 2. Build Frontend

Frontend must be built before packaging:

```bash
./build_frontend.sh

# Verify dist exists
ls -la frontend/dist/
```

### 3. Build Python Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
python -m build

# Or with uv
uv build
```

This creates:
- `dist/slurm_dashboard-0.3.0-py3-none-any.whl`
- `dist/slurm-dashboard-0.3.0.tar.gz`

### 4. Verify Package

```bash
# Check wheel contents - should include backend/app/static/
unzip -l dist/slurm_dashboard-*.whl | grep static

# Expected output:
#   backend/app/static/index.html
#   backend/app/static/assets/...
#   backend/app/static/REIT_logo.png
#   backend/app/static/vite.svg

# Test installation locally
pip install dist/slurm_dashboard-*.whl[web]
slurm-dashboard --help
```

### 5. Upload to Test PyPI (Recommended First)

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# When prompted:
# Username: soerendip
# Password: [your TestPyPI token or password]

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    slurm-dashboard[web]

# Verify it works
slurm-dashboard --help
```

### 6. Upload to Production PyPI

```bash
# Upload to PyPI
twine upload dist/*

# When prompted:
# Username: soerendip
# Password: [your PyPI token or password]

# Test installation
pip install slurm-dashboard[web]
slurm-dashboard --help
```

## Configuration Files

### ~/.pypirc

Create this file to avoid entering credentials each time:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = soerendip
password = <your-api-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = soerendip
password = <your-testpypi-token>
```

**Security Note**: Use API tokens instead of passwords. Generate at:
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/

Set token as password in format: `pypi-AgEIcH...`

### Alternative: Environment Variables

```bash
export TWINE_USERNAME=soerendip
export TWINE_PASSWORD=pypi-AgEIcH...

twine upload dist/*
```

## Troubleshooting

### Frontend Missing from Wheel

If `unzip -l` doesn't show static files:

```bash
# Ensure frontend was built
./build_frontend.sh
ls -la frontend/dist/

# Check pyproject.toml has correct config
grep -A2 "force-include" pyproject.toml

# Should show:
# [tool.hatch.build.targets.wheel.force-include]
# "frontend/dist" = "backend/app/static"

# Rebuild
rm -rf dist/
python -m build
```

### Version Not Updating

```bash
# Verify git tag
git describe --tags

# If wrong, delete and recreate
git tag -d v0.3.0
git push origin :refs/tags/v0.3.0
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0

# Rebuild
rm -rf dist/
python -m build
```

### Upload Fails with 403

- Check username is correct: `soerendip`
- Verify API token is valid
- Ensure package name `slurm-dashboard` is available
- For first upload, you may need to register the package name

## Complete Release Checklist

- [ ] All tests passing
- [ ] CHANGELOG.md updated with release notes
- [ ] Version tag created (e.g., v0.3.0)
- [ ] Frontend built (`./build_frontend.sh`)
- [ ] Package built (`python -m build`)
- [ ] Wheel verified (contains static files)
- [ ] Local installation tested
- [ ] Uploaded to Test PyPI
- [ ] Tested installation from Test PyPI
- [ ] Uploaded to production PyPI
- [ ] Tested installation from production PyPI
- [ ] GitHub/GitLab release created with notes
- [ ] Documentation updated (if needed)
- [ ] Announced to users (if applicable)

## Quick Commands

```bash
# Full release workflow
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin main v0.3.0
./build_frontend.sh
rm -rf dist/ && python -m build
twine upload --repository testpypi dist/*
# Test installation
twine upload dist/*  # Production
```

## Links

- PyPI package: https://pypi.org/project/slurm-dashboard/
- Test PyPI: https://test.pypi.org/project/slurm-dashboard/
- Manage account: https://pypi.org/manage/account/
- API tokens: https://pypi.org/manage/account/token/
