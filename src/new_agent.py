"""
基于多Agent协作的智能客服工单自动处理系统

核心功能：
1. 入口Agent：意图分类与情感识别
2. 路由Agent：任务分发至专家Agent
3. 专家Agent：订单、售后、账户等专项处理
4. 长链推理Agent：复杂问题多步推理（5-8步）
5. 协调Agent：多Agent并行检索与冲突解决
6. 规范检查Agent：语气和合规性校验
7. 闭环验证：用户反馈回流训练集
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
import uuid
import json
import os
from datetime import datetime
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import dotenv

dotenv.load_dotenv()

# 配置API密钥
os.environ["DASHSCOPE_API_KEY"] = os.getenv("DASHSCOPE_API_KEY", "")
os.environ["OPENAI_API_KEY"] = os.getenv("openai_api_key", "")

# ==================== 状态定义 ====================

class CustomerServiceState(TypedDict):
    """客服系统状态"""
    # 用户输入
    user_input: str
    session_id: str
    
    # 意图识别结果
    intent: str  # 订单查询/售后问题/账户问题/复合问题/其他
    sentiment: str  # positive/neutral/negative/angry
    confidence: float
    
    # 消息历史
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 专家Agent处理结果
    order_result: Optional[str]  # 订单Agent结果
    after_sales_result: Optional[str]  # 售后Agent结果
    account_result: Optional[str]  # 账户Agent结果
    
    # 长链推理中间结果
    reasoning_steps: Annotated[List[Dict[str, Any]], add_messages]
    reasoning_complete: bool
    
    # 协调Agent结果
    coordination_result: Optional[str]
    conflict_resolved: bool
    
    # 最终回复
    draft_response: Optional[str]
    final_response: Optional[str]
    response_approved: bool
    
    # 质量检查
    tone_check: Optional[str]  # 语气检查结果
    compliance_check: Optional[str]  # 合规性检查结果
    
    # 闭环反馈
    user_feedback: Optional[str]  # resolved/unresolved
    feedback_timestamp: Optional[str]
    
    # 执行状态
    current_node: str
    processing_complete: bool
    error_message: Optional[str]


# ==================== LLM配置 ====================

def get_chat_llm(temperature=0.2):
    """获取聊天模型实例"""
    return ChatOpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen3.6-plus",
        temperature=temperature,
        streaming=False
    )


# ==================== 工具函数 ====================

def mock_query_order_system(order_id: str) -> Dict[str, Any]:
    """模拟查询订单系统"""
    # 实际项目中应替换为真实的API调用
    return {
        "order_id": order_id,
        "status": "已退货",
        "return_status": "仓库已签收",
        "return_date": "2024-01-15",
        "refund_status": "审核中",
        "refund_amount": 299.00
    }


def mock_query_financial_system(order_id: str) -> Dict[str, Any]:
    """模拟查询财务系统"""
    return {
        "order_id": order_id,
        "refund_record": {
            "status": "pending_approval",
            "submitted_date": "2024-01-16",
            "expected_days": 3,
            "current_stage": "财务审核",
            "delay_reason": "审核积压"
        }
    }


def mock_query_crm(customer_id: str) -> Dict[str, Any]:
    """模拟查询CRM系统"""
    return {
        "customer_id": customer_id,
        "vip_level": "gold",
        "total_orders": 25,
        "complaint_count": 1,
        "satisfaction_score": 4.2
    }


# ==================== Agent节点实现 ====================

def entry_agent(state: CustomerServiceState) -> Dict[str, Any]:
    """
    入口Agent：意图分类与情感识别
    
    功能：
    1. 分析用户输入，识别意图类型
    2. 进行情感分析，判断客户情绪状态
    3. 计算置信度分数
    """
    llm = get_chat_llm(temperature=0.1)
    
    system_prompt = """你是一个专业的客服意图分类和情感分析助手。
    
任务：
1. 意图分类：将用户问题分类为以下类别之一：
   - order_inquiry: 订单查询（订单状态、物流信息等）
   - after_sales: 售后问题（退换货、退款、维修等）
   - account_issue: 账户问题（密码重置、信息修改等）
   - complex_issue: 复合问题（涉及多个系统或流程）
   - other: 其他咨询

2. 情感分析：判断用户情绪状态
   - positive: 积极/满意
   - neutral: 中性/平静
   - negative: 消极/不满
   - angry: 愤怒/强烈不满

3. 置信度评估：给出分类的置信度（0-1之间）

请以JSON格式返回结果，包含以下字段：
- intent: 意图类别
- sentiment: 情感状态
- confidence: 置信度
- reasoning: 简短的分析理由
"""
    
    user_message = f"用户输入：{state['user_input']}"
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        # 解析JSON响应
        result = json.loads(response.content)
        
        return {
            "intent": result.get("intent", "other"),
            "sentiment": result.get("sentiment", "neutral"),
            "confidence": result.get("confidence", 0.5),
            "messages": [AIMessage(content=f"意图识别完成：{result.get('intent')}")]
        }
    except Exception as e:
        return {
            "intent": "other",
            "sentiment": "neutral",
            "confidence": 0.3,
            "error_message": f"意图识别失败：{str(e)}",
            "messages": [AIMessage(content="意图识别出现错误")]
        }


def router_agent(state: CustomerServiceState) -> Dict[str, Any]:
    """
    路由Agent：根据意图分发任务至不同专家Agent
    
    路由规则：
    - order_inquiry -> order_agent
    - after_sales -> after_sales_agent
    - account_issue -> account_agent
    - complex_issue -> coordinator_agent
    - other -> general_handler
    """
    intent = state.get("intent", "other")
    
    routing_map = {
        "order_inquiry": "order_agent",
        "after_sales": "after_sales_agent",
        "account_issue": "account_agent",
        "complex_issue": "coordinator_agent",
        "other": "general_handler"
    }
    
    next_node = routing_map.get(intent, "general_handler")
    
    return {
        "current_node": next_node,
        "messages": [AIMessage(content=f"任务已路由至：{next_node}")]
    }


def order_agent(state: CustomerServiceState) -> Dict[str, Any]:
    """
    订单Agent：处理订单相关查询
    
    功能：
    1. 提取订单号等信息
    2. 查询订单状态、物流信息
    3. 生成回复
    """
    llm = get_chat_llm(temperature=0.2)
    
    system_prompt = """你是专业的订单客服专家。
职责：
1. 从用户输入中提取订单相关信息（订单号、手机号等）
2. 查询订单状态、物流进度、支付信息
3. 解答订单相关问题
4. 提供清晰、准确的回复

如果缺少关键信息（如订单号），请礼貌地请求用户提供。
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户问题：{state['user_input']}")
        ])
        
        return {
            "order_result": response.content,
            "draft_response": response.content,
            "messages": [AIMessage(content="订单Agent处理完成")]
        }
    except Exception as e:
        return {
            "error_message": f"订单Agent处理失败：{str(e)}",
            "messages": [AIMessage(content="订单处理出现错误")]
        }


def after_sales_agent(state: CustomerServiceState) -> Dict[str, Any]:
    """
    售后Agent：处理退换货、退款等售后问题
    
    对于简单售后问题直接处理，复杂问题标记需要长链推理
    """
    llm = get_chat_llm(temperature=0.2)
    
    system_prompt = """你是专业的售后客服专家。
职责：
1. 处理退换货申请和查询
2. 处理退款问题和进度查询
3. 处理商品维修和换货
4. 解释售后政策和流程
5. 安抚客户情绪，提供解决方案

对于涉及多个系统的复杂问题（如"已退货但退款未到账"），请在回复中标记需要进一步调查。
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户问题：{state['user_input']}")
        ])
        
        # 判断是否需要长链推理
        needs_reasoning = any(keyword in state['user_input'] 
                             for keyword in ["退款未到账", "还没收到退款", "退款进度", "为什么还没退"])
        
        return {
            "after_sales_result": response.content,
            "draft_response": response.content if not needs_reasoning else None,
            "reasoning_complete": not needs_reasoning,
            "messages": [AIMessage(content="售后Agent处理完成")]
        }
    except Exception as e:
        return {
            "error_message": f"售后Agent处理失败：{str(e)}",
            "messages": [AIMessage(content="售后处理出现错误")]
        }


def account_agent(state: CustomerServiceState) -> Dict[str, Any]:
    """
    账户Agent：处理账户相关问题
    
    功能：
    1. 密码重置指导
    2. 账户信息修改
    3. 账户安全咨询
    """
    llm = get_chat_llm(temperature=0.2)
    
    system_prompt = """你是专业的账户客服专家。
职责：
1. 指导用户进行密码重置和找回
2. 协助修改账户信息（手机号、邮箱等）
3. 解答账户安全问题
4. 处理账户登录问题
5. 提供账户管理建议

注意：不要直接索要用户的密码或敏感信息，只提供操作指导。
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户问题：{state['user_input']}")
        ])
        
        return {
            "account_result": response.content,
            "draft_response": response.content,
            "messages": [AIMessage(content="账户Agent处理完成")]
        }
    except Exception as e:
        return {
            "error_message": f"账户Agent处理失败：{str(e)}",
            "messages": [AIMessage(content="账户处理出现错误")]
        }


def refund_reasoning_agent(state: CustomerServiceState) -> Dict[str, Any]:
    """
    退款推理Agent：长链推理处理复杂退款问题
    
    推理步骤（5-8步）：
    1. 提取订单号和关键信息
    2. 调用订单系统获取退货状态
    3. 调用财务系统查询退款流水
    4. 分析退款流程和当前环节
    5. 识别异常环节（审核积压/银行延迟/系统故障）
    6. 查询相关政策规定时效
    7. 生成解释说明和补救建议
    8. 记录完整推理过程
    """
    llm = get_chat_llm(temperature=0.1)
    
    reasoning_steps = []
    
    try:
        # Step 1: 信息提取
        step1_llm = get_chat_llm(temperature=0.1)
        extraction_prompt = """从用户问题中提取关键信息：
- 订单号（如果有）
- 问题类型（退款未到账/退款进度查询等）
- 时间信息（何时退货/何时申请退款等）
- 其他相关信息

以JSON格式返回提取的信息。"""
        
        step1_response = step1_llm.invoke([
            SystemMessage(content=extraction_prompt),
            HumanMessage(content=f"用户问题：{state['user_input']}")
        ])
        
        extracted_info = json.loads(step1_response.content)
        reasoning_steps.append({
            "step": 1,
            "action": "信息提取",
            "result": extracted_info,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 2: 查询订单系统
        order_id = extracted_info.get("order_id", "未知")
        order_data = mock_query_order_system(order_id)
        reasoning_steps.append({
            "step": 2,
            "action": "查询订单系统",
            "query": f"订单号：{order_id}",
            "result": order_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 3: 查询财务系统
        financial_data = mock_query_financial_system(order_id)
        reasoning_steps.append({
            "step": 3,
            "action": "查询财务系统",
            "query": f"订单号：{order_id}",
            "result": financial_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 4: 分析退款流程
        step4_prompt = f"""基于以下数据分析退款流程状态：
订单数据：{json.dumps(order_data, ensure_ascii=False)}
财务数据：{json.dumps(financial_data, ensure_ascii=False)}

请分析：
1. 当前退款处于哪个环节？
2. 是否正常？是否存在延迟？
3. 如果延迟，可能的原因是什么？
"""
        
        step4_response = llm.invoke([
            SystemMessage(content="你是退款流程分析专家"),
            HumanMessage(content=step4_prompt)
        ])
        
        reasoning_steps.append({
            "step": 4,
            "action": "流程分析",
            "result": step4_response.content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 5: 识别异常环节
        step5_prompt = f"""根据流程分析结果，识别异常环节：
{step4_response.content}

可能的异常类型：
- 审核积压：退款申请量大，处理缓慢
- 银行延迟：银行处理时间长
- 系统故障：技术原因导致延迟
- 资料不全：缺少必要材料
- 其他原因

请判断最可能的异常类型并说明理由。"""
        
        step5_response = llm.invoke([
            SystemMessage(content="你是问题诊断专家"),
            HumanMessage(content=step5_prompt)
        ])
        
        reasoning_steps.append({
            "step": 5,
            "action": "异常诊断",
            "result": step5_response.content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 6: 查询政策时效
        step6_prompt = """根据电商行业标准和常见政策：
- 退货审核：1-3个工作日
- 财务审核：2-5个工作日  
- 银行转账：3-7个工作日
- 总体时效：7-15个工作日

请结合当前情况分析是否超出正常时效。"""
        
        step6_response = llm.invoke([
            SystemMessage(content="你是政策分析专家"),
            HumanMessage(content=step6_prompt)
        ])
        
        reasoning_steps.append({
            "step": 6,
            "action": "政策时效分析",
            "result": step6_response.content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 7: 生成解释和建议
        step7_prompt = f"""基于以上所有分析，为用户生成一份详细的解释和补救建议。

要求：
1. 用通俗易懂的语言解释退款流程
2. 说明当前状态和延迟原因（如果有）
3. 给出预计完成时间
4. 提供补救措施（如加急处理、补偿方案等）
5. 表达歉意和理解，安抚客户情绪

分析数据：
{json.dumps(reasoning_steps, ensure_ascii=False, indent=2)}
"""
        
        step7_response = llm.invoke([
            SystemMessage(content="你是客户服务专家，擅长沟通和解决问题"),
            HumanMessage(content=step7_prompt)
        ])
        
        reasoning_steps.append({
            "step": 7,
            "action": "生成解决方案",
            "result": step7_response.content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 8: 总结推理过程
        final_summary = f"""## 退款问题分析报告

### 问题描述
{state['user_input']}

### 调查过程
共执行 {len(reasoning_steps)} 步推理分析

### 详细步骤
"""
        
        for step in reasoning_steps:
            final_summary += f"\n**步骤 {step['step']}**: {step['action']}\n"
            if isinstance(step['result'], dict):
                final_summary += f"- 结果：{json.dumps(step['result'], ensure_ascii=False, indent=2)}\n"
            else:
                final_summary += f"- 结果：{str(step['result'])[:300]}\n"
        
        final_summary += f"\n### 最终解决方案\n{step7_response.content}\n"
        
        return {
            "reasoning_steps": reasoning_steps,
            "reasoning_complete": True,
            "draft_response": step7_response.content,
            "messages": [AIMessage(content=f"长链推理完成，共{len(reasoning_steps)}步")]
        }
        
    except Exception as e:
        return {
            "reasoning_steps": reasoning_steps,
            "reasoning_complete": False,
            "error_message": f"退款推理失败：{str(e)}",
            "messages": [AIMessage(content="推理过程出现错误")]
        }


def coordinator_agent(state: CustomerServiceState) -> Dict[str, Any]:
    """
    协调Agent：处理复合问题，动态引入多个专家Agent并行检索
    
    功能：
    1. 分析问题涉及的领域
    2. 并行调用相关专家Agent
    3. 收集各Agent结果
    4. 冲突解决模块合并生成最终回复
    """
    llm = get_chat_llm(temperature=0.2)
    
    coordination_prompt = f"""你是一个协调专家，负责处理复杂的客服问题。

用户问题：{state['user_input']}

已识别为复合问题，可能涉及多个领域。

请分析：
1. 这个问题涉及哪些领域？（订单/售后/账户/其他）
2. 需要调用哪些专家Agent？
3. 如何整合各Agent的结果？
4. 是否存在信息冲突？如何解决？

请提供一个综合性的回复，整合所有相关信息。
"""
    
    try:
        # 模拟并行调用多个Agent
        results = []
        
        # 根据问题内容决定调用哪些Agent
        if any(keyword in state['user_input'] for keyword in ["订单", "物流", "发货"]):
            order_result = order_agent(state)
            results.append(f"订单Agent结果：{order_result.get('order_result', '')}")
        
        if any(keyword in state['user_input'] for keyword in ["退款", "退货", "换货"]):
            after_sales_result = after_sales_agent(state)
            results.append(f"售后Agent结果：{after_sales_result.get('after_sales_result', '')}")
        
        if any(keyword in state['user_input'] for keyword in ["账户", "密码", "登录"]):
            account_result = account_agent(state)
            results.append(f"账户Agent结果：{account_result.get('account_result', '')}")
        
        # 整合结果
        integration_prompt = f"""请整合以下多个专家Agent的结果，生成一个统一、连贯的回复：

{' '.join(results)}

要求：
1. 消除重复信息
2. 解决可能的冲突或不一致
3. 按照逻辑顺序组织内容
4. 保持语气友好和专业
5. 确保回复完整且易于理解
"""
        
        integrated_response = llm.invoke([
            SystemMessage(content="你是信息整合专家"),
            HumanMessage(content=integration_prompt)
        ])
        
        return {
            "coordination_result": integrated_response.content,
            "draft_response": integrated_response.content,
            "conflict_resolved": True,
            "messages": [AIMessage(content="协调Agent完成多Agent结果整合")]
        }
        
    except Exception as e:
        return {
            "error_message": f"协调Agent处理失败：{str(e)}",
            "messages": [AIMessage(content="协调处理出现错误")]
        }


def general_handler(state: CustomerServiceState) -> Dict[str, Any]:
    """
    通用处理器：处理无法归类的问题
    """
    llm = get_chat_llm(temperature=0.3)
    
    system_prompt = """你是友好的客服助手。
对于无法明确归类的问题，请：
1. 礼貌地回应客户
2. 尝试理解客户需求并提供帮助
3. 如果超出能力范围，建议转接人工客服
4. 保持专业和友好的态度
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户问题：{state['user_input']}")
        ])
        
        return {
            "draft_response": response.content,
            "messages": [AIMessage(content="通用处理器完成")]
        }
    except Exception as e:
        return {
            "error_message": f"通用处理失败：{str(e)}",
            "messages": [AIMessage(content="处理出现错误")]
        }


def quality_check_agent(state: CustomerServiceState) -> Dict[str, Any]:
    """
    规范检查Agent：校验回复的语气和合规性
    
    检查项：
    1. 语气检查：是否友好、专业、有同理心
    2. 合规性检查：是否符合公司政策、法律法规
    3. 完整性检查：是否充分回答了用户问题
    4. 敏感性检查：是否包含不当内容或承诺
    """
    llm = get_chat_llm(temperature=0.1)
    
    draft = state.get("draft_response", "")
    
    check_prompt = f"""你是客服质量检查专家。请对以下客服回复草案进行全面检查：

用户问题：{state['user_input']}

回复草案：
{draft}

请检查以下方面：
1. **语气检查**：是否友好、专业、有同理心？是否有冒犯性或冷漠的表达？
2. **合规性检查**：是否符合客服规范？是否有违规承诺或不当表述？
3. **完整性检查**：是否充分回答了用户的问题？是否遗漏重要信息？
4. **准确性检查**：提供的信息是否准确？是否有误导性内容？
5. **敏感性检查**：是否包含敏感信息泄露风险？

请以JSON格式返回检查结果：
{{
  "tone_check": "通过/不通过",
  "tone_issues": "语气问题描述（如果有）",
  "compliance_check": "通过/不通过",
  "compliance_issues": "合规问题描述（如果有）",
  "overall_quality": "优秀/良好/一般/需改进",
  "suggestions": "改进建议",
  "approved": true/false
}}
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content="你是严格的质量检查专家"),
            HumanMessage(content=check_prompt)
        ])
        
        check_result = json.loads(response.content)
        
        # 如果检查不通过，生成改进后的回复
        if not check_result.get("approved", False):
            improvement_prompt = f"""根据以下质量问题，改进客服回复：

原回复：
{draft}

质量问题：
- 语气问题：{check_result.get('tone_issues', '无')}
- 合规问题：{check_result.get('compliance_issues', '无')}
- 改进建议：{check_result.get('suggestions', '无')}

请生成一个改进后的版本，确保语气友好、合规、完整。"""
            
            improved_response = llm.invoke([
                SystemMessage(content="你是客服文案优化专家"),
                HumanMessage(content=improvement_prompt)
            ])
            
            return {
                "tone_check": check_result.get("tone_check"),
                "compliance_check": check_result.get("compliance_check"),
                "final_response": improved_response.content,
                "response_approved": True,
                "messages": [AIMessage(content=f"质量检查完成，已优化回复")]
            }
        else:
            return {
                "tone_check": check_result.get("tone_check"),
                "compliance_check": check_result.get("compliance_check"),
                "final_response": draft,
                "response_approved": True,
                "messages": [AIMessage(content="质量检查通过")]
            }
            
    except Exception as e:
        # 如果检查失败，直接使用草稿作为最终回复
        return {
            "tone_check": "unknown",
            "compliance_check": "unknown",
            "final_response": draft,
            "response_approved": True,
            "error_message": f"质量检查失败：{str(e)}",
            "messages": [AIMessage(content="质量检查出现错误，使用原回复")]
        }


def feedback_collector(state: CustomerServiceState) -> Dict[str, Any]:
    """
    反馈收集器：记录用户反馈，用于后续模型微调
    
    此节点在实际应用中会通过API接收用户反馈
    """
    return {
        "feedback_timestamp": datetime.now().isoformat(),
        "processing_complete": True,
        "messages": [AIMessage(content="反馈已记录，感谢您的使用")]
    }


# ==================== 路由逻辑 ====================

def route_after_entry(state: CustomerServiceState) -> str:
    """入口Agent后的路由"""
    return "router_agent"


def route_after_router(state: CustomerServiceState) -> str:
    """路由Agent后的分发"""
    next_node = state.get("current_node", "general_handler")
    return next_node


def route_after_after_sales(state: CustomerServiceState) -> str:
    """售后Agent后的路由：判断是否需要长链推理"""
    if not state.get("reasoning_complete", True):
        return "refund_reasoning_agent"
    return "quality_check_agent"


def should_do_reasoning(state: CustomerServiceState) -> str:
    """判断是否需要进行长链推理"""
    # 检查是否是退款相关的复杂问题
    user_input = state.get("user_input", "")
    needs_reasoning = any(keyword in user_input 
                         for keyword in ["退款未到账", "还没收到退款", "退款进度", "为什么还没退"])
    
    if needs_reasoning and state.get("intent") == "after_sales":
        return "refund_reasoning_agent"
    return "quality_check_agent"


# ==================== 构建工作流 ====================

def build_customer_service_graph():
    """构建客服系统LangGraph工作流"""
    
    workflow = StateGraph(CustomerServiceState)
    
    # 添加节点
    workflow.add_node("entry_agent", entry_agent)
    workflow.add_node("router_agent", router_agent)
    workflow.add_node("order_agent", order_agent)
    workflow.add_node("after_sales_agent", after_sales_agent)
    workflow.add_node("account_agent", account_agent)
    workflow.add_node("refund_reasoning_agent", refund_reasoning_agent)
    workflow.add_node("coordinator_agent", coordinator_agent)
    workflow.add_node("general_handler", general_handler)
    workflow.add_node("quality_check_agent", quality_check_agent)
    workflow.add_node("feedback_collector", feedback_collector)
    
    # 添加边
    workflow.add_edge(START, "entry_agent")
    workflow.add_conditional_edges("entry_agent", route_after_entry)
    workflow.add_conditional_edges("router_agent", route_after_router)
    
    # 专家Agent处理后进入质量检查或长链推理
    workflow.add_edge("order_agent", "quality_check_agent")
    workflow.add_conditional_edges("after_sales_agent", should_do_reasoning)
    workflow.add_edge("account_agent", "quality_check_agent")
    workflow.add_edge("refund_reasoning_agent", "quality_check_agent")
    workflow.add_edge("coordinator_agent", "quality_check_agent")
    workflow.add_edge("general_handler", "quality_check_agent")
    
    # 质量检查后收集反馈
    workflow.add_edge("quality_check_agent", "feedback_collector")
    workflow.add_edge("feedback_collector", END)
    
    # 编译工作流
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    return graph


# 创建全局graph实例（供LangGraph服务器使用）
graph = build_customer_service_graph()


# ==================== FastAPI接口 ====================

app = FastAPI(
    title="智能客服工单自动处理系统",
    description="基于多Agent协作的智能客服系统，支持意图识别、任务分发、长链推理等功能",
    version="1.0.0"
)

class CustomerServiceRequest(BaseModel):
    """客服请求模型"""
    user_input: str
    session_id: str = ""
    metadata: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    """反馈请求模型"""
    session_id: str
    feedback: str  # resolved / unresolved
    comment: Optional[str] = None


@app.post("/customer-service")
async def handle_customer_service(request: CustomerServiceRequest):
    """
    处理客服请求
    
    接收用户问题，通过多Agent协作生成回复
    """
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    initial_state = {
        "user_input": request.user_input,
        "session_id": session_id,
        "intent": "",
        "sentiment": "",
        "confidence": 0.0,
        "messages": [],
        "order_result": None,
        "after_sales_result": None,
        "account_result": None,
        "reasoning_steps": [],
        "reasoning_complete": False,
        "coordination_result": None,
        "conflict_resolved": False,
        "draft_response": None,
        "final_response": None,
        "response_approved": False,
        "tone_check": None,
        "compliance_check": None,
        "user_feedback": None,
        "feedback_timestamp": None,
        "current_node": "",
        "processing_complete": False,
        "error_message": None
    }
    
    try:
        # 执行工作流
        result = await graph.ainvoke(initial_state, config=config)
        
        return {
            "session_id": session_id,
            "status": "success",
            "intent": result.get("intent"),
            "sentiment": result.get("sentiment"),
            "confidence": result.get("confidence"),
            "final_response": result.get("final_response"),
            "quality_checks": {
                "tone_check": result.get("tone_check"),
                "compliance_check": result.get("compliance_check")
            },
            "reasoning_steps": result.get("reasoning_steps", []),
            "processing_complete": result.get("processing_complete")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败：{str(e)}")


@app.post("/customer-service/stream")
async def handle_customer_service_stream(request: CustomerServiceRequest):
    """
    流式处理客服请求（SSE）
    
    实时返回每个Agent的处理进度
    """
    session_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    initial_state = {
        "user_input": request.user_input,
        "session_id": session_id,
        "intent": "",
        "sentiment": "",
        "confidence": 0.0,
        "messages": [],
        "order_result": None,
        "after_sales_result": None,
        "account_result": None,
        "reasoning_steps": [],
        "reasoning_complete": False,
        "coordination_result": None,
        "conflict_resolved": False,
        "draft_response": None,
        "final_response": None,
        "response_approved": False,
        "tone_check": None,
        "compliance_check": None,
        "user_feedback": None,
        "feedback_timestamp": None,
        "current_node": "",
        "processing_complete": False,
        "error_message": None
    }
    
    async def generate_stream():
        try:
            async for chunk in graph.astream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    event = {
                        "node": node_name,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # 根据不同节点返回不同信息
                    if node_name == "entry_agent":
                        event["type"] = "intent_recognition"
                        event["intent"] = node_output.get("intent")
                        event["sentiment"] = node_output.get("sentiment")
                        
                    elif node_name == "quality_check_agent":
                        event["type"] = "final_response"
                        event["response"] = node_output.get("final_response")
                        event["quality_checks"] = {
                            "tone_check": node_output.get("tone_check"),
                            "compliance_check": node_output.get("compliance_check")
                        }
                        
                    elif node_name == "refund_reasoning_agent":
                        event["type"] = "reasoning_progress"
                        event["steps_count"] = len(node_output.get("reasoning_steps", []))
                        event["complete"] = node_output.get("reasoning_complete", False)
                        
                    else:
                        event["type"] = "progress"
                    
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    
        except Exception as e:
            error_event = {
                "type": "error",
                "error": str(e),
                "session_id": session_id
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    提交用户反馈
    
    用于闭环验证和模型微调
    """
    config = {"configurable": {"thread_id": request.session_id}}
    
    try:
        # 更新状态中的反馈信息
        graph.update_state(config, {
            "user_feedback": request.feedback,
            "feedback_timestamp": datetime.now().isoformat()
        })
        
        # 在实际应用中，这里应该将反馈数据存储到训练数据集
        # 用于每周的模型微调
        
        return {
            "status": "success",
            "message": "反馈已记录",
            "session_id": request.session_id,
            "feedback": request.feedback
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈提交失败：{str(e)}")


@app.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """
    获取会话状态和历史
    """
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        state = graph.get_state(config)
        
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "session_id": session_id,
            "state": state.values,
            "next": state.next,
            "history": [
                {
                    "role": msg.type,
                    "content": msg.content
                }
                for msg in state.values.get("messages", [])
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话失败：{str(e)}")


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("智能客服工单自动处理系统启动中...")
    print("=" * 60)
    print("\n系统特性：")
    print("✓ 多Agent协作架构")
    print("✓ 意图识别与情感分析")
    print("✓ 智能路由分发")
    print("✓ 长链推理（5-8步）")
    print("✓ 质量检查与合规验证")
    print("✓ 用户反馈闭环")
    print("\n访问 http://localhost:8000/docs 查看API文档")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)