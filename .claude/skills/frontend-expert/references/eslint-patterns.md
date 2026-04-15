# ESLint Patterns & Bulk Fix Techniques

## Fast scan (use for iterative fixes)
```bash
cd frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache
```
After config change: `rm -f .eslintcache` first.

## Error-only count by rule
```bash
./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache --format json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
total={}
[total.update({m['ruleId']:total.get(m['ruleId'],0)+1}) for f in data for m in f['messages'] if m['severity']==2]
[print(f'{c:4} {r}') for r,c in sorted(total.items(),key=lambda x:x[1],reverse=True)]
print(f'TOTAL: {sum(total.values())}')
"
```

## Bulk void insertion (no-floating-promises)
```bash
npx eslint src/ --format json > /tmp/eslint.json
python3 << 'SCRIPT'
import json
data = json.load(open('/tmp/eslint.json'))
file_errors = {}
for f in data:
    errs = [(m['line'], m['column']) for m in f['messages']
            if m['severity'] == 2 and m['ruleId'] == '@typescript-eslint/no-floating-promises']
    if errs:
        file_errors[f['filePath']] = sorted(errs, reverse=True)
fixed = 0
for filepath, errors in file_errors.items():
    lines = open(filepath).readlines()
    mod = False
    for line_num, col in errors:
        idx, col_idx = line_num - 1, col - 1
        if col_idx >= len(lines[idx]): continue
        if lines[idx][col_idx:].lstrip().startswith(('void ', 'await ', 'return ')): continue
        lines[idx] = lines[idx][:col_idx] + 'void ' + lines[idx][col_idx:]
        mod, fixed = True, fixed + 1
    if mod:
        open(filepath, 'w').writelines(lines)
print(f"Fixed {fixed} in {len(file_errors)} files")
SCRIPT
```

## no-misused-promises JSX pattern
React async event handlers (onClick, onSubmit) trigger false errors. Config fix:
```js
"@typescript-eslint/no-misused-promises": ["error", {
  checksVoidReturn: { attributes: false, arguments: false }
}]
```
`attributes: false` = JSX event handlers. `arguments: false` = setInterval/forEach callbacks.

## eslint-disable placement rules
- **Must be EXACTLY on line before violation** (no blank lines between)
- **Multi-line function params:** disable goes on line ESLint reports (often closing `)`)
- **sonarjs/cognitive-complexity in useMemo:** before the `() => {`, not before the function containing useMemo
- **JSX map callbacks:** wrap in `{ // eslint-disable-next-line ... \n fn.map(...) }`
- Run `prettier --write file.tsx` after any JSX restructuring

## Type-checked rules disabled for test files
In eslint.config.mjs, `tseslint.configs.disableTypeChecked` spread on test file patterns saves 30-40% scan time. MUST be separate config block from relaxed rules (spread overwrites if combined).

## Dead code audit
```bash
npx knip          # ⚠️ High false positive rate (barrel spreads, Next.js routes, devDeps)
npx madge --circular src/ --extensions ts,tsx  # Known: 2 cycles in offer-studio
```

## File split pattern (for large data files like registry.ts)
1. Extract sections to partial files: `export const REGISTRY_X: Type[] = [...]`
2. Thin combiner: `export const FULL = [...REGISTRY_A, ...REGISTRY_B]`
3. ⚠️ Strip trailing blank lines when extracting with Python (causes `Expression expected` TS error)
