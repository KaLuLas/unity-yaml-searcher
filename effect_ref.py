class EffectRef:
    """
    特效资源引用类
    """
    def __init__(self, effect_path):
        self.effect_path = effect_path
        self.effect_name = effect_path[effect_path.rfind('/')+1:]
        # 引用形式 -> 引用计数
        self.ref_dict = {}

    def add_ref(self, ref_type:str):
        if ref_type not in self.ref_dict.keys():
            self.ref_dict[ref_type] = 1
            return
        
        self.ref_dict[ref_type] += 1


class EffectRefDict:
    """
    存储对复数特效资源的引用情况
    """
    def __init__(self, file_name, file_path):
        self.file_name = file_name
        self.file_path = file_path
        self.dict = {}

    def add_ref(self, effect_path, ref_type):
        """
        :param effect_path: 特效路径
        :param ref_type: 引用类型
        """
        if effect_path not in self.dict.keys():
            effect_ref = EffectRef(effect_path)
            effect_ref.add_ref(ref_type)
            self.dict[effect_path] = effect_ref
            return

        self.dict[effect_path].add_ref(ref_type)

    def get_ref_list(self,):
        """
        获取引用情况列表
        """
        result = []
        for path, refInfo in self.dict.items():
            for ref_type, count in refInfo.ref_dict.items():
                result.append([self.file_name, self.file_path, refInfo.effect_name, refInfo.effect_path, ref_type, count])

        return result
