#!/bin/bash

#!/bin/bash
set -e

echo "🚀 Setting up Remotion environment..."

# Install dependencies
echo "📦 Installing dependencies..."
NODE_ENV=production npm install --no-audit --no-fund

# Remove webpack progress plugin from bundler config
echo "🔧 Configuring webpack..."
if [ -f "node_modules/@remotion/bundler/dist/webpack-config.js" ]; then
    sed -i 's/new webpack.ProgressPlugin(),//' node_modules/@remotion/bundler/dist/webpack-config.js
fi

# Build TypeScript
echo "🔨 Building TypeScript..."
npm run build

# Create tsconfig.json
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ESNext"],
    "module": "ESNext",
    "moduleResolution": "node",
    "jsx": "react-jsx",
    "strict": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    },
    "types": ["node", "react", "react-dom"],
    "outDir": "dist"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
EOF

# Make script executable
chmod +x init.sh
