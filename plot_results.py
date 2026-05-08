import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ── 读取 OpenFAST 输出文件 ──
with open('5MW_OC3Trpd_DLL_WSt_WavesReg.out') as f:
    for _ in range(6):
        f.readline()
    names = f.readline().strip().split('\t')

df = pd.read_csv('5MW_OC3Trpd_DLL_WSt_WavesReg.out', sep='\t',
                 skiprows=8, header=None, names=names)
for c in df.columns:
    df[c] = pd.to_numeric(df[c], errors='coerce')

t = df['Time'].values

# ── 图1: 塔顶位移（对应报告中的节点位移图）──
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(t, df['TwHt1TPxi'], 'b-', linewidth=0.3, label='Fore-aft')
ax.plot(t, df['TwHt1TPyi'], 'r-', linewidth=0.3, label='Side-side')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Displacement (m)')
ax.set_title('Tower Top Displacement (600s)')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plot01_displacement.png', dpi=150)
print('Saved: plot01_displacement.png')

# ── 图2: 波浪与塔底弯矩对比（波-结构耦合效应）──
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
seg = (t >= 100) & (t <= 200)
ax1.plot(t[seg], df['Wave1Elev'][seg], 'b-', linewidth=0.5)
ax1.set_ylabel('Wave Elevation (m)')
ax1.set_title('Wave - Structure Coupling (100-200s)')
ax1.grid(True, alpha=0.3)
ax2.plot(t[seg], df['YawBrMyp'][seg] / 1000, 'b-', linewidth=0.5)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Tower Base Moment My (kN-m)')
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plot02_wave_structure_coupling.png', dpi=150)
print('Saved: plot02_wave_structure_coupling.png')

# ── 图3: 波面频谱（验证 JONSWAP 谱形）──
fs = 1 / 0.04  # DT_Out = 0.04s → 25 Hz
from scipy import signal
f, Pxx = signal.periodogram(df['Wave1Elev'].values, fs=fs, window='hann', scaling='density')
fig, ax = plt.subplots(figsize=(14, 4))
ax.semilogy(f[f < 1.5], Pxx[f < 1.5], 'b-')
ax.axvline(1 / 10, color='r', linestyle='--', alpha=0.5, label='Tp=10s (f=0.1Hz)')
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('PSD (m²/Hz)')
ax.set_title('Wave Spectrum - JONSWAP (Hs=8m, Tp=10s)')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plot03_spectrum.png', dpi=150)
print('Saved: plot03_spectrum.png')

# ── 图4: 发电机功率 ──
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(t, df['GenPwr'], 'g-', linewidth=0.3)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Power (kW)')
ax.set_title('Generator Power Output (600s)')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plot04_power.png', dpi=150)
print('Saved: plot04_power.png')

# ── 图5: 总水动力 ──
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(t, df['HydroFxi'] / 1e6, 'b-', linewidth=0.3, label='Fxi')
ax.plot(t, df['HydroFzi'] / 1e6, 'r-', linewidth=0.3, label='Fzi')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Force (MN)')
ax.set_title('Total Hydrodynamic Forces (600s)')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plot05_hydro_forces.png', dpi=150)
print('Saved: plot05_hydro_forces.png')

print('\nAll plots generated successfully!')
