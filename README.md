# unity-yaml-searcher
使用unity-yaml-parser进行项目资源检索

### 运行环境

括号内为开发环境

- python3(3.8.5)
- tpdm(4.51.0)
- unityparser(2.0.0)

### 使用说明

导出结果为csv格式文件，其中：

1. ResourceName：引用特效的资源名
2. ResourcePath：引用特效资源的绝对路径
3. Type：应用类型
   1. effect helper：特效助手引用
   2. prefab instance：直接放置特效prefab
4. EffectName：特效名称
5. EffectPath：特效相对Resources文件夹目录