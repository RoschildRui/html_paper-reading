#!/usr/bin/env bash
# blog2html 交付前静态检查
# 用法: bash validate.sh <file.html>
# 检查: 1) JS 字符串嵌套同类型引号  2) <script> 标签配对  3) getElementById 引用的 DOM id 是否存在
set -u
[ $# -eq 1 ] || { echo "用法: bash validate.sh <file.html>"; exit 2; }
file="$1"
[ -f "$file" ] || { echo "文件不存在: $file"; exit 2; }
fail=0

# 1. JS 字符串里嵌套同类型引号 —— 会让整个 <script> parse 失败
if rg -n '(title|body|hint|example|label|text):\s*"[^"]*"[^"]*"' "$file"; then
  echo '✗ JS 字符串嵌套双引号：中文引用改「」『』，或换引号类型 / 模板字符串'
  fail=1
fi
if rg -n "(title|body|hint|example|label|text):\s*'[^']*'[^']*'" "$file"; then
  echo '✗ JS 字符串嵌套单引号：同上'
  fail=1
fi

# 2. <script> / </script> 成对
open_n=$(grep -o '<script' "$file" | wc -l | tr -d ' ')
close_n=$(grep -o '</script>' "$file" | wc -l | tr -d ' ')
if [ "$open_n" -ne "$close_n" ]; then
  echo "✗ <script> 标签不配对：开 $open_n / 关 $close_n"
  fail=1
fi

# 3. getElementById 的字面量 id 都真实存在（模板字符串拼接的动态 id 不检查）
ids=$(grep -oE "getElementById\(['\"][^'\"]+['\"]\)" "$file" \
  | sed -E "s/getElementById\(['\"]([^'\"]+)['\"]\)/\1/" | sort -u)
for id in $ids; do
  if ! grep -qE "id=[\"']${id}[\"']" "$file"; then
    echo "✗ getElementById('$id') 找不到对应的 DOM id"
    fail=1
  fi
done

[ "$fail" -eq 0 ] && echo "✓ 静态检查通过（运行时层仍需浏览器验证）"
exit $fail
