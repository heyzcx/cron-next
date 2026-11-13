# cron-next

算出一个 cron 表达式接下来 N 次的运行时间。零依赖 Python CLI。

## 安装

只需要 Python 3.8+，不用装任何包：

```bash
python3 cron_next.py "30 9 * * 1-5"
```

## 用法

```bash
# 默认显示接下来 5 次（从现在开始算）
python3 cron_next.py "30 9 * * 1-5"

# 指定显示次数
python3 cron_next.py "0 0 1 * *" --count 3

# 从指定时间开始算
python3 cron_next.py "*/15 * * * *" --from "2026-11-13 10:00"
```

输出示例：

```
2026-11-16 09:30 (Monday)
2026-11-17 09:30 (Tuesday)
2026-11-18 09:30 (Wednesday)
2026-11-19 09:30 (Thursday)
2026-11-20 09:30 (Friday)
```

支持标准 5 字段格式（分 时 日 月 周），包括列表、范围、步长和英文月份/星期名：

- `*/15 * * * *` —— 每 15 分钟
- `0 0 1 jan *` —— 每年 1 月 1 日 0 点
- `0 12 1 * 5` —— 每月 1 日或每周五中午 12 点（日与周按经典 cron 的 OR 规则）

## 测试

```bash
python3 test_cron_next.py
```
