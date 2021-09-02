# unity-yaml-searcher
使用unity-yaml-parser进行项目资源检索

### 运行环境

括号内为开发环境

- python3(3.8.5)
- tpdm(4.51.0)
- unityparser(2.0.0)
- gitpython(3.1.18)

### 耗时情况

1. UIPrefab中的特效引用梳理：11min15sec
2. Cutscene / Timeline中的特效引用梳理：3min43sec
3. 场景文件中的特效引用梳理：1hour13min19sec



### 使用说明

#### 执行脚本

python search.py <sys_env.json绝对路径>

例：python search.py C:/ROGameFeature/sys_env.json

#### 导出结果

导出结果为csv格式文件，命名格式"\<time\>-\<branch\>-\<commit_id\>.csv"其中：

1. ResourceName：引用特效的资源名
2. ResourcePath：引用特效资源的绝对路径
3. Type：应用类型
   1. effect_helper：特效助手引用
   2. prefab_instance：直接放置特效prefab
   3. timeline：CutScene中以ID形式配置的特效
4. EffectName：特效名称
5. EffectPath：特效相对Resources文件夹目录
6. RefCount：引用计数