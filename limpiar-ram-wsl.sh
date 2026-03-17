#!/bin/bash
# Script para liberar caché de RAM en WSL 2
echo "Liberando PageCache, dentries y inodes..."
echo 3 | sudo tee /proc/sys/vm/drop_caches
echo "¡Memoria liberada exitosamente!"
