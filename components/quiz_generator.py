import pandas as pd
import os
import random
import json
from typing import List, Dict, Any, Tuple

class QuizGenerator:
    """选择题生成器组件"""
    
    def __init__(self):
        # 使用相对路径，适合云端部署
        self.templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "generated_quizzes")
        
        # 确保输出目录存在
        os.makedirs(self.outputs_dir, exist_ok=True)
    
    def read_excel_file(self, file_path: str) -> pd.DataFrame:
        """读取Excel文件并验证格式"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证必需的列
            required_columns = ['题干', '选项A', '选项B', '选项C', '选项D', '答案']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Excel文件缺少必需的列: {missing_columns}")
            
            # 填充空值
            df = df.fillna('')
            
            return df
            
        except Exception as e:
            raise Exception(f"读取Excel文件失败: {str(e)}")
    
    def identify_question_type(self, row: pd.Series) -> str:
        """智能识别题目类型"""
        options = [row['选项A'], row['选项B'], row['选项C'], row['选项D']]
        non_empty_options = [opt for opt in options if str(opt).strip()]
        
        if len(non_empty_options) == 4:
            return "四选项选择题"
        elif len(non_empty_options) == 3:
            return "三选项选择题"
        elif len(non_empty_options) == 0:
            return "填空题"
        else:
            return "其他选择题"
    
    def process_questions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """处理题目数据，使用pandas向量化操作优化性能"""
        questions = []
        
        # 向量化识别题目类型
        df['题目类型'] = df.apply(self.identify_question_type, axis=1)
        
        for index, row in df.iterrows():
            question_data = {
                'id': index + 1,
                'question': str(row['题干']).strip(),
                'type': row['题目类型'],
                'answer': str(row['答案']).strip(),
                'options': []
            }
            
            # 处理选择题选项
            if '选择题' in row['题目类型']:
                options = []
                answer_letter = str(row['答案']).strip().upper()
                correct_answer_text = ""
                
                for opt_key in ['选项A', '选项B', '选项C', '选项D']:
                    opt_value = str(row[opt_key]).strip()
                    if opt_value:
                        option_letter = opt_key[-1]  # A, B, C, D
                        options.append({
                            'label': option_letter,
                            'text': opt_value
                        })
                        
                        # 如果这个选项是正确答案，记录其内容
                        if option_letter == answer_letter:
                            correct_answer_text = opt_value
                
                question_data['options'] = options
                # 将答案从字母转换为具体内容
                question_data['answer'] = correct_answer_text if correct_answer_text else str(row['答案']).strip()
            
            questions.append(question_data)
        
        return questions
    
    def load_template(self, template_name: str) -> str:
        """加载模板文件"""
        template_path = os.path.join(self.templates_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise Exception(f"模板文件不存在: {template_path}")
    
    def generate_quiz_html(self, questions: List[Dict[str, Any]], quiz_title: str, watermark: str = "坦克云课堂") -> str:
        """生成完整的HTML测试页面"""
        # 加载模板
        header_html = self.load_template('header.html')
        footer_html = self.load_template('footer.html')
        
        # 读取CSS样式
        css_content = self.load_template('styles.css')
        
        # 添加水印样式
        watermark_css = f"""
        .navigation-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
        }}
        
        .nav-buttons {{
            display: flex;
            gap: 10px;
        }}
        
        .watermark {{
            font-size: 12px;
            color: #666;
            opacity: 0.5;
            pointer-events: none;
            font-family: Arial, sans-serif;
            margin-right: 10px;
        }}
        """
        css_content += watermark_css
        
        # 生成题目HTML
        questions_html = self.generate_questions_html(questions)
        
        # 生成完整HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{quiz_title}</title>
    <style>
{css_content}
    </style>
</head>
<body>
    {header_html}
    
    <main class="content">
        <div class="container">
            <div class="quiz-container">
                <div class="quiz-header">
                    <h1 class="quiz-title">{quiz_title}</h1>
                    
                    <!-- 用户控制选项 -->
                    <div class="quiz-controls">
                        <div class="control-group">
                            <label for="shuffleQuestions">题目乱序:</label>
                            <label class="switch">
                                <input type="checkbox" id="shuffleQuestions">
                                <span class="slider"></span>
                            </label>
                        </div>
                        <div class="control-group">
                            <label for="shuffleOptions">选项乱序:</label>
                            <label class="switch">
                                <input type="checkbox" id="shuffleOptions">
                                <span class="slider"></span>
                            </label>
                        </div>
                        <button class="start-btn" onclick="startQuiz()">开始答题</button>
                    </div>
                </div>
                
                <!-- 进度条 -->
                <div class="progress-container" id="progressContainer" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">0 / {len(questions)}</div>
                </div>
                
                <!-- 题目导航 -->
                <div class="question-nav" id="questionNav" style="display: none;"></div>
                
                <!-- 题目容器 -->
                <div id="questionsContainer" style="display: none;">
                    {questions_html}
                </div>
                
                <!-- 导航按钮 -->
                <div class="navigation-container" id="navigationContainer" style="display: none;">
                    <div class="nav-buttons">
                        <button class="nav-btn" id="prevBtn" onclick="previousQuestion()" disabled>上一题</button>
                        <button class="nav-btn" id="nextBtn" onclick="nextQuestion()">下一题</button>
                        <button class="nav-btn" id="submitBtn" onclick="submitQuiz()" style="display: none;">提交答案</button>
                    </div>
                    <div class="watermark">{watermark}</div>
                </div>
                
                <!-- 结果容器 -->
                <div id="resultsContainer" style="display: none;"></div>
            </div>
        </div>
    </main>
    
    {footer_html}
    
    <script>
{self.generate_quiz_javascript(questions)}
    </script>
</body>
</html>"""
        
        return html_content
    
    def generate_questions_html(self, questions: List[Dict[str, Any]]) -> str:
        """生成题目HTML"""
        html_parts = []
        
        for i, question in enumerate(questions):
            question_html = f"""
                <div class="question-container" id="question_{i}" style="display: none;">
                    <div class="question-number">第 {i + 1} 题</div>
                    <div class="question-text">{question['question']}</div>
                    """
            
            if question['type'] == '填空题':
                question_html += f"""
                    <input type="text" class="fill-blank-input" id="answer_{i}" placeholder="请输入答案...">
                """
            else:
                question_html += '<div class="options-container">'
                for j, option in enumerate(question['options']):
                    question_html += f"""
                        <div class="option" onclick="selectOption({i}, {j})" id="option_{i}_{j}">
                            <span class="option-label">{option['label']}</span>
                            <span class="option-text">{option['text']}</span>
                        </div>
                    """
                question_html += '</div>'
            
            question_html += '</div>'
            html_parts.append(question_html)
        
        return '\n'.join(html_parts)
    
    def generate_quiz_javascript(self, questions: List[Dict[str, Any]]) -> str:
        """生成测试页面的JavaScript代码"""
        questions_json = json.dumps(questions, ensure_ascii=False, indent=2)
        
        js_code = f"""
// 测试数据和状态管理
let originalQuestions = {questions_json};
let questions = [...originalQuestions];
let currentQuestionIndex = 0;
let userAnswers = {{}};
let quizStarted = false;
let startTime = null;

// 开始测试
function startQuiz() {{
    const shuffleQuestions = document.getElementById('shuffleQuestions').checked;
    const shuffleOptions = document.getElementById('shuffleOptions').checked;
    
    // 重置数据
    questions = [...originalQuestions];
    userAnswers = {{}};
    currentQuestionIndex = 0;
    startTime = new Date();
    
    // 题目乱序
    if (shuffleQuestions) {{
        questions = shuffleArray([...questions]);
    }}
    
    // 选项乱序
    if (shuffleOptions) {{
        questions.forEach(question => {{
            if (question.options && question.options.length > 0) {{
                question.options = shuffleArray([...question.options]);
            }}
        }});
    }}
    
    // 显示测试界面
    document.querySelector('.quiz-controls').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('questionNav').style.display = 'flex';
    document.getElementById('questionsContainer').style.display = 'block';
    document.getElementById('navigationContainer').style.display = 'flex';
    
    // 初始化题目导航
    initQuestionNavigation();
    
    // 显示第一题
    showQuestion(0);
    
    // 更新进度
    updateProgress();
    
    quizStarted = true;
}}

// 数组乱序函数
function shuffleArray(array) {{
    const newArray = [...array];
    for (let i = newArray.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
    }}
    return newArray;
}}

// 初始化题目导航
function initQuestionNavigation() {{
    const nav = document.getElementById('questionNav');
    nav.innerHTML = '';
    
    questions.forEach((_, index) => {{
        const btn = document.createElement('button');
        btn.className = 'question-nav-btn';
        btn.textContent = index + 1;
        btn.onclick = () => showQuestion(index);
        btn.id = `nav_btn_${{index}}`;
        nav.appendChild(btn);
    }});
}}

// 显示指定题目
function showQuestion(index) {{
    // 隐藏所有题目
    questions.forEach((_, i) => {{
        const questionEl = document.getElementById(`question_${{i}}`);
        if (questionEl) questionEl.style.display = 'none';
    }});
    
    // 显示当前题目
    const currentQuestionEl = document.getElementById(`question_${{index}}`);
    if (currentQuestionEl) {{
        currentQuestionEl.style.display = 'block';
    }}
    
    currentQuestionIndex = index;
    
    // 更新导航按钮状态
    updateNavigationButtons();
    updateQuestionNavigation();
    
    // 恢复用户答案
    restoreUserAnswer(index);
}}

// 选择选项
function selectOption(questionIndex, optionIndex) {{
    const question = questions[questionIndex];
    const selectedOption = question.options[optionIndex];
    const correctAnswer = question.answer;
    
    // 清除之前的选择和反馈样式
    question.options.forEach((_, i) => {{
        const optionEl = document.getElementById(`option_${{questionIndex}}_${{i}}`);
        if (optionEl) {{
            optionEl.classList.remove('selected', 'correct', 'incorrect');
        }}
    }});
    
    // 标记当前选择
    const optionEl = document.getElementById(`option_${{questionIndex}}_${{optionIndex}}`);
    if (optionEl) optionEl.classList.add('selected');
    
    // 保存用户答案
    userAnswers[questionIndex] = selectedOption.text;
    
    // 显示即时反馈
    const isCorrect = selectedOption.text === correctAnswer;
    
    // 标记所有选项的正确性
    question.options.forEach((option, i) => {{
        const optEl = document.getElementById(`option_${{questionIndex}}_${{i}}`);
        if (optEl) {{
            if (option.text === correctAnswer) {{
                // 正确答案用绿色标记
                optEl.classList.add('correct');
            }} else if (i === optionIndex && !isCorrect) {{
                // 用户选择的错误答案用红色标记
                optEl.classList.add('incorrect');
            }}
        }}
    }});
    
    // 更新题目导航状态
    updateQuestionNavigation();
    
    // 显示提交按钮（如果是最后一题）
    if (currentQuestionIndex === questions.length - 1) {{
        document.getElementById('submitBtn').style.display = 'inline-block';
    }}
    
    // 检查是否所有题目都已回答
    const allAnswered = questions.every((_, index) => userAnswers.hasOwnProperty(index));
    if (allAnswered) {{
        document.getElementById('submitBtn').style.display = 'inline-block';
    }}
}}

// 恢复用户答案
function restoreUserAnswer(questionIndex) {{
    const question = questions[questionIndex];
    const userAnswer = userAnswers[questionIndex];
    
    if (!userAnswer) {{
        // 清除所有反馈样式
        if (question.options) {{
            question.options.forEach((_, i) => {{
                const optionEl = document.getElementById(`option_${{questionIndex}}_${{i}}`);
                if (optionEl) {{
                    optionEl.classList.remove('selected', 'correct', 'incorrect');
                }}
            }});
        }}
        return;
    }}
    
    if (question.type === '填空题') {{
        const input = document.getElementById(`answer_${{questionIndex}}`);
        if (input) input.value = userAnswer;
    }} else {{
        // 选择题 - 只恢复选择状态，不显示反馈
        question.options.forEach((option, i) => {{
            const optionEl = document.getElementById(`option_${{questionIndex}}_${{i}}`);
            if (optionEl) {{
                // 清除所有样式
                optionEl.classList.remove('selected', 'correct', 'incorrect');
                
                // 只标记用户选择的答案
                if (option.text === userAnswer) {{
                    optionEl.classList.add('selected');
                }}
            }}
        }});
    }}
}}

// 处理填空题输入
document.addEventListener('input', function(e) {{
    if (e.target.classList.contains('fill-blank-input')) {{
        const questionIndex = parseInt(e.target.id.split('_')[1]);
        userAnswers[questionIndex] = e.target.value.trim();
        updateQuestionNavigation();
    }}
}});

// 上一题
function previousQuestion() {{
    if (currentQuestionIndex > 0) {{
        showQuestion(currentQuestionIndex - 1);
    }}
}}

// 下一题
function nextQuestion() {{
    if (currentQuestionIndex < questions.length - 1) {{
        showQuestion(currentQuestionIndex + 1);
    }}
}}

// 更新导航按钮状态
function updateNavigationButtons() {{
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    prevBtn.disabled = currentQuestionIndex === 0;
    nextBtn.style.display = currentQuestionIndex === questions.length - 1 ? 'none' : 'inline-block';
    
    // 检查是否所有题目都已回答
    const allAnswered = questions.every((_, index) => userAnswers.hasOwnProperty(index));
    if (allAnswered || currentQuestionIndex === questions.length - 1) {{
        submitBtn.style.display = 'inline-block';
    }}
}}

// 更新题目导航状态
function updateQuestionNavigation() {{
    questions.forEach((question, index) => {{
        const navBtn = document.getElementById(`nav_btn_${{index}}`);
        if (navBtn) {{
            navBtn.classList.remove('current', 'answered', 'correct', 'incorrect');
            
            if (index === currentQuestionIndex) {{
                navBtn.classList.add('current');
            }}
            
            if (userAnswers.hasOwnProperty(index)) {{
                navBtn.classList.add('answered');
                
                // 检查答案正确性并添加相应的颜色状态
                const userAnswer = userAnswers[index];
                const correctAnswer = question.answer;
                const isCorrect = userAnswer.toLowerCase().trim() === correctAnswer.toLowerCase().trim();
                
                if (isCorrect) {{
                    navBtn.classList.add('correct');
                }} else {{
                    navBtn.classList.add('incorrect');
                }}
            }}
        }}
    }});
}}

// 更新进度
function updateProgress() {{
    const answeredCount = Object.keys(userAnswers).length;
    const totalCount = questions.length;
    const percentage = (answeredCount / totalCount) * 100;
    
    document.getElementById('progressFill').style.width = `${{percentage}}%`;
    document.getElementById('progressText').textContent = `${{answeredCount}} / ${{totalCount}}`;
}}

// 提交测试
function submitQuiz() {{
    const endTime = new Date();
    const totalTime = Math.round((endTime - startTime) / 1000);
    
    // 计算成绩
    const results = calculateResults();
    
    // 显示结果
    showResults(results, totalTime);
}}

// 计算成绩
function calculateResults() {{
    let correctCount = 0;
    let allAnswers = [];
    
    questions.forEach((question, index) => {{
        const userAnswer = userAnswers[index] || '';
        const correctAnswer = question.answer;
        
        // 判断答案是否正确（忽略大小写）
        const isCorrect = userAnswer.toLowerCase().trim() === correctAnswer.toLowerCase().trim();
        
        if (isCorrect) {{
            correctCount++;
        }}
        
        // 记录所有题目的答题情况
        allAnswers.push({{
            questionNumber: index + 1,
            question: question.question,
            userAnswer: userAnswer || '未回答',
            correctAnswer: correctAnswer,
            type: question.type,
            isCorrect: isCorrect
        }});
    }});
    
    const totalCount = questions.length;
    const wrongCount = totalCount - correctCount;
    const accuracy = Math.round((correctCount / totalCount) * 100);
    
    return {{
        totalCount,
        correctCount,
        wrongCount,
        accuracy,
        allAnswers
    }};
}}

// 显示结果
function showResults(results, totalTime) {{
    const container = document.getElementById('resultsContainer');
    
    // 隐藏测试界面
    document.getElementById('progressContainer').style.display = 'none';
    document.getElementById('questionNav').style.display = 'none';
    document.getElementById('questionsContainer').style.display = 'none';
    document.getElementById('navigationContainer').style.display = 'none';
    
    // 确定成绩等级
    let scoreClass = 'score-poor';
    let scoreText = '需要加强';
    if (results.accuracy >= 90) {{
        scoreClass = 'score-excellent';
        scoreText = '优秀';
    }} else if (results.accuracy >= 70) {{
        scoreClass = 'score-good';
        scoreText = '良好';
    }}
    
    // 生成所有题目回顾列表
    let allAnswersHtml = '';
    if (results.allAnswers.length > 0) {{
        allAnswersHtml = `
            <div class="all-answers">
                <h3>题目回顾</h3>
                ${{results.allAnswers.map(item => `
                    <div class="answer-item ${{item.isCorrect ? 'correct-item' : 'incorrect-item'}}">
                        <div class="answer-question">
                            <span class="question-status ${{item.isCorrect ? 'status-correct' : 'status-incorrect'}}">
                                ${{item.isCorrect ? '✓' : '✗'}}
                            </span>
                            第${{item.questionNumber}}题: ${{item.question}}
                        </div>
                        <div class="answer-details">
                            <div class="user-answer ${{item.isCorrect ? 'correct-answer' : 'wrong-answer'}}">
                                你的答案: ${{item.userAnswer}}
                            </div>
                            <div class="correct-answer-display">
                                正确答案: ${{item.correctAnswer}}
                            </div>
                        </div>
                    </div>
                `).join('')}}
            </div>
        `;
    }}
    
    container.innerHTML = `
        <div class="results-container">
            <h2 class="results-title">测试完成！</h2>
            <div class="score-display ${{scoreClass}}">${{results.accuracy}}% (${{scoreText}})</div>
            
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${{results.totalCount}}</div>
                    <div class="stat-label">总题数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${{results.correctCount}}</div>
                    <div class="stat-label">正确题数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${{results.wrongCount}}</div>
                    <div class="stat-label">错误题数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${{Math.floor(totalTime / 60)}}:${{String(totalTime % 60).padStart(2, '0')}}</div>
                    <div class="stat-label">用时</div>
                </div>
            </div>
            
            ${{allAnswersHtml}}
            
            <button class="restart-btn" onclick="restartQuiz()">重新开始</button>
        </div>
    `;
    
    container.style.display = 'block';
}}

// 重新开始测试
function restartQuiz() {{
    // 重置所有状态
    questions = [...originalQuestions];
    userAnswers = {{}};
    currentQuestionIndex = 0;
    quizStarted = false;
    startTime = null;
    
    // 重置界面
    document.querySelector('.quiz-controls').style.display = 'flex';
    document.getElementById('progressContainer').style.display = 'none';
    document.getElementById('questionNav').style.display = 'none';
    document.getElementById('questionsContainer').style.display = 'none';
    document.getElementById('navigationContainer').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'none';
    
    // 重置控制选项
    document.getElementById('shuffleQuestions').checked = false;
    document.getElementById('shuffleOptions').checked = false;
}}

// 监听进度更新
setInterval(() => {{
    if (quizStarted) {{
        updateProgress();
    }}
}}, 1000);
        """
        
        return js_code
    
    def generate_quiz_from_excel(self, excel_file_path: str, watermark: str = "坦克云课堂") -> Tuple[str, str]:
        """从Excel文件生成测试HTML"""
        try:
            # 读取Excel文件
            df = self.read_excel_file(excel_file_path)
            
            # 处理题目数据
            questions = self.process_questions(df)
            
            if not questions:
                raise Exception("没有找到有效的题目数据")
            
            # 生成文件名
            base_name = os.path.splitext(os.path.basename(excel_file_path))[0]
            quiz_title = base_name
            output_filename = f"{base_name}.html"
            output_path = os.path.join(self.outputs_dir, output_filename)
            
            # 生成HTML内容
            html_content = self.generate_quiz_html(questions, quiz_title, watermark)
            
            # 保存HTML文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path, f"成功生成测试文件: {output_filename}\n包含 {len(questions)} 道题目"
            
        except Exception as e:
            raise Exception(f"生成测试失败: {str(e)}")
    
    def batch_generate_quizzes(self, excel_files: List[str], watermark: str = "坦克云课堂") -> List[Tuple[str, str]]:
        """批量生成测试HTML文件"""
        results = []
        
        for excel_file in excel_files:
            try:
                output_path, message = self.generate_quiz_from_excel(excel_file, watermark)
                results.append((output_path, message))
            except Exception as e:
                results.append((None, f"处理文件 {excel_file} 失败: {str(e)}"))
        
        return results
    
    def get_quiz_statistics(self, excel_file_path: str) -> Dict[str, Any]:
        """获取题目统计信息"""
        try:
            df = self.read_excel_file(excel_file_path)
            questions = self.process_questions(df)
            
            # 统计题目类型
            type_counts = {}
            for question in questions:
                q_type = question['type']
                type_counts[q_type] = type_counts.get(q_type, 0) + 1
            
            return {
                'total_questions': len(questions),
                'question_types': type_counts,
                'file_name': os.path.basename(excel_file_path)
            }
            
        except Exception as e:
            return {'error': str(e)}