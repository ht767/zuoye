"""Generate corrected HTML report for Condition 3 with embedded images."""
import base64

images = {
    'comparison': '工况三_结点位移对比.png',
    'top': '工况三_上部顶端_位移加速度.png',
    'brace': '工况三_斜撑交汇_位移加速度.png',
    'leg': '工况三_下部腿柱_位移加速度.png',
    'wave': '工况三_波面时程频谱.png',
}

b64 = {}
for key, fname in images.items():
    with open(fname, 'rb') as f:
        b64[key] = base64.b64encode(f.read()).decode()

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>海上风电三脚架支撑结构全耦合动力响应分析报告 - 工况三</title>
<style>
body {{ font-family: "Microsoft YaHei", SimHei, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #fff; color: #333; line-height: 1.7; }}
h1, h2, h3 {{ color: #1a5276; }}
h1 {{ border-bottom: 3px solid #2980b9; padding-bottom: 10px; }}
h2 {{ border-bottom: 2px solid #85c1e9; padding-bottom: 5px; margin-top: 40px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
th {{ background: #2980b9; color: white; }}
tr:nth-child(even) {{ background: #f8f9fa; }}
img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px; }}
.note {{ background: #eaf2f8; padding: 15px; border-left: 4px solid #2980b9; margin: 15px 0; border-radius: 3px; }}
</style>
</head>
<body>

<h1>海上风电三脚架支撑结构全耦合动力响应分析报告</h1>
<h2>工况三：风荷载 + JONSWAP 不规则波（Hs=8m, Tp=10s）</h2>

<div class="note">
<strong>概述：</strong>本报告基于 NREL 5MW 海上风力发电机和 OC3 Tripod 三脚架导管架基础，使用 OpenFAST v3.4.1 进行全耦合仿真分析。风荷载来自 MyWindLoads.txt（通过 StC 模块施加），波浪为 JONSWAP 不规则波（WaveMod=2, Hs=8m, Tp=10s），方向沿 X 轴。仿真时长 600 秒。加速度通过对位移时程低通滤波（fc=5Hz）后两次数值微分计算。
</div>

<h2>一、仿真配置</h2>
<table>
<tr><th>参数</th><th>值</th></tr>
<tr><td>波浪模型</td><td>JONSWAP 不规则波（WaveMod=2）</td></tr>
<tr><td>有效波高 WaveHs</td><td>8 m</td></tr>
<tr><td>谱峰周期 WaveTp</td><td>10 s</td></tr>
<tr><td>谱峰参数 WavePkShp</td><td>DEFAULT（γ=3.3）</td></tr>
<tr><td>传播方向 WaveDir</td><td>0°（+X 方向）</td></tr>
<tr><td>TMax / DT / DT_Out</td><td>600 s / 0.008 s / 0.04 s</td></tr>
</table>

<h2>二、监测结点</h2>
<table>
<tr><th>结点</th><th>坐标</th><th>输出通道</th></tr>
<tr><td><strong>上部顶端</strong></td><td>(0, 0, 10m)</td><td>M3N1TDxss / M3N1TDyss</td></tr>
<tr><td><strong>斜撑交汇</strong></td><td>(0, 0, -10m)</td><td>M2N1TDxss / M2N1TDyss</td></tr>
<tr><td><strong>下部腿柱</strong></td><td>(0, 0, -34.71m)</td><td>M4N1TDxss / M4N1TDyss</td></tr>
</table>

<h2>三、仿真结果</h2>

<h3>3.1 三结点X方向位移对比</h3>
<img src="data:image/png;base64,{b64['comparison']}" alt="三结点位移对比">

<h3>3.2 上部顶端（Z=10m）</h3>
<img src="data:image/png;base64,{b64['top']}" alt="上部顶端">
<ul>
<li>X方向位移峰峰值：<strong>0.0173 m</strong>（17.3 mm）</li>
<li>X方向加速度最大值：<strong>0.915 m/s²</strong></li>
</ul>

<h3>3.3 斜撑交汇（Z=-10m）</h3>
<img src="data:image/png;base64,{b64['brace']}" alt="斜撑交汇">
<ul>
<li>X方向位移峰峰值：<strong>0.0161 m</strong>（16.1 mm）</li>
<li>X方向加速度最大值：<strong>0.647 m/s²</strong></li>
</ul>

<h3>3.4 下部腿柱（Z=-34.71m）</h3>
<img src="data:image/png;base64,{b64['leg']}" alt="下部腿柱">
<ul>
<li>X方向位移峰峰值：<strong>0.0027 m</strong>（2.7 mm）</li>
<li>X方向加速度最大值：<strong>0.145 m/s²</strong></li>
</ul>

<h3>3.5 波面时程与频谱</h3>
<img src="data:image/png;base64,{b64['wave']}" alt="波面时程频谱">

<h3>3.6 结果汇总</h3>
<table>
<tr><th>结点</th><th>X位移峰峰值</th><th>X位移标准差</th><th>X加速度最大值</th></tr>
<tr><td>上部顶端（Z=10m）</td><td>0.0173 m</td><td>0.0021 m</td><td>0.915 m/s²</td></tr>
<tr><td>斜撑交汇（Z=-10m）</td><td>0.0161 m</td><td>0.0022 m</td><td>0.647 m/s²</td></tr>
<tr><td>下部腿柱（Z=-34.71m）</td><td>0.0027 m</td><td>0.0004 m</td><td>0.145 m/s²</td></tr>
</table>

</body>
</html>'''

with open('仿真报告_工况三.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Saved: 仿真报告_工况三.html')
