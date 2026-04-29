"""
智能客服系统API测试脚本

使用方法：
1. 确保服务已启动：python src/new_agent.py
2. 运行此脚本：python examples/test_api.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_standard_request():
    """测试标准请求"""
    print("=" * 60)
    print("测试1：标准客服请求")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "订单查询",
            "input": "帮我查一下订单12345的物流状态"
        },
        {
            "name": "退款问题",
            "input": "我的商品已经退货一周了，但是退款还没到账，怎么回事？"
        },
        {
            "name": "密码重置",
            "input": "我忘记了登录密码，怎么重置？"
        },
        {
            "name": "复合问题",
            "input": "我想修改订单地址，同时申请一张优惠券补偿"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}] {case['name']}")
        print(f"用户输入：{case['input']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/customer-service",
                json={
                    "user_input": case["input"],
                    "session_id": f"test-{i}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 意图识别：{result.get('intent')}")
                print(f"✓ 情感分析：{result.get('sentiment')}")
                print(f"✓ 置信度：{result.get('confidence'):.2f}")
                print(f"✓ 回复：{result.get('final_response', '')[:200]}...")
                
                # 显示质量检查
                quality = result.get('quality_checks', {})
                print(f"✓ 语气检查：{quality.get('tone_check')}")
                print(f"✓ 合规检查：{quality.get('compliance_check')}")
            else:
                print(f"✗ 错误：{response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"✗ 异常：{str(e)}")
        
        time.sleep(1)


def test_streaming_request():
    """测试流式请求"""
    print("\n" + "=" * 60)
    print("测试2：流式客服请求（实时进度）")
    print("=" * 60)
    
    user_input = "我的商品已退货但退款还没到账，订单号是ORDER20240115"
    print(f"\n用户输入：{user_input}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/customer-service/stream",
            json={
                "user_input": user_input,
                "session_id": "stream-test-001"
            },
            stream=True,
            timeout=60
        )
        
        print("处理进度：")
        print("-" * 60)
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str.replace('data: ', '')
                    try:
                        event = json.loads(data_str)
                        node = event.get('node', '')
                        event_type = event.get('type', '')
                        
                        # 格式化输出
                        if event_type == 'intent_recognition':
                            print(f"\n📋 [{node}] 意图识别完成")
                            print(f"   意图：{event.get('intent')}")
                            print(f"   情感：{event.get('sentiment')}")
                            
                        elif event_type == 'reasoning_progress':
                            steps = event.get('steps_count', 0)
                            complete = event.get('complete', False)
                            status = "✓ 完成" if complete else "进行中"
                            print(f"\n🔍 [{node}] 长链推理 {status}")
                            print(f"   已完成步骤：{steps}")
                            
                        elif event_type == 'final_response':
                            print(f"\n✅ [{node}] 最终回复生成")
                            response_text = event.get('response', '')
                            print(f"   回复内容：\n   {response_text[:300]}...")
                            
                            quality = event.get('quality_checks', {})
                            print(f"\n   质量检查：")
                            print(f"   - 语气：{quality.get('tone_check')}")
                            print(f"   - 合规：{quality.get('compliance_check')}")
                            
                        else:
                            print(f"\n⚙️  [{node}] {event_type}")
                            
                    except json.JSONDecodeError:
                        pass
        
        print("\n" + "-" * 60)
        print("✓ 流式响应测试完成")
        
    except Exception as e:
        print(f"✗ 异常：{str(e)}")


def test_feedback_submission():
    """测试反馈提交"""
    print("\n" + "=" * 60)
    print("测试3：用户反馈提交")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/feedback",
            json={
                "session_id": "test-1",
                "feedback": "resolved",
                "comment": "问题已解决，回复很详细"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 反馈提交成功")
            print(f"  会话ID：{result.get('session_id')}")
            print(f"  反馈类型：{result.get('feedback')}")
            print(f"  消息：{result.get('message')}")
        else:
            print(f"✗ 错误：{response.status_code}")
            
    except Exception as e:
        print(f"✗ 异常：{str(e)}")


def test_session_query():
    """测试会话查询"""
    print("\n" + "=" * 60)
    print("测试4：查询会话状态")
    print("=" * 60)
    
    session_id = "test-1"
    print(f"\n查询会话：{session_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/session/{session_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 会话查询成功")
            print(f"  会话ID：{result.get('session_id')}")
            print(f"  下一步：{result.get('next')}")
            
            history = result.get('history', [])
            print(f"  消息历史：{len(history)} 条")
            
            if history:
                print(f"\n  最近消息：")
                for msg in history[-2:]:
                    print(f"  - [{msg['role']}] {msg['content'][:100]}...")
        else:
            print(f"✗ 错误：{response.status_code}")
            
    except Exception as e:
        print(f"✗ 异常：{str(e)}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("智能客服系统 - API测试套件")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ 服务正常运行\n")
        else:
            print("✗ 服务未正常响应，请确保已启动服务\n")
            return
    except Exception:
        print("✗ 无法连接到服务，请确保已运行：python src/new_agent.py\n")
        return
    
    # 运行测试
    test_standard_request()
    test_streaming_request()
    test_feedback_submission()
    test_session_query()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
