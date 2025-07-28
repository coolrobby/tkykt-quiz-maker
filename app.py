import streamlit as st
import pandas as pd
import os
import zipfile
from io import BytesIO
import base64
from datetime import datetime
import re

# 设置页面配置
st.set_page_config(
    page_title="题目大师 - 坦克云课堂",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stTitle {
        color: #1e3c72;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-section {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 2px dashed #667eea;
    }
    .success-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .info-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    .download-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        text-decoration: none;
        font-weight: 600;
        display: inline-block;
        margin: 0.5rem;
        transition: all 0.3s ease;
    }
    .download-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

def load_template(template_name):
    """加载HTML模板文件"""
    template_path = os.path.join("templates", template_name)
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def detect_question_type(row):
    """智能识别题目类型"""
    options = [row.get('选项A', ''), row.get('选项B', ''), row.get('选项C', ''), row.get('选项D', '')]
    
    # 移除空值和NaN
    valid_options = [opt for opt in options if pd.notna(opt) and str(opt).strip() != '']
    
    if len(valid_options) == 0:
        return 'fill_blank'  # 填空题
    elif len(valid_options) >= 3:
        return 'multiple_choice'  # 选择题
    else:
        return 'multiple_choice'  # 默认为选择题

def generate_html_content(df, filename):
    """生成HTML内容"""
    # 加载模板
    header_template = load_template('header.html')
    footer_template = load_template('footer.html')
    
    # 获取文件名（不含扩展名）作为标题
    title = os.path.splitext(filename)[0]
    
    # 替换模板中的标题占位符
    header_content = header_template.replace('{{title}}', title)
    
    # 生成题目数据
    questions_data = []
    for idx, row in df.iterrows():
        question_type = detect_question_type(row)
        
        question_data = {
            'id': idx + 1,
            'type': question_type,
            'question': str(row.get('题干', '')),
            'answer': str(row.get('答案', ''))
        }
        
        if question_type == 'multiple_choice':
            options = []
            for opt_key in ['选项A', '选项B', '选项C', '选项D']:
                opt_value = row.get(opt_key, '')
                if pd.notna(opt_value) and str(opt_value).strip() != '':
                    options.append(str(opt_value))
            question_data['options'] = options
        
        questions_data.append(question_data)
    
    # 生成主要内容区域的HTML
    main_content = f"""
    <main class="content">
        <div class="container">
            <div class="quiz-container">
                <div class="quiz-header">
                    <h1 class="quiz-title">{title}</h1>
                    <div class="quiz-controls">
                        <div class="control-group">
                            <label class="switch">
                                <input type="checkbox" id="shuffleQuestions">
                                <span class="slider"></span>
                            </label>
                            <span class="control-label">题目乱序</span>
                        </div>
                        <div class="control-group">
                            <label class="switch">
                                <input type="checkbox" id="shuffleOptions">
                                <span class="slider"></span>
                            </label>
                            <span class="control-label">选项乱序</span>
                        </div>
                        <button id="startQuiz" class="start-btn">开始答题</button>
                    </div>
                </div>
                
                <div class="quiz-progress" id="quizProgress" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">0 / {len(questions_data)}</div>
                </div>
                
                <div class="question-navigation" id="questionNav" style="display: none;">
                    <div class="nav-buttons" id="navButtons"></div>
                </div>
                
                <div class="quiz-content" id="quizContent" style="display: none;">
                    <div class="question-container" id="questionContainer"></div>
                    <div class="quiz-actions">
                        <button id="prevBtn" class="nav-btn" disabled>上一题</button>
                        <button id="nextBtn" class="nav-btn">下一题</button>
                        <button id="submitBtn" class="submit-btn" style="display: none;">提交答案</button>
                    </div>
                </div>
                
                <div class="quiz-result" id="quizResult" style="display: none;">
                    <div class="result-summary" id="resultSummary"></div>
                    <div class="wrong-answers" id="wrongAnswers"></div>
                    <button id="restartBtn" class="restart-btn">重新开始</button>
                </div>
            </div>
        </div>
    </main>
    
    <style>
    /* 答题界面样式 */
    .quiz-container {{
        max-width: 800px;
        margin: 2rem auto;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        overflow: hidden;
    }}
    
    .quiz-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        text-align: center;
    }}
    
    .quiz-title {{
        font-size: 2rem;
        margin-bottom: 1.5rem;
        font-weight: 700;
    }}
    
    .quiz-controls {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2rem;
        flex-wrap: wrap;
    }}
    
    .control-group {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .control-label {{
        font-weight: 500;
        font-size: 1rem;
    }}
    
    /* 开关样式 */
    .switch {{
        position: relative;
        display: inline-block;
        width: 50px;
        height: 24px;
    }}
    
    .switch input {{
        opacity: 0;
        width: 0;
        height: 0;
    }}
    
    .slider {{
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255,255,255,0.3);
        transition: .4s;
        border-radius: 24px;
    }}
    
    .slider:before {{
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
    }}
    
    input:checked + .slider {{
        background-color: rgba(255,255,255,0.8);
    }}
    
    input:checked + .slider:before {{
        transform: translateX(26px);
    }}
    
    .start-btn, .nav-btn, .submit-btn, .restart-btn {{
        background: rgba(255,255,255,0.2);
        color: white;
        border: 2px solid white;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .start-btn:hover, .nav-btn:hover, .submit-btn:hover, .restart-btn:hover {{
        background: white;
        color: #667eea;
    }}
    
    .nav-btn:disabled {{
        opacity: 0.5;
        cursor: not-allowed;
    }}
    
    .nav-btn:disabled:hover {{
        background: rgba(255,255,255,0.2);
        color: white;
    }}
    
    /* 进度条样式 */
    .quiz-progress {{
        padding: 1.5rem;
        background: #f8f9fa;
        border-bottom: 1px solid #e9ecef;
    }}
    
    .progress-bar {{
        width: 100%;
        height: 8px;
        background: #e9ecef;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }}
    
    .progress-fill {{
        height: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        width: 0%;
        transition: width 0.3s ease;
    }}
    
    .progress-text {{
        text-align: center;
        font-weight: 600;
        color: #667eea;
    }}
    
    /* 题号导航 */
    .question-navigation {{
        padding: 1rem;
        background: #f8f9fa;
        border-bottom: 1px solid #e9ecef;
    }}
    
    .nav-buttons {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
    }}
    
    .nav-number {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid #e9ecef;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .nav-number:hover {{
        border-color: #667eea;
        color: #667eea;
    }}
    
    .nav-number.current {{
        background: #667eea;
        color: white;
        border-color: #667eea;
    }}
    
    .nav-number.answered {{
        background: #28a745;
        color: white;
        border-color: #28a745;
    }}
    
    /* 题目内容 */
    .quiz-content {{
        padding: 2rem;
    }}
    
    .question-container {{
        margin-bottom: 2rem;
    }}
    
    .question-text {{
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        color: #2c3e50;
        line-height: 1.6;
    }}
    
    .options-container {{
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }}
    
    .option {{
        display: flex;
        align-items: center;
        padding: 1rem;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
        background: white;
    }}
    
    .option:hover {{
        border-color: #667eea;
        background: #f8f9fa;
    }}
    
    .option.selected {{
        border-color: #667eea;
        background: #e7f3ff;
    }}
    
    .option.correct {{
        border-color: #28a745;
        background: #d4edda;
    }}
    
    .option.wrong {{
        border-color: #dc3545;
        background: #f8d7da;
    }}
    
    .option-radio {{
        margin-right: 1rem;
        width: 20px;
        height: 20px;
    }}
    
    .option-text {{
        font-size: 1rem;
        flex: 1;
    }}
    
    /* 填空题样式 */
    .fill-blank-input {{
        width: 100%;
        padding: 1rem;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }}
    
    .fill-blank-input:focus {{
        outline: none;
        border-color: #667eea;
    }}
    
    /* 答题操作按钮 */
    .quiz-actions {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 2rem;
    }}
    
    /* 结果页面 */
    .quiz-result {{
        padding: 2rem;
        text-align: center;
    }}
    
    .result-summary {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
    }}
    
    .result-title {{
        font-size: 2rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }}
    
    .result-stats {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-top: 1.5rem;
    }}
    
    .stat-item {{
        background: rgba(255,255,255,0.2);
        padding: 1rem;
        border-radius: 10px;
    }}
    
    .stat-number {{
        font-size: 2rem;
        font-weight: bold;
        display: block;
    }}
    
    .stat-label {{
        font-size: 0.9rem;
        opacity: 0.9;
    }}
    
    .wrong-answers {{
        text-align: left;
        margin-bottom: 2rem;
    }}
    
    .wrong-answer-item {{
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #dc3545;
    }}
    
    .wrong-question {{
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #2c3e50;
    }}
    
    .wrong-details {{
        color: #6c757d;
        font-size: 0.9rem;
    }}
    
    /* 响应式设计 */
    @media (max-width: 768px) {{
        .quiz-controls {{
            flex-direction: column;
            gap: 1rem;
        }}
        
        .quiz-title {{
            font-size: 1.5rem;
        }}
        
        .quiz-actions {{
            flex-direction: column;
            gap: 1rem;
        }}
        
        .nav-btn, .submit-btn {{
            width: 100%;
        }}
        
        .result-stats {{
            grid-template-columns: repeat(2, 1fr);
        }}
    }}
    
    @media (max-width: 480px) {{
        .quiz-container {{
            margin: 1rem;
            border-radius: 15px;
        }}
        
        .quiz-header {{
            padding: 1.5rem;
        }}
        
        .quiz-content {{
            padding: 1.5rem;
        }}
        
        .nav-buttons {{
            gap: 0.25rem;
        }}
        
        .nav-number {{
            width: 35px;
            height: 35px;
            font-size: 0.9rem;
        }}
        
        .result-stats {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>
    
    <script>
    // 题目数据
    const questionsData = {questions_data};
    
    // 全局变量
    let currentQuestionIndex = 0;
    let userAnswers = {{}};
    let shuffledQuestions = [];
    let startTime = null;
    let isQuizStarted = false;
    
    // 初始化
    document.addEventListener('DOMContentLoaded', function() {{
        initializeQuiz();
    }});
    
    function initializeQuiz() {{
        // 绑定开始按钮事件
        document.getElementById('startQuiz').addEventListener('click', startQuiz);
        
        // 绑定导航按钮事件
        document.getElementById('prevBtn').addEventListener('click', () => navigateQuestion(-1));
        document.getElementById('nextBtn').addEventListener('click', () => navigateQuestion(1));
        document.getElementById('submitBtn').addEventListener('click', submitQuiz);
        document.getElementById('restartBtn').addEventListener('click', restartQuiz);
    }}
    
    function startQuiz() {{
        isQuizStarted = true;
        startTime = new Date();
        
        // 获取用户设置
        const shuffleQuestions = document.getElementById('shuffleQuestions').checked;
        const shuffleOptions = document.getElementById('shuffleOptions').checked;
        
        // 准备题目数据
        shuffledQuestions = [...questionsData];
        if (shuffleQuestions) {{
            shuffledQuestions = shuffleArray(shuffledQuestions);
        }}
        
        // 如果需要选项乱序，处理每个题目的选项
        if (shuffleOptions) {{
            shuffledQuestions.forEach(question => {{
                if (question.type === 'multiple_choice' && question.options) {{
                    question.shuffledOptions = shuffleArray([...question.options]);
                }}
            }});
        }}
        
        // 显示答题界面
        document.getElementById('quizProgress').style.display = 'block';
        document.getElementById('questionNav').style.display = 'block';
        document.getElementById('quizContent').style.display = 'block';
        
        // 生成题号导航
        generateQuestionNavigation();
        
        // 显示第一题
        currentQuestionIndex = 0;
        showQuestion(currentQuestionIndex);
        
        // 更新进度
        updateProgress();
    }}
    
    function shuffleArray(array) {{
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {{
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }}
        return shuffled;
    }}
    
    function generateQuestionNavigation() {{
        const navButtons = document.getElementById('navButtons');
        navButtons.innerHTML = '';
        
        shuffledQuestions.forEach((question, index) => {{
            const button = document.createElement('div');
            button.className = 'nav-number';
            button.textContent = index + 1;
            button.addEventListener('click', () => {{
                currentQuestionIndex = index;
                showQuestion(currentQuestionIndex);
                updateProgress();
            }});
            navButtons.appendChild(button);
        }});
    }}
    
    function showQuestion(index) {{
        const question = shuffledQuestions[index];
        const container = document.getElementById('questionContainer');
        
        let html = `<div class="question-text">${{index + 1}}. ${{question.question}}</div>`;
        
        if (question.type === 'multiple_choice') {{
            html += '<div class="options-container">';
            const options = question.shuffledOptions || question.options;
            options.forEach((option, optIndex) => {{
                const optionId = `q${{index}}_opt${{optIndex}}`;
                html += `
                    <div class="option" onclick="selectOption(${{index}}, '${{option}}')"> 
                        <input type="radio" name="q${{index}}" value="${{option}}" id="${{optionId}}" class="option-radio">
                        <label for="${{optionId}}" class="option-text">${{String.fromCharCode(65 + optIndex)}}. ${{option}}</label>
                    </div>
                `;
            }});
            html += '</div>';
        }} else if (question.type === 'fill_blank') {{
            html += `<input type="text" class="fill-blank-input" id="fillBlank${{index}}" placeholder="请输入答案..." onchange="saveFillBlankAnswer(${{index}}, this.value)">`;
        }}
        
        container.innerHTML = html;
        
        // 恢复之前的答案
        if (userAnswers[index]) {{
            if (question.type === 'multiple_choice') {{
                const radio = document.querySelector(`input[name="q${{index}}"][value="${{userAnswers[index]}}"]`);
                if (radio) {{
                    radio.checked = true;
                    radio.closest('.option').classList.add('selected');
                }}
            }} else if (question.type === 'fill_blank') {{
                document.getElementById(`fillBlank${{index}}`).value = userAnswers[index];
            }}
        }}
        
        // 更新导航按钮状态
        updateNavigationButtons();
        updateQuestionNavigation();
    }}
    
    function selectOption(questionIndex, optionValue) {{
        userAnswers[questionIndex] = optionValue;
        
        // 更新选中状态
        const options = document.querySelectorAll(`input[name="q${{questionIndex}}"]`);
        options.forEach(option => {{
            option.closest('.option').classList.remove('selected');
        }});
        
        const selectedOption = document.querySelector(`input[name="q${{questionIndex}}"][value="${{optionValue}}"]`);
        if (selectedOption) {{
            selectedOption.checked = true;
            selectedOption.closest('.option').classList.add('selected');
        }}
        
        updateQuestionNavigation();
        updateProgress();
    }}
    
    function saveFillBlankAnswer(questionIndex, value) {{
        userAnswers[questionIndex] = value.trim();
        updateQuestionNavigation();
        updateProgress();
    }}
    
    function navigateQuestion(direction) {{
        const newIndex = currentQuestionIndex + direction;
        if (newIndex >= 0 && newIndex < shuffledQuestions.length) {{
            currentQuestionIndex = newIndex;
            showQuestion(currentQuestionIndex);
            updateProgress();
        }}
    }}
    
    function updateNavigationButtons() {{
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const submitBtn = document.getElementById('submitBtn');
        
        prevBtn.disabled = currentQuestionIndex === 0;
        
        if (currentQuestionIndex === shuffledQuestions.length - 1) {{
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'inline-block';
        }} else {{
            nextBtn.style.display = 'inline-block';
            submitBtn.style.display = 'none';
        }}
    }}
    
    function updateQuestionNavigation() {{
        const navButtons = document.querySelectorAll('.nav-number');
        navButtons.forEach((button, index) => {{
            button.classList.remove('current', 'answered');
            if (index === currentQuestionIndex) {{
                button.classList.add('current');
            }} else if (userAnswers[index] !== undefined && userAnswers[index] !== '') {{
                button.classList.add('answered');
            }}
        }});
    }}
    
    function updateProgress() {{
        const answeredCount = Object.keys(userAnswers).filter(key => userAnswers[key] !== undefined && userAnswers[key] !== '').length;
        const totalCount = shuffledQuestions.length;
        const percentage = (answeredCount / totalCount) * 100;
        
        document.getElementById('progressFill').style.width = percentage + '%';
        document.getElementById('progressText').textContent = `${{answeredCount}} / ${{totalCount}}`;
    }}
    
    function submitQuiz() {{
        const endTime = new Date();
        const totalTime = Math.round((endTime - startTime) / 1000);
        
        // 计算成绩
        let correctCount = 0;
        let wrongAnswers = [];
        
        shuffledQuestions.forEach((question, index) => {{
            const userAnswer = userAnswers[index] || '';
            const correctAnswer = question.answer;
            
            let isCorrect = false;
            if (question.type === 'fill_blank') {{
                isCorrect = userAnswer.toLowerCase().trim() === correctAnswer.toLowerCase().trim();
            }} else {{
                isCorrect = userAnswer === correctAnswer;
            }}
            
            if (isCorrect) {{
                correctCount++;
            }} else {{
                wrongAnswers.push({{
                    question: question.question,
                    userAnswer: userAnswer || '未答',
                    correctAnswer: correctAnswer,
                    type: question.type
                }});
            }}
        }});
        
        const accuracy = Math.round((correctCount / shuffledQuestions.length) * 100);
        
        // 显示结果
        showResult(correctCount, shuffledQuestions.length, accuracy, totalTime, wrongAnswers);
    }}
    
    function showResult(correctCount, totalCount, accuracy, totalTime, wrongAnswers) {{
        // 隐藏答题界面
        document.getElementById('quizProgress').style.display = 'none';
        document.getElementById('questionNav').style.display = 'none';
        document.getElementById('quizContent').style.display = 'none';
        
        // 显示结果界面
        const resultContainer = document.getElementById('quizResult');
        resultContainer.style.display = 'block';
        
        // 生成结果摘要
        const summaryHtml = `
            <div class="result-title">答题完成！</div>
            <div class="result-stats">
                <div class="stat-item">
                    <span class="stat-number">${{totalCount}}</span>
                    <span class="stat-label">总题数</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${{correctCount}}</span>
                    <span class="stat-label">正确题数</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${{totalCount - correctCount}}</span>
                    <span class="stat-label">错误题数</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${{accuracy}}%</span>
                    <span class="stat-label">正确率</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${{Math.floor(totalTime / 60)}}:${{String(totalTime % 60).padStart(2, '0')}}</span>
                    <span class="stat-label">用时</span>
                </div>
            </div>
        `;
        
        document.getElementById('resultSummary').innerHTML = summaryHtml;
        
        // 生成错题回顾
        let wrongAnswersHtml = '';
        if (wrongAnswers.length > 0) {{
            wrongAnswersHtml = '<h3 style="margin-bottom: 1rem; color: #dc3545;">错题回顾</h3>';
            wrongAnswers.forEach((item, index) => {{
                wrongAnswersHtml += `
                    <div class="wrong-answer-item">
                        <div class="wrong-question">${{index + 1}}. ${{item.question}}</div>
                        <div class="wrong-details">
                            <div>你的答案：${{item.userAnswer}}</div>
                            <div>正确答案：${{item.correctAnswer}}</div>
                        </div>
                    </div>
                `;
            }});
        }} else {{
            wrongAnswersHtml = '<div style="text-align: center; color: #28a745; font-size: 1.2rem; font-weight: 600;">🎉 恭喜！全部答对！</div>';
        }}
        
        document.getElementById('wrongAnswers').innerHTML = wrongAnswersHtml;
    }}
    
    function restartQuiz() {{
        // 重置所有状态
        currentQuestionIndex = 0;
        userAnswers = {{}};
        shuffledQuestions = [];
        startTime = null;
        isQuizStarted = false;
        
        // 重置界面
        document.getElementById('shuffleQuestions').checked = false;
        document.getElementById('shuffleOptions').checked = false;
        document.getElementById('quizProgress').style.display = 'none';
        document.getElementById('questionNav').style.display = 'none';
        document.getElementById('quizContent').style.display = 'none';
        document.getElementById('quizResult').style.display = 'none';
    }}
    </script>
    """
    
    # 组合完整的HTML
    full_html = header_content + main_content + footer_template
    
    return full_html

def process_excel_files(uploaded_files):
    """处理上传的Excel文件"""
    results = []
    
    for uploaded_file in uploaded_files:
        try:
            # 读取Excel文件
            df = pd.read_excel(uploaded_file)
            
            # 验证必要的列
            required_columns = ['题干', '答案']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"文件 {uploaded_file.name} 缺少必要的列: {', '.join(missing_columns)}")
                continue
            
            # 生成HTML内容
            html_content = generate_html_content(df, uploaded_file.name)
            
            # 生成文件名
            html_filename = os.path.splitext(uploaded_file.name)[0] + '.html'
            
            results.append({
                'filename': html_filename,
                'content': html_content,
                'question_count': len(df)
            })
            
        except Exception as e:
            st.error(f"处理文件 {uploaded_file.name} 时出错: {str(e)}")
    
    return results

def create_download_link(content, filename):
    """创建下载链接"""
    b64 = base64.b64encode(content.encode('utf-8')).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}" class="download-btn">📥 下载 {filename}</a>'
    return href

def create_zip_download(results):
    """创建批量下载的ZIP文件"""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for result in results:
            zip_file.writestr(result['filename'], result['content'])
    
    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="题目大师_生成文件_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip" class="download-btn">📦 批量下载所有文件</a>'
    return href

# 主界面
def main():
    # 标题
    st.markdown('<h1 class="stTitle">📚 题目大师 - 智能题目生成器</h1>', unsafe_allow_html=True)
    
    # 功能介绍
    st.markdown("""
    <div class="info-box">
        <h3>🎯 功能特色</h3>
        <ul>
            <li>📊 <strong>智能识别</strong>：自动识别选择题、填空题类型</li>
            <li>🔀 <strong>灵活乱序</strong>：支持题目和选项乱序功能</li>
            <li>📱 <strong>响应式设计</strong>：完美适配PC和移动端</li>
            <li>⚡ <strong>即时反馈</strong>：实时显示答题进度和结果</li>
            <li>📈 <strong>详细统计</strong>：完整的答题报告和错题回顾</li>
            <li>💾 <strong>离线可用</strong>：生成的HTML文件无需网络即可使用</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 文件上传区域
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📁 上传Excel文件")
    
    # Excel格式说明
    st.markdown("""
    <div class="feature-card">
        <h4>📋 Excel格式要求</h4>
        <p>请确保您的Excel文件包含以下列：</p>
        <ul>
            <li><strong>题干</strong>：题目内容（必需）</li>
            <li><strong>选项A</strong>：第一个选项（选择题必需）</li>
            <li><strong>选项B</strong>：第二个选项（选择题必需）</li>
            <li><strong>选项C</strong>：第三个选项（选择题必需）</li>
            <li><strong>选项D</strong>：第四个选项（可选，三选项题目可为空）</li>
            <li><strong>答案</strong>：正确答案内容（必需）</li>
        </ul>
        <p><strong>注意</strong>：填空题请将所有选项列留空，系统会自动识别为填空题。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 文件上传组件
    uploaded_files = st.file_uploader(
        "选择Excel文件",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="支持批量上传多个Excel文件"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 处理上传的文件
    if uploaded_files:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown(f"### ✅ 已上传 {len(uploaded_files)} 个文件")
        
        # 显示文件列表
        for file in uploaded_files:
            st.markdown(f"- 📄 {file.name}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 处理按钮
        if st.button("🚀 开始生成HTML文件", type="primary"):
            with st.spinner("正在处理文件，请稍候..."):
                results = process_excel_files(uploaded_files)
            
            if results:
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown(f"### 🎉 成功生成 {len(results)} 个HTML文件")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 显示处理结果
                st.markdown("### 📊 处理结果")
                
                # 创建结果表格
                result_data = []
                for result in results:
                    result_data.append({
                        '文件名': result['filename'],
                        '题目数量': result['question_count'],
                        '状态': '✅ 成功'
                    })
                
                result_df = pd.DataFrame(result_data)
                st.dataframe(result_df, use_container_width=True)
                
                # 下载区域
                st.markdown("### 📥 下载文件")
                
                # 单个文件下载
                st.markdown("**单个文件下载：**")
                download_html = ""
                for result in results:
                    download_html += create_download_link(result['content'], result['filename']) + " "
                
                st.markdown(download_html, unsafe_allow_html=True)
                
                # 批量下载
                if len(results) > 1:
                    st.markdown("**批量下载：**")
                    zip_download = create_zip_download(results)
                    st.markdown(zip_download, unsafe_allow_html=True)
                
                # 使用说明
                st.markdown("""
                <div class="info-box">
                    <h4>📖 使用说明</h4>
                    <ol>
                        <li>下载生成的HTML文件到本地</li>
                        <li>使用浏览器打开HTML文件</li>
                        <li>设置题目乱序和选项乱序选项</li>
                        <li>点击"开始答题"开始测试</li>
                        <li>完成后查看详细的答题报告</li>
                    </ol>
                    <p><strong>提示</strong>：生成的HTML文件完全独立，无需网络连接即可使用。</p>
                </div>
                """, unsafe_allow_html=True)
            
            else:
                st.error("❌ 没有成功处理任何文件，请检查文件格式是否正确。")
    
    # 侧边栏信息
    with st.sidebar:
        st.markdown("### 📋 项目信息")
        st.markdown("""
        **题目大师 v1.0**
        
        🏫 **坦克云课堂**
        
        ✨ **主要功能：**
        - Excel转HTML题目
        - 智能题型识别
        - 响应式设计
        - 离线答题系统
        
        🔧 **技术栈：**
        - Streamlit
        - Pandas
        - HTML/CSS/JavaScript
        
        📞 **联系方式：**
        - 微信：tank_0771
        - 网站：tkykt.com
        """)
        
        st.markdown("---")
        st.markdown("### 📊 使用统计")
        
        # 简单的使用统计（可以后续扩展）
        if 'file_count' not in st.session_state:
            st.session_state.file_count = 0
        
        if uploaded_files:
            st.session_state.file_count += len(uploaded_files)
        
        st.metric("累计处理文件", st.session_state.file_count)

if __name__ == "__main__":
    main()