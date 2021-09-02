from io import TextIOWrapper
from unityparser import UnityDocument
from effect_ref import EffectRefDict
from yaml_effect_searcher import *
from utils import local_time_str
from config import *
from tqdm import tqdm
from git import Repo
import json
import os
import csv
import sys
import traceback

# 写入CSV文件
output_file_path = 'result.csv'
# 文件句柄
output_file:TextIOWrapper = None
# csv写者
output_csv_writer = None
helper_searcher:HelperEffectYamlSearcher = None
prefab_searcher:PrefabEffectYamlSearcher = None
timeline_searcher:TimelineEffectYamlSearcher = None

# CSV文件表头
headers = ['ResourceName', 'ResourcePath', 'EffectName', 'EffectPath', 'Type', 'RefCount']
# CSV文件内容
rows = []


def get_artres_branch_and_commit(artres_path):
    """
    获取artres库当前分支与提交ID
    :param artres_path: artres库绝对路径
    :return: 当前分支:str, 提交ID8位截断:str
    """
    try:
        artres_repo = Repo.init(artres_path, False)
        return str(artres_repo.active_branch), str(artres_repo.active_branch.commit)[:8]
    except Exception:
        print(f'[{local_time_str()}] \'{artres_path}\'路径下artres库初始化失败，退出')
        print(traceback.format_exc())
        exit()


def create_table_header(filename):
    """
    创建写入文件，并添加表头
    :param file_name: 写入文件名
    """
    global output_file_path
    global output_file
    global output_csv_writer
    output_file_path = filename
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


def load_and_filter_yaml(file_path, searchers:list):
    """
    解析YAML文件，打印出特效节点信息
    :param file_path: yaml文件绝对路径
    :param searchers: YamlEffectSearcher队列
    """
    doc = UnityDocument.load_yaml(file_path=file_path)
    file_name = file_path[file_path.rfind('/')+1:]
    effect_ref_dict = EffectRefDict(file_name, file_path)
    for searcher in searchers:
        searcher.search(doc, effect_ref_dict)

    result_list = effect_ref_dict.get_ref_list()
    for result in result_list:
        add_row_data(result)


def walk_through_directory(directory, filter, searchers:list):
    """
    递归遍历目录下的每一个prefab文件
    :param directory: 根目录
    :param filter: 筛选文件后缀
    :param searchers: YamlEffectSearcher队列
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
            # 显示正在处理的文件
            # pbar.set_description_str(f'正在处理\'{path}\'')
            load_and_filter_yaml(path, searchers)
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
    config_path = sys_env[MOONCLIENT_CONFIG_PATH]
    active_branch, commit_id = get_artres_branch_and_commit(artres_path)
    output_filename = f'{local_time_str("%Y%m%d%H%M%S")}-{active_branch}-{commit_id}.csv'

    helper_searcher = HelperEffectYamlSearcher()
    prefab_searcher = PrefabEffectYamlSearcher().prepare(artres_path + EFFECT_PREFAB_RELATIVE_PATH)
    timeline_searcher = TimelineEffectYamlSearcher().prepare(config_path + EFFECT_TABLE_RELATIVE_PATH)

    create_table_header(output_filename) # 创建写入文件
    # 查询UIPrefab中对特效资源的引用
    walk_through_directory(artres_path + UI_PREFAB_RELATIVE_PATH, PREFAB_FILE_SUFFIX, [helper_searcher, prefab_searcher])
    # 查询Cutscene/Timeline中对特效资源的引用
    walk_through_directory(artres_path + TIMELINE_RESOURCE_RELATIVE_PATH, TIMELINE_FILE_SUFFIX, [timeline_searcher, ])
    # 查询场景资源中对特效资源的引用
    walk_through_directory(artres_path + SCENE_RESOURCE_RELATIVE_PATH, SCENE_FILE_SUFFIX, [prefab_searcher, ])
    
    output_file.close()
    print(f'[{local_time_str()}] 特效引用搜索结果输出到文件\'{output_file_path}\'')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'[{local_time_str()}] 请指定sys_env.json绝对路径: python search.py <path>')
        exit()

    main(sys.argv[1])
