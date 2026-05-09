"""
JONSWAP 波浪荷载计算 --- 为 ANSYS 瞬态分析提供波浪压力时程
适用于 OC3 Tripod 三脚架导管架基础

输出文件:
  1. ansys_forces_case2.csv — 规则波（工况二）各结点力时程
  2. ansys_forces_case3.csv — JONSWAP不规则波（工况三）各结点力时程
  3. submerged_nodes.txt — 浸没结点坐标汇总
  4. ansys_import_commands.txt — APDL 导入命令流
  5. ansys_force_nodeCaseX_XXX.txt — 每个结点独立力时程文件
"""

import numpy as np
import pandas as pd

# ============================================================
# 一、波浪参数
# ============================================================
rho = 1025.0        # 海水密度 (kg/m3)
g = 9.81            # 重力加速度 (m/s2)
water_depth = 45.0  # 水深 (m)

# Morison 系数
Cd = 1.2            # 拖曳力系数
Cm = 2.0            # 惯性力系数

# 仿真参数
T_max = 600.0       # 仿真时长 (s)
dt = 0.1            # 时间步长
nsteps = int(T_max / dt) + 1
time = np.linspace(0, T_max, nsteps)

# --- 工况二：规则波 ---
H_reg = 8.0
T_reg = 10.0
omega_reg = 2 * np.pi / T_reg

def wave_number(omega, d):
    k0 = omega**2 / g
    for _ in range(20):
        k0 = omega**2 / (g * np.tanh(k0 * d))
    return k0

k_reg = wave_number(omega_reg, water_depth)

# --- 工况三：JONSWAP 不规则波 ---
Hs = 8.0
Tp = 10.0
fp = 1.0 / Tp
gamma = 3.3

n_freq = 200
freqs = np.linspace(0.02, 0.5, n_freq)
df = freqs[1] - freqs[0]
omega_f = 2 * np.pi * freqs

sigma = np.where(freqs <= fp, 0.07, 0.09)
alpha_j = 5.0 * (Hs/2)**2 * fp**4 / (16.0 * 0.0624)
S_j = (alpha_j * g**2 / (2*np.pi)**4 / freqs**5 *
       np.exp(-1.25 * (fp/freqs)**4) *
       gamma**np.exp(-(freqs-fp)**2 / (2 * sigma**2 * fp**2)))
S_j[freqs <= 0] = 0

rng = np.random.RandomState(123456789)
phase = rng.uniform(0, 2*np.pi, n_freq)
amplitude = np.sqrt(2 * S_j * df)
k_n = np.array([wave_number(om, water_depth) for om in omega_f])


# ============================================================
# 二、读取 SubDyn 模型
# ============================================================
with open('NRELOffshrBsline5MW_OC3Tripod_SubDyn.dat', 'r',
          encoding='utf-8', errors='ignore') as f:
    model_lines = f.readlines()

# 解析 Joint 坐标
joint_start = None
for i, line in enumerate(model_lines):
    if line.strip().startswith('JointID') and 'JointXss' in line:
        joint_start = i + 2
        break

joints = {}
for i in range(joint_start, len(model_lines)):
    line = model_lines[i].strip()
    if not line or '------' in line:
        break
    parts = line.split()
    if len(parts) >= 8:
        joints[int(parts[0])] = (float(parts[1]), float(parts[2]), float(parts[3]))

# 解析 Member
mem_start = None
for i, line in enumerate(model_lines):
    if line.strip().startswith('MemberID') and 'MJointID1' in line:
        mem_start = i + 2
        break

members = []
for i in range(mem_start, len(model_lines)):
    line = model_lines[i].strip()
    if not line or '------' in line:
        break
    parts = line.split()
    if len(parts) >= 6:
        members.append((int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])))

# 解析截面属性
prop_start = None
for i, line in enumerate(model_lines):
    if 'XsecD' in line and 'XsecT' in line:
        prop_start = i + 2
        break

props = {}
for i in range(prop_start, len(model_lines)):
    line = model_lines[i].strip()
    if not line or '------' in line:
        break
    parts = line.split()
    if len(parts) >= 6:
        props[int(parts[0])] = (float(parts[4]), float(parts[5]))


# ============================================================
# 三、确定浸没结点
# ============================================================
submerged_joints = []

for jid, (x, y, z) in joints.items():
    if z >= 0:
        continue

    total_len = 0.0
    total_area = 0.0
    total_vol = 0.0

    for mid, j1, j2, p1 in members:
        if j1 == jid or j2 == jid:
            other = j2 if j1 == jid else j1
            if other in joints:
                ox, oy, oz = joints[other]
                L = np.sqrt((ox-x)**2 + (oy-y)**2 + (oz-z)**2)
                if p1 in props:
                    od, thick = props[p1]
                    total_len += L
                    total_area += od * L
                    total_vol += (np.pi * od**2 / 4) * L

    if total_len > 0:
        submerged_joints.append({
            'jid': jid, 'x': x, 'y': y, 'z': z,
            'total_len': total_len,
            'proj_area': total_area,
            'disp_vol': total_vol,
            'diam_avg': total_area / total_len
        })

submerged_joints.sort(key=lambda j: j['jid'])
print('浸没结点数: %d' % len(submerged_joints))


# ============================================================
# 四、波浪运动学
# ============================================================
def kinematics_regular(x, z, t):
    eta = 0.5 * H_reg * np.cos(k_reg * x - omega_reg * t)
    u = (0.5 * H_reg * omega_reg *
         np.cosh(k_reg * (z + water_depth)) / np.sinh(k_reg * water_depth) *
         np.cos(k_reg * x - omega_reg * t))
    w = (0.5 * H_reg * omega_reg *
         np.sinh(k_reg * (z + water_depth)) / np.sinh(k_reg * water_depth) *
         np.sin(k_reg * x - omega_reg * t))
    du = (0.5 * H_reg * omega_reg**2 *
          np.cosh(k_reg * (z + water_depth)) / np.sinh(k_reg * water_depth) *
          np.sin(k_reg * x - omega_reg * t))
    dw = (-0.5 * H_reg * omega_reg**2 *
          np.sinh(k_reg * (z + water_depth)) / np.sinh(k_reg * water_depth) *
          np.cos(k_reg * x - omega_reg * t))
    return u, w, du, dw, eta

def kinematics_jonswap(x, z, t):
    u = w = du = dw = eta = 0.0
    for n in range(n_freq):
        om = omega_f[n]
        k = k_n[n]
        amp = amplitude[n]
        phi = phase[n]
        theta = k * x - om * t + phi
        ch = np.cosh(k * (z + water_depth)) / np.sinh(k * water_depth)
        sh = np.sinh(k * (z + water_depth)) / np.sinh(k * water_depth)
        eta += amp * np.cos(theta)
        u += amp * om * ch * np.cos(theta)
        w += amp * om * sh * np.sin(theta)
        du += amp * om**2 * ch * np.sin(theta)
        dw += -amp * om**2 * sh * np.cos(theta)
    return u, w, du, dw, eta


# ============================================================
# 五、计算并导出
# ============================================================
def morison_force(u, du, area, vol):
    Fd = 0.5 * rho * Cd * area * np.abs(u) * u
    Fi = rho * Cm * vol * du
    return Fd + Fi, Fd, Fi

# 对每个工况计算
for case_name, wave_label, kin_func in [
    ('Case2', '规则波', kinematics_regular),
    ('Case3', 'JONSWAP不规则波', kinematics_jonswap)
]:
    print('\n正在计算 %s ...' % wave_label)
    all_rows = []
    wave_series = []

    for it in range(nsteps):
        if it % 1000 == 0:
            print('  时间步 %d / %d' % (it, nsteps))
        t = time[it]

        _, _, _, _, eta = kin_func(0.0, 0.0, t)
        wave_series.append([t, eta])

        for sj in submerged_joints:
            x, y, z = sj['x'], sj['y'], sj['z']
            u, w, du, dw, _ = kin_func(x, z, t)
            fx, fd, fi = morison_force(u, du, sj['proj_area'], sj['disp_vol'])
            fy = 0.0
            fz = rho * Cm * sj['disp_vol'] * dw
            all_rows.append([t, sj['jid'], sj['x'], sj['y'], sj['z'],
                           fx, fy, fz, fd, fi])

    # 波面时程
    wf = 'wave_elevation_%s.txt' % case_name
    pd.DataFrame(wave_series, columns=['Time(s)', 'Elevation(m)']).to_csv(
        wf, sep='\t', index=False, float_format='%.4f')
    print('  波面: %s' % wf)

    # 总力文件
    cols = ['Time(s)', 'NodeID', 'X(m)', 'Y(m)', 'Z(m)',
            'Fx(N)', 'Fy(N)', 'Fz(N)', 'Fd(N)', 'Fi(N)']
    ff = 'ansys_forces_%s.csv' % case_name
    pd.DataFrame(all_rows, columns=cols).to_csv(
        ff, sep=',', index=False, float_format='%.2f')
    print('  总力文件: %s (%d 行)' % (ff, len(all_rows)))

    # 每个结点独立文件
    all_jids = set(r[1] for r in all_rows)
    for jid in all_jids:
        node_rows = [r for r in all_rows if r[1] == jid]
        nf = 'ansys_force_node%s_%03d.txt' % (case_name, jid)
        pd.DataFrame(node_rows,
            columns=['Time(s)', 'NodeID', 'X(m)', 'Y(m)', 'Z(m)',
                    'Fx(N)', 'Fy(N)', 'Fz(N)', 'Fd(N)', 'Fi(N)']).to_csv(
            nf, sep='\t', index=False,
            columns=['Time(s)', 'Fx(N)', 'Fy(N)', 'Fz(N)'],
            float_format='%.2f')
    print('  结点文件: %d 个' % len(all_jids))

# 导出浸没结点汇总
with open('submerged_nodes.txt', 'w', encoding='utf-8') as f:
    f.write('OC3 Tripod submerged nodes summary\n')
    f.write('=' * 90 + '\n')
    f.write('Wave direction: +X (0 deg)\n')
    f.write('Water depth: %.1f m\n' % water_depth)
    f.write('Total submerged nodes: %d\n' % len(submerged_joints))
    f.write('=' * 90 + '\n')
    line = '%8s %10s %10s %10s %10s %12s %12s\n' % (
        'NodeID', 'X(m)', 'Y(m)', 'Z(m)', 'D_avg(m)', 'Area(m2)', 'Vol(m3)')
    f.write(line)
    f.write('-' * 90 + '\n')
    for sj in submerged_joints:
        f.write('%8d %10.3f %10.3f %10.3f %10.3f %12.2f %12.2f\n' % (
            sj['jid'], sj['x'], sj['y'], sj['z'],
            sj['diam_avg'], sj['proj_area'], sj['disp_vol']))

print('\n浸没结点汇总: submerged_nodes.txt')

# 导出 APDL 导入命令
with open('ansys_import_commands.txt', 'w', encoding='utf-8') as f:
    f.write('! ANSYS APDL Commands - Import wave loads\n')
    f.write('! Usage: /INPUT in ANSYS Mechanical APDL\n\n')
    f.write('! =========================================\n')
    f.write('! METHOD 1: Use individual node files\n')
    f.write('! =========================================\n')
    f.write('\n')

    # 显示前5个结点示例
    for sj in submerged_joints[:5]:
        jid = sj['jid']
        f.write('! Node %d at (%.2f, %.2f, %.2f)\n' % (
            jid, sj['x'], sj['y'], sj['z']))
        f.write('*dim,fx_%03d,array,%d\n' % (jid, nsteps))
        f.write('*dim,fy_%03d,array,%d\n' % (jid, nsteps))
        f.write('*dim,fz_%03d,array,%d\n' % (jid, nsteps))
        f.write('*vread,fx_%03d(1),ansys_force_nodeCase3_%03d.txt,,,1,%d,,,1\n' % (
            jid, jid, nsteps))
        f.write('(f12.2)\n')
        f.write('*vread,fy_%03d(1),ansys_force_nodeCase3_%03d.txt,,,1,%d,,,2\n' % (
            jid, jid, nsteps))
        f.write('(f12.2)\n')
        f.write('*vread,fz_%03d(1),ansys_force_nodeCase3_%03d.txt,,,1,%d,,,3\n' % (
            jid, jid, nsteps))
        f.write('(f12.2)\n\n')

    f.write('! =========================================\n')
    f.write('! METHOD 2: For Workbench users (easier)\n')
    f.write('! =========================================\n')
    f.write('! 1. From submerged_nodes.txt, pick target coordinates\n')
    f.write('! 2. In Workbench: create Remote Points matching coords\n')
    f.write('! 3. Insert Force -> Tabular -> Import node force file\n')
    f.write('! 4. Repeat for each submerged node\n')
    f.write('! =========================================\n')

print('APDL commands: ansys_import_commands.txt')
print('\nAll done!')
