import pandas as pd
import numpy as np
import xgboost as xgb
import os

def main():
    print("Loading Subscription Service Churn Dataset...")
    csv_path = os.path.join(os.path.dirname(__file__), 'Subscription_Service_Churn_Dataset.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)
    
    print("Performing EDA & Feature Engineering...")
    # Drop rows without target variable
    df = df.dropna(subset=['Churn'])
    
    # Select our numerical features
    features = ['AccountAge', 'MonthlyCharges', 'ViewingHoursPerWeek', 'SupportTicketsPerMonth', 'UserRating']
    X = df[features].copy()
    y = df['Churn']
    
    # Impute missing values with median
    for col in features:
        if X[col].isnull().sum() > 0:
            median_val = X[col].median()
            X.fillna({col: median_val}, inplace=True)
            
    print(f"Dataset shape: {X.shape}")
    print(f"Churn rate: {y.mean():.2%}")
    
    print("Performing Train/Test Split (80/20)...")
    np.random.seed(42)
    indices = np.random.permutation(len(X))
    train_size = int(0.8 * len(X))
    train_idx, test_idx = indices[:train_size], indices[train_size:]
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    print("Training XGBoost Churn Predictor on Real Data...")
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    
    params = {
        'max_depth': 5,
        'eta': 0.1,
        'objective': 'binary:logistic',
        'eval_metric': 'logloss'
    }
    
    # Train final model
    model = xgb.train(params, dtrain, num_boost_round=50)
    
    print("\n--- Model Evaluation (Test Set) ---")
    preds_prob = model.predict(dtest)
    preds = (preds_prob > 0.5).astype(int)
    
    accuracy = (preds == y_test).mean()
    
    # Calculate Precision and Recall manually
    true_positives = np.sum((preds == 1) & (y_test == 1))
    false_positives = np.sum((preds == 1) & (y_test == 0))
    false_negatives = np.sum((preds == 0) & (y_test == 1))
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"Test Accuracy:  {accuracy:.2%}")
    print(f"Test Precision: {precision:.2%}")
    print(f"Test Recall:    {recall:.2%}")
    print(f"Test F1-Score:  {f1_score:.2%}")
    print("-----------------------------------\n")
    
    # Save model
    model_path = os.path.join(os.path.dirname(__file__), 'xgboost_churn_model.json')
    model.save_model(model_path)
    print(f"Real Model successfully trained and saved to: {model_path}")

if __name__ == "__main__":
    main()
