# 老年人健康档案服务平台

## 项目简介
本项目旨在为老年人提供一个全面的健康管理服务平台，通过数据整合、分析和个性化建议，帮助老年人更好地管理自己的健康状况。

## 功能模块
1. 健康数据整合模块
   - 整合体检报告
   - 病史记录管理
   - 日常健康监测数据记录

2. 健康数据分析模块
   - 健康趋势分析
   - 潜在风险识别
   - 健康需求评估

3. 个性化健康建议与预防方案模块
   - 个性化健康建议生成
   - 预防方案制定
   - 健康改善追踪

4. 健康教育资源模块
   - 疾病预防知识库
   - 健康生活方式指南
   - 健康知识推送

## 技术栈
- 后端：Python Flask
- 数据库：SQLite
- 前端：HTML5, CSS3, JavaScript
- UI框架：Bootstrap 5

## 如何运行
1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python app.py
```

3. 访问网站：
打开浏览器访问 http://localhost:5000

## 项目结构
```
project/
├── app.py              # 主应用文件
├── config.py           # 配置��件
├── requirements.txt    # 项目依赖
├── static/            # 静态文件目录
│   ├── css/          # CSS文件
│   ├── js/           # JavaScript文件
│   └── images/       # 图片资源
├── templates/         # HTML模板目录
└── database/         # 数据库文件目录
``` 