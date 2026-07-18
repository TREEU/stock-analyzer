#!/bin/bash
# A股量化分析平台启动脚本

echo "🚀 启动 A股量化分析平台..."

# 启动后端
echo "📡 启动后端 API (端口 8000)..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端就绪
sleep 2

# 启动前端
echo "🎨 启动前端界面 (端口 5173)..."
npm run dev --prefix frontend &
FRONTEND_PID=$!

echo ""
echo "✅ 启动完成！"
echo "   后端 API:  http://localhost:8000/docs"
echo "   前端界面:  http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '已停止'" EXIT

# 等待
wait
