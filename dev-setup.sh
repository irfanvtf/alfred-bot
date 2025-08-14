#!/bin/bash
# dev-setup.sh - Development setup script

echo "Setting up Alfred Bot development environment..."

# Setup backend
echo "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Setup frontend
echo "Setting up frontend..."
cd ../frontend

# Install frontend dependencies
echo "Installing frontend dependencies..."
npm install

echo "Development setup complete!"
echo ""
echo "To start the development environment:"
echo "1. In one terminal, start the backend:"
echo "   cd backend && source venv/bin/activate && python main.py"
echo ""
echo "2. In another terminal, start the frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "Backend will be available at http://localhost:8000"
echo "Frontend will be available at http://localhost:3000"