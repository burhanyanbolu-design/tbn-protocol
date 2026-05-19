"""
Hardin Data Network — Natural Language Search Engine
Type plain English. Get intelligent answers from the database.
"""

import psycopg2

DB = dict(dbname="hardin_data_network", user="hardin_admin",
          password="hardin2026", host="localhost", port=5433)

def db(sql, params=None):
    try:
        conn = psycopg2.connect(**DB)
        cur  = conn.cursor()
        cur.execute(sql, params or [])
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except Exception as e:
        return []

# ── Team list ─────────────────────────────────────────────
TEAMS = ['Arsenal','Chelsea','Liverpool','Man United','Man City',
         'Tottenham','Newcastle','West Ham','Aston Villa','Brighton',
         'Everton','Fulham','Brentford','Crystal Palace','Wolves',
         'Nottingham Forest','Burnley','Sheffield United','Luton','Bournemouth',
         'Manchester United','Manchester City','Leeds United','Oxford United']

CITIES = ['London','Manchester','Birmingham','Leeds','Liverpool','Sheffield',
          'Bristol','Edinburgh','Glasgow','Cardiff','Newcastle','Nottingham',
          'Leicester','Oxford','Cambridge','Brighton','Southampton','Coventry']

def find_teams(q):
    found = []
    # Map common names to DB names
    aliases = {
        'manchester united': 'Man United',
        'man utd': 'Man United',
        'man united': 'Man United',
        'manchester city': 'Man City',
        'man city': 'Man City',
        'spurs': 'Tottenham',
        'tottenham hotspur': 'Tottenham',
    }
    ql = q.lower()
    for alias, db_name in aliases.items():
        if alias in ql and db_name not in found:
            found.append(db_name)

    for t in TEAMS:
        for word in t.split():
            if len(word) > 3 and word.lower() in ql and t not in found:
                found.append(t)
    return found

def find_city(q):
    for c in CITIES:
        if c.lower() in q.lower():
            return c
    return 'London'

def find_currency(q):
    if 'dollar' in q or 'usd' in q: return 'USD'
    if 'euro' in q or 'eur' in q:   return 'EUR'
    if 'yen' in q or 'jpy' in q:    return 'JPY'
    return 'USD'

def find_commodity(q):
    for c in ['Silver','Crude Oil','Copper','Platinum','Natural Gas','Coffee','Corn','Aluminum']:
        if c.lower() in q.lower(): return c
    return 'Gold'

def find_manufacturer(q):
    for m in ['Ford','Tesla','Toyota','Volkswagen','BMW','Mercedes','Audi','Vauxhall','Nissan','Kia']:
        if m.lower() in q.lower(): return m
    return None

# ── Intent detection ──────────────────────────────────────
def intent(query):
    q = query.lower()

    # Weather first (before restaurant)
    if any(w in q for w in ['weather','temperature','rain','forecast','climate','sunny','cold']):
        return 'weather', find_city(q)

    # Lottery (before currency — euromillions has 'euro')
    if any(w in q for w in ['lottery','lotto','euromillions','jackpot','winning numbers','lucky numbers']):
        return 'lottery', None

    # Horse racing (before football — 'race' keyword)
    if any(w in q for w in ['horse','jockey','cheltenham','ascot','epsom','racecourse','horse racing']):
        return 'horse', None

    # Football
    if any(w in q for w in ['vs','versus','playing','match','fixture','form','results','who will win','likely to win','league']):
        teams = find_teams(q)
        return 'football', teams or []

    # University
    if any(w in q for w in ['university','universities','college','degree','oxford','cambridge','ranking','tuition']):
        return 'university', find_city(q)

    # School
    if any(w in q for w in ['school','ofsted','primary','secondary','academy']):
        return 'school', find_city(q)

    # Restaurant
    if any(w in q for w in ['restaurant','eat','food','takeaway','curry','pizza','kebab','chinese','indian','thai','italian']):
        return 'restaurant', find_city(q)

    # Commodity
    if any(w in q for w in ['gold','silver','oil','copper','commodity','buy gold','invest in','platinum','natural gas']):
        return 'commodity', find_commodity(q)

    # Currency
    if any(w in q for w in ['currency','exchange rate','pound','dollar','gbp','usd','eur','forex']):
        return 'currency', find_currency(q)

    # Economy
    if any(w in q for w in ['gdp','economy','unemployment','inflation','interest rate','economic','recession']):
        return 'economy', None

    # Cars
    if any(w in q for w in ['car','vehicle','ford','tesla','toyota','bmw','audi','sales','manufacturer','electric']):
        return 'cars', find_manufacturer(q)

    # Trade
    if any(w in q for w in ['import','export','trade','tariff']):
        return 'trade', None

    # Team names mentioned without keywords
    teams = find_teams(q)
    if teams:
        return 'football', teams

    return 'unknown', q

# ── Answer functions ──────────────────────────────────────

def football(teams, query):
    out = "⚽ FOOTBALL ANALYSIS\n" + "="*50 + "\n\n"

    stats = {}
    for team in teams:
        rows = db("""
            SELECT COUNT(*),
                SUM(CASE WHEN (home_team=%s AND home_score>away_score) OR (away_team=%s AND away_score>home_score) THEN 1 ELSE 0 END),
                SUM(CASE WHEN home_score=away_score THEN 1 ELSE 0 END),
                ROUND(AVG(CASE WHEN home_team=%s THEN home_score ELSE away_score END),1),
                ROUND(AVG(CASE WHEN home_team=%s THEN away_score ELSE home_score END),1)
            FROM football_matches WHERE home_team=%s OR away_team=%s
        """, [team,team,team,team,team,team])
        if rows and rows[0][0]:
            p,w,d,gs,gc = rows[0]
            l = p - w - d
            wr = round(w/p*100,1) if p else 0
            stats[team] = {'p':p,'w':w,'d':d,'l':l,'wr':wr,'gs':gs or 0,'gc':gc or 0}

    if not stats:
        out += "  No match data found for these teams.\n"
        return out

    out += "📊 RECENT FORM\n"
    for team, s in stats.items():
        out += f"  {team}: {s['w']}W {s['d']}D {s['l']}L | Win rate: {s['wr']}% | Goals: {s['gs']} scored, {s['gc']} conceded\n"

    # Head to head
    if len(teams) >= 2:
        h2h = db("""
            SELECT match_date, home_team, away_team, home_score, away_score
            FROM football_matches
            WHERE (home_team=%s AND away_team=%s) OR (home_team=%s AND away_team=%s)
            ORDER BY match_date DESC LIMIT 5
        """, [teams[0],teams[1],teams[1],teams[0]])

        if h2h:
            out += f"\n🔄 HEAD TO HEAD (Last {len(h2h)} meetings)\n"
            t1w = t2w = dr = 0
            for r in h2h:
                date,home,away,hs,as_ = r
                if home == teams[0]:
                    res = "Win" if hs>as_ else ("Draw" if hs==as_ else "Loss")
                    if hs>as_: t1w+=1
                    elif hs==as_: dr+=1
                    else: t2w+=1
                else:
                    res = "Win" if as_>hs else ("Draw" if hs==as_ else "Loss")
                    if as_>hs: t1w+=1
                    elif hs==as_: dr+=1
                    else: t2w+=1
                out += f"  {str(date)[:10]}: {home} {hs}-{as_} {away}\n"
            out += f"\n  H2H: {teams[0]} {t1w}W {dr}D {t2w}L vs {teams[1]}\n"

        # Prediction
        out += "\n🔮 PREDICTION\n"
        s1 = stats.get(teams[0],{})
        s2 = stats.get(teams[1],{})
        if s1 and s2:
            wr1, wr2 = s1['wr'], s2['wr']
            if wr1 > wr2 + 10:
                out += f"  ✅ {teams[0]} are FAVOURITES (Win rate {wr1}% vs {wr2}%)\n"
                out += f"  Predicted result: {teams[0]} Win\n"
                out += f"  Confidence: HIGH\n"
            elif wr2 > wr1 + 10:
                out += f"  ✅ {teams[1]} are FAVOURITES (Win rate {wr2}% vs {wr1}%)\n"
                out += f"  Predicted result: {teams[1]} Win\n"
                out += f"  Confidence: HIGH\n"
            else:
                out += f"  ⚖️  EVENLY MATCHED ({teams[0]} {wr1}% vs {teams[1]} {wr2}%)\n"
                out += f"  Predicted result: Could go either way — Draw possible\n"
                out += f"  Confidence: MEDIUM\n"

            # Goal prediction
            avg_goals = round((s1['gs'] + s2['gs']) / 2, 1)
            out += f"  Expected goals: ~{avg_goals} per team\n"
        else:
            out += f"  Not enough data for a confident prediction\n"

    elif len(teams) == 1:
        team = teams[0]
        s = stats.get(team, {})
        if s:
            out += f"\n🔮 {team.upper()} PREDICTION\n"
            if s['wr'] > 60:
                out += f"  Strong form — likely to WIN their next match\n"
            elif s['wr'] > 40:
                out += f"  Average form — match could go either way\n"
            else:
                out += f"  Poor form — at risk of losing next match\n"

    out += f"\n  ⚠️  Based on historical data in our database"
    return out


def restaurant(city, query):
    cuisine = None
    for c in ['indian','chinese','pizza','kebab','japanese','thai','italian','mexican']:
        if c in query.lower():
            cuisine = c
            break

    if cuisine:
        rows = db("""SELECT restaurant_name, cuisine_type, overall_rating, food_hygiene_rating
            FROM restaurants WHERE city=%s AND cuisine_type=%s
            ORDER BY overall_rating DESC LIMIT 10""", [city, cuisine])
    else:
        rows = db("""SELECT restaurant_name, cuisine_type, overall_rating, food_hygiene_rating
            FROM restaurants WHERE city=%s
            ORDER BY overall_rating DESC LIMIT 10""", [city])

    title = f"{'BEST ' + cuisine.upper() + ' ' if cuisine else ''}RESTAURANTS IN {city.upper()}"
    out = f"🍽️  {title}\n" + "="*50 + "\n\n"

    if rows:
        for i,r in enumerate(rows,1):
            hygiene = f" | Hygiene: {r[3]}/5" if r[3] else ""
            out += f"  {i}. {r[0]} ({r[1]}) — ⭐ {r[2]}{hygiene}\n"
        out += f"\n  📊 {len(rows)} restaurants found"
    else:
        out += f"  No restaurants found in {city}"
        if cuisine: out += f" for {cuisine} cuisine"
        out += "\n  Try: London, Manchester, Birmingham, Leeds"
    return out


def commodity(name, query):
    rows = db("""SELECT price_date, price, unit FROM commodities
        WHERE commodity_name=%s ORDER BY price_date DESC LIMIT 30""", [name])

    if not rows:
        return f"No data found for {name}"

    prices = [float(r[1]) for r in rows]
    latest, avg = prices[0], sum(prices)/len(prices)
    high, low = max(prices), min(prices)
    trend = prices[0] - prices[-1]

    out = f"🥇 {name.upper()} PRICE ANALYSIS\n" + "="*50 + "\n\n"
    out += f"  Current price:  ${latest:.2f} {rows[0][2]}\n"
    out += f"  30-day average: ${avg:.2f}\n"
    out += f"  30-day high:    ${high:.2f}\n"
    out += f"  30-day low:     ${low:.2f}\n"
    out += f"  Trend:          {'📈 Rising' if trend > 0 else '📉 Falling'}\n\n"
    out += "🔮 RECOMMENDATION\n"

    if latest < avg * 0.95:
        out += f"  ✅ BUY SIGNAL — Price is {round((avg-latest)/avg*100,1)}% BELOW average\n"
        out += f"  Looks undervalued. Could be a good entry point.\n"
    elif latest > avg * 1.05:
        out += f"  ⚠️  CAUTION — Price is {round((latest-avg)/avg*100,1)}% ABOVE average\n"
        out += f"  May be overvalued. Consider waiting for a dip.\n"
    else:
        out += f"  ➡️  NEUTRAL — Price is near the 30-day average\n"
        out += f"  No strong buy or sell signal right now.\n"

    out += "\n  ⚠️  Data analysis only — not financial advice"
    return out


def currency(code, query):
    rows = db("""SELECT rate_date, exchange_rate FROM currency_rates
        WHERE target_currency=%s ORDER BY rate_date DESC LIMIT 30""", [code])

    if not rows:
        avail = db("SELECT DISTINCT target_currency FROM currency_rates LIMIT 10")
        return f"No data for GBP/{code}. Available currencies: {', '.join(r[0] for r in avail)}"

    rates = [float(r[1]) for r in rows]
    latest, avg = rates[0], sum(rates)/len(rates)
    trend = rates[0] - rates[-1]

    out = f"💱 GBP/{code} EXCHANGE RATE\n" + "="*50 + "\n\n"
    out += f"  Current:        1 GBP = {latest:.4f} {code}\n"
    out += f"  30-day average: {avg:.4f}\n"
    out += f"  Trend:          {'📈 GBP Strengthening' if trend > 0 else '📉 GBP Weakening'}\n\n"
    out += "🔮 ANALYSIS\n"

    if latest > avg * 1.02:
        out += f"  GBP is STRONG vs {code} — good time to exchange GBP\n"
    elif latest < avg * 0.98:
        out += f"  GBP is WEAK vs {code} — consider waiting before exchanging\n"
    else:
        out += f"  GBP/{code} trading near average — neutral outlook\n"
    return out


def economy(query):
    # Get latest data for each indicator
    rows = db("""
        SELECT DISTINCT ON (indicator)
            indicator, value, unit, year, quarter
        FROM government_statistics
        WHERE country = 'United Kingdom'
        ORDER BY indicator, year DESC, quarter DESC
    """)

    # Build a dict for easy access
    data = {r[0]: {'value': float(r[1]), 'unit': r[2], 'year': r[3], 'quarter': r[4]} for r in rows}

    out = "📊 UK ECONOMY ANALYSIS\n" + "="*50 + "\n\n"

    # Key indicators
    out += "📈 KEY INDICATORS (Latest)\n"
    if 'GDP' in data:
        d = data['GDP']
        out += f"  GDP:               £{d['value']:,.0f} {d['unit']} ({d['year']} {d['quarter']})\n"
    if 'GDP Per Capita' in data:
        d = data['GDP Per Capita']
        out += f"  GDP Per Capita:    ${d['value']:,.0f} {d['unit']}\n"
    if 'Inflation Rate' in data:
        d = data['Inflation Rate']
        out += f"  Inflation (CPI):   {d['value']}%\n"
    if 'Interest Rate' in data:
        d = data['Interest Rate']
        out += f"  Bank Rate:         {d['value']}%\n"
    if 'Unemployment Rate' in data:
        d = data['Unemployment Rate']
        out += f"  Unemployment:      {d['value']}%\n"
    if 'Government Debt' in data:
        d = data['Government Debt']
        out += f"  Government Debt:   {d['value']}% of GDP\n"
    if 'Trade Balance' in data:
        d = data['Trade Balance']
        out += f"  Trade Balance:     £{d['value']}bn\n"
    if 'Average Weekly Earnings' in data:
        d = data['Average Weekly Earnings']
        out += f"  Avg Weekly Wage:   £{d['value']:,.0f}\n"
    if 'House Price Index' in data:
        d = data['House Price Index']
        out += f"  Avg House Price:   £{d['value']:,.0f}\n"

    # Analysis
    out += "\n🔮 ECONOMIC ANALYSIS\n"

    inflation = data.get('Inflation Rate', {}).get('value', 0)
    interest  = data.get('Interest Rate', {}).get('value', 0)
    unemploy  = data.get('Unemployment Rate', {}).get('value', 0)
    debt      = data.get('Government Debt', {}).get('value', 0)
    confidence = data.get('Consumer Confidence', {}).get('value', 0)
    pmi       = data.get('Manufacturing PMI', {}).get('value', 0)

    # Inflation assessment
    if inflation < 2.0:
        out += f"  ✅ Inflation ({inflation}%): Below target — economy may need stimulus\n"
    elif inflation <= 3.0:
        out += f"  ✅ Inflation ({inflation}%): Near Bank of England 2% target — HEALTHY\n"
    elif inflation <= 5.0:
        out += f"  ⚠️  Inflation ({inflation}%): Above target — Bank likely to keep rates high\n"
    else:
        out += f"  🔴 Inflation ({inflation}%): HIGH — cost of living pressure on households\n"

    # Interest rate assessment
    if interest <= 2.0:
        out += f"  ✅ Interest Rate ({interest}%): Low — cheap borrowing, good for growth\n"
    elif interest <= 4.0:
        out += f"  ⚠️  Interest Rate ({interest}%): Moderate — mortgage costs elevated\n"
    else:
        out += f"  🔴 Interest Rate ({interest}%): HIGH — expensive mortgages, slowing growth\n"

    # Unemployment assessment
    if unemploy < 4.0:
        out += f"  ✅ Unemployment ({unemploy}%): LOW — strong jobs market\n"
    elif unemploy <= 5.0:
        out += f"  ✅ Unemployment ({unemploy}%): Normal range — stable jobs market\n"
    else:
        out += f"  ⚠️  Unemployment ({unemploy}%): Rising — labour market weakening\n"

    # Debt assessment
    if debt < 60:
        out += f"  ✅ Government Debt ({debt}% GDP): Manageable\n"
    elif debt < 100:
        out += f"  ⚠️  Government Debt ({debt}% GDP): High — limits spending options\n"
    else:
        out += f"  🔴 Government Debt ({debt}% GDP): Very high — fiscal pressure\n"

    # PMI
    if pmi > 50:
        out += f"  ✅ Manufacturing PMI ({pmi}): Above 50 — sector EXPANDING\n"
    else:
        out += f"  ⚠️  Manufacturing PMI ({pmi}): Below 50 — sector contracting\n"

    # Consumer confidence
    if confidence > 0:
        out += f"  ✅ Consumer Confidence ({confidence}): Positive — households optimistic\n"
    else:
        out += f"  ⚠️  Consumer Confidence ({confidence}): Negative — households cautious\n"

    # Overall verdict
    out += "\n📋 OVERALL VERDICT\n"
    positives = sum([
        inflation <= 3.0,
        interest <= 4.0,
        unemploy <= 5.0,
        debt < 100,
        pmi > 50,
    ])

    if positives >= 4:
        out += "  🟢 UK economy is in GOOD shape overall\n"
        out += "  Growth is steady, inflation is under control\n"
    elif positives >= 3:
        out += "  🟡 UK economy is MIXED — some strengths, some challenges\n"
        out += "  High interest rates and debt are the main concerns\n"
    else:
        out += "  🔴 UK economy faces SIGNIFICANT challenges\n"
        out += "  Multiple indicators showing stress\n"

    out += "\n  ⚠️  Source: ONS, Bank of England, IMF data"
    return out


def cars(manufacturer, query):
    if manufacturer:
        rows = db("""SELECT manufacturer, SUM(units_sold), ROUND(AVG(market_share),2)
            FROM uk_car_sales WHERE manufacturer=%s GROUP BY manufacturer""", [manufacturer])
        title = f"🚗 {manufacturer.upper()} UK SALES"
    else:
        rows = db("""SELECT manufacturer, SUM(units_sold), ROUND(AVG(market_share),2)
            FROM uk_car_sales GROUP BY manufacturer ORDER BY SUM(units_sold) DESC LIMIT 10""")
        title = "🚗 TOP 10 UK CAR MANUFACTURERS"

    out = title + "\n" + "="*50 + "\n\n"
    for i,r in enumerate(rows,1):
        out += f"  {i}. {r[0]}: {int(r[1]):,} units | Market share: {r[2]}%\n"
    return out


def university(city, query):
    rows = db("""SELECT name, city, ranking_uk, ranking_world, graduate_employment_rate, tuition_fees_gbp
        FROM uk_universities ORDER BY ranking_uk LIMIT 10""")

    out = "🎓 TOP UK UNIVERSITIES\n" + "="*50 + "\n\n"
    if rows:
        for r in rows:
            out += f"  #{r[2]} {r[0]} ({r[1]})\n"
            out += f"      World: #{r[3]} | Employment: {r[4]}% | Tuition: £{int(r[5]):,}/yr\n"
    else:
        out += "  No university data found\n"
    return out


def school(city, query):
    rows = db("""SELECT name, phase, ofsted_rating, student_count
        FROM uk_schools WHERE city=%s AND ofsted_rating IN ('Outstanding','Good')
        ORDER BY ofsted_rating, student_count DESC LIMIT 10""", [city])

    out = f"🏫 SCHOOLS IN {city.upper()}\n" + "="*50 + "\n\n"
    if rows:
        for r in rows:
            out += f"  {r[0]} ({r[1]}) — Ofsted: {r[2]} | Students: {r[3]}\n"
    else:
        out += f"  No schools found in {city}\n"
    return out


def lottery(query):
    rows = db("""SELECT lottery_name, draw_date, main_numbers, bonus_numbers, jackpot_amount
        FROM lottery_draws ORDER BY draw_date DESC LIMIT 8""")

    out = "🎰 LATEST LOTTERY DRAWS\n" + "="*50 + "\n\n"
    if rows:
        for r in rows:
            out += f"  {r[0]} — {str(r[1])[:10]}\n"
            out += f"  Numbers: {r[2]}"
            if r[3]: out += f" | Bonus: {r[3]}"
            if r[4]: out += f" | Jackpot: £{float(r[4]):,.0f}"
            out += "\n\n"
    else:
        out += "  No lottery data available\n"
    return out


def horse(query):
    rows = db("""SELECT race_name, race_date, racecourse, distance, winner_horse, winner_jockey, odds
        FROM horse_races ORDER BY race_date DESC LIMIT 8""")

    out = "🏇 RECENT HORSE RACES\n" + "="*50 + "\n\n"
    if rows:
        for r in rows:
            out += f"  {r[0]} — {str(r[1])[:10]} at {r[2]}\n"
            out += f"  Distance: {r[3]} | Winner: {r[4]} (Jockey: {r[5]}) | Odds: {r[6]}\n\n"
    else:
        out += "  No horse racing data found\n"
    return out


def weather(city, query):
    # Try exact city first, then any city
    rows = db("""SELECT city, temperature, weather_condition, humidity, wind_speed, recorded_at
        FROM weather_data WHERE city=%s ORDER BY recorded_at DESC LIMIT 3""", [city])

    if not rows:
        # Get any available weather data
        rows = db("""SELECT city, temperature, weather_condition, humidity, wind_speed, recorded_at
            FROM weather_data ORDER BY recorded_at DESC LIMIT 5""")
        if rows:
            available_city = rows[0][0]
            out = f"🌤️  WEATHER (No data for {city} — showing {available_city})\n" + "="*50 + "\n\n"
        else:
            return f"🌤️  No weather data available\n"
    else:
        out = f"🌤️  WEATHER IN {city.upper()}\n" + "="*50 + "\n\n"

    for r in rows:
        out += f"  {r[0]}: {r[1]}°C — {r[2]}\n"
        out += f"  Humidity: {r[3]}% | Wind: {r[4]} mph\n"
        out += f"  Recorded: {str(r[5])[:16]}\n\n"
    return out


def trade(query):
    rows = db("""SELECT trade_type, country, commodity, value_gbp, year
        FROM trade_data ORDER BY value_gbp DESC LIMIT 10""")

    out = "📦 UK TRADE DATA\n" + "="*50 + "\n\n"
    for r in rows:
        out += f"  {r[0]}: {r[2]} {'to' if r[0]=='Export' else 'from'} {r[1]} — £{float(r[3]):,.0f} ({r[4]})\n"
    return out


def unknown(query):
    out = f"🔍 SEARCH: '{query}'\n" + "="*50 + "\n\n"
    out += "  I couldn't find a specific match. Try:\n\n"
    out += "  ⚽ 'Chelsea vs Arsenal who will win?'\n"
    out += "  🍽️  'Best Indian restaurants in Birmingham'\n"
    out += "  🥇 'Should I buy gold now?'\n"
    out += "  💱 'GBP to USD exchange rate'\n"
    out += "  📊 'UK unemployment rate'\n"
    out += "  🚗 'Top selling cars 2026'\n"
    out += "  🎓 'Best universities in UK'\n"
    out += "  🎰 'Latest EuroMillions numbers'\n"
    out += "  🌤️  'Weather in Manchester'\n"
    out += "  🏇 'Latest horse racing results'\n"
    return out


# ── Main search ───────────────────────────────────────────

def search(query):
    """Main entry point — plain English in, intelligent answer out"""
    i, data = intent(query)

    if i == 'football':   return football(data, query)
    if i == 'restaurant': return restaurant(data, query)
    if i == 'commodity':  return commodity(data, query)
    if i == 'currency':   return currency(data, query)
    if i == 'economy':    return economy(query)
    if i == 'cars':       return cars(data, query)
    if i == 'university': return university(data, query)
    if i == 'school':     return school(data, query)
    if i == 'lottery':    return lottery(query)
    if i == 'horse':      return horse(query)
    if i == 'weather':    return weather(data, query)
    if i == 'trade':      return trade(query)
    return unknown(query)


# ── Test ──────────────────────────────────────────────────

if __name__ == '__main__':
    tests = [
        "Chelsea playing Manchester United at home who is likely to win?",
        "Best Indian restaurants in Birmingham",
        "Should I buy gold now?",
        "GBP to USD exchange rate",
        "UK unemployment rate",
        "Top selling cars in 2026",
        "Best universities in UK",
        "Latest EuroMillions numbers",
        "Arsenal recent form",
        "Weather in Manchester",
        "Latest horse racing results",
    ]

    for q in tests:
        print(f"\n{'='*60}")
        print(f"🔍 {q}")
        print('='*60)
        print(search(q))
