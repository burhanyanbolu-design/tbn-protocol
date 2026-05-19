#!/usr/bin/env python3
"""
Analytics Bot - TBN Certified ⭐⭐⭐⭐ (Expert Bot)
Analyzes data and provides insights, predictions, and answers questions
"""

import subprocess
import json
from datetime import datetime, timedelta

def run_query(sql):
    """Execute SQL query and return results"""
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'hardin_data_network', '-t', '-c', sql],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def run_query_json(sql):
    """Execute SQL query and return JSON results"""
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'hardin_data_network', '-t', '-A', '-F,', '-c', sql],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

class AnalyticsBot:
    """Intelligent bot that analyzes data and answers questions"""
    
    def __init__(self):
        self.name = "AnalyticsBot"
        self.intelligence = "⭐⭐⭐⭐ Expert"
        
    # ==================== RESTAURANT ANALYTICS ====================
    
    def best_restaurants_by_city(self, city="London", limit=10):
        """Find best restaurants in a city"""
        sql = f"""
        SELECT restaurant_name, cuisine_type, overall_rating, food_hygiene_rating, city
        FROM restaurants
        WHERE city = '{city}'
        ORDER BY overall_rating DESC
        LIMIT {limit};
        """
        print(f"\n🍽️  TOP {limit} RESTAURANTS IN {city.upper()}:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    def cuisine_analysis(self):
        """Analyze restaurant cuisines"""
        sql = """
        SELECT 
            cuisine_type,
            COUNT(*) as count,
            ROUND(AVG(overall_rating), 2) as avg_rating,
            MAX(overall_rating) as best_rating
        FROM restaurants
        GROUP BY cuisine_type
        ORDER BY count DESC;
        """
        print("\n📊 CUISINE ANALYSIS:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    def predict_restaurant_success(self, cuisine, city):
        """Predict if a new restaurant would succeed"""
        sql = f"""
        SELECT 
            COUNT(*) as existing_count,
            ROUND(AVG(overall_rating), 2) as avg_rating,
            MAX(overall_rating) as top_rating
        FROM restaurants
        WHERE cuisine_type = '{cuisine}' AND city = '{city}';
        """
        result = run_query(sql)
        print(f"\n🔮 PREDICTION: New {cuisine} restaurant in {city}")
        print("=" * 70)
        print(result)
        print("\nInsight: If avg_rating > 4.5 and existing_count < 20, market is good!")
        return result
    
    # ==================== AUTOMOTIVE ANALYTICS ====================
    
    def car_sales_trends(self):
        """Analyze car sales trends"""
        sql = """
        SELECT 
            manufacturer,
            SUM(units_sold) as total_sales,
            ROUND(AVG(market_share), 2) as avg_market_share
        FROM uk_car_sales
        WHERE year = 2026
        GROUP BY manufacturer
        ORDER BY total_sales DESC
        LIMIT 10;
        """
        print("\n🚗 TOP 10 CAR MANUFACTURERS BY SALES (2026):")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    def predict_car_demand(self, manufacturer):
        """Predict future car demand"""
        sql = f"""
        SELECT 
            year,
            month,
            SUM(units_sold) as monthly_sales
        FROM uk_car_sales
        WHERE manufacturer = '{manufacturer}'
        GROUP BY year, month
        ORDER BY year DESC, month DESC
        LIMIT 12;
        """
        print(f"\n📈 SALES TREND FOR {manufacturer.upper()} (Last 12 months):")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        print("\nPrediction: Average last 3 months + 5% growth = next month forecast")
        return result
    
    def import_export_balance(self):
        """Analyze UK car import/export balance"""
        sql = """
        SELECT 
            'Imports' as type,
            SUM(units_imported) as units,
            SUM(value_gbp) as value_gbp
        FROM uk_car_imports
        WHERE year = 2026
        UNION ALL
        SELECT 
            'Exports' as type,
            SUM(units_exported) as units,
            SUM(value_gbp) as value_gbp
        FROM uk_car_exports
        WHERE year = 2026;
        """
        print("\n💷 UK CAR TRADE BALANCE (2026):")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    # ==================== FINANCIAL ANALYTICS ====================
    
    def currency_trends(self, currency="USD", days=30):
        """Analyze currency trends"""
        sql = f"""
        SELECT 
            date,
            rate,
            rate - LAG(rate) OVER (ORDER BY date) as daily_change
        FROM currency_rates
        WHERE target_currency = '{currency}'
        ORDER BY date DESC
        LIMIT {days};
        """
        print(f"\n💱 GBP/{currency} EXCHANGE RATE (Last {days} days):")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    def commodity_price_analysis(self, commodity="Gold"):
        """Analyze commodity prices"""
        sql = f"""
        SELECT 
            price_date,
            price,
            unit,
            price - LAG(price) OVER (ORDER BY price_date) as price_change
        FROM commodities
        WHERE commodity_name = '{commodity}'
        ORDER BY price_date DESC
        LIMIT 20;
        """
        print(f"\n🥇 {commodity.upper()} PRICE ANALYSIS (Last 20 records):")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    def predict_commodity_price(self, commodity="Gold"):
        """Predict future commodity price"""
        sql = f"""
        SELECT 
            ROUND(AVG(price),2) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price,
            ROUND(STDDEV(price),2) as volatility
        FROM commodities
        WHERE commodity_name = '{commodity}';
        """
        print(f"\n🔮 {commodity.upper()} PRICE PREDICTION:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        print("\nPrediction: avg_price ± volatility = expected range")
        return result
    
    def economic_indicators(self):
        """Show key economic indicators"""
        sql = """
        SELECT 
            indicator,
            value,
            unit,
            year,
            quarter
        FROM government_statistics
        WHERE country = 'United Kingdom'
        ORDER BY indicator
        LIMIT 10;
        """
        print("\n📊 UK ECONOMIC INDICATORS:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    # ==================== EDUCATION ANALYTICS ====================
    
    def university_rankings(self, limit=10):
        """Show top universities"""
        sql = f"""
        SELECT 
            name,
            city,
            ranking_uk,
            ranking_world,
            graduate_employment_rate
        FROM uk_universities
        ORDER BY ranking_uk
        LIMIT {limit};
        """
        print(f"\n🎓 TOP {limit} UK UNIVERSITIES:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    def school_ofsted_analysis(self):
        """Analyze Ofsted ratings"""
        sql = """
        SELECT 
            ofsted_rating,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM uk_schools
        GROUP BY ofsted_rating
        ORDER BY count DESC;
        """
        print("\n📚 OFSTED RATING DISTRIBUTION:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    def best_schools_by_city(self, city="London"):
        """Find best schools in a city"""
        sql = f"""
        SELECT 
            name,
            phase,
            ofsted_rating,
            student_count
        FROM uk_schools
        WHERE city = '{city}' AND ofsted_rating = 'Outstanding'
        ORDER BY student_count DESC
        LIMIT 10;
        """
        print(f"\n🏫 OUTSTANDING SCHOOLS IN {city.upper()}:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    # ==================== SPORTS ANALYTICS ====================
    
    def football_team_performance(self, team="Arsenal"):
        """Analyze football team performance"""
        sql = f"""
        SELECT 
            match_date,
            home_team,
            away_team,
            home_score,
            away_score,
            league,
            CASE 
                WHEN home_team = '{team}' AND home_score > away_score THEN 'Win'
                WHEN away_team = '{team}' AND away_score > home_score THEN 'Win'
                WHEN home_score = away_score THEN 'Draw'
                ELSE 'Loss'
            END as result
        FROM football_matches
        WHERE home_team = '{team}' OR away_team = '{team}'
        ORDER BY match_date DESC
        LIMIT 10;
        """
        print(f"\n⚽ {team.upper()} - RECENT MATCHES:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        return result
    
    def lottery_hot_numbers(self, lottery="EuroMillions"):
        """Find recent lottery draws"""
        sql = f"""
        SELECT 
            draw_name,
            numbers,
            bonus_numbers,
            draw_date,
            jackpot_amount
        FROM lottery_draws
        WHERE draw_name LIKE '%{lottery}%'
        ORDER BY draw_date DESC
        LIMIT 10;
        """
        print(f"\n🎰 {lottery.upper()} - RECENT DRAWS:")
        print("=" * 70)
        result = run_query(sql)
        print(result)
        print("\nAnalysis: Look for frequently appearing numbers!")
        return result
    
    # ==================== CROSS-DATA INSIGHTS ====================
    
    def city_insights(self, city="London"):
        """Comprehensive city insights"""
        print(f"\n🌆 COMPREHENSIVE INSIGHTS FOR {city.upper()}")
        print("=" * 70)
        
        sql = f"SELECT COUNT(*) FROM restaurants WHERE city = '{city}';"
        print(f"Restaurants:  {run_query(sql)}")
        
        sql = f"SELECT COUNT(*) FROM uk_schools WHERE city = '{city}';"
        print(f"Schools:      {run_query(sql)}")
        
        sql = f"SELECT COUNT(*) FROM uk_universities WHERE city = '{city}';"
        print(f"Universities: {run_query(sql)}")

        sql = f"SELECT COUNT(*) FROM football_matches WHERE home_team LIKE '%{city}%' OR away_team LIKE '%{city}%';"
        print(f"Football matches involving {city}: {run_query(sql)}")

        return f"City profile complete for {city}"
    
    def correlation_analysis(self):
        """Find interesting correlations in the data"""
        print("\n🔗 INTERESTING DATA INSIGHTS:")
        print("=" * 70)

        # Top commodities by price
        sql = """
        SELECT commodity_name, ROUND(AVG(price),2) as avg_price, unit
        FROM commodities
        GROUP BY commodity_name, unit
        ORDER BY avg_price DESC
        LIMIT 8;
        """
        print("Top commodities by average price:")
        print(run_query(sql))

        # Currency rates snapshot
        sql = """
        SELECT target_currency, ROUND(AVG(rate),4) as avg_rate
        FROM currency_rates
        GROUP BY target_currency
        ORDER BY avg_rate DESC
        LIMIT 8;
        """
        print("\nTop currency rates vs GBP:")
        print(run_query(sql))

        print("\nInsight: Higher rate = weaker GBP against that currency")
        return "Correlation analysis complete"
    
    # ==================== MAIN ANALYTICS DASHBOARD ====================
    
    def run_full_analysis(self):
        """Run comprehensive analysis"""
        print("\n" + "=" * 70)
        print("🤖 HARDIN DATA NETWORK - INTELLIGENT ANALYTICS")
        print("=" * 70)
        
        # Restaurant insights
        self.best_restaurants_by_city("London", 5)
        self.cuisine_analysis()
        
        # Automotive insights
        self.car_sales_trends()
        self.import_export_balance()
        
        # Financial insights
        self.economic_indicators()
        self.commodity_price_analysis("Gold")
        
        # Education insights
        self.university_rankings(5)
        self.school_ofsted_analysis()
        
        # Sports insights
        self.football_team_performance("Arsenal")
        
        # City insights
        self.city_insights("London")
        
        # Correlations
        self.correlation_analysis()
        
        print("\n" + "=" * 70)
        print("✅ FULL ANALYSIS COMPLETE!")
        print("=" * 70)

if __name__ == '__main__':
    bot = AnalyticsBot()
    
    print("=" * 70)
    print("🤖 ANALYTICS BOT - TBN Certified ⭐⭐⭐⭐")
    print("Intelligent data analysis and predictions")
    print("=" * 70)
    
    # Run full analysis
    bot.run_full_analysis()
    
    print("\n" + "=" * 70)
    print("💡 AVAILABLE ANALYTICS:")
    print("=" * 70)
    print("1. Restaurant Analytics - Best restaurants, cuisine trends")
    print("2. Automotive Analytics - Sales trends, import/export")
    print("3. Financial Analytics - Currency, commodities, economy")
    print("4. Education Analytics - University rankings, Ofsted ratings")
    print("5. Sports Analytics - Team performance, lottery numbers")
    print("6. City Insights - Comprehensive city profiles")
    print("7. Predictions - Future trends and forecasts")
    print("=" * 70)
