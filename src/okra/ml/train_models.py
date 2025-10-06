#!/usr/bin/env python3
"""
Training script for Okra ML models.

This script trains both the credit scoring and BNPL optimization models
and saves them for production use.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from okra.ml.credit_scoring_model import credit_scoring_model
from okra.ml.bnpl_optimization_model import bnpl_optimization_model


def train_credit_scoring_model():
    """Train the credit scoring model."""
    print("🚀 Training Credit Scoring ML Model")
    print("=" * 50)
    
    try:
        results = credit_scoring_model.train_model(n_samples=10000)
        
        print(f"✅ Credit Scoring Model Training Complete!")
        print(f"📊 AUC Score: {results['auc_score']:.4f}")
        print(f"📊 Log Loss: {results['log_loss']:.4f}")
        print(f"📊 Training Samples: {results['training_samples']}")
        
        # Show top features
        feature_importance = results['feature_importance']
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print("\n🔝 Top 5 Most Important Features:")
        for feature, importance in top_features:
            print(f"   {feature}: {importance:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Credit Scoring Model Training Failed: {e}")
        return False


def train_bnpl_optimization_model():
    """Train the BNPL optimization model."""
    print("\n🚀 Training BNPL Optimization ML Model")
    print("=" * 50)
    
    try:
        results = bnpl_optimization_model.train_model(n_samples=8000)
        
        print(f"✅ BNPL Optimization Model Training Complete!")
        print(f"📊 R² Score: {results['r2_score']:.4f}")
        print(f"📊 RMSE: {results['rmse']:.4f}")
        print(f"📊 Training Samples: {results['training_samples']}")
        
        # Show top features
        feature_importance = results['feature_importance']
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print("\n🔝 Top 5 Most Important Features:")
        for feature, importance in top_features:
            print(f"   {feature}: {importance:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ BNPL Optimization Model Training Failed: {e}")
        return False


def main():
    """Main training function."""
    print("🤖 Okra ML Models Training")
    print("=" * 60)
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Version: {sys.version}")
    print()
    
    # Check if we're in the right directory
    if not Path("src/okra/ml").exists():
        print("❌ Error: Please run this script from the okra agent root directory")
        sys.exit(1)
    
    # Train credit scoring model
    credit_success = train_credit_scoring_model()
    
    # Train BNPL optimization model
    bnpl_success = train_bnpl_optimization_model()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TRAINING SUMMARY")
    print("=" * 60)
    
    if credit_success:
        print("✅ Credit Scoring Model: SUCCESS")
    else:
        print("❌ Credit Scoring Model: FAILED")
    
    if bnpl_success:
        print("✅ BNPL Optimization Model: SUCCESS")
    else:
        print("❌ BNPL Optimization Model: FAILED")
    
    if credit_success and bnpl_success:
        print("\n🎉 All ML models trained successfully!")
        print("🚀 Okra is now ready for ML-enhanced credit scoring!")
        
        # Show model locations
        print("\n📁 Model Locations:")
        print(f"   Credit Scoring: {credit_scoring_model.model_dir}")
        print(f"   BNPL Optimization: {bnpl_optimization_model.model_dir}")
        
    else:
        print("\n⚠️ Some models failed to train. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
