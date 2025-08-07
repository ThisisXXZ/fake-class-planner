import pandas as pd
import string
from datetime import datetime
from collections import defaultdict
import re

class CourseDataProcessor:
    def __init__(self, xlsx_file_path):
        self.df = pd.read_excel(xlsx_file_path)
        self.df.columns = self.df.columns.str.strip()  # 清理列名
        self.processed_courses = None
        
    def get_semester_from_section(self, section):
        """从CLASS SECTION确定学期"""
        section_str = str(section)
        if section_str.startswith('1'):
            return 'Sem1'
        elif section_str.startswith('2'):
            return 'Sem2' 
        elif section_str.startswith('S'):
            return 'Summer'
        else:
            return 'Other'
    
    def process_courses(self):
        """处理课程数据，按CLASS NUMBER正确分组subclass和time slots"""
        courses_by_semester = {
            'Sem1': {},
            'Sem2': {},
            'Summer': {},
            'Other': {}
        }
        
        # 按课程代码分组
        for course_code in self.df['COURSE CODE'].unique():
            if pd.isna(course_code):
                continue
                
            course_data = self.df[self.df['COURSE CODE'] == course_code].copy()
            course_info = course_data.iloc[0]  # 获取课程基本信息
            
            # 按学期分组处理
            entries_by_semester = defaultdict(list)
            
            for _, row in course_data.iterrows():
                semester = self.get_semester_from_section(row['CLASS SECTION'])
                
                # 获取上课日期
                days = []
                for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']:
                    if pd.notna(row[day]):
                        days.append(day)
                
                if days:  # 只有有上课日期的entry才加入
                    entry = {
                        'section': str(row['CLASS SECTION']) if pd.notna(row['CLASS SECTION']) else '',
                        'days': days,
                        'start_time': str(row['START TIME']) if pd.notna(row['START TIME']) else '',
                        'end_time': str(row['END TIME']) if pd.notna(row['END TIME']) else '',
                        'venue': str(row['VENUE']) if pd.notna(row['VENUE']) else '',
                        'instructor': str(row['INSTRUCTOR']) if pd.notna(row['INSTRUCTOR']) else '',
                        'class_number': str(row['CLASS NUMBER']) if pd.notna(row['CLASS NUMBER']) else ''
                    }
                    entries_by_semester[semester].append(entry)
            
            # 为每个学期的课程创建subclass
            for semester, entries in entries_by_semester.items():
                if entries:  # 只有有entries的学期才创建课程
                    subclasses = {}
                    
                    # 按CLASS NUMBER分组，每个CLASS NUMBER对应一个subclass
                    entries_by_class_number = defaultdict(list)
                    for entry in entries:
                        entries_by_class_number[entry['class_number']].append(entry)
                    
                    # 为每个CLASS NUMBER创建一个subclass
                    for class_number, class_entries in entries_by_class_number.items():
                        if not class_entries:
                            continue
                        
                        # 使用第一个entry的section作为subclass标识
                        first_entry = class_entries[0]
                        subclass_label = first_entry['section']
                        
                        # 创建time slots列表
                        time_slots = []
                        for entry in class_entries:
                            time_slots.append({
                                'days': entry['days'],
                                'start_time': entry['start_time'],
                                'end_time': entry['end_time'],
                                'venue': entry['venue'],
                                'instructor': entry['instructor']
                            })
                        
                        subclasses[subclass_label] = {
                            'label': subclass_label,
                            'section': first_entry['section'],
                            'class_number': class_number,
                            'instructor': first_entry['instructor'],
                            'time_slots': time_slots
                        }
                    
                    courses_by_semester[semester][course_code] = {
                        'code': course_code,
                        'title': str(course_info['COURSE TITLE']) if pd.notna(course_info['COURSE TITLE']) else '',
                        'department': str(course_info['OFFER DEPT']) if pd.notna(course_info['OFFER DEPT']) else '',
                        'term': str(course_info['TERM']) if pd.notna(course_info['TERM']) else '',
                        'career': str(course_info['ACAD_CAREER']) if pd.notna(course_info['ACAD_CAREER']) else '',
                        'semester': semester,
                        'subclasses': subclasses
                    }
        
        self.processed_courses = courses_by_semester
        return courses_by_semester
    
    def get_courses_by_semester(self, semester):
        """获取特定学期的课程"""
        if not self.processed_courses:
            self.process_courses()
        return self.processed_courses.get(semester, {})
    
    def search_courses(self, query='', department='', semester='Sem1'):
        """搜索课程"""
        semester_courses = self.get_courses_by_semester(semester)
        
        results = []
        query = query.lower() if query else ''
        department = department.upper() if department else ''
        
        for course_code, course_info in semester_courses.items():
            # 搜索匹配
            match = True
            if query:
                match = (query in course_code.lower() or 
                        query in course_info['title'].lower())
            
            if department and match:
                match = department in course_info['department'].upper()
            
            if match:
                results.append(course_info)
        
        return results
    
    def get_course_by_code_and_semester(self, course_code, semester):
        """根据课程代码和学期获取课程信息"""
        semester_courses = self.get_courses_by_semester(semester)
        return semester_courses.get(course_code)
    
    def get_all_departments(self, semester='Sem1'):
        """获取特定学期的所有院系"""
        semester_courses = self.get_courses_by_semester(semester)
        
        departments = set()
        for course_info in semester_courses.values():
            if course_info['department']:
                departments.add(course_info['department'])
        
        return sorted(departments)
    
    def get_available_semesters(self):
        """获取所有可用的学期"""
        if not self.processed_courses:
            self.process_courses()
        
        available = []
        for semester, courses in self.processed_courses.items():
            if courses:  # 只返回有课程的学期
                available.append(semester)
        return available
    
    def get_time_conflict(self, schedule, semester):
        """检查时间冲突，考虑每个subclass的所有time slots"""
        time_slots = []
        
        for item in schedule:
            course_code = item['course_code']
            subclass_label = item['subclass']
            
            course = self.get_course_by_code_and_semester(course_code, semester)
            if course and subclass_label in course['subclasses']:
                subclass = course['subclasses'][subclass_label]
                # 遍历该subclass的所有time slots
                for time_slot in subclass['time_slots']:
                    for day in time_slot['days']:
                        time_slots.append({
                            'day': day,
                            'start': time_slot['start_time'],
                            'end': time_slot['end_time'],
                            'course': f"{course_code} ({subclass_label})"
                        })
        
        # 检查冲突
        conflicts = []
        for i in range(len(time_slots)):
            for j in range(i + 1, len(time_slots)):
                slot1, slot2 = time_slots[i], time_slots[j]
                if (slot1['day'] == slot2['day'] and 
                    self._time_overlap(slot1['start'], slot1['end'], slot2['start'], slot2['end'])):
                    conflicts.append((slot1['course'], slot2['course']))
        
        return conflicts
    
    def _time_overlap(self, start1, end1, start2, end2):
        """检查两个时间段是否重叠"""
        try:
            start1 = datetime.strptime(start1, '%H:%M:%S').time()
            end1 = datetime.strptime(end1, '%H:%M:%S').time()
            start2 = datetime.strptime(start2, '%H:%M:%S').time()
            end2 = datetime.strptime(end2, '%H:%M:%S').time()
            
            return not (end1 <= start2 or end2 <= start1)
        except:
            return False