from unityparser import UnityDocument
from effect_ref import EffectRefDict
from tqdm import tqdm
import json
import os
import csv
import time
import traceback

SYS_ENV_JSON_PATH = 'C:/ROGameFeature/sys_env.json'
MOON_RES_PATH = 'MoonResPath'
# 写入CSV文件
output_file_path = 'result.csv'

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


def add_row_data(resource_name, resource_path, type, effect_name, effect_path):
    """
    [弃用]往文件中写入一条记录
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
        rows.append(result)


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
        except Exception as e:
            print(f'[{path}] 解析YAML时发生错误')
            print(traceback.format_exc())
    
    print(f'[{local_time_str()}] \'{directory}\'目录深度解析完毕')


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
        build_guid_to_effect_info(artres_path + EFFECT_PREFAB_RELATIVE_PATH)
        walk_through_directory(artres_path + UI_PREFAB_RELATIVE_PATH, PREFAB_FILE_SUFFIX)
        # walk_through_directory(artres_path + SCENE_RESOURCE_RELATIVE_PATH, SCENE_FILE_SUFFIX)
    
    save_result()


if __name__ == '__main__':
    # TODO 脚本参数传入
    main()
