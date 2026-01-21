#!/bin/bash

# 1. CHANGE THIS to your package name on PyPI
PKG_NAME="N-FileJ"

# 2. LIST ALL OLD VERSIONS (the ones already on PyPI)
VERSIONS=("0.0.1" "0.0.2" "0.0.3" "0.0.4" "0.0.5" "0.0.6" "0.0.7" "0.0.8" "0.0.9" "0.1.0" "0.1.1" "0.1.2" "0.1.3" "0.1.4" "0.1.5" "0.1.6" "0.1.7" "0.1.8")

for V in "${VERSIONS[@]}"
do
    echo "--------------------------------------"
    echo "Syncing $V from PyPI to GitHub..."
    
    # Create a clean folder for this version's files
    mkdir -p "sync_tmp"
    
    # Download the exact files you already published to PyPI
    pip download --no-deps "$PKG_NAME==$V" -d "sync_tmp"

    # Push the release to GitHub with those files attached
    # Note: Using --target main ensures it links to your current code
    gh release create "v$V" sync_tmp/* --title "v$V" --notes "Archived release from PyPI"

    # Cleanup the temp folder
    rm -rf "sync_tmp"
    
    echo "✅ Version $V is now on GitHub."
done

echo "DONE. All old releases are synced."