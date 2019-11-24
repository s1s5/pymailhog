#!/bin/bash
rm -fr PyMailHog
rm -fr src/assets/__pycache__
python3 -m zipapp src -o PyMailHog -p "/usr/bin/env python3"
chmod +x PyMailHog
