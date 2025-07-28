import streamlit as st
import os
import pandas as pd
from typing import List, Tuple
from components.quiz_generator import QuizGenerator
import tempfile
import shutil
from datetime import datetime
import zipfile
import io

class StreamlitQuizGeneratorApp:
    """选择题生成器Streamlit应用"""
    
    def __init__(self):
        self.generator = QuizGenerator()
        if 'temp_dir' not in st.session_state:
            st.session_state.temp_dir = tempfile.mkdtemp()
    
    def process_uploaded_files(self, files: List, watermark: str = "坦克云课堂") -> Tuple[str, str, List[str]]:
        """处理上传的Excel文件"""
        if not files:
            return "❌ 请上传至少一个Excel文件", "", []
        
        try:
            # 验证文件格式
            valid_files = []
            invalid_files = []
            
            for uploaded_file in files:
                if uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
                    # 保存上传的文件到临时目录
                    temp_file_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
                    with open(temp_file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    valid_files.append(temp_file_path)
                else:
                    invalid_files.append(uploaded_file.name)
            
            if not valid_files:
                return "❌ 没有找到有效的Excel文件", "", []
            
            # 生成详细报告
            report_lines = []
            report_lines.append("📊 **文件处理报告**\n")
            
            if invalid_files:
                report_lines.append(f"⚠️ **跳过的无效文件** ({len(invalid_files)}个):")
                for file in invalid_files:
                    report_lines.append(f"   • {file}")
                report_lines.append("")
            
            # 批量生成测试文件
            results = self.generator.batch_generate_quizzes(valid_files, watermark)
            
            # 统计结果
            successful_files = []
            failed_files = []
            total_questions = 0
            
            for file_path, result in zip(valid_files, results):
                file_name = os.path.basename(file_path)
                if isinstance(result, tuple) and len(result) == 2:
                    output_path, message = result
                    successful_files.append(output_path)
                    
                    # 从消息中提取题目数量
                    try:
                        # 从类似"成功生成测试文件: xxx.html\n包含 5 道题目"的消息中提取数字
                        import re
                        match = re.search(r'包含 (\d+) 道题目', message)
                        if match:
                            questions_count = int(match.group(1))
                            total_questions += questions_count
                            report_lines.append(f"✅ **{file_name}**: 成功生成 {questions_count} 道题目")
                        else:
                            report_lines.append(f"✅ **{file_name}**: 生成成功")
                    except (ValueError, AttributeError):
                        report_lines.append(f"✅ **{file_name}**: 生成成功")
                else:
                    failed_files.append((file_name, str(result)))
                    report_lines.append(f"❌ **{file_name}**: 处理失败 - {result}")
            
            # 添加统计信息
            report_lines.append("")
            report_lines.append("📈 **处理统计**")
            report_lines.append(f"• 总文件数: {len(valid_files)}")
            report_lines.append(f"• 成功处理: {len(successful_files)}")
            report_lines.append(f"• 失败文件: {len(failed_files)}")
            report_lines.append(f"• 总题目数: {total_questions}")
            
            if successful_files:
                report_lines.append("")
                report_lines.append(f"📁 **输出目录**: `{os.path.abspath(self.generator.outputs_dir)}`")
                report_lines.append(f"📥 **生成文件**: {len(successful_files)} 个HTML文件")
            
            # 生成状态消息
            if successful_files and not failed_files:
                status = f"✅ 全部处理成功！共生成 {len(successful_files)} 个测试页面，包含 {total_questions} 道题目"
            elif successful_files and failed_files:
                status = f"⚠️ 部分处理成功！成功 {len(successful_files)} 个，失败 {len(failed_files)} 个"
            else:
                status = f"❌ 处理失败！{len(failed_files)} 个文件处理失败"
            
            return status, "\n".join(report_lines), successful_files
            
        except Exception as e:
            error_msg = f"❌ 处理过程中发生错误: {str(e)}"
            return error_msg, error_msg, []
    
    def create_download_zip(self, generated_files: List[str]) -> bytes:
        """创建包含所有生成文件的ZIP压缩包"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in generated_files:
                if os.path.exists(file_path):
                    # 使用文件名作为ZIP内的路径
                    arcname = os.path.basename(file_path)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def preview_excel_content(self, uploaded_file) -> str:
        """预览Excel文件内容"""
        try:
            # 读取上传的文件
            df = pd.read_excel(uploaded_file)
            
            # 基本信息
            preview_lines = []
            preview_lines.append(f"📄 **文件名**: {uploaded_file.name}")
            preview_lines.append(f"📊 **数据行数**: {len(df)} 行")
            preview_lines.append(f"📋 **列数**: {len(df.columns)} 列")
            preview_lines.append("")
            
            # 列名检查
            required_columns = ['题干', '选项A', '选项B', '选项C', '选项D', '答案']
            existing_columns = df.columns.tolist()
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            preview_lines.append("🔍 **列名检查**")
            if missing_columns:
                preview_lines.append(f"❌ 缺少必需的列: {missing_columns}")
                preview_lines.append(f"📋 现有列名: {existing_columns}")
            else:
                preview_lines.append("✅ 所有必需的列都存在")
            
            preview_lines.append("")
            
            # 数据预览（前5行）
            preview_lines.append("👀 **数据预览** (前5行)")
            preview_lines.append("")
            
            if not missing_columns:
                # 只显示必需的列
                preview_df = df[required_columns].head(5).fillna('')
                
                for idx, row in preview_df.iterrows():
                    preview_lines.append(f"**题目 {idx + 1}:**")
                    preview_lines.append(f"• 题干: {row['题干']}")
                    preview_lines.append(f"• 选项A: {row['选项A']}")
                    preview_lines.append(f"• 选项B: {row['选项B']}")
                    preview_lines.append(f"• 选项C: {row['选项C']}")
                    preview_lines.append(f"• 选项D: {row['选项D']}")
                    preview_lines.append(f"• 答案: {row['答案']}")
                    preview_lines.append("")
            else:
                preview_lines.append("⚠️ 由于缺少必需的列，无法预览题目内容")
            
            return "\n".join(preview_lines)
            
        except Exception as e:
            return f"❌ 预览失败: {str(e)}"
    
    def run(self):
        """运行Streamlit应用"""
        # 页面配置
        st.set_page_config(
            page_title="坦克云课堂 - 选择题生成器",
            page_icon="🎯",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 自定义CSS样式
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            color: #2c3e50;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .main-subtitle {
            text-align: center;
            color: #7f8c8d;
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }
        
        .feature-box {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin: 1rem 0;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 页面标题
        st.markdown('<div class="main-header">Quiz Maker</div>', unsafe_allow_html=True)
        st.markdown('<div class="main-subtitle">智能Excel转HTML测试页面，支持选择题和填空题</div>', unsafe_allow_html=True)
        st.markdown('<div class="main-subtitle">制作：川哥</div>', unsafe_allow_html=True)
        
        # 侧边栏
        with st.sidebar:
            st.markdown("### ✨ 功能特性")
            st.markdown("""
            🎯 **智能题型识别**
            • 四选项选择题 (ABCD都有内容)
            • 三选项选择题 (ABC有内容，D为空)
            • 填空题 (所有选项为空)
            
            🎮 **用户控制选项**
            • 题目乱序开关
            • 选项乱序开关
            • 实时答题进度
            
            📊 **自动批改统计**
            • 即时答案反馈
            • 详细成绩报告
            • 错题回顾分析
            • 答题时间统计
            
            🎨 **界面设计**
            • 欧美大学风格
            • 完美移动端适配
            • 单文件无依赖
            
            💧 **水印**: 坦克云课堂
            """)
            
            # 固定水印文字
            watermark_text = "坦克云课堂"
        
        # 主要内容区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📁 上传Excel文件")
            st.markdown("""
            **支持的格式**: .xlsx, .xls  
            **必需的列**: 题干, 选项A, 选项B, 选项C, 选项D, 答案  
            **题目类型**: 自动识别四选项、三选项选择题和填空题
            """)
            
            uploaded_files = st.file_uploader(
                "选择Excel文件",
                type=['xlsx', 'xls'],
                accept_multiple_files=True,
                help="可以同时上传多个Excel文件进行批量处理"
            )
            
            # 按钮区域
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                preview_btn = st.button("📋 预览文件内容", use_container_width=True)
            
            with col_btn2:
                generate_btn = st.button("🚀 生成测试页面", use_container_width=True, type="primary")
        
        with col2:
            st.markdown("### 📊 处理状态")
            status_placeholder = st.empty()
            
            if uploaded_files:
                status_placeholder.info(f"已上传 {len(uploaded_files)} 个文件，等待处理...")
            else:
                status_placeholder.info("等待文件上传...")
        
        # 预览功能
        if preview_btn and uploaded_files:
            st.markdown("### 👀 文件预览")
            # 预览第一个文件
            preview_content = self.preview_excel_content(uploaded_files[0])
            st.markdown(preview_content)
        
        # 生成功能
        if generate_btn:
            if not uploaded_files:
                st.error("❌ 请先上传Excel文件")
            else:
                with st.spinner("正在处理文件，请稍候..."):
                    status, report, generated_files = self.process_uploaded_files(uploaded_files, watermark_text)
                
                # 显示处理状态
                if "✅" in status:
                    st.success(status)
                elif "⚠️" in status:
                    st.warning(status)
                else:
                    st.error(status)
                
                # 显示详细报告
                if report:
                    st.markdown("### 📋 详细报告")
                    st.markdown(report)
                
                # 提供下载
                if generated_files:
                    st.markdown("### 📥 下载生成的文件")
                    
                    # 创建ZIP文件
                    zip_data = self.create_download_zip(generated_files)
                    
                    # 提供ZIP下载
                    st.download_button(
                        label="📦 下载所有HTML文件 (ZIP)",
                        data=zip_data,
                        file_name=f"quiz_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    # 单独文件下载
                    st.markdown("**单独下载:**")
                    for file_path in generated_files:
                        if os.path.exists(file_path):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            file_name = os.path.basename(file_path)
                            st.download_button(
                                label=f"📄 {file_name}",
                                data=file_content,
                                file_name=file_name,
                                mime="text/html",
                                key=f"download_{file_name}"
                            )
        
        # 使用说明
        with st.expander("📖 使用说明", expanded=False):
            st.markdown("""
            ### 📝 Excel文件格式要求
            
            您的Excel文件必须包含以下6列（列名必须完全匹配）：
            
            | 列名 | 说明 | 示例 |
            |------|------|------|
            | 题干 | 题目内容 | "苹果的英文是什么？" |
            | 选项A | 第一个选项 | "apple" |
            | 选项B | 第二个选项 | "banana" |
            | 选项C | 第三个选项 | "orange" |
            | 选项D | 第四个选项 | "grape" |
            | 答案 | 正确答案 | "apple" |
            
            ### 🎯 题目类型说明
            
            **四选项选择题**: ABCD四个选项都有内容  
            **三选项选择题**: ABC有内容，D选项为空  
            **填空题**: 所有选项字段为空，只有题干和答案
            
            ### 🚀 生成的HTML特性
            
            ✅ **单文件包含**: 所有CSS、JS内嵌，无外部依赖  
            ✅ **离线可用**: 生成后可离线使用  
            ✅ **跨平台兼容**: 支持所有现代浏览器  
            ✅ **移动端优化**: 触摸友好的交互设计  
            ✅ **答案乱序**: 显示实际内容而非字母标识  
            ✅ **智能批改**: 自动判断对错并生成报告
            """)
        
        # 页脚信息
    


def main():
    """主函数"""
    app = StreamlitQuizGeneratorApp()
    app.run()

if __name__ == "__main__":
    main()