import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# ── 中文字体设置 ──
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DengXian']
plt.rcParams['axes.unicode_minus'] = False

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── 读取 OpenFAST 输出文件 ──
outfile = '5MW_OC3Trpd_DLL_WSt_WavesReg.out'
with open(outfile) as f:
    for _ in range(6):
        f.readline()
    names = f.readline().strip().split('\t')

df = pd.read_csv(outfile, sep='\t', skiprows=8, header=None, names=names)
for c in df.columns:
    df[c] = pd.to_numeric(df[c], errors='coerce')

t = df['Time'].values
dt_out = 0.04
fs = 1 / dt_out

# ── 三个监测结点 ──
nodes = {
    '上部顶端':   {'dx': 'M3N1TDxss', 'dy': 'M3N1TDyss', 'z': 'Z=10m'},
    '斜撑交汇':   {'dx': 'M2N1TDxss', 'dy': 'M2N1TDyss', 'z': 'Z=-10m'},
    '下部腿柱':   {'dx': 'M4N1TDxss', 'dy': 'M4N1TDyss', 'z': 'Z=-34.71m'},
}
colors = {'上部顶端': 'red', '斜撑交汇': 'green', '下部腿柱': 'purple'}

# ── 低通滤波器（用于加速度计算）──
def butter_lowpass(data, cutoff=5, fs=25, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return signal.filtfilt(b, a, data)

def compute_acceleration(dx, dt=0.04):
    dx_filt = butter_lowpass(dx, cutoff=5, fs=fs)
    vx = np.gradient(dx_filt, dt)
    ax = np.gradient(vx, dt)
    return ax

# ── 图1: 三结点X方向位移对比 ──
fig, ax = plt.subplots(figsize=(14, 5))
for name, ch in nodes.items():
    ax.plot(t, df[ch['dx']], color=colors[name], linewidth=0.3, label=f'{name} {ch["z"]}')
ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
ax.set_xlabel('时间 (s)')
ax.set_ylabel('X方向位移 (m)')
ax.set_title('工况三：三结点X方向位移对比（JONSWAP不规则波 Hs=8m, Tp=10s）')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('工况三_结点位移对比.png', dpi=150)
print('Saved: 工况三_结点位移对比.png')

# ── 每个结点单独作图 ──
for name, ch in nodes.items():
    dx = df[ch['dx']].values
    acc = compute_acceleration(dx)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

    ax1.plot(t, dx, 'b-', linewidth=0.3)
    ax1.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
    ax1.set_ylabel('X方向位移 (m)')
    ax1.set_title(f'工况三：{name} {ch["z"]} — X方向位移与加速度')
    ax1.grid(True, alpha=0.3)

    ax2.plot(t, acc, 'r-', linewidth=0.3)
    ax2.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
    ax2.set_xlabel('时间 (s)')
    ax2.set_ylabel('加速度 (m/s²)')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    fname = f'工况三_{name}_位移加速度.png'
    plt.savefig(fname, dpi=150)
    print(f'Saved: {fname}')

# ── 统计信息 ──
print('\n===== 工况三 结果汇总 =====')
for name, ch in nodes.items():
    dx = df[ch['dx']].values
    dy = df[ch['dy']].values
    acc = compute_acceleration(dx)
    dx_pp = dx.max() - dx.min()
    dx_std = dx.std()
    amax = np.abs(acc).max()
    print(f'{name:10s} {ch["z"]:12s}  X位移峰峰值: {dx_pp:.4f} m  X位移标准差: {dx_std:.4f} m  X加速度最大值: {amax:.4f} m/s²')

# ── 波浪验证 ──
wave = df['Wave1Elev'].values
hs = 4 * wave.std()
f_w, Pxx_w = signal.periodogram(wave, fs=fs, window='hann', scaling='density')
peak_idx = np.argmax(Pxx_w[f_w < 0.5])
fp = f_w[f_w < 0.5][peak_idx]
tp = 1 / fp
print(f'\n波浪验证: Hs = {hs:.2f} m (目标 8m), 谱峰周期 Tp = {tp:.1f} s (目标 10s)')

# ── 图: 波面时程 + 频谱 ──
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6))
seg = (t >= 100) & (t <= 200)
ax1.plot(t[seg], wave[seg], 'b-', linewidth=0.5)
ax1.set_ylabel('波面高度 (m)')
ax1.set_title('工况三：JONSWAP不规则波面时程 (100-200s)')
ax1.grid(True, alpha=0.3)

ax2.semilogy(f_w[f_w < 0.5], Pxx_w[f_w < 0.5], 'b-')
ax2.axvline(1/10, color='r', linestyle='--', alpha=0.5, label='f=0.1Hz (T=10s)')
ax2.set_xlabel('频率 (Hz)')
ax2.set_ylabel('PSD (m²/Hz)')
ax2.set_title('工况三：JONSWAP波浪频谱')
ax2.legend()
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('工况三_波面时程频谱.png', dpi=150)
print('Saved: 工况三_波面时程频谱.png')

print('\n所有图片生成完成！')
