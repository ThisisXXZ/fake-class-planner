#!/usr/bin/env python3
"""
选课网站启动脚本
运行命令：uv run python run.py
"""

from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("      选课网站启动中...")
    print("=" * 50)
    print("访问地址:")
    print("  课程浏览: http://localhost:5000/courses")
    print("  我的日程: http://localhost:5000/schedule")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)