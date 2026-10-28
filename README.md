# MindGrove

AI学习资料整理助手——把零散课件整理成一片知识森林。

人工智能导论课程实践项目。上传一份课程课件（PDF/PPT/Word），系统自动完成文档解析、知识点抽取、结构化笔记、思维导图与自测题生成，帮助复习阶段快速把课件整理成体系化内容。

## 功能

- 多格式课件解析：PDF（文本版+扫描版OCR）、PPT、Word
- 结构化笔记：按章节自动抽取知识点，输出Markdown笔记
- 思维导图：一键生成可折叠的知识结构导图
- 自测题：基于内容生成选择题，检验复习效果
- 浏览器界面：上传→等待数十秒→直接看到全部成果

## 技术栈

- 界面：Gradio
- 文档解析：PyMuPDF / python-pptx / python-docx / RapidOCR
- 大模型：豆包API（火山方舟，OpenAI兼容接口）
- 思维导图：markmap（前端CDN渲染）

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 复制 `.env.example` 为 `.env`，填入豆包API Key和模型endpoint id
3. 运行：`python app.py`
4. 浏览器打开终端显示的本地地址，上传课件即可

## 项目结构

```
mindgrove/
├── app.py          # Gradio主入口
├── parser.py       # 文档解析
├── llm.py          # 大模型调用
├── notes.py        # 笔记生成
├── mindmap.py      # 思维导图
├── questions.py    # 自测题生成
├── requirements.txt
└── .env.example
```

## 里程碑

- [x] W1-2：环境搭建 + 文档解析demo
- [ ] W3-4：笔记生成 + prompt调优
- [ ] W5-6：思维导图 + 出题
- [ ] W7-8：Gradio全链路串联
- [ ] W9：缓冲与样例补采
- [ ] W10：结题报告 + 课堂展示
