#!/bin/bash

# Image Optimization Script for SwiftHost Website
# This script converts JPG/PNG images to WebP format with quality control

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "Error: ImageMagick is not installed. Please install it first."
    echo "Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "MacOS: brew install imagemagick"
    echo "Windows: Download from https://imagemagick.org/script/download.php"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p images/optimized

# Process all JPG files
for file in images/*.jpg; do
    if [ -f "$file" ]; then
        filename=$(basename -- "$file")
        name="${filename%.*}"
        
        echo "Converting $filename to WebP..."
        
        # Create WebP version with 85% quality
        convert "$file" -resize "1920x1080>" -quality 85 -define webp:lossless=false "images/optimized/${name}.webp"
        
        # Create thumbnail version
        convert "$file" -resize "400x300>" -quality 75 -define webp:lossless=false "images/optimized/${name}-thumb.webp"
        
        echo "✓ Converted $filename to WebP"
    fi
done

# Process all PNG files
for file in images/*.png; do
    if [ -f "$file" ]; then
        filename=$(basename -- "$file")
        name="${filename%.*}"
        
        echo "Converting $filename to WebP..."
        
        # Create WebP version with lossless for PNGs
        convert "$file" -resize "1920x1080>" -define webp:lossless=true "images/optimized/${name}.webp"
        
        echo "✓ Converted $filename to WebP"
    fi
done

echo "Image optimization complete! Optimized images are in images/optimized/ directory."
echo "Remember to update your HTML to use the new WebP images with fallbacks." 