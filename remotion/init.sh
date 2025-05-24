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

# Skip TypeScript build for now - just ensure dependencies are installed
echo "✅ Remotion setup completed!"
