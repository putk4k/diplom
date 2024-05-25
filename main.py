import sys
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
import json
import warnings

def load_data(filename):
    data = pd.read_csv(filename, sep=",", na_values='.')
    return data

def label_encode_columns(data, column):
    label_encoder = LabelEncoder()
    encoded_column = column + '_encoded'
    data[encoded_column] = label_encoder.fit_transform(data[column])
    print(f"Применен label encoding к столбцу '{column}', новый столбец '{encoded_column}' создан.")
    return encoded_column

def apply_interval_partitioning(data, column, numgroups):
    min_val = data[column].min()
    max_val = data[column].max()
    bins = np.linspace(min_val, max_val, numgroups + 1)
    labels = range(numgroups)
    interval_column = column + '_interval'
    data[interval_column] = pd.cut(data[column], bins=bins, labels=labels, include_lowest=True).astype(str)
    print(f"Равномерное разбиение числовых данных выполнено для столбца '{column}'.")
    return interval_column

def partition_data(data, selected_columns, numeric_column,numgroups):
    if numeric_column:
        data = data.sort_values(by=numeric_column)
    else:
        group_sizes = data.size().reset_index(name='group_size')
        data = data.sort_values(by="group_size")
    total_records = len(data)
    target_num_groups = numgroups
    target_group_size = total_records // target_num_groups
    groups = []
    start_idx = 0

    for i in range(target_num_groups):
        end_idx = start_idx + target_group_size
        if i == target_num_groups - 1:
            end_idx = total_records 
        group = data.iloc[start_idx:end_idx]
        groups.append(group)
        start_idx = end_idx

    data['Group Number'] = 0
    for i, group in enumerate(groups):
        data.loc[group.index, 'Group Number'] = i + 1
    return groups

def evaluate_distribution(groups):
    total_items = [len(group) for group in groups]
    max_items = max(total_items)
    min_items = min(total_items)
    percentage_difference = (max_items - min_items) / max_items * 100
    if percentage_difference <= 10:
        return True, total_items
    else:
        print("\nПартицирование согласно заданным условиям невозможно")
        return False, total_items

def format_output(groups, final_columns, data, numeric_column,numeric_columns):
    print(f"Партицирование возможно. Итоговое количество групп: {len(groups)}")
    total_records = len(data)

    for i, group in enumerate(groups):
        group_size = len(group)
        group_percentage = (group_size / total_records) * 100
        keys = {}

        for column in final_columns:
            if column in final_columns:
                min_val = group[column].min()
                max_val = group[column].max()
                keys[column] = (min_val, max_val)
            else:
                values = set(group[column])
                keys[column] = values

        formatted_keys = [f"{key}: {values}" for key, values in keys.items()]
        print(f"Group {i + 1} ({group_size} записей, {group_percentage:.2f}%): (" + " , ".join(formatted_keys) + ")")

def check_date_format(date_series):
    try:
        pd.to_datetime(date_series)
        return True
    except ValueError:
        return False

def main():
    if len(sys.argv) < 2 or sys.argv[1]== "uploads":
        print("Для начала работы необходимо выбрать файл")
        return  
    filename = sys.argv[1]
    numgroups = int(sys.argv[2])
    if numgroups <= 0:
        print("Некорректное значение. Введите другое количество необходимых партиций")
    selected_columns = sys.argv[3:]
    if not selected_columns:
        print("Для начала работы необходимо выбрать столбцы")
        return
    
    data = load_data(filename)
    data = data.infer_objects()
    final_columns = selected_columns.copy()
    print("Выбранные столбцы:", selected_columns)
    print("Количество партиций:",numgroups)
    num_col = []
    numeric_columns = []

    num_counter = 0
    for column in final_columns:
        if check_date_format(data[column].astype(str)) or (data[column].dtype in ['int64', 'float64'] and num_counter > 0):
            encoded_column = apply_interval_partitioning(data, column, numgroups)
            selected_columns.remove(column)
            selected_columns.append(encoded_column)
        elif data[column].dtype == 'object':
            encoded_column = label_encode_columns(data, column)
            selected_columns.remove(column)
            selected_columns.append(encoded_column)
        elif data[column].dtype in ['int64', 'float64']:
            numeric_columns.append(column)
            num_col.append(column);
            encoded_column = apply_interval_partitioning(data, column,numgroups)
            selected_columns.remove(column)
            selected_columns.append(encoded_column)
            num_counter += 1

    if not numeric_columns:
        if selected_columns:
            numeric_columns.append(selected_columns[0])
        # return

    print("\nСписок обработанных столбцов:", selected_columns)

    #for col in numeric_columns:
        #if col + '_interval' in selected_columns:
            #selected_columns.remove(col + '_interval')
        #if col + '_interval_encoded' in selected_columns:
            #selected_columns.remove(col + '_interval_encoded')

    groups = partition_data(data, selected_columns, numeric_columns[0] if numeric_columns else selected_columns[0], numgroups)

    can_partition, total_items = evaluate_distribution(groups)
    if can_partition:
        format_output(groups, final_columns, data, numeric_columns[0] if numeric_columns else selected_columns[0],num_col)

if __name__ == "__main__":
    warnings.filterwarnings("ignore", message="Could not infer format")
    main()
