# 快速开始指南

## 5分钟快速启动

### Windows用户

1. **双击运行** `setup.bat` - 自动安装环境
2. **配置API密钥**：
   - 复制 `.env.example` 为 `.env`
   - 编辑 `.env` 文件，填入你的API密钥
3. **双击运行** `start.bat` - 启动服务
4. **访问** http://localhost:8000/docs

### Linux/Mac用户

```bash
# 1. 设置环境
chmod +x setup.sh start.sh
./setup.sh

# 2. 配置API密钥
cp .env.example .env
# 编辑 .env 文件

# 3. 启动服务
./start.sh

# 4. 访问文档
# http://localhost:8000/docs
```

## API测试

### 方法1：使用浏览器访问Swagger文档

打开 http://localhost:8000/docs ，可以直接在浏览器中测试所有API。

### 方法2：使用测试脚本

```bash
python examples/test_api.py
```

### 方法3：使用curl命令

```bash
# 标准请求
curl -X POST http://localhost:8000/customer-service \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我的订单什么时候发货？",
    "session_id": "test-001"
  }'

# 流式请求
curl -X POST http://localhost:8000/customer-service/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我的商品已退货但退款还没到账",
    "session_id": "test-002"
  }'
```

## 获取API密钥

1. 访问 [阿里云DashScope](https://dashscope.aliyun.com/)
2. 注册账号并登录
3. 进入"API-KEY管理"页面
4. 创建新的API Key
5. 复制到 `.env` 文件中

## 常见问题

### Q: 提示找不到模块？
A: 确保已运行 `setup.bat` 或 `setup.sh` 安装依赖

### Q: API密钥在哪里获取？
A: 访问 https://dashscope.aliyun.com/ 注册并获取

### Q: 如何修改端口？
A: 编辑 `src/new_agent.py` 最后一行，修改 `port=8000` 为其他端口

### Q: 如何查看处理日志？
A: 服务运行时会在控制台输出详细日志

### Q: 支持哪些模型？
A: 默认使用通义千问 qwen3.6-plus，可修改代码使用其他OpenAI兼容模型

## 下一步

- 📖 阅读完整文档：[README.md](README.md)
- 🧪 查看示例：[examples/](examples/)
- 🔧 自定义开发：参考README中的"开发指南"章节

---

**祝您使用愉快！** 🚀
