SHELL := /bin/sh
.DEFAULT_GOAL := help

.PHONY: help binance binance-bar

help:
	@printf '%s\n' \
	  'Coinx 常用命令' \
	  '  make binance      在终端输出币安只读持仓报告' \
	  '  make binance-bar  在 Mac 菜单栏显示币安今日盈亏'

binance:
	@python3 scripts/binance/binance_report.py

binance-bar:
	@nohup uv run scripts/binance/binance_menubar.py < /dev/null > /tmp/binance_menubar.log 2>&1 &
	@echo '菜单栏已在后台启动，日志：/tmp/binance_menubar.log'
