@echo off
chcp 65001 >nul
cd /d "C:\Users\danny\Desktop\Claude Code\Daily News Agent"

if exist output\* del /q output\*

call "C:\Users\danny\AppData\Roaming\npm\claude.cmd" -p --dangerously-skip-permissions "CLAUDE.md의 일일 워크플로우를 Step 1부터 Step 11까지 순서대로 전부 실행해줘. 모든 단계를 자동으로 진행하고 중간에 멈추지 마. 오류 발생 시 텔레그램으로 알림 보내고 다음 단계로 진행해."
