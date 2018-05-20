#!/bin/bash
if [ "$#" -ne 1 ]; then
        stats=$(docker stats --no-stream --format '"{{.Name}}":{"CPU":"{{.CPUPerc}}","Mem":"{{.MemPerc}}","Net":"{{.NetIO}}"}')
        out=$(echo "{$stats}" | tr '\n' ',' | tr -d '[:space:]')
        echo "${out::-1}"
else
        stats=$(docker stats --no-stream --format '"{{.Name}}":{"CPU":"{{.CPUPerc}}","Mem":"{{.MemPerc}}","Net":"{{.NetIO}}"}' "$1")
        out=$(echo "{$stats}" | tr '\n' ',' | tr -d '[:space:]')
        echo "${out::-1}"
fi