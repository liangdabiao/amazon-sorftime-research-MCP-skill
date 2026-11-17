#!/usr/bin/env python3
"""alexa_question_gen.py — ALEXA AEO 问题生成规范加载器。

ALEXA AEO 不再用固定问题库（固定问题必有品类偏向：Electronics 写成耳机专场、
Pet 写成狗用品……），改为：Agent 读 references/alexa_question_protocol.md 规范
+ listing 全文，针对【该具体产品】生成买家问题，再判断 listing 能否回答。

本脚本职责：
  - load_protocol()：加载规范全文（alexa_check.get_agent_prompt 内部也读同一文件）
  - CLI：打印规范，供人查看 / 调试 / 确认 Agent 的问题生成口径

用法：
  python scripts/alexa_question_gen.py          # 打印问题生成规范全文
"""

import sys
import argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_PATH = SKILL_ROOT / "references" / "alexa_question_protocol.md"


def load_protocol():
    """加载 AEO 问题生成规范全文。"""
    if not PROTOCOL_PATH.exists():
        return ""
    return PROTOCOL_PATH.read_text(encoding="utf-8")


def main():
    argparse.ArgumentParser(description="ALEXA AEO 问题生成规范加载器").parse_args()
    protocol = load_protocol()
    if not protocol:
        print(f"规范文件未找到: {PROTOCOL_PATH}", file=sys.stderr)
        sys.exit(1)
    print(protocol)
    sys.exit(0)


if __name__ == "__main__":
    main()
