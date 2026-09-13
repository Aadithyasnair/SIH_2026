# Git Instructions — SIH_2026

Repo: https://github.com/Aadithyasnair/SIH_2026.git

Read this once before writing any code. Following it exactly is what prevents commits from 
overwriting each other and pushes from getting rejected.

---

## Branch Names (use exactly these)

| Person | Branch |
|---|---|
| Madhumitha A Rao (Ingestion) | `module/ingestion` |
| Sufiyan Khan (Correlation/Clustering) | `module/correlation` |
| Aadithya S Nair (ML Detection) | `module/ml_detection` |
| Maumita Saha (Explainability) | `module/explainability` |
| Mohammed Saleem (Frontend) | `module/frontend` |
| Lakshmi A (Backend/Integration) | `module/backend` |

For the one-time shared schema task (whoever does it first): `module/shared-schema`

`main` is the only shared branch everyone merges into. Nobody pushes to `main` directly.

---

## One-Time Setup (repo owner only)

```bash
git init
git remote add origin https://github.com/Aadithyasnair/SIH_2026.git
git branch -M main
git push -u origin main
```

Then on GitHub: **Settings → Branches → Add branch protection rule** for `main`:
- Require a pull request before merging
- Require at least 1 approval (Lakshmi reviews/approves everyone's PRs)
- Do not allow force pushes to `main`
- Do not allow deletions

---

## One-Time Setup (everyone else, first time only)

```bash
git clone https://github.com/Aadithyasnair/SIH_2026.git
cd SIH_2026
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

## Every Time You Start Work

Always sync `main` before branching off, even if you already have a branch — this pulls in 
anything merged since you last worked:

```bash
git checkout main
git pull origin main
git checkout -b module/<your-module>      # only the FIRST time you create it
```

If your branch already exists from a previous session:

```bash
git checkout main
git pull origin main
git checkout module/<your-module>
git merge main                            # bring your branch up to date with main
```

---

## While Working

Commit often, in small logical chunks — not one giant commit at the end.

```bash
git add .
git commit -m "[module-name] short description"
```

**Commit message format:** `[module-name] description`
Examples:
- `[ingestion] add synthetic data generator with anomaly injection`
- `[correlation] add Node2Vec embedding clustering`
- `[frontend] add live globe arc animations`

---

## Before Every Push (this is what prevents rejections)

```bash
git pull --rebase origin main
```

This replays your local commits on top of the latest `main` instead of creating a messy merge 
commit. Outcomes:
- **"Already up to date"** → you're clear, push normally.
- **Conflicts shown** → git pauses on the conflicting file(s). Open them, resolve the 
  conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), then:
  ```bash
  git add <fixed-file>
  git rebase --continue
  ```
  Repeat until the rebase finishes.

---

## Pushing Your Branch

```bash
git push origin module/<your-module>
```

First push of a brand-new branch, if it complains about no upstream:

```bash
git push -u origin module/<your-module>
```

**Never run `git push origin main` directly** — branch protection should block it anyway, but 
don't try to bypass it. All changes to `main` go through a pull request.

---

## Opening a Pull Request

1. Push your branch (above).
2. On GitHub, open a PR from `module/<your-module>` → `main`.
3. Title it `[module-name] short summary`.
4. Tag Lakshmi as reviewer.
5. Wait for approval before merging — don't self-merge even if you technically can.

Open a PR when your module's Definition of Done (from the agent prompts doc) is met, not 
continuously for every small commit — batch related work into one PR.

---

## If a Push Is Rejected ("non-fast-forward" / "updates were rejected")

This means someone else pushed to that branch (or `main`) since you last pulled.

```bash
git pull --rebase origin <branch-name>
git push origin <branch-name>
```

**Never use `git push --force`** — it can silently wipe a teammate's commits. If you absolutely 
must force-push after a rebase (e.g. cleaning up your own branch's history before a PR), use:

```bash
git push --force-with-lease origin module/<your-module>
```

This refuses to push if someone else has pushed to that branch since your last pull, instead of 
blindly overwriting them like a normal `--force` would.

---

## Avoiding Conflicts in the First Place

- **Never edit inside another person's module folder.** Stick to your own `/sih26146/<module>` 
  directory. Shared files (`/shared/schemas/records.py`, `docker-compose.yml`, this repo's 
  `README.md`) go through the contract-change process — propose the change, get it approved, 
  then whoever owns integration (Lakshmi) applies it.
- **Pull before you branch, and pull-rebase before every push.** Most "erased work" incidents 
  happen from skipping this, not from git itself.
- **Commit often.** Small, frequent commits are easier to merge/rebase than one huge commit 
  with days of changes.
- **Don't work directly on `main` locally**, even if you forget to branch — if you catch 
  yourself on `main` with uncommitted changes:
  ```bash
  git stash
  git checkout -b module/<your-module>
  git stash pop
  ```

---

## Quick Reference

```bash
# Start of a session
git checkout main && git pull origin main
git checkout module/<your-module> && git merge main

# During work
git add .
git commit -m "[module-name] description"

# Before pushing
git pull --rebase origin main

# Push
git push origin module/<your-module>

# If rejected
git pull --rebase origin module/<your-module>
git push origin module/<your-module>
```
