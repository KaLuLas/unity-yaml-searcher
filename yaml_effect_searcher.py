from unityparser import UnityDocument
from effect_ref import EffectRefDict
from utils import PREFAB_FILE_SUFFIX, META_FILE_SUFFIX, local_time_str
from tqdm import tqdm
import os

class YamlEffectSearcher:
    """
    从Yaml文件中查找特效资源引用
    """
    def __init__(self, ):
        pass

    def prepare(self, directory:str=''):
        return self

    def search(self, doc:UnityDocument, ref_dict:EffectRefDict):
        print('[YamlEffectSearcher] search')


class HelperYamlEffectSearcher(YamlEffectSearcher):
    """
    在Yaml文件中查找特效助手对特效资源的引用
    """
    KEY = 'effect_helper'

    def search(self, doc:UnityDocument, ref_dict:EffectRefDict):
        # 特效助手配置路径
        entries = doc.filter(('MonoBehaviour',), ('EffectPath',))
        # entry.anchor is fileID
        for entry in entries:
            # 特效助手配置的路径不带文件后缀
            effect_path = entry.EffectPath + PREFAB_FILE_SUFFIX
            ref_dict.add_ref(effect_path, HelperYamlEffectSearcher.KEY)
            # print(f"[{ref_dict.file_path}][{HelperYamlEffectSearcher.KEY}]: {effect_path}")


class PrefabYamlEffectSearcher(YamlEffectSearcher):
    """
    在Yaml文件中查找特效prefab实例对特效资源的引用
    """
    KEY = 'prefab_instance'

    def __init__(self, ):
        # 特效prefab的guid(str)映射到特效prefab绝对路径
        self.guid_to_effect_path = {}

    def prepare(self, directory: str):
        """
        建立特效prefab guid到特效prefab绝对路径的映射
        :param directory: 特效prefab存放目录
        :return: self
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
            self.guid_to_effect_path[guid] = effect_path
    
        print(f'[{local_time_str()}] \'{directory}\'目录特效资源索引建立完毕')
        return self


    def search(self, doc: UnityDocument, ref_dict: EffectRefDict):
        # 特效prefab直接放在UIprefab中
        entries = doc.filter(('PrefabInstance',))
        for entry in entries:
            modifications = entry.m_Modification['m_Modifications']
            for modification in modifications:
                # 检测到prefab的guid是特效guid
                prefab_guid = modification['target'].get('guid', '')
                if prefab_guid == '':
                    continue

                if prefab_guid in self.guid_to_effect_path.keys():
                    effect_path = self.guid_to_effect_path[prefab_guid]
                    # 绝对路径调整为Effects开始的Resources相对路径
                    effect_path = effect_path[effect_path.find('Effects'):]
                    ref_dict.add_ref(effect_path, PrefabYamlEffectSearcher.KEY)
                    # print(f"[{ref_dict.file_path}][{PrefabYamlEffectSearcher.KEY}]: {effect_path}")
                    # 不用检测当前prefabInstance的其他改动，都是引用同一个prefab
                    break
