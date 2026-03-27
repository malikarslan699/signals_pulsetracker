#!/bin/bash
# PulseSignal Pro — Initial Setup Script
# Run this once on a fresh server

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PulseSignal Pro — Setup Script"
echo "  signals.pulsetracker.net"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt-get install -y docker-compose-plugin
fi

# Create .env from example if not exists
if [ ! -f backend/.env ]; then
    echo "Creating backend/.env from example..."
    cp backend/.env.example backend/.env

    # Generate random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your_secret_key_here_minimum_32_chars/$SECRET_KEY/" backend/.env

    echo "Edit backend/.env and fill in your API keys!"
fi

# Create nginx ssl directory
mkdir -p nginx/ssl

# Start services
echo "Starting services..."
docker compose -f docker-compose.yml up -d postgres redis

echo "Waiting for database..."
sleep 10

echo "Running database migrations..."
docker compose -f docker-compose.yml run --rm backend alembic upgrade head

echo "Seeding owner account..."
docker compose -f docker-compose.yml run --rm backend python /scripts/seed_owner.py

echo "Starting all services..."
docker compose -f docker-compose.yml up -d

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ PulseSignal Pro is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Frontend:  https://signals.pulsetracker.net"
echo "  API:       https://signals.pulsetracker.net/api/v1"
echo "  API Docs:  https://signals.pulsetracker.net/api/docs"
echo "  Admin:     https://signals.pulsetracker.net/admin"
echo ""
echo "  Owner Login:"
echo "    Email:    malik.g72@gmail.com"
echo "    Password: PulseOwner2025!  (change after first login)"
echo ""
echo "  Telegram Bot: @pulsesignalprobot"
echo ""
echo "Next steps:"
echo "  1. SSL: certbot certonly --webroot -d signals.pulsetracker.net"
echo "  2. Update backend/.env with Stripe & Binance API keys"
echo "  3. Change owner password at /settings"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
