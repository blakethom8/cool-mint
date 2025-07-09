#!/bin/bash

# Activity Selector Frontend Installation Script

echo "Installing Activity Selector Frontend..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
npm install

# Create a .env file for local development
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Frontend configuration
VITE_API_BASE_URL=http://localhost:8080
EOL
fi

echo "Installation complete!"
echo ""
echo "To start the development server:"
echo "  npm run dev"
echo ""
echo "The frontend will be available at http://localhost:3000"
echo "Make sure your backend API is running on http://localhost:8080"