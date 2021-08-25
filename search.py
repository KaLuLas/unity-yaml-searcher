from unityparser import UnityDocument
import json
import os

SYS_ENV_JSON_PATH = 'C:/ROGameFeature/sys_env.json'

EFFECT_RESOURCE_PREFIX = 'fx'
PREFAB_FILE_SUFFIX = '.prefab'
MOON_RES_PATH = 'MoonResPath'
UI_PREFAB_RELATIVE_PATH = '/Resources/UI/Prefabs/'

def load_and_filter_yaml(file_path):
    """
    解析YAML文件，打印出特效节点信息
    :param file_path: yaml文件绝对路径
    """
    doc = UnityDocument.load_yaml(file_path=file_path)
    # 特效助手配置路径
    entries = doc.filter(('MonoBehaviour',), ('EffectPath',))
    for entry in entries:
        print(f"[{file_path}][EFFECT HELPER]: {entry.EffectPath}")

    # 特效prefab直接放在UIprefab中
    entries = doc.filter(('PrefabInstance',))
    for entry in entries:
        modifications = entry.m_Modification['m_Modifications']
        for modification in modifications:
            if modification['propertyPath'] == 'm_Name':
                name = modification['value']
                if str(name)[:2].lower() == EFFECT_RESOURCE_PREFIX:
                    print(f"[{file_path}][PREFAB INSTANCE]: {name}")


def walk_through_directory(directory):
    """
    递归遍历目录下的每一个prefab文件
    :param directory: 根目录
    """
    prefab_path_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file).replace('\\', '/')
            if not file_path.endswith(PREFAB_FILE_SUFFIX):
                continue
            prefab_path_list.append(file_path)
    
    for prefab_path in prefab_path_list:
        try:
            load_and_filter_yaml(prefab_path)
        except Exception as e:
            print(f'[{prefab_path}] 解析YAML时发生错误')
            print(e)


def main():
    fp = open(SYS_ENV_JSON_PATH, 'r')
    sys_env = json.load(fp)
    if MOON_RES_PATH in sys_env.keys():
        artres_path = sys_env[MOON_RES_PATH]
        walk_through_directory(artres_path + UI_PREFAB_RELATIVE_PATH)


if __name__ == '__main__':
    # TODO 进度条
    # TODO 脚本参数传入
    # TODO 结果写入文件
    main()
