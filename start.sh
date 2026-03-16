#!/bin/bash
# ============================================================
# Spoken Social — Start Script
# Run: ./start.sh
# ============================================================

echo "🚀 Starting Spoken Social..."

# 1. Ensure PostgreSQL is running
echo "📦 Checking PostgreSQL..."
sudo systemctl start postgresql 2>/dev/null || echo "  (PostgreSQL may already be running)"

# 2. Start Backend (in background)
echo "🐍 Starting Backend (port 8000)..."
cd /home/ubuntu/spoken-social/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# 3. Start Frontend (in background)
echo "⚡ Starting Frontend (port 5173)..."
cd /home/ubuntu/spoken-social/frontend
npm run dev -- --host &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

# 4. Wait a moment and show URLs
sleep 3
echo ""
echo "============================================"
echo "  ✅ Spoken Social is running!"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop both servers."

# Trap Ctrl+C to kill both processes
trap "echo '🛑 Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for either to exit
wait
