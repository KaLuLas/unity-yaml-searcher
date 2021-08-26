from io import TextIOWrapper
from unityparser import UnityDocument
from effect_ref import EffectRefDict
from tqdm import tqdm
import json
import os
import csv
import sys
import time
import traceback

MOON_RES_PATH = 'MoonResPath'

# 写入CSV文件
output_file_path = 'result.csv'
# 文件句柄
output_file:TextIOWrapper = None
# csv写者
output_csv_writer = None

EFFECT_PREFIX = 'fx_'
PREFAB_FILE_SUFFIX = '.prefab'
SCENE_FILE_SUFFIX = '.unity'
META_FILE_SUFFIX = '.meta'

# Effect prefab目录相对artres库路径
EFFECT_PREFAB_RELATIVE_PATH = '/Resources/Effects/Prefabs/'
# UI prefab目录相对artres库路径
UI_PREFAB_RELATIVE_PATH = '/Resources/UI/Prefabs/'
# 场景目录相对artres库路径
SCENE_RESOURCE_RELATIVE_PATH = '/Resources/Scenes/'

EFFECT_HELPER_KEY = 'effect_helper'
PREFAB_INSTANCE_KEY = 'prefab_instance'

# CSV文件表头
headers = ['ResourceName', 'ResourcePath', 'EffectName', 'EffectPath', 'Type', 'RefCount']
# CSV文件内容
rows = []
# 特效prefab的guid(str)映射到特效prefab绝对路径
guid_to_effect_path = {}

def local_time_str(format:str=None):
    """
    日志用
    :param format: 格式字符串，为空默认"%Y-%m-%d %H:%M:%S"
    :return: 本地时间字符串
    """
    formatStr = format or '%Y-%m-%d %H:%M:%S'
    return time.strftime(formatStr, time.localtime())


def create_table_header():
    """
    创建写入文件，并添加表头
    """
    global output_file_path
    global output_file
    global output_csv_writer
    output_file_path = local_time_str('%Y%m%d%H%M%S') + '.csv'
    output_file = open(output_file_path, 'a', newline='')
    output_csv_writer = csv.writer(output_file)
    output_csv_writer.writerow(headers)
    output_file.flush()
    print(f'[{local_time_str()}] 已创建输出文件\'{output_file_path}\'，开始写入...')


def add_row_data(result:list):
    """
    往文件中写入一条记录
    """
    output_csv_writer.writerow(result)
    output_file.flush()


def load_and_filter_yaml(file_path):
    """
    解析YAML文件，打印出特效节点信息
    :param file_path: yaml文件绝对路径
    """
    doc = UnityDocument.load_yaml(file_path=file_path)
    file_name = file_path[file_path.rfind('/')+1:]
    effect_ref_dict = EffectRefDict(file_name, file_path)
    # 特效助手配置路径
    entries = doc.filter(('MonoBehaviour',), ('EffectPath',))
    # entry.anchor is fileID
    for entry in entries:
        # 特效助手配置的路径不带文件后缀
        effect_path = entry.EffectPath + PREFAB_FILE_SUFFIX
        effect_ref_dict.add_ref(effect_path, EFFECT_HELPER_KEY)
        # print(f"[{file_path}][{EFFECT_HELPER_KEY}]: {effect_path}")

    # 特效prefab直接放在UIprefab中
    entries = doc.filter(('PrefabInstance',))
    for entry in entries:
        modifications = entry.m_Modification['m_Modifications']
        for modification in modifications:
            # 检测到prefab的guid是特效guid
            prefab_guid = modification['target'].get('guid', '')
            if prefab_guid == '':
                continue

            if prefab_guid in guid_to_effect_path.keys():
                effect_path = guid_to_effect_path[prefab_guid]
                # 绝对路径调整为Effects开始的Resources相对路径
                effect_path = effect_path[effect_path.find('Effects'):]
                effect_ref_dict.add_ref(effect_path, PREFAB_INSTANCE_KEY)
                # print(f"[{file_path}][{PREFAB_INSTANCE_KEY}]: {effect_path}")
                # 不用检测当前prefabInstance的其他改动，都是引用同一个prefab
                break

    result_list = effect_ref_dict.get_ref_list()
    for result in result_list:
        add_row_data(result)


def build_guid_to_effect_info(directory):
    """
    建立特效prefab guid到特效prefab绝对路径的映射
    :param directory: 特效prefab存放目录
    """
    effect_prefab_list = []
    print(f'[{local_time_str()}] 于\'{directory}\'目录建立特效资源索引...')
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file).replace('\\', '/')
            if file_path.endswith(META_FILE_SUFFIX):
                continue
            effect_prefab_list.append(file_path)

    pbar = tqdm(effect_prefab_list)
    for effect_path in pbar:
        meta_doc = UnityDocument.load_yaml(effect_path + META_FILE_SUFFIX)
        guid = meta_doc.entry['guid']
        guid_to_effect_path[guid] = effect_path
    
    print(f'[{local_time_str()}] \'{directory}\'目录特效资源索引建立完毕')


def walk_through_directory(directory, filter):
    """
    递归遍历目录下的每一个prefab文件
    :param directory: 根目录
    :param filter: 筛选文件后缀
    """
    path_list = []
    print(f'[{local_time_str()}] 对\'{directory}\'目录深度搜索解析...')
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file).replace('\\', '/')
            if not file_path.endswith(filter):
                continue
            path_list.append(file_path)
    
    pbar = tqdm(path_list)
    for path in pbar:
        try:
            pbar.set_description_str(f'正在处理\'{path}\'')
            load_and_filter_yaml(path)
        except Exception:
            print(f'[{path}] 解析YAML时发生错误')
            print(traceback.format_exc())
    
    print(f'[{local_time_str()}] \'{directory}\'目录深度解析完毕')


def save_result():
    """
    [废弃] 将搜索结果写入到`OUTPUT_FILE_PATH`
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


def main(sys_env_json_path):
    print(f'[{local_time_str()}] 开始特效引用搜索...')

    try:
        fp = open(sys_env_json_path, 'r')
        sys_env = json.load(fp)
        fp.close()
    except Exception:
        print(f'[{local_time_str()}] 读取\'{sys_env_json_path}\'配置文件失败，退出')
        print(traceback.format_exc())
        exit()

    if MOON_RES_PATH not in sys_env.keys():
        print(f'[{local_time_str()}] 未找到artres库路径，退出')
        exit()

    artres_path = sys_env[MOON_RES_PATH]
    build_guid_to_effect_info(artres_path + EFFECT_PREFAB_RELATIVE_PATH)
    create_table_header() # 创建写入文件
    walk_through_directory(artres_path + UI_PREFAB_RELATIVE_PATH, PREFAB_FILE_SUFFIX)
    walk_through_directory(artres_path + SCENE_RESOURCE_RELATIVE_PATH, SCENE_FILE_SUFFIX)
    
    output_file.close()
    print(f'[{local_time_str()}] 特效引用搜索结果输出到文件\'{output_file_path}\'')


if __name__ == '__main__':
    # TODO 文件名加入当前分支+提交id
    # TODO 提取timeline.playable中的特效引用
    if len(sys.argv) < 2:
        print(f'[{local_time_str()}] 请指定sys_env.json绝对路径: python search.py <path>')
        exit()

    main(sys.argv[1])
