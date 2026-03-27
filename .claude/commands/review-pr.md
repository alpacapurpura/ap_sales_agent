Review changes on the current branch compared to main.

Steps:
1. Get current branch: `git branch --show-current`
2. Show commit log since diverging from main: `git log main..HEAD --oneline`
3. Show full diff: `git diff main...HEAD --stat`
4. For each changed file, review:
   - Does it follow DDD layering (backend) or FSD (frontend)?
   - Is tenant_id properly filtered in queries?
   - Are there any security concerns (.env, credentials, SQL injection)?
   - Are migrations idempotent?
5. Report findings with file:line references
