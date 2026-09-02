git config user.email "dev@example.com"
git config user.name "Hackathon Dev"
git add .gitignore
git commit -m "chore: add gitignore"
git add requirements.txt
git commit -m "chore: add requirements for backend"
git add docker-compose.yml
git commit -m "infra: setup local redis and postgres via docker"
git add backend/ml_models.py
git commit -m "feat(ai): integrate CMAB and XGBoost churn models"
git add backend/train_model.py
git commit -m "feat(ml): training script for churn prediction on real dataset"
git add backend/Subscription_Service_Churn_Dataset.csv
git commit -m "data: add real world subscription dataset for training"
git add backend/xgboost_churn_model.json
git commit -m "chore: export pre-trained xgboost weights"
git add backend/main.py
git commit -m "feat(api): create FastAPI webhooks and metrics routes"
git add backend/agent.py
git commit -m "feat(ai): build langgraph state machine for dunning"
git add frontend/
git commit -m "feat(ui): implement premium dark-water financial dashboard"
git add README.md
git commit -m "docs: add architecture sequence diagram and ML metrics"
git add .
git commit -m "chore: final cleanup"
git push origin main
