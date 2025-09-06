#!/bin/bash

# MediaGrand Renaming Script
# This script renames all occurrences of mediagrand, MediaGrand, MEDIAGRAND, 
# MediaGrand, and other variations to mediagrand

set -e

echo "🚀 Starting MediaGrand renaming process..."

# Define color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to safely replace text in files
safe_replace() {
    local search_pattern="$1"
    local replacement="$2"
    local file_pattern="$3"
    local description="$4"
    
    print_status "Replacing $description..."
    
    # Find files that contain the pattern
    if command -v grep >/dev/null 2>&1; then
        local files=$(find . -type f \( $file_pattern \) -exec grep -l "$search_pattern" {} \; 2>/dev/null || true)
        
        if [ -n "$files" ]; then
            echo "$files" | while read -r file; do
                if [ -f "$file" ]; then
                    # Create backup
                    cp "$file" "${file}.bak"
                    
                    # Perform replacement
                    if command -v sed >/dev/null 2>&1; then
                        sed -i "s/$search_pattern/$replacement/g" "$file"
                        print_success "Updated: $file"
                    else
                        print_error "sed command not found"
                        return 1
                    fi
                fi
            done
        else
            print_warning "No files found containing '$search_pattern'"
        fi
    else
        print_error "grep command not found"
        return 1
    fi
}

# Function to rename files and directories
rename_paths() {
    print_status "Renaming files and directories containing 'mediagrand'..."
    
    # Find and rename files
    find . -name "*mediagrand*" -type f 2>/dev/null | while read -r file; do
        if [ -f "$file" ]; then
            local dir=$(dirname "$file")
            local basename=$(basename "$file")
            local new_name=$(echo "$basename" | sed 's/mediagrand/mediagrand/g')
            local new_path="$dir/$new_name"
            
            if [ "$file" != "$new_path" ]; then
                mv "$file" "$new_path"
                print_success "Renamed file: $file → $new_path"
            fi
        fi
    done
    
    # Find and rename directories (process from deepest to shallowest)
    find . -name "*mediagrand*" -type d 2>/dev/null | sort -r | while read -r dir; do
        if [ -d "$dir" ]; then
            local parent=$(dirname "$dir")
            local basename=$(basename "$dir")
            local new_name=$(echo "$basename" | sed 's/mediagrand/mediagrand/g')
            local new_path="$parent/$new_name"
            
            if [ "$dir" != "$new_path" ]; then
                mv "$dir" "$new_path"
                print_success "Renamed directory: $dir → $new_path"
            fi
        fi
    done
}

# Main renaming process
main() {
    print_status "Starting comprehensive renaming to MediaGrand..."
    
    # File patterns to search in
    local file_patterns="-name '*.py' -o -name '*.md' -o -name '*.txt' -o -name '*.yml' -o -name '*.yaml' -o -name '*.json' -o -name '*.sh' -o -name '*.html' -o -name '*.js' -o -name '*.css' -o -name 'Dockerfile' -o -name '*.conf' -o -name '*.ini' -o -name '*.env'"
    
    # 1. Replace MEDIAGRAND (all caps)
    safe_replace "MEDIAGRAND" "MEDIAGRAND" "$file_patterns" "MEDIAGRAND → MEDIAGRAND"
    
    # 2. Replace MediaGrand (title case)
    safe_replace "MediaGrand" "MediaGrand" "$file_patterns" "MediaGrand → MediaGrand"
    
    # 3. Replace mediagrand (lowercase)
    safe_replace "mediagrand" "mediagrand" "$file_patterns" "mediagrand → mediagrand"
    
    # 4. Replace MediaGrand API
    safe_replace "MediaGrand API" "MediaGrand API" "$file_patterns" "MediaGrand API → MediaGrand API"
    
    # 5. Replace MediaGrand (without API)
    safe_replace "MediaGrand" "MediaGrand" "$file_patterns" "MediaGrand → MediaGrand"
    
    # 6. Replace MediaGrand (no spaces)
    safe_replace "MediaGrand" "MediaGrand" "$file_patterns" "MediaGrand → MediaGrand"
    
    # 7. Replace standalone NCA references in appropriate contexts
    safe_replace "NCA" "MediaGrand" "$file_patterns" "NCA → MediaGrand"
    
    # 8. Handle Docker image references
    safe_replace "isaacgounton/mediagrand" "isaacgounton/mediagrand" "$file_patterns" "Docker image references"
    
    # 9. Handle domain references
    safe_replace "mediagrand\.com" "mediagrand.com" "$file_patterns" "Domain references"
    safe_replace "tts\.mediagrand\.com" "tts.mediagrand.com" "$file_patterns" "TTS domain references"
    safe_replace "shorts\.mediagrand\.com" "shorts.mediagrand.com" "$file_patterns" "Shorts domain references"
    
    # 10. Handle email references
    safe_replace "admin@mediagrand\.local" "admin@mediagrand.local" "$file_patterns" "Email references"
    
    # 11. Handle GitHub repository references
    safe_replace "github\.com/isaacgounton/mediagrand" "github.com/isaacgounton/mediagrand" "$file_patterns" "GitHub repository references"
    
    # 12. Handle API key prefixes
    safe_replace "mediagrand-" "mediagrand-" "$file_patterns" "API key and resource prefixes"
    
    # 13. Handle Docker Hub references
    safe_replace "hub\.docker\.com/r/isaacgounton/mediagrand" "hub.docker.com/r/isaacgounton/mediagrand" "$file_patterns" "Docker Hub references"
    
    # 14. Handle project names in GCP and other cloud references
    safe_replace "mediagrand-project" "mediagrand-project" "$file_patterns" "GCP project references"
    safe_replace "mediagrand-service" "mediagrand-service" "$file_patterns" "GCP service account references"
    safe_replace "mediagrand-media" "mediagrand-media" "$file_patterns" "GCP bucket references"
    
    # 15. Handle container and network names
    safe_replace "mediagrand-redis" "mediagrand-redis" "$file_patterns" "Redis container names"
    safe_replace "mediagrand-network" "mediagrand-network" "$file_patterns" "Docker network names"
    safe_replace "mediagrand_data" "mediagrand_data" "$file_patterns" "Docker volume names"
    
    # 16. Handle JWT issuer
    safe_replace "mediagrand-admin" "mediagrand-admin" "$file_patterns" "JWT issuer references"
    
    # 17. Update generate_vector.sh specific content
    if [ -f "./generate_vector.sh" ]; then
        safe_replace "MediaGrand API Vector Doc\.txt" "MediaGrand API Vector Doc.txt" "-name 'generate_vector.sh'" "Vector documentation filename"
    fi
    
    # 18. Rename files and directories
    rename_paths
    
    print_success "Renaming process completed!"
    
    # Summary
    echo ""
    echo "======================================"
    echo "         RENAMING SUMMARY"
    echo "======================================"
    echo "✅ Application name: mediagrand → mediagrand"
    echo "✅ Project title: MediaGrand → MediaGrand"  
    echo "✅ API name: MediaGrand API → MediaGrand API"
    echo "✅ Docker images: isaacgounton/mediagrand → isaacgounton/mediagrand"
    echo "✅ Domains: *.mediagrand.com → *.mediagrand.com"
    echo "✅ Cloud resources: mediagrand-* → mediagrand-*"
    echo "✅ Documentation updated"
    echo "✅ Configuration files updated"
    echo "✅ Scripts and deployment files updated"
    echo ""
    
    print_warning "IMPORTANT NEXT STEPS:"
    echo "1. Review the changes in your files"
    echo "2. Update your Docker Hub repository name if needed"
    echo "3. Update your domain DNS settings"
    echo "4. Update any external service configurations"
    echo "5. Test the application thoroughly"
    echo "6. Update your Git repository name if needed"
    echo ""
    
    print_status "Backup files created with .bak extension"
    print_status "Run 'find . -name \"*.bak\" -delete' to remove backups after verification"
}

# Cleanup function for backups
cleanup_backups() {
    print_status "Cleaning up backup files..."
    find . -name "*.bak" -type f -delete
    print_success "Backup files removed"
}

# Help function
show_help() {
    echo "MediaGrand Renaming Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h      Show this help message"
    echo "  --cleanup       Remove all .bak backup files"
    echo "  --dry-run       Show what would be changed without making changes"
    echo ""
    echo "Examples:"
    echo "  $0              # Run the full renaming process"
    echo "  $0 --cleanup    # Remove backup files"
    echo "  $0 --dry-run    # Preview changes without applying them"
}

# Dry run function
dry_run() {
    print_status "DRY RUN MODE - No changes will be made"
    echo ""
    echo "The following patterns would be replaced:"
    echo "• MEDIAGRAND → MEDIAGRAND"
    echo "• MediaGrand → MediaGrand"
    echo "• mediagrand → mediagrand"
    echo "• MediaGrand API → MediaGrand API"
    echo "• MediaGrand → MediaGrand"
    echo "• MediaGrand → MediaGrand"
    echo "• isaacgounton/mediagrand → isaacgounton/mediagrand"
    echo "• *.mediagrand.com → *.mediagrand.com"
    echo "• mediagrand-* → mediagrand-*"
    echo ""
    echo "Files that would be affected:"
    find . -type f \( -name '*.py' -o -name '*.md' -o -name '*.txt' -o -name '*.yml' -o -name '*.yaml' -o -name '*.json' -o -name '*.sh' -o -name '*.html' -o -name '*.js' -o -name '*.css' -o -name 'Dockerfile' -o -name '*.conf' -o -name '*.ini' -o -name '*.env' \) -exec grep -l "mediagrand\|MediaGrand\|MEDIAGRAND\|NCA" {} \; 2>/dev/null | head -20
    echo ""
    print_status "Run without --dry-run to apply changes"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --cleanup)
        cleanup_backups
        exit 0
        ;;
    --dry-run)
        dry_run
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac