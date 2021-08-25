from unityparser import UnityDocument
from tqdm import tqdm
import json
import os
import csv
import time

SYS_ENV_JSON_PATH = 'C:/ROGameFeature/sys_env.json'
# 写入CSV文件
output_file_path = 'result.csv'

UI_EFFECT_PREFIX = 'fx_ui'
PREFAB_FILE_SUFFIX = '.prefab'
MOON_RES_PATH = 'MoonResPath'
UI_PREFAB_RELATIVE_PATH = '/Resources/UI/Prefabs/'
UI_EFFECT_RELATIVE_PATH = 'Effects/Prefabs/Creature/Ui/'

# CSV文件表头
headers = ['ResourceName', 'ResourcePath', 'Type', 'EffectName', 'EffectPath']
# CSV文件内容
rows = []

def local_time_str(format:str=None):
    """
    日志用
    :param format: 格式字符串，为空默认"%Y-%m-%d %H:%M:%S"
    :return: 本地时间字符串
    """
    formatStr = format or '%Y-%m-%d %H:%M:%S'
    return time.strftime(formatStr, time.localtime())


def add_row_data(resource_name, resource_path, type, effect_name, effect_path):
    """
    往文件中写入一条记录
    :param resource_name: 引用特效资源名
    :param resource_path: 引用特效资源路径
    :param type: 资源类型
    :param effect_name: 特效名
    :param effect_path: 特效路径
    """
    rows.append([resource_name, resource_path, type, effect_name, effect_path])

def load_and_filter_yaml(file_path):
    """
    解析YAML文件，打印出特效节点信息
    :param file_path: yaml文件绝对路径
    """
    doc = UnityDocument.load_yaml(file_path=file_path)
    file_name = file_path[file_path.rfind('/')+1:]
    # 特效助手配置路径
    entries = doc.filter(('MonoBehaviour',), ('EffectPath',))
    for entry in entries:
        effect_path = entry.EffectPath
        effect_name = effect_path[effect_path.rfind('/')+1:]
        add_row_data(file_name, file_path, 'effect helper', effect_name, effect_path)
        # print(f"[{file_path}][EFFECT HELPER]: {entry.EffectPath}")

    # 特效prefab直接放在UIprefab中
    entries = doc.filter(('PrefabInstance',))
    for entry in entries:
        modifications = entry.m_Modification['m_Modifications']
        for modification in modifications:
            if modification['propertyPath'] != 'm_Name':
                continue
            name = modification['value']
            if str(name)[:5].lower() != UI_EFFECT_PREFIX:
                continue
            add_row_data(file_name, file_path, 'prefab instance', name, UI_EFFECT_RELATIVE_PATH + name)
            # print(f"[{file_path}][PREFAB INSTANCE]: {name}")


def walk_through_directory(directory):
    """
    递归遍历目录下的每一个prefab文件
    :param directory: 根目录
    """
    prefab_path_list = []
    print(f'[{local_time_str()}] 对\'{directory}\'目录深度搜索搜索...')
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file).replace('\\', '/')
            if not file_path.endswith(PREFAB_FILE_SUFFIX):
                continue
            prefab_path_list.append(file_path)
    
    pbar = tqdm(prefab_path_list)
    for prefab_path in pbar:
        try:
            load_and_filter_yaml(prefab_path)
            pbar.set_description_str(f'正在处理\'{prefab_path}\'')
        except Exception as e:
            print(f'[{prefab_path}] 解析YAML时发生错误')
            print(e)


def save_result():
    """
    将搜索结果写入到`OUTPUT_FILE_PATH`
    """
    write_success = False
    output_file_path = local_time_str('%Y%m%d%H%M%S') + '.csv'
    with open(output_file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
        write_success = True
    
    result_str = write_success and '成功' or '失败'
    print(f'[{local_time_str()}] 特效引用搜索结果输出到文件\'{output_file_path}\'{result_str}')


def main():
    print(f'[{local_time_str()}] 开始特效引用搜索...')

    fp = open(SYS_ENV_JSON_PATH, 'r')
    sys_env = json.load(fp)
    if MOON_RES_PATH in sys_env.keys():
        artres_path = sys_env[MOON_RES_PATH]
        walk_through_directory(artres_path + UI_PREFAB_RELATIVE_PATH)
    save_result()


if __name__ == '__main__':
    # TODO 脚本参数传入
    # TODO .unity特效查找
    main()
