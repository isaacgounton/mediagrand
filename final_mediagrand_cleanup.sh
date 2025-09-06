#!/bin/bash

# Final MediaGrand cleanup script
# This script handles the remaining domain and URL patterns

echo "🔧 Final MediaGrand cleanup - handling remaining patterns..."

# Function to replace patterns in files
fix_remaining_patterns() {
    local pattern="$1"
    local replacement="$2"
    local description="$3"
    
    echo "Fixing $description..."
    
    # Find files containing the pattern and replace
    find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" -o -name "*.sh" -o -name "*.html" -o -name "*.js" -o -name "*.css" -o -name "Dockerfile" -o -name "*.conf" -o -name "*.ini" -o -name "*.env" \) -not -name "*.bak" | xargs grep -l "$pattern" 2>/dev/null | while read -r file; do
        if [ -f "$file" ]; then
            # Create backup if not already exists
            [ ! -f "${file}.bak" ] && cp "$file" "${file}.bak"
            
            # Replace the pattern
            sed -i "s|$pattern|$replacement|g" "$file"
            echo "✅ Updated: $file"
        fi
    done
}

# Fix remaining patterns
fix_remaining_patterns "tts\.mediagrand\.com" "tts.mediagrand.com" "TTS domain dots"
fix_remaining_patterns "shorts\.mediagrand\.com" "shorts.mediagrand.com" "Shorts domain dots"  
fix_remaining_patterns "admin@mediagrand\.local" "admin@mediagrand.local" "Email dots"
fix_remaining_patterns "github\.com/isaacgounton/mediagrand" "github.com/isaacgounton/mediagrand" "GitHub URL dots"
fix_remaining_patterns "hub\.docker\.com/r/isaacgounton/mediagrand" "hub.docker.com/r/isaacgounton/mediagrand" "Docker Hub URL dots"

# Fix any container/network names that might have been missed
fix_remaining_patterns "mediagrand-redis" "mediagrand-redis" "Redis container names"
fix_remaining_patterns "mediagrand-network" "mediagrand-network" "Network names"
fix_remaining_patterns "mediagrand_data" "mediagrand_data" "Volume names"

# Fix any remaining docker image references
fix_remaining_patterns "isaacgounton/mediagrand" "isaacgounton/mediagrand" "Docker image references"

echo "✅ Final cleanup completed!"
echo ""
echo "🔍 Checking for any remaining references..."

# Check for any missed dahopevi references
if grep -r "dahopevi" . --exclude-dir=.git --exclude="*.bak" 2>/dev/null; then
    echo "⚠️  Found remaining 'dahopevi' references above"
else
    echo "✅ No remaining 'dahopevi' references found"
fi

# Check for any missed DahoPevi references
if grep -r "DahoPevi" . --exclude-dir=.git --exclude="*.bak" 2>/dev/null; then
    echo "⚠️  Found remaining 'DahoPevi' references above"
else
    echo "✅ No remaining 'DahoPevi' references found"
fi

echo ""
echo "🎉 MediaGrand renaming process is complete!"
echo ""
echo "📋 Summary of changes:"
echo "• All code files updated to use 'MediaGrand' branding"
echo "• Configuration files updated"
echo "• Documentation updated"
echo "• Docker configurations updated"
echo "• Scripts and deployment files updated"
echo ""
echo "⚠️  Manual tasks still needed:"
echo "1. Update your Docker Hub repository name"
echo "2. Update domain DNS settings"
echo "3. Update external service configurations"
echo "4. Test the application"
echo "5. Consider updating your Git repository name"