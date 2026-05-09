%% ANSYS_ExportWindFx.m
% 将风荷载数据导出为 ANSYS 可导入的格式
% 读取 wind_force_data_11.3mps_kaimal_0dot2.txt
% 提取 Fx 列(第36列)，乘以1000转换为N，导出为 ANSYS 表格导入格式
%
% 输出文件:
%   WindLoad_Fx_ANSYS.txt    — 空格分隔（远程力用）
%   WindLoad_Fx_ANSYS.csv    — 逗号分隔，带表头（推荐）
%   WindLoad_Fx_ANSYS_tab.txt — Tab分隔（可复制粘贴）

clear; clc; close all;

%% 1. 读取原始风数据
fprintf('正在读取风数据...\n');
data = load('wind_force_data_11.3mps_kaimal_0dot2.txt');
fprintf('原始数据: %d 行, %d 列\n', size(data,1), size(data,2));

%% 2. 只取前 600 秒
mask = data(:,1) <= 600;
t = data(mask, 1);       % 时间 (s)
Fx_raw = data(mask, 36); % 第36列 = Fx

% MATLAB 原代码乘以 1e3 转换为 N
Fx = Fx_raw * 1000;

fprintf('600秒数据: %d 行\n', length(t));
fprintf('时间步长: %.4f s\n', t(2)-t(1));
fprintf('Fx 范围: %.2f ~ %.2f N\n', min(Fx), max(Fx));
fprintf('Fx 均值: %.2f N\n', mean(Fx));

%% 3. 验证：画图检查
figure('Position', [100 100 1200 400]);
plot(t, Fx, 'b-', 'LineWidth', 0.3);
grid on; xlabel('Time (s)'); ylabel('Fx (N)');
title('Wind Load Fx (前600秒)');
xlim([0 600]);

%% 4. 导出 ANSYS 可读格式

% 4.1 空格分隔（无表头）— 用于远程力 -> X分量 -> 表格导入
fid = fopen('WindLoad_Fx_ANSYS.txt', 'w');
for i = 1:length(t)
    fprintf(fid, '%.4f %.2f\n', t(i), Fx(i));
end
fclose(fid);
fprintf('\n已生成: WindLoad_Fx_ANSYS.txt (空格分隔, %d 行)\n', length(t));

% 4.2 逗号分隔 CSV（带表头）— 推荐用于 力 -> 大小 -> 表格导入
fid = fopen('WindLoad_Fx_ANSYS.csv', 'w');
fprintf(fid, 'Time,Fx_N\n');
for i = 1:length(t)
    fprintf(fid, '%.4f,%.2f\n', t(i), Fx(i));
end
fclose(fid);
fprintf('已生成: WindLoad_Fx_ANSYS.csv (逗号分隔, 带表头)\n');

% 4.3 Tab 分隔（无表头）— 可复制粘贴到 ANSYS 表格
fid = fopen('WindLoad_Fx_ANSYS_tab.txt', 'w');
for i = 1:length(t)
    fprintf(fid, '%.4f\t%.2f\n', t(i), Fx(i));
end
fclose(fid);
fprintf('已生成: WindLoad_Fx_ANSYS_tab.txt (Tab分隔, 可复制粘贴)\n');

%% 5. 显示前 5 行预览
fprintf('\n前 5 行数据预览:\n');
fprintf('  Time(s)    Fx(N)\n');
for i = 1:5
    fprintf('  %.4f  %.2f\n', t(i), Fx(i));
end

fprintf('\n✅ 全部完成! 请用 ANSYS 导入 WindLoad_Fx_ANSYS.csv\n');
fprintf('    操作方法: 力荷载 → 大小 → 表格(导入)\n');
