#!/bin/bash

# 测试READY标志的脚本

echo "测试各个节点的READY标志..."
echo ""

# 测试ASR
echo "1. 测试 ASR 节点..."
timeout 30 python3 nodes/asr_node.py > /tmp/test_asr.log 2>&1 &
PID=$!
sleep 5
if grep -q "PETBOT_ASR_READY" /tmp/test_asr.log; then
    echo "   ✓ ASR READY标志正常"
else
    echo "   ✗ ASR READY标志未找到"
fi
kill $PID 2>/dev/null
echo ""

# 测试TTS
echo "2. 测试 TTS 节点..."
timeout 30 python3 nodes/tts_node.py > /tmp/test_tts.log 2>&1 &
PID=$!
sleep 5
if grep -q "PETBOT_TTS_READY" /tmp/test_tts.log; then
    echo "   ✓ TTS READY标志正常"
else
    echo "   ✗ TTS READY标志未找到"
fi
kill $PID 2>/dev/null
echo ""

# 测试Chat
echo "3. 测试 Chat 节点..."
timeout 30 python3 nodes/chat/chat_node.py > /tmp/test_chat.log 2>&1 &
PID=$!
sleep 5
if grep -q "PETBOT_CHAT_READY" /tmp/test_chat.log; then
    echo "   ✓ Chat READY标志正常"
else
    echo "   ✗ Chat READY标志未找到"
fi
kill $PID 2>/dev/null
echo ""

# 测试Face
echo "4. 测试 Face 节点..."
timeout 30 python3 nodes/vision/face_detection_node.py > /tmp/test_face.log 2>&1 &
PID=$!
sleep 5
if grep -q "PETBOT_FACE_READY" /tmp/test_face.log; then
    echo "   ✓ Face READY标志正常"
else
    echo "   ✗ Face READY标志未找到"
fi
kill $PID 2>/dev/null
echo ""

# 测试Expression
echo "5. 测试 Expression 服务器..."
timeout 10 python3 nodes/expression_server.py > /tmp/test_expr.log 2>&1 &
PID=$!
sleep 3
if grep -q "PETBOT_EXPRESSION_READY" /tmp/test_expr.log; then
    echo "   ✓ Expression READY标志正常"
else
    echo "   ✗ Expression READY标志未找到"
fi
kill $PID 2>/dev/null
echo ""

echo "测试完成！"
echo ""
echo "查看详细日志:"
echo "  cat /tmp/test_*.log"

