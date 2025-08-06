1. Create a virtual environment: `python -m venv .venv`
2. Activate the environment: `.\.venv\Scripts\activate`
3. Install requirements.txt: `pip install -r .\requirements.txt`
4. Run the server: `uvicorn main:app --reload`
5. Access swagger: http://127.0.0.1:8000/docs

# 1. Switch to the production branch
git checkout production

# 2. Pull the latest changes from remote (optional but recommended)
git pull origin production

# 3. Merge changes from main into production
git merge main

# 4. Push the updated production branch to remote
git push origin production

# 5. Switch back to main
git checkout main