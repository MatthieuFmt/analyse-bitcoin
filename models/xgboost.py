# Sélection des colonnes pour l'entraînement (on exclut le prix brut et la target)
features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_7', 'SMA_30', 'Log_Ret', 'Daily_Range', 'RSI', 'Vol_Change']
X = df_ready[features]
y = df_ready['Target_Return']

# Split temporel (très important pour la crypto !)
split = int(len(df_ready) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# Configuration du modèle XGBoost
model = xgb.XGBRegressor(
    n_estimators=1000,
    learning_rate=0.01, # Petit pour éviter l'overfitting
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='reg:squarederror',
    random_state=42
)

# Entraînement
model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=False
)

# Prédiction
predictions = model.predict(X_test)
print(f"Score R2 : {r2_score(y_test, predictions):.4f}")