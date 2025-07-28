# 坦克云课堂选择题生成器 - Streamlit版本

🎯 智能Excel转HTML测试页面生成器，支持选择题和填空题的自动识别与生成。

## ✨ 功能特性

### 🎯 智能题型识别
- **四选项选择题**: ABCD四个选项都有内容
- **三选项选择题**: ABC有内容，D选项为空
- **填空题**: 所有选项字段为空，只有题干和答案

### 🎮 用户控制选项
- 题目乱序开关
- 选项乱序开关
- 实时答题进度

### 📊 自动批改统计
- 即时答案反馈
- 详细成绩报告
- 错题回顾分析
- 答题时间统计

### 🎨 界面设计
- 欧美大学风格
- 完美移动端适配
- 单文件无依赖

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run streamlit_app.py
```

### 3. 访问应用

打开浏览器访问: http://localhost:8501

## 📝 Excel文件格式要求

您的Excel文件必须包含以下6列（列名必须完全匹配）：

| 列名 | 说明 | 示例 |
|------|------|------|
| 题干 | 题目内容 | "苹果的英文是什么？" |
| 选项A | 第一个选项 | "apple" |
| 选项B | 第二个选项 | "banana" |
| 选项C | 第三个选项 | "orange" |
| 选项D | 第四个选项 | "grape" |
| 答案 | 正确答案 | "apple" |

## 🎯 题目类型说明

### 四选项选择题
- ABCD四个选项都有内容
- 系统自动识别为标准选择题

### 三选项选择题
- ABC有内容，D选项为空
- 适用于只有三个选项的题目

### 填空题
- 所有选项字段为空，只有题干和答案
- 系统自动识别为填空题类型

## 🚀 生成的HTML特性

✅ **单文件包含**: 所有CSS、JS内嵌，无外部依赖  
✅ **离线可用**: 生成后可离线使用  
✅ **跨平台兼容**: 支持所有现代浏览器  
✅ **移动端优化**: 触摸友好的交互设计  
✅ **答案乱序**: 显示实际内容而非字母标识  
✅ **智能批改**: 自动判断对错并生成报告

## 📁 项目结构

```
坦克云课堂网站-题目大师-streamlit/
├── streamlit_app.py          # Streamlit主应用文件
├── app.py                    # 原Gradio应用文件（保留）
├── components/
│   └── quiz_generator.py     # 核心题目生成器
├── templates/                # HTML模板文件
│   ├── header.html
│   ├── footer.html
│   └── styles.css
├── outputs/                  # 输出目录
│   └── generated_quizzes/    # 生成的HTML文件
├── requirements.txt          # 依赖包列表
└── README_STREAMLIT.md       # 本说明文件
```

## 🔧 部署到Streamlit Cloud

### 1. 准备GitHub仓库

1. 将项目上传到GitHub仓库
2. 确保`streamlit_app.py`在根目录
3. 确保`requirements.txt`包含所有依赖

### 2. 部署到Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用GitHub账号登录
3. 点击"New app"
4. 选择你的GitHub仓库
5. 设置主文件为`streamlit_app.py`
6. 点击"Deploy"

### 3. 配置文件（可选）

创建`.streamlit/config.toml`文件进行高级配置：

```toml
[theme]
base = "light"
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
maxUploadSize = 200
```

## 🛠️ 开发说明

### 核心组件

- **StreamlitQuizGeneratorApp**: 主应用类，处理UI和用户交互
- **QuizGenerator**: 核心生成器，处理Excel文件和HTML生成
- **模板系统**: 使用Jinja2模板生成HTML文件

### 性能优化

- 使用pandas向量化操作处理大量数据
- 临时文件管理，避免内存泄漏
- 批量处理多个Excel文件
- ZIP压缩下载，减少网络传输

### 错误处理

- 完善的文件格式验证
- 详细的错误信息反馈
- 优雅的异常处理机制

## 📊 使用流程

1. **上传Excel文件**: 支持单个或多个文件批量上传
2. **预览文件内容**: 检查文件格式和数据结构
3. **设置水印**: 自定义答题卡水印文字
4. **生成测试页面**: 一键生成HTML测试文件
5. **下载结果**: 支持单个下载或ZIP批量下载

## 🔍 故障排除

### 常见问题

**Q: 上传文件后提示格式错误？**
A: 请确保Excel文件包含必需的6列：题干、选项A、选项B、选项C、选项D、答案

**Q: 生成的HTML文件无法正常显示？**
A: 请检查浏览器是否支持现代Web标准，建议使用Chrome、Firefox或Edge

**Q: 部署到Streamlit Cloud失败？**
A: 请检查requirements.txt文件是否包含所有依赖，确保文件路径正确

### 日志查看

在本地运行时，可以在终端查看详细的处理日志和错误信息。

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: support@tankcloud.com
- 🌐 官网: https://www.tankcloud.com
- 📱 微信: tankcloud

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

---

**坦克云课堂** - 让学习更简单，让教学更高效！ 🚀