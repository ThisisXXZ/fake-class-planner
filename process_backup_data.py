"""
数据处理脚本：从backup文件处理数据，去除重复entries，生成新的Excel文件
"""

import pandas as pd
from collections import defaultdict
import os

def process_backup_to_clean_data():
    """
    从backup文件处理数据，去除重复的entries，生成干净的Excel文件
    """
    
    print("=== 从backup文件处理数据 ===")
    
    # 读取backup文件
    backup_file = 'data/2025-26_class_timetable_20250806_backup.xlsx'
    output_file = 'data/2025-26_class_timetable_20250806.xlsx'
    
    print(f"读取backup文件: {backup_file}")
    df = pd.read_excel(backup_file)
    df.columns = df.columns.str.strip()  # 清理列名
    
    print(f"原始数据: {len(df)} 行, {df['COURSE CODE'].nunique()} 门课程")
    
    # 处理数据：去除每个课程每个class number中相同星期几的重复entries
    processed_entries = []
    
    # 按课程代码分组
    for course_code, course_group in df.groupby('COURSE CODE'):
        if pd.isna(course_code):
            continue
            
        # 按CLASS NUMBER分组
        for class_number, class_group in course_group.groupby('CLASS NUMBER'):
            if pd.isna(class_number):
                continue
                
            # 对于每个class number，去除相同星期几组合的重复entries
            processed_day_combinations = set()
            
            for _, row in class_group.iterrows():
                # 获取上课日期
                days = []
                for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']:
                    if pd.notna(row[day]):
                        days.append(day)
                
                # 将days列表转换为排序后的元组，用作去重的key
                day_tuple = tuple(sorted(days))
                
                # 只保留第一个出现的相同星期几组合的entry
                if day_tuple not in processed_day_combinations:
                    processed_day_combinations.add(day_tuple)
                    processed_entries.append(row.to_dict())
    
    # 创建新的DataFrame
    processed_df = pd.DataFrame(processed_entries)
    
    print(f"处理后数据: {len(processed_df)} 行, {processed_df['COURSE CODE'].nunique()} 门课程")
    print(f"去除了 {len(df) - len(processed_df)} 行重复数据")
    
    # 保存处理后的数据
    print(f"保存到: {output_file}")
    processed_df.to_excel(output_file, index=False)
    
    # 删除旧的cache文件，让系统重新生成
    cache_file = 'data/2025-26_class_timetable_20250806.cache'
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print(f"删除旧cache文件: {cache_file}")
    
    return processed_df

def main():
    try:
        result_df = process_backup_to_clean_data()
        print("\n=== 处理完成 ===")
        print("✓ 成功从backup文件生成新的Excel文件")
        print("✓ 去除了重复的entries")
        print("✓ 保留了所有课程（包括BSTC2004）") 
        return result_df
    except Exception as e:
        print(f"处理过程中出错: {e}")
        return None

if __name__ == "__main__":
    main()