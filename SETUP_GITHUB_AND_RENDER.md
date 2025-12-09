## Initialize git and first commit

```bash
git init
git add .
git commit -m "Initial FD Global Roster scaffold"
```

## Push to GitHub

On GitHub, create an empty repo (e.g. `fd-global-roster`), then:

```bash
git remote add origin https://github.com/<YOUR_USERNAME>/fd-global-roster.git
git branch -M main
git push -u origin main
```

## Deploy on Render (Docker)

1. New Web Service → connect the GitHub repo.
2. Environment: **Docker**.
3. Build Command: leave blank (Dockerfile handles it).
4. Start Command: leave blank (Docker CMD runs uvicorn).
5. Port: **10000**.
6. Deploy.

## Local run

```bash
uvicorn app.main:app --reload
```

