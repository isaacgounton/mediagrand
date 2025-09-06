#!/bin/bash
# Quick deployment validation script

echo "🔍 Validating deployment readiness..."

# Check if required files exist
files=(
    "docker-compose.yml"
    ".dockerignore" 
    ".env"
    "docker/Dockerfile"
    "scripts/run_services.sh"
    "app.py"
    "requirements.txt"
)

echo ""
echo "📋 Checking required files:"
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING!"
    fi
done

echo ""
echo "🐳 Checking Docker configuration:"

# Check if docker-compose.yml points to correct Dockerfile
if grep -q "dockerfile: docker/Dockerfile" docker-compose.yml; then
    echo "✅ docker-compose.yml correctly references docker/Dockerfile"
else
    echo "❌ docker-compose.yml doesn't reference docker/Dockerfile correctly"
fi

# Check if Dockerfile references correct script path
if grep -q "scripts/run_services.sh" docker/Dockerfile; then
    echo "✅ Dockerfile correctly references scripts/run_services.sh"
else
    echo "❌ Dockerfile doesn't reference scripts/run_services.sh correctly"
fi

# Check if Redis port is not exposed (for deployment)
if grep -q "6379:6379" docker-compose.yml; then
    echo "⚠️  Redis port 6379 is exposed - may cause conflicts in deployment"
else
    echo "✅ Redis port not exposed externally (deployment ready)"
fi

echo ""
echo "📝 Checking environment variables:"

# Check if key environment variables are set
if grep -q "API_KEY=" .env; then
    echo "✅ API_KEY is configured"
else
    echo "❌ API_KEY is missing in .env"
fi

if grep -q "APP_DOMAIN=" .env; then
    echo "✅ APP_DOMAIN is configured"
else
    echo "❌ APP_DOMAIN is missing in .env"
fi

echo ""
echo "🚀 Deployment validation complete!"