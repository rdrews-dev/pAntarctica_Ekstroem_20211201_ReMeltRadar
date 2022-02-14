#!/bin/bash
#
# Auth: J.D. Hawkins
# Date: 2022-02-10

# Define variables
PROJ_ROOT="../../../../"
PYTHON_ROOT="Src/ApRES/Rover/HF/"

PYTHON_FILES=(
    "generate_doc_graphs.py"
)

# Execute python files
for f in ${PYTHON_FILES[@]}; do
echo "Executing $PROJ_ROOT$PYTHON_ROOT$f"
python3 "$PROJ_ROOT$PYTHON_ROOT$f"
done