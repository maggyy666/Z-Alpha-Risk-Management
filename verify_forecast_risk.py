#!/usr/bin/env python3
"""
Skrypt do weryfikacji danych Forecast Risk Contribution
Sprawdza czy DOMO (19.2%) jest największym kontrybutorem ryzyka
"""

import numpy as np
import requests
import json
from typing import Dict, List, Tuple
import pandas as pd

class ForecastRiskVerifier:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def get_concentration_data(self, username: str = "admin") -> Dict:
        """Pobiera dane koncentracji z endpointu"""
        try:
            response = requests.get(f"{self.base_url}/concentration-risk-data", 
                                 params={"username": username})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Błąd pobierania danych koncentracji: {e}")
            return None
    
    def get_forecast_risk_data(self, vol_model: str = "EGARCH", username: str = "admin") -> Dict:
        """Pobiera dane forecast risk contribution z endpointu"""
        try:
            response = requests.get(f"{self.base_url}/forecast-risk-contribution", 
                                 params={"vol_model": vol_model, "username": username})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Błąd pobierania danych forecast risk: {e}")
            return None
    
    def get_covariance_matrix(self, tickers: List[str], vol_model: str = "EGARCH", username: str = "admin") -> np.ndarray:
        """Pobiera macierz kowariancji z endpointu"""
        try:
            response = requests.get(f"{self.base_url}/covariance-matrix", 
                                 params={"vol_model": vol_model, "tickers": ",".join(tickers), "username": username})
            response.raise_for_status()
            return np.array(response.json()["cov_matrix"])
        except Exception as e:
            print(f"❌ Błąd pobierania macierzy kowariancji: {e}")
            return None
    
    def calculate_risk_contribution_manual(self, weights: np.ndarray, cov_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Ręczne obliczenie MRC i RC zgodnie ze wzorami:
        
        σ_p = √(w^T Σ w)
        MRC_i = (Σ w)_i / σ_p
        RC_i = w_i * MRC_i
        RC%_i = RC_i / σ_p
        """
        # Portfolio volatility
        sigma_p = np.sqrt(weights @ cov_matrix @ weights)
        
        # Marginal Risk Contribution
        mrc = (cov_matrix @ weights) / sigma_p
        
        # Total Risk Contribution
        rc = weights * mrc
        
        # Percentage Risk Contribution
        rc_pct = rc / sigma_p
        
        return mrc, rc_pct, sigma_p
    
    def verify_dashboard_data(self, username: str = "admin", vol_model: str = "EGARCH"):
        """Główna funkcja weryfikacji"""
        print("WERYFIKACJA DANYCH FORECAST RISK CONTRIBUTION")
        print("=" * 60)
        
        # 1. Pobierz dane z dashboardu
        print("\n📊 1. Pobieranie danych z dashboardu...")
        dashboard_data = self.get_forecast_risk_data(vol_model, username)
        if not dashboard_data:
            return
        
        # 2. Pobierz dane koncentracji (wagi)
        print("\n📊 2. Pobieranie wag z concentration-risk-data...")
        conc_data = self.get_concentration_data(username)
        if not conc_data:
            return
        
        # 3. Przygotuj dane do weryfikacji
        print("\n📊 3. Przygotowanie danych do weryfikacji...")
        
        # Wagi z concentration data
        portfolio_items = conc_data["portfolio_data"]
        tickers = [item["ticker"] for item in portfolio_items]
        weights = np.array([item["weight_frac"] for item in portfolio_items])
        
        print(f"   Tickers: {tickers}")
        print(f"   Wagi: {weights}")
        print(f"   Suma wag: {weights.sum():.6f}")
        
        # 4. Sprawdź czy wagi są znormalizowane
        if abs(weights.sum() - 1.0) > 1e-6:
            print(f"⚠️  Suma wag nie jest 1.0: {weights.sum():.6f}")
            weights = weights / weights.sum()
            print(f"   Znormalizowane wagi: {weights}")
        
        # 5. Pobierz macierz kowariancji Σ
        print(f"\n📊 4. Pobieranie macierzy kowariancji...")
        cov_matrix = self.get_covariance_matrix(tickers, vol_model, username)
        if cov_matrix is None:
            return
        
        print(f"   Macierz Σ: {cov_matrix.shape[0]}x{cov_matrix.shape[1]}")
        print(f"   Portfolio volatility z Σ: {np.sqrt(weights @ cov_matrix @ weights):.4f}")
        
        # 6. Manualne przeliczenie RC% z macierzy Σ
        print(f"\n📊 5. Manualne przeliczenie RC%...")
        mrc_manual, rc_pct_manual, sigma_p_manual = self.calculate_risk_contribution_manual(weights, cov_matrix)
        
        print(f"   Portfolio volatility (manual): {sigma_p_manual:.4f}")
        print(f"   Suma RC% (manual): {(rc_pct_manual * 100).sum():.6f}")
        
        # 7. Pobierz dane z dashboardu
        dashboard_tickers = dashboard_data["tickers"]
        dashboard_rc_pct = np.array(dashboard_data["total_rc_pct"])
        dashboard_mrc_pct = np.array(dashboard_data["marginal_rc_pct"])
        dashboard_portfolio_vol = dashboard_data["portfolio_vol"]
        
        print(f"\n📊 6. Dane z dashboardu:")
        print(f"   Portfolio Volatility: {dashboard_portfolio_vol:.4f}")
        print(f"   Tickers: {dashboard_tickers}")
        
        # 8. Porównaj manualne obliczenia z dashboardem
        print(f"\n📊 7. Porównanie manualne vs dashboard:")
        diff_rc = rc_pct_manual * 100 - dashboard_rc_pct
        max_diff = np.max(np.abs(diff_rc))
        
        if max_diff > 0.1:  # tolerancja 0.1 pp
            print(f"❌ NIEZGODNE: Maksymalna różnica RC% = {max_diff:.3f} pp")
            print(f"   Największe różnice:")
            for i, (ticker, diff) in enumerate(zip(dashboard_tickers, diff_rc)):
                if abs(diff) > 0.05:
                    print(f"     {ticker}: {diff:+.3f} pp")
        else:
            print(f"✅ ZGODNE: RC% z dashboardu ~= wyliczone ręcznie (max różnica: {max_diff:.3f} pp)")
        
        # 9. Znajdź top risk contributor z obu źródeł
        max_rc_idx = np.argmax(dashboard_rc_pct)
        top_contributor = dashboard_tickers[max_rc_idx]
        top_rc_pct = dashboard_rc_pct[max_rc_idx]
        
        max_rc_manual_idx = np.argmax(rc_pct_manual)
        top_contributor_manual = dashboard_tickers[max_rc_manual_idx]
        top_rc_manual_pct = rc_pct_manual[max_rc_manual_idx] * 100
        
        print(f"\n🏆 8. Top Risk Contributor:")
        print(f"   Dashboard: {top_contributor} ({top_rc_pct:.2f}%)")
        print(f"   Manualne:  {top_contributor_manual} ({top_rc_manual_pct:.2f}%)")
        
        # 10. Sprawdź czy oba dają ten sam wynik
        if top_contributor == top_contributor_manual:
            print("✅ ZGODNE: Oba źródła wskazują na tego samego top contributor")
        else:
            print(f"❌ NIEZGODNE: Różne top contributory")
        
        # 11. Sprawdź czy to DOMO
        if top_contributor == "DOMO":
            print("✅ ZGODNE: DOMO jest top risk contributor")
        else:
            print(f"❌ NIEZGODNE: Top contributor to {top_contributor}, nie DOMO")
        
        # 8. Sprawdź czy RC% sumuje się do 100%
        rc_sum = dashboard_rc_pct.sum()
        print(f"\n📊 6. Suma RC%: {rc_sum:.6f}")
        if abs(rc_sum - 100.0) < 1e-2:
            print("✅ ZGODNE: RC% sumuje się do 100%")
        else:
            print(f"❌ NIEZGODNE: RC% nie sumuje się do 100% (różnica: {rc_sum - 100.0:.6f})")
        
        # 9. Sprawdź czy portfolio volatility się zgadza
        expected_vol = dashboard_portfolio_vol * 100  # na procenty
        print(f"\n📊 7. Portfolio Volatility: {expected_vol:.2f}%")
        
        # 10. Wyświetl ranking RC%
        print(f"\n📊 8. Ranking Risk Contribution (%):")
        rc_ranking = list(zip(dashboard_tickers, dashboard_rc_pct))
        rc_ranking.sort(key=lambda x: x[1], reverse=True)
        
        for i, (ticker, rc_pct) in enumerate(rc_ranking[:10]):
            marker = "🏆" if i == 0 else "  "
            print(f"   {marker} {i+1:2d}. {ticker:6s}: {rc_pct:6.2f}%")
        
        # 11. Sprawdź czy są ujemne MRC (hedging)
        negative_mrc = dashboard_mrc_pct < 0
        if np.any(negative_mrc):
            print(f"\n📊 9. Hedging positions (ujemne MRC):")
            for ticker, mrc in zip(dashboard_tickers, dashboard_mrc_pct):
                if mrc < 0:
                    print(f"   🔽 {ticker}: {mrc:.2f}%")
        else:
            print(f"\n📊 9. Brak hedging positions (wszystkie MRC ≥ 0)")
        
        # 12. Podsumowanie
        print(f"\n📊 10. PODSUMOWANIE:")
        print(f"   Model: {vol_model}")
        print(f"   Portfolio Volatility: {dashboard_portfolio_vol:.4f}")
        print(f"   Top Contributor: {top_contributor} ({top_rc_pct:.2f}%)")
        print(f"   Hedging Positions: {np.sum(negative_mrc)}")
        print(f"   Total Positions: {len(dashboard_tickers)}")
        
        return {
            "top_contributor": top_contributor,
            "top_rc_pct": top_rc_pct,
            "portfolio_vol": dashboard_portfolio_vol,
            "hedging_count": np.sum(negative_mrc),
            "total_positions": len(dashboard_tickers),
            "rc_sum": rc_sum
        }

def main():
    """Główna funkcja"""
    print("🚀 Uruchamianie weryfikacji Forecast Risk Contribution")
    print("=" * 60)
    
    verifier = ForecastRiskVerifier()
    
    # Sprawdź różne modele
    models = ["EWMA (5D)", "EWMA (30D)", "EWMA (200D)", "GARCH", "EGARCH"]
    
    results = {}
    
    for model in models:
        print(f"\n🔍 Sprawdzanie modelu: {model}")
        print("-" * 40)
        
        try:
            result = verifier.verify_dashboard_data(username="admin", vol_model=model)
            if result:
                results[model] = result
        except Exception as e:
            print(f"❌ Błąd podczas sprawdzania modelu {model}: {e}")
    
    # Podsumowanie wszystkich modeli
    print(f"\n📊 PODSUMOWANIE WSZYSTKICH MODELI:")
    print("=" * 60)
    
    for model, result in results.items():
        status = "✅" if result["top_contributor"] == "DOMO" else "❌"
        print(f"{status} {model:15s}: {result['top_contributor']:6s} ({result['top_rc_pct']:6.2f}%)")

if __name__ == "__main__":
    main()
