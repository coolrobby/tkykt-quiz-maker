# Quiz Maker - Streamlit Cloud Deployment

## 🚀 部署到 Streamlit.io

### 1. 准备工作
- 确保所有文件已上传到 GitHub 仓库
- 主应用文件：`run.py`
- 依赖文件：`requirements.txt`
- 配置文件：`.streamlit/config.toml`

### 2. 部署步骤
1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 连接你的 GitHub 账户
3. 选择包含此项目的仓库
4. 设置主文件为：`run.py`
5. 点击 "Deploy" 开始部署

### 3. 项目结构
```
├── run.py                    # 主启动文件 (Streamlit.io 入口)
├── streamlit_app.py         # 主应用逻辑
├── requirements.txt         # 依赖包列表
├── .streamlit/
│   └── config.toml         # Streamlit 配置
├── components/
│   └── quiz_generator.py   # 核心生成器
├── templates/              # HTML 模板
└── outputs/                # 输出目录
```

### 4. 功能特性
- ✅ 智能Excel转HTML测试页面
- ✅ 支持选择题和填空题
- ✅ 批量文件处理
- ✅ 移动端友好界面
- ✅ 云端部署优化

### 5. 使用说明
1. 上传Excel文件（包含：题干、选项A-D、答案列）
2. 点击"生成测试页面"
3. 下载生成的HTML文件
4. 在浏览器中打开HTML文件进行测试

---
**制作：川哥**