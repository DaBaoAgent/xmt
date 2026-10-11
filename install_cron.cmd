@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在创建每天 05:00 的定时任务...
schtasks /Create /TN "xmt_dashboard_daily_5am" /TR "%~dp0run.cmd" /SC DAILY /ST 05:00 /F
if %errorlevel%==0 (
  echo [OK] 已安装：xmt_dashboard_daily_5am 每天 05:00 运行 run.cmd
) else (
  echo [FAIL] 安装失败，请用管理员身份重试
)
echo.
echo 当前任务状态：
schtasks /Query /TN "xmt_dashboard_daily_5am"
echo.
echo 手动测试一次： schtasks /Run /TN "xmt_dashboard_daily_5am"
echo 删除任务：     schtasks /Delete /TN "xmt_dashboard_daily_5am" /F
pause
