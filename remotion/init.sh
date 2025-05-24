#!/bin/bash

# Install dependencies
npm install

echo "🚀 Setting up Remotion environment..."

# Create necessary directories
mkdir -p src/components
mkdir -p scripts
mkdir -p public

# Install all dependencies from package.json
echo "📦 Installing dependencies..."
npm install

# Download Google Fonts
echo "🔤 Setting up Google Fonts..."
npx remotion install-fonts

# Test TypeScript compilation
echo "🔍 Testing TypeScript setup..."
npx tsc --noEmit

# Run ESLint check
echo "🧹 Running ESLint..."
npx eslint src --ext ts,tsx

# Run test render
echo "🎬 Running test render..."
node scripts/test-render.js

echo "✅ Remotion setup completed!"
echo "💡 Try 'npm run preview' to see the compositions in action"

# Install Remotion and core dependencies
npm install \
  @remotion/bundler \
  @remotion/cli \
  @remotion/renderer \
  remotion \
  react \
  react-dom

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
