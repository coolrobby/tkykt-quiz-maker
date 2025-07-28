import gradio as gr
import os
import pandas as pd
from typing import List, Tuple
from components.quiz_generator import QuizGenerator
import tempfile
import shutil
from datetime import datetime

class QuizGeneratorApp:
    """选择题生成器Gradio应用"""
    
    def __init__(self):
        self.generator = QuizGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def process_uploaded_files(self, files: List[str], watermark: str = "坦克云课堂") -> Tuple[str, str, List[str]]:
        """处理上传的Excel文件"""
        if not files:
            return "❌ 请上传至少一个Excel文件", "", []
        
        try:
            # 验证文件格式
            valid_files = []
            invalid_files = []
            
            for file_path in files:
                if file_path.lower().endswith(('.xlsx', '.xls')):
                    valid_files.append(file_path)
                else:
                    invalid_files.append(os.path.basename(file_path))
            
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
            
            report_lines.append(f"✅ **成功处理的文件** ({len([r for r in results if r[0] is not None])}个):")
            
            for output_path, message in results:
                if output_path:
                    successful_files.append(output_path)
                    # 获取统计信息
                    try:
                        excel_file = valid_files[len(successful_files) - 1]
                        stats = self.generator.get_quiz_statistics(excel_file)
                        if 'error' not in stats:
                            total_questions += stats['total_questions']
                            type_info = ", ".join([f"{k}: {v}" for k, v in stats['question_types'].items()])
                            report_lines.append(f"   • {stats['file_name']} → {os.path.basename(output_path)}")
                            report_lines.append(f"     📝 {stats['total_questions']}道题目 ({type_info})")
                        else:
                            report_lines.append(f"   • {message}")
                    except:
                        report_lines.append(f"   • {message}")
                else:
                    failed_files.append(message)
            
            if failed_files:
                report_lines.append("")
                report_lines.append(f"❌ **处理失败的文件** ({len(failed_files)}个):")
                for error in failed_files:
                    report_lines.append(f"   • {error}")
            
            # 总结
            report_lines.append("")
            report_lines.append("📈 **处理总结:**")
            report_lines.append(f"   • 总文件数: {len(files)}")
            report_lines.append(f"   • 成功生成: {len(successful_files)}")
            report_lines.append(f"   • 处理失败: {len(failed_files)}")
            report_lines.append(f"   • 总题目数: {total_questions}")
            report_lines.append(f"   • 输出目录: {self.generator.outputs_dir}")
            
            # 生成状态消息
            if successful_files:
                if failed_files:
                    status = f"⚠️ 部分成功: {len(successful_files)}个文件生成成功，{len(failed_files)}个失败"
                else:
                    status = f"✅ 全部成功: {len(successful_files)}个文件生成完成，共{total_questions}道题目"
            else:
                status = "❌ 全部失败: 没有成功生成任何文件"
            
            return status, "\n".join(report_lines), successful_files
            
        except Exception as e:
            error_msg = f"❌ 处理过程中发生错误: {str(e)}"
            return error_msg, error_msg, []
    
    def create_download_files(self, generated_files: List[str]) -> List[str]:
        """创建可下载的文件列表"""
        if not generated_files:
            return []
        
        # 返回生成的HTML文件路径
        return generated_files
    
    def backup_project(self) -> str:
        """备份整个项目文件夹到指定目录"""
        try:
            # 获取当前时间作为文件夹名
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder_name = f"坦克云课堂题目大师_{current_time}"
            
            # 目标备份路径
            backup_base_dir = "D:\\BaiduSyncdisk\\坦克云课堂题目大师"
            backup_target_dir = os.path.join(backup_base_dir, backup_folder_name)
            
            # 确保目标目录存在
            os.makedirs(backup_base_dir, exist_ok=True)
            
            # 源项目目录
            source_dir = os.getcwd()
            
            # 复制整个项目文件夹
            shutil.copytree(source_dir, backup_target_dir)
            
            return f"✅ 项目备份成功！\n📁 备份位置: {backup_target_dir}\n⏰ 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        except Exception as e:
            return f"❌ 备份失败: {str(e)}"
    
    def preview_excel_content(self, file_path: str) -> str:
        """预览Excel文件内容"""
        if not file_path:
            return "请先上传Excel文件"
        
        try:
            df = pd.read_excel(file_path)
            
            # 检查必需的列
            required_columns = ['题干', '选项A', '选项B', '选项C', '选项D', '答案']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            preview_lines = []
            preview_lines.append("📋 **Excel文件预览**\n")
            
            if missing_columns:
                preview_lines.append(f"⚠️ **缺少必需的列**: {', '.join(missing_columns)}")
                preview_lines.append("\n**要求的列格式**: 题干, 选项A, 选项B, 选项C, 选项D, 答案\n")
            
            preview_lines.append(f"📊 **文件信息**:")
            preview_lines.append(f"   • 文件名: {os.path.basename(file_path)}")
            preview_lines.append(f"   • 总行数: {len(df)}")
            preview_lines.append(f"   • 列数: {len(df.columns)}")
            preview_lines.append(f"   • 列名: {', '.join(df.columns.tolist())}")
            
            # 显示前几行数据
            if len(df) > 0:
                preview_lines.append("\n📝 **前5行数据预览**:")
                preview_df = df.head(5).fillna('')
                
                for i, row in preview_df.iterrows():
                    preview_lines.append(f"\n**第{i+1}行**:")
                    for col in df.columns:
                        value = str(row[col]).strip() if pd.notna(row[col]) else ''
                        if len(value) > 50:
                            value = value[:50] + '...'
                        preview_lines.append(f"   • {col}: {value}")
            
            return "\n".join(preview_lines)
            
        except Exception as e:
            return f"❌ 预览失败: {str(e)}"
    
    def create_interface(self):
        """创建Gradio界面"""
        
        # 自定义CSS样式
        custom_css = """
        .gradio-container {
            font-family: 'Georgia', 'Times New Roman', serif;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .gr-button-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: none !important;
            color: white !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        .gr-button-primary:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        }
        
        .gr-file {
            border: 2px dashed #667eea !important;
            border-radius: 12px !important;
            background: #f8f9fa !important;
        }
        
        .gr-textbox {
            border-radius: 8px !important;
            border: 1px solid #e9ecef !important;
        }
        
        .gr-markdown {
            font-size: 14px !important;
            line-height: 1.6 !important;
        }
        
        .header-title {
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
        
        .header-subtitle {
            text-align: center;
            color: #7f8c8d;
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }
        """
        
        with gr.Blocks(css=custom_css, title="坦克云课堂 - 选择题生成器") as interface:
            # 页面标题
            gr.HTML("""
            <div class="header-title">🎯 坦克云课堂选择题生成器</div>
            <div class="header-subtitle">智能Excel转HTML测试页面，支持选择题和填空题</div>
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    # 文件上传区域
                    gr.Markdown("### 📁 上传Excel文件")
                    gr.Markdown("""
                    **支持的格式**: .xlsx, .xls  
                    **必需的列**: 题干, 选项A, 选项B, 选项C, 选项D, 答案  
                    **题目类型**: 自动识别四选项、三选项选择题和填空题
                    """)
                    
                    file_upload = gr.File(
                        label="选择Excel文件",
                        file_count="multiple",
                        file_types=[".xlsx", ".xls"],
                        height=120
                    )
                    
                    # 水印设置
                    gr.Markdown("### 💧 水印设置")
                    watermark_text = gr.Textbox(
                        label="水印文字",
                        value="坦克云课堂",
                        placeholder="请输入水印文字",
                        info="将在答题卡右下角显示，透明度50%"
                    )
                    
                    # 预览按钮
                    preview_btn = gr.Button("📋 预览文件内容", variant="secondary", size="sm")
                    
                    # 生成按钮
                    generate_btn = gr.Button("🚀 生成测试页面", variant="primary", size="lg")
                    
                    # 备份按钮
                    backup_btn = gr.Button("💾 备份项目", variant="secondary", size="sm")
                
                with gr.Column(scale=1):
                    # 功能特性说明
                    gr.Markdown("### ✨ 功能特性")
                    gr.Markdown("""
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
                    """)
            
            # 分隔线
            gr.HTML("<hr style='margin: 2rem 0; border: 1px solid #e9ecef;'>")
            
            with gr.Row():
                with gr.Column():
                    # 处理状态
                    status_output = gr.Textbox(
                        label="📊 处理状态",
                        placeholder="等待文件上传...",
                        interactive=False,
                        max_lines=2
                    )
                    
                    # 详细报告
                    report_output = gr.Markdown(
                        label="📋 详细报告",
                        value="上传Excel文件后，这里将显示详细的处理报告..."
                    )
                    
                    # 文件预览
                    preview_output = gr.Markdown(
                        label="👀 文件预览",
                        value="点击'预览文件内容'查看Excel文件结构...",
                        visible=False
                    )
                    
                    # 下载区域
                    download_files = gr.File(
                        label="📥 下载生成的HTML文件",
                        file_count="multiple",
                        interactive=False,
                        visible=False
                    )
                    
                    # 备份状态
                    backup_status = gr.Textbox(
                        label="💾 备份状态",
                        placeholder="点击备份按钮进行项目备份...",
                        interactive=False,
                        visible=False
                    )
            
            # 使用说明
            with gr.Accordion("📖 使用说明", open=False):
                gr.Markdown("""
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
            
            # 事件绑定
            def handle_file_upload(files):
                if files:
                    return gr.update(visible=True)
                return gr.update(visible=False)
            
            def handle_preview(files):
                if not files:
                    return "请先上传Excel文件", gr.update(visible=True)
                
                # 预览第一个文件
                preview_content = self.preview_excel_content(files[0])
                return preview_content, gr.update(visible=True)
            
            def handle_generate(files, watermark):
                if not files:
                    return "❌ 请先上传Excel文件", "请上传Excel文件后再生成", gr.update(visible=False)
                
                status, report, generated_files = self.process_uploaded_files(files, watermark)
                
                if generated_files:
                    return status, report, gr.update(value=generated_files, visible=True)
                else:
                    return status, report, gr.update(visible=False)
            
            def handle_backup():
                backup_result = self.backup_project()
                return backup_result, gr.update(visible=True)
            
            # 绑定事件
            file_upload.change(
                fn=handle_file_upload,
                inputs=[file_upload],
                outputs=[preview_output]
            )
            
            preview_btn.click(
                fn=handle_preview,
                inputs=[file_upload],
                outputs=[preview_output, preview_output]
            )
            
            generate_btn.click(
                fn=handle_generate,
                inputs=[file_upload, watermark_text],
                outputs=[status_output, report_output, download_files]
            )
            
            backup_btn.click(
                fn=handle_backup,
                inputs=[],
                outputs=[backup_status, backup_status]
            )
        
        return interface
    
    def launch(self, **kwargs):
        """启动应用"""
        interface = self.create_interface()
        
        # 默认启动参数
        default_kwargs = {
            'server_name': '0.0.0.0',
            'server_port': 7860,
            'share': False,
            'debug': False,
            'show_error': True,
            'quiet': False
        }
        
        # 合并用户参数
        launch_kwargs = {**default_kwargs, **kwargs}
        
        print("🚀 启动坦克云课堂选择题生成器...")
        print(f"📊 输出目录: {os.path.abspath(self.generator.outputs_dir)}")
        print(f"🌐 访问地址: http://localhost:{launch_kwargs['server_port']}")
        
        interface.launch(**launch_kwargs)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='坦克云课堂选择题生成器')
    parser.add_argument('--server_port', type=int, default=7860, help='服务器端口')
    parser.add_argument('--share', action='store_true', help='创建公共链接')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    app = QuizGeneratorApp()
    app.launch(
        server_port=args.server_port,
        share=args.share,
        debug=args.debug
    )

if __name__ == "__main__":
    main()