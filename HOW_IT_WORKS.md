# How QuantFlow Works: A Complete Beginner's Guide

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [The Big Picture: How a Trade Happens](#2-the-big-picture-how-a-trade-happens)
3. [Technical Indicators](#3-technical-indicators)
4. [Machine Learning: LightGBM Quantile Regression](#4-machine-learning-lightgbm-quantile-regression)
5. [Triple-Barrier Labeling](#5-triple-barrier-labeling)
6. [Walk-Forward Validation](#6-walk-forward-validation)
7. [Regime Detection (Hidden Markov Model)](#7-regime-detection-hidden-markov-model)
8. [Signal Fusion: Regime-Gated Mixture of Experts](#8-signal-fusion-regime-gated-mixture-of-experts)
9. [Sentiment Analysis](#9-sentiment-analysis)
10. [Risk Management](#10-risk-management)
11. [Backtesting](#11-backtesting)
12. [Execution](#12-execution)
13. [Model Persistence](#13-model-persistence)
14. [Monitoring, Alerting & Observability](#14-monitoring-alerting--observability)
15. [The Dashboard](#15-the-dashboard)
16. [Data Sources & Demo Mode](#16-data-sources--demo-mode)
17. [Running the System](#17-running-the-system)
18. [Glossary](#18-glossary)

---

## 1. What Is This Project?

QuantFlow is an AI-powered trading system designed for cryptocurrency spot markets (like Bitcoin and Ethereum). Instead of a human staring at charts and deciding when to buy or sell, QuantFlow uses a pipeline of mathematical indicators, machine learning models, and safety mechanisms to make those decisions automatically. The system first figures out what kind of market environment we are in (trending upward, bouncing around, or chaotic), then combines signals from technical analysis, ML predictions, and news sentiment -- weighting each differently depending on that environment. When the system is unsure, it trades smaller. When losses get too large, it shuts down entirely. Everything runs through paper trading (fake money) first before real capital is ever at risk.

---

## 2. The Big Picture: How a Trade Happens

Before diving into individual components, here is the full journey from raw market data to an executed trade, step by step.

**Step 1: Gather Market Data:**
Every 4 hours, QuantFlow pulls candle data from cryptocurrency exchanges like Binance and Coinbase. A "candle" is a summary of what happened to a price during that time period: the opening price, closing price, highest price, lowest price, and how much was traded (volume).

**Step 2: Compute Technical Features:**
The raw candle data is transformed into meaningful measurements called technical indicators. These include things like RSI (how overbought or oversold something is), ATR (how much prices are swinging around), and Bollinger Bands (whether the price is unusually high or low compared to recent history). Think of this step as converting raw ingredients into a recipe that the system can understand.

**Step 3: Run the Machine Learning Model:**
A LightGBM model takes the technical features as input and makes a prediction: will the price likely go up, down, or stay flat? Crucially, it does not just give a single answer -- it provides five different estimates (quantiles) that describe a range of possible outcomes. This tells us not just "where" the price might go, but "how sure" we are about it.

**Step 4: Detect the Market Regime:**
A Hidden Markov Model (HMM) looks at recent returns and volatility to classify the current market into one of three states: trending (prices moving cleanly in one direction), mean-reverting (prices bouncing back and forth around a level), or choppy (wild, unpredictable swings). This is like a weather forecast for the market.

**Step 5: Score News Sentiment:**
Separately, the system ingests news headlines from CryptoPanic and Reddit posts, scores them as positive or negative, filters out likely spam or manipulation attempts, and produces an overall sentiment score.

**Step 6: Fuse the Signals:**
The Regime-Gated Mixture of Experts (MoE) system takes the three signal sources (technical, ML, sentiment) and combines them using weights that depend on the current regime. In a trending market, the ML model gets more weight. In a mean-reverting market, technical indicators dominate. In a choppy market, everything gets scaled down significantly because the environment is too noisy to trade aggressively.

**Step 7: Size the Position:**
Based on the fused signal's strength and the model's confidence, the volatility-targeted position sizer decides how much capital to allocate. High volatility means smaller positions. Low confidence means smaller positions. This keeps risk consistent no matter the market conditions.

**Step 8: Run Risk Checks:**
Before any trade goes out, a battery of safety checks runs: Is the kill switch active? Have we lost too much money already? Is this trade too large relative to our portfolio? Is our data fresh enough to trust? If any check fails, the trade is blocked.

**Step 9: Execute the Trade:**
If all risk checks pass, the order is submitted. In paper mode (the default), this is simulated with fake money. In live mode, the order goes to the exchange with handling for partial fills, retries, and timeouts.

**Step 10: Monitor:**
After execution, the system tracks portfolio equity, drawdown, and model drift. Everything feeds into a real-time dashboard so you can see what is happening at a glance.

---

## 3. Technical Indicators

Technical indicators are mathematical formulas applied to price and volume data. They transform raw numbers into signals that highlight patterns invisible to the naked eye. QuantFlow computes six core indicators.

### Log Returns

**What it measures:** The percentage change in price from one candle to the next, expressed on a logarithmic scale.

**Why it matters:** Log returns are the foundation of almost everything in quantitative finance. They have nicer mathematical properties than simple percentage returns -- most importantly, they are additive over time. If Bitcoin goes up 5% today and 3% tomorrow, you can simply add the log returns to get the total return, which is not true for regular percentages.

**The intuition:** Think of it as keeping a running tally of "how much did the price move since last time?" using a scale that makes the math cleaner.

**The formula:**

```
log_return = ln(price_now / price_previous)
```

Where `ln` is the natural logarithm.

### RSI (Relative Strength Index)

**What it measures:** Whether the price has been going up or down more over a recent window, expressed as a number between 0 and 100.

**Why it matters:** RSI acts like a thermometer for how "overbought" or "oversold" the market is. When RSI is above 70, the asset has been rising aggressively and may be due for a pullback -- like a rubber band stretched too far. When RSI is below 30, it has been falling hard and might bounce. This helps the system identify potential reversal points.

**The intuition:** Imagine tracking your daily mood on a scale of 0 to 100 over two weeks. If you have been extremely happy (100) for many days straight, there is a good chance some average or below-average days are coming. RSI does this with price movements.

**The formula:**

```
RS = Average Gain over N periods / Average Loss over N periods
RSI = 100 - (100 / (1 + RS))
```

QuantFlow uses a 14-period lookback (14 candles of 4 hours each = about 2.3 days) and calculates the averages using an exponential moving average, which gives more weight to recent data.

### ATR (Average True Range)

**What it measures:** How much the price is moving around on average, including gaps between candles.

**Why it matters:** ATR tells us how "wild" the market is right now. A high ATR means big price swings -- the market is volatile. A low ATR means the market is calm. This is critical for position sizing: if the market is swinging wildly, you want to trade smaller to keep your risk constant. ATR also helps set profit targets and stop losses at levels that make sense for the current volatility.

**The intuition:** Think of ATR like a weather report for storm intensity. On a calm day (low ATR), you can walk outside without worry. On a stormy day (high ATR), you should prepare accordingly -- or stay inside.

**The formula:**

True Range is the largest of these three values:
- Current high minus current low
- Absolute value of current high minus previous close
- Absolute value of current low minus previous close

ATR is the average of True Range over 14 periods.

```
True Range = max(high - low, |high - prev_close|, |low - prev_close|)
ATR = rolling average of True Range over 14 bars
```

### Bollinger Bands %B

**What it measures:** Where the current price sits relative to its recent range, expressed as a number between 0 and 1 (though it can go outside that range).

**Why it matters:** Bollinger Bands create an envelope around the price. The upper band represents a price that is unusually high compared to the recent average, and the lower band represents an unusually low price. The %B value tells you exactly where you are in that envelope. A %B of 1.0 means you are touching the upper band (expensive relative to recent history). A %B of 0.0 means you are at the lower band (cheap). Values above 1.0 or below 0.0 mean the price has broken out of the "normal" range entirely.

**The intuition:** Imagine a school grading curve. The middle band is the class average, and the upper/lower bands are one or two standard deviations away. Bollinger %B tells you where a particular student's score falls on that curve. A student scoring at the very top of the curve (%B near 1.0) might not sustain that performance, and one at the very bottom (%B near 0.0) might improve.

**The formula:**

```
Middle Band = 20-period Simple Moving Average (SMA)
Upper Band = SMA + (2 x Standard Deviation)
Lower Band = SMA - (2 x Standard Deviation)
%B = (Price - Lower Band) / (Upper Band - Lower Band)
```

### VWAP Deviation

**What it measures:** How far the current price has drifted from the volume-weighted average price over a recent window.

**Why it matters:** VWAP (Volume-Weighted Average Price) is the "fair" price that incorporates not just where prices have been, but how much trading happened at each price level. If the current price is significantly above VWAP, it may be overextended (buyers have been aggressive). If it is below VWAP, sellers have been in control. Institutional traders often use VWAP as a benchmark for whether they got a "good" price.

**The intuition:** Think of VWAP as the average price that the "typical" trader paid today. If you are buying above VWAP, you are paying more than average. If you are buying below, you are getting a relative bargain. VWAP deviation tells you how big that gap is.

**The formula:**

```
VWAP = sum(Price * Volume) over N bars / sum(Volume) over N bars
VWAP Deviation = (Current Price - VWAP) / VWAP
```

QuantFlow uses a 24-bar rolling window (24 four-hour candles = 4 days).

### Realized Volatility

**What it measures:** How much the price has actually been fluctuating recently, annualized into a yearly rate.

**Why it matters:** Realized volatility is the ground truth of market risk. It directly answers the question: "How wild have things actually been?" This number drives position sizing (more volatile = smaller positions), regime detection (high vol can indicate a choppy regime), and risk management. It is also one of the two features fed into the HMM regime detector.

**The intuition:** If you are on a boat, realized volatility is like measuring how much the boat has actually been rocking over the past few hours. A smooth ride (low vol) is very different from rough seas (high vol), and you should adjust your behavior accordingly.

**The formula:**

```
Realized Vol = Standard Deviation of Log Returns over 24 bars * sqrt(6 * 365)
```

The `sqrt(6 * 365)` factor annualizes from 4-hour bars (there are 6 four-hour bars per day, 365 days per year).

---

## 4. Machine Learning: LightGBM Quantile Regression

### What Is Machine Learning in a Trading Context?

Machine learning (ML) is a way for a computer to learn patterns from historical data and make predictions about new, unseen data. In trading, we feed the computer historical technical indicators (RSI, ATR, etc.) along with what actually happened to the price afterward. The model learns relationships like "when RSI is very high AND volatility is rising AND VWAP deviation is positive, the price tends to fall." These are patterns that would be difficult or impossible for a human to find manually across thousands of data points.

The key difference between ML and simple rule-based trading ("buy when RSI drops below 30") is that ML can discover complex, multi-variable relationships and weight them appropriately -- it can learn that RSI below 30 is bullish in a trending market but meaningless in a choppy one, for example.

### What Is LightGBM?

LightGBM (Light Gradient Boosting Machine) is a specific machine learning algorithm developed by Microsoft. It belongs to the family of "gradient boosted decision trees," which are among the most powerful and practical algorithms in machine learning.

Here is the core idea: imagine building a team of simple decision-makers (decision trees). The first tree makes predictions but gets some wrong. The second tree focuses specifically on correcting those mistakes. The third tree corrects the remaining mistakes, and so on. Each tree is simple on its own, but together they form a powerful ensemble. "Gradient boosting" is the mathematical method for deciding what each new tree should focus on.

LightGBM is popular in quantitative finance because:
- It is fast to train, even on large datasets
- It handles tabular data (rows and columns, like a spreadsheet) extremely well
- It is robust to noisy data, which financial data always is
- It does not require much preprocessing or normalization
- It can handle missing values naturally

### What Are Quantiles?

A quantile is a value that divides a distribution at a specific point. You are probably already familiar with some quantiles:
- The **median** is the 50th percentile (or 0.5 quantile) -- half the values are below it, half above
- The **25th percentile** (0.25 quantile) means 25% of values fall below this point
- The **75th percentile** (0.75 quantile) means 75% of values fall below it

QuantFlow's LightGBM model predicts five quantiles: the 10th, 25th, 50th, 75th, and 90th percentiles. Together, these paint a picture of the full range of possible outcomes, not just a single "best guess."

### What Is Quantile Regression?

Standard regression gives you a single prediction -- the "average" expected outcome. Quantile regression instead predicts specific points on the distribution of possible outcomes.

Think of it this way: a standard weather forecast might say "tomorrow's high will be 75 degrees." A quantile regression forecast would say:

- 10th percentile: "There is a 90% chance it will be warmer than 65 degrees"
- 25th percentile: "There is a 75% chance it will be warmer than 70 degrees"
- 50th percentile: "The median prediction is 75 degrees"
- 75th percentile: "There is only a 25% chance it will be warmer than 80 degrees"
- 90th percentile: "There is only a 10% chance it will be warmer than 85 degrees"

The second forecast is far more useful because it tells you about uncertainty. If the 10th and 90th percentiles are 65 and 85 (a wide range), the forecast is uncertain. If they are 73 and 77 (a narrow range), the forecast is quite confident.

### Why Uncertainty Matters in Trading

QuantFlow uses the gap between the 75th and 25th percentile predictions (called the **Interquartile Range** or IQR) as a direct measure of how confident the model is. This is then converted into a confidence score between 0 and 1:

- **Narrow IQR** (small gap between q25 and q75) means the model's predictions are tightly clustered, suggesting high confidence. Result: larger positions.
- **Wide IQR** (large gap between q25 and q75) means the model is uncertain about what will happen. Result: smaller positions or no trade at all.

This is a crucial safety mechanism. When the model "does not know," it automatically scales back risk instead of charging ahead with a shaky prediction.

```
confidence = 1.0 - (IQR - min_IQR) / (max_IQR - min_IQR)
```

If the IQR is at its minimum observed value, confidence is 1.0. If it is at the maximum, confidence is 0.0.

### The Classifier Component

In addition to the quantile regressors, QuantFlow also trains a LightGBM **classifier** that directly predicts one of three labels: down (0), neutral (1), or up (2). The classifier's probability distribution (how sure it is about its chosen label) provides another layer of confidence measurement. The model outputs both the predicted direction and the probability it assigned to that direction.

---

## 5. Triple-Barrier Labeling

### The Problem with Simple Labels

When training a machine learning model for trading, you need "labels" -- the correct answers the model should learn to predict. The simplest approach is: "Did the price go up or down over the next N bars?" For example, "was the price higher 12 bars from now?"

This sounds reasonable but has a serious flaw: it ignores what happened in between. The price might have shot up 5%, then crashed 8%, and ended up slightly positive. A simple label would call this "up," but any trader who bought at the start would have hit their stop loss during that 8% crash and exited at a loss. The label says "win" but the reality is "loss."

### The Three Barriers

Triple-barrier labeling solves this by simulating what an actual trader would experience. For each point in time, it sets up three conditions (barriers) and labels based on which one is hit first:

**Barrier 1: Profit Target (Upper Barrier)**
If the price rises by a certain percentage (default: 3%) before anything else happens, the trade is labeled as "up" (label = 2). The trader would have taken their profit and exited.

**Barrier 2: Stop Loss (Lower Barrier)**
If the price falls by a certain percentage (default: 1.5%) before anything else happens, the trade is labeled as "down" (label = 0). The trader would have been stopped out at a loss.

**Barrier 3: Time Limit (Vertical Barrier)**
If neither the profit target nor the stop loss is hit within a maximum holding period (default: 12 bars = 48 hours), the label is determined by where the price ended up:
- Slightly positive (above 0.5%) = "up" (label = 2)
- Slightly negative (below -0.5%) = "down" (label = 0)
- In between = "neutral" (label = 1)

### Why This Is Better

Triple-barrier labeling produces training data that reflects actual trading outcomes, not theoretical end-of-period returns. The ML model learns to predict scenarios that map directly to profitable trades, stop-loss exits, and inconclusive holds. This alignment between what the model predicts and what the trading system actually does is critical for performance.

Note that the stop loss (1.5%) is tighter than the profit target (3%). This is intentional -- it creates an asymmetric risk/reward profile where each winning trade earns twice as much as each losing trade costs, which means you can be profitable even if you are right less than half the time.

---

## 6. Walk-Forward Validation

### Why You Cannot Just Train on All the Data

Imagine you are studying for an exam. If someone gives you the exact exam questions beforehand, you will score 100% -- but you will not have actually learned anything. You will fail any new exam with different questions.

The same problem exists in machine learning. If you train a model on a dataset and then test it on the same dataset, it will appear to perform brilliantly because it has "memorized" the data. But when it encounters new, unseen market conditions, it will fail. This is called **overfitting**.

### What Is Lookahead Bias?

Lookahead bias is the cardinal sin of backtesting. It means accidentally using information from the future to make decisions in the past. For example, if your model was trained on data from January through December, and you test it on data from July, the model has "seen" July's data during training. Its good performance on July is an illusion -- it already knew what would happen.

In financial ML, lookahead bias is especially dangerous because it creates wildly unrealistic backtests that look profitable on paper but lose money in reality. This is one of the most common reasons trading strategies fail when deployed live.

### How Walk-Forward Validation Works

Walk-forward validation is a rigorous testing method that mimics real-world conditions. Instead of a single train/test split, it creates multiple sequential splits that march forward through time:

```
Fold 1: [=====TRAIN=====][purge][===TEST===][embargo]
Fold 2:                                              [=====TRAIN=====][purge][===TEST===][embargo]
Fold 3:                                                                                           [=====TRAIN=====][purge][===TEST===]
```

For each fold:
1. Train the model on a window of historical data (default: 1000 bars)
2. Skip a purge gap (default: 3 bars)
3. Test the model on the next window (default: 100 bars)
4. Skip an embargo period (default: 2 bars)
5. Move the entire window forward and repeat

The model is retrained on each fold, so it adapts to evolving market conditions over time -- just like a real trading system would be periodically retrained.

### Purge Gaps

The purge gap is a small buffer of bars between the training data and the test data. Why is this necessary? Because of triple-barrier labeling. If the last training bar is bar 1000, its label might depend on what happens at bars 1001, 1002, and 1003 (the label looks forward in time to see if barriers are hit). If bar 1001 is the first test bar, we have a subtle data leak -- the training label at bar 1000 was partially informed by the test data.

The purge gap of 3 bars ensures this cannot happen. It is like a demilitarized zone between train and test data.

### Embargo Periods

The embargo period is a buffer after the test window before the next training window begins. This prevents information from the test period from bleeding into the next fold's training data. Without it, autocorrelation in financial data (today's return being similar to yesterday's) could create subtle leakage.

QuantFlow uses a default embargo of 2 bars.

---

## 7. Regime Detection (Hidden Markov Model)

### What Are Market Regimes?

Financial markets do not behave the same way all the time. Sometimes prices trend steadily upward (or downward) for weeks. Other times, prices bounce back and forth in a range. And sometimes, prices move wildly in all directions with no clear pattern. These different behavioral states are called "regimes."

A strategy that works brilliantly in one regime can lose money in another. A trend-following approach ("buy things that are going up") thrives in a trending market but gets destroyed in a mean-reverting one where every rise is followed by a fall. Conversely, a mean-reversion approach ("buy things that just dropped") works in range-bound markets but fights the trend in a trending market.

This is why QuantFlow does not use a one-size-fits-all approach. It first identifies the current regime, then adjusts its behavior accordingly.

### What Is a Hidden Markov Model (HMM)?

An HMM is a statistical model for systems that switch between hidden (unobservable) states over time. The "hidden" part means we cannot directly see the state -- we can only observe clues (data) that the state produces.

Here is a real-world analogy: imagine you are trying to figure out the weather in a city you have never visited, but all you can observe is what people in that city are wearing (your friend sends you photos). On some days they wear sunglasses and shorts (clue suggests sunny). On other days they wear raincoats and carry umbrellas (rainy). You cannot see the weather directly, but you can infer it from what you observe.

An HMM does three things:
1. **Learns the hidden states** (in our case: trending, mean-reverting, choppy)
2. **Learns what each state "looks like"** in terms of observable data (what returns and volatility typically look like in each regime)
3. **Learns the transition probabilities** (how likely the market is to switch from one regime to another)

### The Three States in QuantFlow

QuantFlow's HMM uses two observable features -- log returns and realized volatility -- to classify the market into three states:

**Trending (lowest volatility state)**
Clean, directional price moves. Volatility is relatively low because prices are moving steadily in one direction without much back-and-forth. Think of a river flowing smoothly downstream. This is the easiest regime to trade: follow the direction.

**Mean-Reverting (medium volatility state)**
Prices oscillate around a central level. Moves up tend to be followed by moves down, and vice versa. Think of a pendulum swinging back and forth. Good for strategies that buy dips and sell rallies.

**Choppy (highest volatility state)**
Wild, unpredictable price swings. Volatility is high, and there is no consistent pattern. Think of a boat in a storm being tossed in random directions. This is the most dangerous regime to trade, and QuantFlow responds by aggressively scaling down position sizes.

### How States Are Mapped

After the HMM is fitted, it produces states labeled 0, 1, and 2, but those numbers do not inherently mean anything. QuantFlow maps them to regimes by sorting on the average volatility of each state:
- The state with the **lowest average volatility** is mapped to "trending"
- The state with **medium volatility** is mapped to "mean-reverting"
- The state with the **highest average volatility** is mapped to "choppy"

This mapping is based on the empirical observation that trending markets tend to have lower intrabar volatility (smooth moves), while choppy markets have high volatility (erratic swings).

---

## 8. Signal Fusion: Regime-Gated Mixture of Experts

### What Is Mixture of Experts (MoE)?

A Mixture of Experts is an approach where you have multiple "experts" (signal sources), each specializing in different conditions, and a "gating" mechanism that decides how much to listen to each expert depending on the current situation.

Think of it like managing a sports team. You have a sprinter (great on straightaways), a climber (great on hills), and an all-rounder. Instead of always starting the same person, a smart coach picks the lineup based on the course -- flat courses favor the sprinter, mountain stages favor the climber. That is what regime-gated MoE does with trading signals.

### The Three Experts in QuantFlow

QuantFlow has three signal components (experts):

1. **Technical signals** -- derived from the indicators described in Section 3
2. **ML signals** -- predictions from the LightGBM model described in Section 4
3. **Sentiment signals** -- news and social media analysis described in Section 9

Each expert produces a score (positive = bullish, negative = bearish, zero = neutral).

### How Regime Changes the Weights

The regime detected by the HMM determines how much each expert's opinion counts. Here are the default weight configurations:

| Regime | Technical Weight | ML Weight | Sentiment Weight |
|--------|-----------------|-----------|-----------------|
| Trending | 0.4 | 0.5 | 0.1 |
| Mean-Reverting | 0.5 | 0.3 | 0.2 |
| Choppy | 0.3 | 0.3 | 0.4 |

**Why these weights?**

- In a **trending** regime, the ML model gets the most weight (0.5) because it can identify the strength and direction of trends from multi-variable patterns. Technical indicators are also strong (0.4) because trend-following indicators work well here. Sentiment gets minimal weight (0.1) because trend momentum speaks for itself.

- In a **mean-reverting** regime, technical indicators dominate (0.5) because oscillators like RSI and Bollinger %B were literally designed for range-bound conditions. The ML model gets moderate weight (0.3), and sentiment gets more influence (0.2) since news can define the range boundaries.

- In a **choppy** regime, no single signal source is reliable. Sentiment gets the most weight (0.4) because fundamental news might be the only thing that cuts through the noise. But more importantly, the entire signal gets scaled down (see below).

### Choppy Scaling

When the regime is choppy, QuantFlow applies a scaling factor of 0.3 to the combined signal. This means the final signal strength is reduced to just 30% of what it would otherwise be. This is one of the system's most important safety features -- it acknowledges that choppy markets are hard to predict and responds by dramatically reducing exposure.

```
If regime == CHOPPY:
    signal_strength = signal_strength * 0.3
```

### Confidence Adjustment

After regime-based weighting and choppy scaling, the combined signal is further multiplied by the model's confidence score (from the quantile regression IQR, described in Section 4). This means:

```
final_strength = weighted_signal * choppy_scale * confidence
```

If the ML model is uncertain (wide IQR, low confidence), the final signal is reduced even further. This creates a double safety net: both market conditions (regime) and model certainty (confidence) must be favorable for a large trade.

### Direction Determination

The final signal strength is a number between -1 and +1. QuantFlow converts this into a trading direction:

- Strength above +0.05 = **LONG** (buy, expecting prices to rise)
- Strength below -0.05 = **SHORT** (sell, expecting prices to fall)
- Strength between -0.05 and +0.05 = **FLAT** (do nothing, signal is too weak)

The 0.05 threshold prevents the system from trading on extremely weak signals that are likely just noise.

---

## 9. Sentiment Analysis

### How Sentiment Scoring Works

QuantFlow ingests news and social media data from two sources:
- **CryptoPanic** -- a cryptocurrency news aggregator
- **Reddit** -- posts and comments from relevant subreddits

Each piece of content (a headline or post) is scored on a scale of -1 (very bearish) to +1 (very bullish), along with a confidence rating.

The raw sentiment events are then aggregated into a single composite score per symbol. But raw aggregation would be naive and vulnerable to manipulation, so QuantFlow applies several filters.

### Anti-Manipulation Filters

Markets are full of people trying to manipulate sentiment -- posting fake news, flooding social media with bot-generated content, or coordinating "pump and dump" campaigns. QuantFlow defends against this with three mechanisms:

**1. Deduplication**
The system creates a fingerprint (hash) of each event based on its source, title, and approximate time. If it has seen an identical or near-identical event before, it is discarded. This prevents the same news story (or copies of it) from being counted multiple times and artificially inflating the sentiment score.

**2. Source Caps**
No single source can contribute more than 10 events to the aggregate score. If someone is flooding Reddit with 50 bullish posts, only the 10 most recent are counted. This prevents any one actor or platform from dominating the sentiment signal.

**3. Staleness Filtering**
Events older than 24 hours are discarded entirely. Old news is no longer actionable -- the market has already reacted to it.

### Time Decay

Even within the 24-hour window, not all events are weighted equally. Recent events matter more than older ones. QuantFlow applies exponential decay with a 12-hour half-life:

```
decay_weight = 0.5 ^ (hours_since_event / 12)
```

This means:
- An event from 0 hours ago has a weight of 1.0
- An event from 12 hours ago has a weight of 0.5
- An event from 24 hours ago has a weight of 0.25

The final sentiment score is the weighted average of all surviving events, weighted by both their confidence and their time decay. This naturally pulls the score toward neutral (0.0) as events age, which is the correct behavior -- old news should not drive new trades.

---

## 10. Risk Management

Risk management is arguably the most important part of any trading system. A strategy with mediocre signals but excellent risk management will survive and potentially profit. A strategy with brilliant signals but poor risk management will eventually blow up. QuantFlow has three layers of risk management.

### Position Sizing: Volatility-Targeted

**What it does:** Determines how much capital to allocate to each trade.

**Why it matters:** If you always bet the same dollar amount, your actual risk varies wildly. Putting $10,000 into a stable asset (like a Treasury bond) is very different from putting $10,000 into a volatile crypto token. The dollar amount is the same, but the potential loss is vastly different.

Volatility-targeted sizing solves this by adjusting position size inversely to volatility. When the market is calm (low realized vol), positions can be larger. When the market is chaotic (high realized vol), positions shrink. The goal is to keep the portfolio's expected risk (as measured by volatility) constant at a target level -- in QuantFlow's case, 15% annualized.

**The formula:**

```
raw_size = (vol_target / realized_vol) * |signal_strength|
sized = raw_size * confidence
capped = min(sized, max_position_pct)
dollar_value = capped * portfolio_equity
quantity = dollar_value / current_price
```

Step by step:
1. Calculate the ratio of your target volatility to the current realized volatility
2. Multiply by the absolute signal strength (stronger signal = bigger position)
3. Scale by model confidence (less certain = smaller position)
4. Cap at a maximum percentage of portfolio equity (default: 25%)
5. Convert from a portfolio percentage to an actual quantity of the asset

**Example:** If Bitcoin's realized volatility is 60% (four times the 15% target), the vol_ratio is 0.25, immediately cutting the position to a quarter of what it would be in a "normal" volatility environment.

### Risk Checks

Before any trade is submitted, it must pass through a gauntlet of safety checks. Every single check must pass; if any one fails, the trade is blocked entirely.

**Kill Switch (-15% Drawdown)**

This is the most important safety mechanism in the entire system. If the portfolio has lost 15% from its peak value, the kill switch activates and **all trading is immediately halted**. No new orders can be placed. The system cannot be restarted automatically -- a human must manually review the situation and reset the kill switch. This prevents catastrophic losses from cascading failures, bad market conditions, or model errors.

Why 15%? It is a balance between giving the strategy enough room to operate (all strategies have losing periods) and protecting against ruin. Losing 15% requires a 17.6% gain to recover. Losing 50% requires a 100% gain to recover. The relationship between losses and recovery becomes exponentially harder, which is why cutting losses early is critical.

**Concentration Limits (30% Maximum)**

No single trade can represent more than 30% of the portfolio's equity. This prevents the "all eggs in one basket" problem. Even if the model is extremely confident about one trade, it is not allowed to bet the farm. Diversification is enforced mechanically, not left to the model's judgment.

**Position Size Limits (25% Maximum)**

Similar to concentration limits but applied at the individual position level. No single position can exceed 25% of equity.

**Minimum Trade Size ($10)**

Trades below $10 are not worth executing because transaction costs (fees, slippage) would eat a disproportionate share of the potential profit. This filter prevents "dust" trades that cost more than they could ever earn.

**Staleness Detection (30-Minute Threshold)**

If the most recent market data is more than 30 minutes old, the trade is blocked. Trading on stale data is like driving by looking in the rearview mirror -- the world may have changed since your last observation. Stale data can occur due to API outages, network issues, or exchange downtime. Rather than trading blind, the system stops and waits for fresh data.

### Drawdown Monitoring

The drawdown monitor continuously tracks the portfolio's equity relative to its all-time peak. It answers the question: "How far have we fallen from our best moment?"

```
drawdown = (peak_equity - current_equity) / peak_equity
```

This is updated every time new equity information arrives. If the drawdown ever reaches or exceeds the threshold (15%), the kill switch triggers.

The drawdown monitor also feeds into the dashboard, giving the operator a real-time view of how deep the portfolio is in a drawdown and how close it is to the kill switch threshold.

**Post-Trade Checks**

After a trade is executed, the risk checker runs again to verify that the trade did not push the portfolio past any limits. This catches edge cases where a trade appeared safe before execution but, due to slippage or price movement during execution, resulted in a portfolio state that violates risk limits.

---

## 11. Backtesting

### What Is Backtesting?

Backtesting is the process of testing a trading strategy on historical data to see how it would have performed in the past. It is like a flight simulator for trading -- you get to practice and evaluate your approach without risking real money.

However, backtesting comes with a major caveat: past performance does not guarantee future results. A backtest can tell you "this strategy would have worked over the past two years" but cannot promise "it will work over the next two years." This is why QuantFlow uses multiple backtesting approaches and robustness tests to build confidence.

### Vectorized vs. Event-Driven Backtesting

QuantFlow implements two different backtest engines:

**Vectorized Backtesting (Fast, Approximate)**

In vectorized backtesting, all calculations are done at once using array operations. Think of it like calculating a spreadsheet: you fill in all the formulas for every row simultaneously. This is extremely fast -- it can process years of data in seconds -- but it makes simplifying assumptions. It assumes all orders are filled instantly at the closing price, there are no partial fills, and there is no latency between signal generation and execution.

Vectorized backtesting is ideal for rapid iteration during strategy development. You can test hundreds of parameter combinations quickly to find promising regions before running the more expensive event-driven backtest.

**Event-Driven Backtesting (Slow, Realistic)**

The event-driven engine processes each bar one at a time, in sequence, simulating the exact event flow that would happen in live trading:

1. **BAR_CLOSE** -- A new candle closes, updating market data
2. **SIGNAL** -- The strategy generates a trading signal based on current data
3. **ORDER** -- If the signal calls for a position change, an order is created
4. **FILL** -- The order is filled (possibly with delay and partial fills)

This is much slower because it processes bars sequentially (each bar depends on the state after the previous one), but it captures realistic effects like:
- **Fill delay:** Orders may not be filled on the same bar they are submitted
- **Partial fills:** Not all of your order may be filled immediately (default is configurable)
- **Cost model interaction:** Costs depend on trade size relative to average daily volume

**Which to use?** Start with vectorized for exploration, then validate promising strategies with the event-driven engine.

### Cost Modeling

One of the biggest mistakes in backtesting is ignoring transaction costs. A strategy that looks profitable before costs may be a loser after costs. QuantFlow models several types of costs:

**Trading Fees**
Exchanges charge a fee on every trade, typically a small percentage of the trade value (e.g., 0.1% per trade on Binance). This seems tiny but adds up fast -- if you trade 500 times in a backtest, fees alone consume 0.5-1.0% of your capital per trade cycle.

**Slippage**
Slippage is the difference between the price you expected and the price you actually got. When you place a market order to buy, you push the price up slightly because you are consuming liquidity from the order book. The larger your order relative to the available liquidity, the more slippage you experience. QuantFlow models this as a function of trade size relative to average daily volume.

**Spread**
The bid-ask spread is the gap between the highest price a buyer is willing to pay (bid) and the lowest price a seller is willing to accept (ask). Every time you trade, you "cross" the spread, paying a small cost. In liquid markets (like BTC/USDT on Binance), the spread is tiny. In illiquid markets, it can be significant.

### Monte Carlo Simulation

Even after running a realistic backtest, how do you know the results are not just luck? Maybe the strategy happened to catch a few lucky trades that will not repeat. Monte Carlo simulation addresses this question by running the backtest thousands of times with randomized variations.

**What Is Monte Carlo Simulation?**

Named after the famous casino in Monaco, Monte Carlo simulation is a technique for understanding uncertainty by running many random experiments. Instead of asking "what happened?" it asks "what range of outcomes was plausible?"

**Block Bootstrap Resampling**

QuantFlow uses a technique called block bootstrap. It takes the actual daily returns from the backtest and randomly rearranges them -- but in blocks rather than individually. Blocks are used (default: 20 bars per block) because financial returns are not independent from one bar to the next. Today's return is correlated with yesterday's return (this is called autocorrelation). By shuffling blocks instead of individual returns, the simulation preserves these short-term correlations.

Each simulation produces a slightly different equity curve, and from the full set of simulations (default: 1000), QuantFlow computes:
- **Mean Sharpe ratio** -- the average risk-adjusted return across all simulations
- **5th percentile Sharpe ratio** -- the Sharpe ratio you would get in a "bad luck" scenario (only 5% of simulations did worse)
- **95th percentile Sharpe ratio** -- the "good luck" scenario
- **5th percentile total return** -- worst-case total return you should plan for
- **Max drawdown distribution** -- how bad drawdowns could get under different luck scenarios

If the 5th percentile Sharpe ratio is still positive, that is a strong signal that the strategy's edge is robust and not just luck.

**Parameter Perturbation**

In addition to resampling returns, QuantFlow also tests robustness by perturbing the strategy's parameters by up to 20% in each direction. If changing the RSI lookback period from 14 to 11.2 or 16.8 causes the strategy to collapse, it was probably overfit to the exact parameters -- a red flag. A robust strategy should degrade gracefully under small parameter changes.

---

## 12. Execution

### Paper Mode vs. Live Mode

QuantFlow has two execution modes, and paper mode is always the starting point.

**Paper Mode (Simulated Trading)**

In paper mode, no real money is involved. When the system generates a trade signal, the order manager simulates the execution: it immediately "fills" the order at the current price and updates an internal ledger of positions and equity. This lets you:
- Validate that the strategy works as expected in real-time market conditions
- Verify that all signals, risk checks, and position sizing behave correctly
- Build confidence before committing real capital
- Debug issues without financial consequences

Paper mode is the default. The system is designed so that flipping to live mode requires an explicit configuration change (setting `execution.mode: live` in the config file), preventing accidental live trading.

**Live Mode (Real Trading)**

In live mode, orders are sent to actual cryptocurrency exchanges (Binance or Coinbase) through their APIs via the ccxt library. Live mode adds complexity that paper mode does not have:
- Network latency (it takes time for orders to reach the exchange)
- Rate limiting (exchanges restrict how many requests you can make per minute)
- API outages (the exchange may be temporarily unreachable)
- Order rejection (the exchange may reject your order for various reasons)

The order manager handles all of these with retry logic (up to 3 retries) and timeout handling (120-second timeout per order).

### Order Lifecycle

Every order goes through a defined lifecycle:

1. **Created** -- The signal fusion and risk check pipeline produces a trade decision. An order object is created with a unique ID, symbol, side (buy/sell), quantity, and order type (market or limit).

2. **Submitted** -- The order is sent to the exchange (or simulated in paper mode).

3. **Filled / Partially Filled / Cancelled** -- The exchange reports back on the order's status.
   - **Filled** means the full quantity was executed.
   - **Partially filled** means only some of the quantity was executed (this happens when there is not enough liquidity at the desired price).
   - **Cancelled** means the order was not executed (e.g., the exchange rejected it).

4. **Recorded** -- The order's outcome is logged for monitoring and analysis.

### Partial Fills

In real markets, you cannot always buy or sell the exact quantity you want at the exact price you want. If you try to buy 10 BTC but there are only 7 BTC available at the current price, you get a partial fill of 7 BTC. The remaining 3 BTC either stay as an open order (for limit orders) or get filled at a slightly worse price (for market orders).

QuantFlow's event-driven backtest engine simulates partial fills with a configurable parameter (`partial_fill_pct`). The order manager in live mode tracks open orders and polls the exchange for status updates, handling partial fills gracefully by updating the portfolio state with whatever quantity was actually filled.

---

## 13. Model Persistence

### The Ephemeral Filesystem Problem

Cloud platforms like Railway run containers that are rebuilt on every deploy. Any file written inside the container — including trained ML model `.pkl` files on disk — disappears when the container restarts. Without a persistence strategy, the worker would re-train from scratch on every deploy, spending the first pipeline tick (up to 4 hours) without a usable model.

### The `model_artifacts` Table

QuantFlow solves this by storing serialized models directly in TimescaleDB. Migration 004 (`migrations/004_model_artifacts.sql`) creates:

```sql
CREATE TABLE IF NOT EXISTS model_artifacts (
    model_id   TEXT PRIMARY KEY,
    model_type TEXT NOT NULL,
    artifact   BYTEA NOT NULL,   -- pickled model binary
    metadata   JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

The `artifact` column holds the raw bytes from `pickle.dumps(model)`. Because TimescaleDB is backed by managed storage (Timescale Cloud), the data survives container restarts indefinitely.

### How It Works

`ModelRegistry` (in `packages/models/model_registry.py`) has two storage paths:

**Local disk (development)**
- `save(model, ...)` → writes `models/{model_id}/model.pkl` and `metadata.json`
- `load(model_id)` → reads from the same path
- Fast, but lost on Railway restart

**Database (production)**
- `save_to_db(engine, model, ...)` → pickles the model and upserts into `model_artifacts` using `ON CONFLICT (model_id) DO UPDATE`. This means re-training always overwrites the previous version cleanly.
- `load_from_db(engine, model_id)` → fetches the BYTEA, calls `pickle.loads()`, deserializes the metadata JSON

**On worker startup**, the signal pipeline calls `load_from_db()` first. If a saved model exists, training is skipped for that cycle and the pre-trained model is used immediately. This means a Railway redeploy costs zero retraining time.

### Model Retrain API

The API exposes two endpoints to manage the model lifecycle:

- `POST /api/model/retrain` — triggers a background retrain job (protected by `asyncio.Lock` so only one job runs at a time). Returns the retrain status immediately.
- `GET /api/model/status` — returns the current state: `not_trained`, `training`, or `ok` with the last retrain timestamp and metrics.

---

## 14. Monitoring, Alerting & Observability

QuantFlow has three observability layers: Prometheus metrics, Grafana dashboards, and Telegram alerts.

### Prometheus Metrics

`packages/monitoring/metrics_exporter.py` exports runtime gauges from the worker process to a Prometheus-compatible HTTP endpoint (default port 9090). Key metrics include:

- `quantflow_equity` — current portfolio equity in USD
- `quantflow_drawdown_pct` — current drawdown from peak (0.0–1.0)
- `quantflow_kill_switch_active` — 1 when kill switch is triggered, 0 otherwise
- `quantflow_signal_strength` — latest fused signal strength per symbol
- `quantflow_regime` — current HMM regime as a label
- `quantflow_orders_total` — cumulative order count by side and status
- `quantflow_risk_rejections_total` — count of orders blocked by risk checks

These are collected by the Prometheus server running as a Docker service and stored in its time-series database.

### Grafana Dashboard

`monitoring/grafana/dashboards/quantflow.json` defines a 7-panel dashboard provisioned automatically when Docker Compose starts. Panels:

| Panel | Type | What it shows |
|-------|------|---------------|
| Equity Over Time | Time series | Portfolio value (USD) |
| Drawdown Gauge | Gauge | Current drawdown vs. kill switch threshold |
| Active Signals | Stat | Current signal direction/strength per symbol |
| Regime | Stat | Current HMM regime |
| Orders/Hour | Time series | Order throughput rate |
| Kill Switch | Stat | Active/Inactive with color coding |
| Risk Rejections | Time series | Rate of pre-trade blocks |

The Grafana admin password reads from `${GRAFANA_ADMIN_PASSWORD:-admin}` (override via Docker `.env`). Prometheus is automatically configured as the data source via provisioning in `monitoring/grafana/datasources/`.

### Telegram Alerts

`packages/monitoring/alerting.py` provides `AlertManager` — a rule engine that fires human-readable notifications to a Telegram chat when trading conditions warrant attention.

**AlertSeverity** controls how often each alert can fire (cooldown):

| Severity | Cooldown | When to use |
|----------|----------|-------------|
| `CRITICAL` | None (fires every check) | Kill switch active |
| `HIGH` | 15 minutes | Drawdown approaching threshold (>10%) |
| `MEDIUM` | 60 minutes | Model drift detected |
| `LOW` | 120 minutes | Candle ingestion stalled |

**Routing:** Only `HIGH` and `CRITICAL` alerts are forwarded to Telegram. `LOW` and `MEDIUM` are logged only. This prevents alert fatigue for non-urgent conditions.

**Delivery:** `send_telegram()` uses Python's stdlib `urllib` (no `requests` dependency). It sends HTML-formatted messages to the configured `chat_id` via the Bot API. On any network error, it logs a warning and returns `False` — it never raises, so a Telegram outage cannot crash the worker.

**Configuration** (via environment variables):
```
TELEGRAM_BOT_TOKEN=<your bot token from @BotFather>
TELEGRAM_CHAT_ID=<your chat ID>
```

The worker's `health_check_task` calls `alert_manager.evaluate_all()` every 60 seconds.

---

## 15. The Dashboard

QuantFlow includes a 4-page web dashboard built with Next.js 15, React 19, and Tailwind CSS 4. It uses a terminal-inspired dark theme with an industrial aesthetic -- JetBrains Mono for numbers, Inter for labels, cyan/green/red accent colors on a near-black background. The layout is shared across all pages: a `SharedHeader` component provides the QUANT::FLOW branding, navigation bar, version number, candle count, and a LIVE/DEMO/OFFLINE status indicator. The frontend polls the FastAPI backend every 5-15 seconds for fresh data.

### Page 1: Dashboard (`/`)

The main overview page showing portfolio health at a glance.

**Metric Cards**
Six cards across the top display: Equity, Cash, Positions Value, Unrealized PnL, Realized PnL, and Drawdown. Each card has a Lucide icon, color-coding (green for positive PnL, red for negative, amber/red for dangerous drawdown levels), and the primary equity card pulses subtly to indicate the system is live.

**Signal Panel**
Shows the current trading signals for each asset in the universe (BTC/USDT, ETH/USDT, SOL/USDT), including the direction (long/short/flat), signal strength, confidence level, and which components (technical, ML, sentiment) contributed to the signal. This lets you understand not just what the system wants to do, but why.

**Equity Chart**
A Recharts-powered area chart showing the portfolio's equity over time. The chart uses a green/red gradient fill -- green when equity is above the starting point, red when below. It supports time range selection (1W, 1M, 3M, All) and updates every 15 seconds by polling the `/api/equity-history` endpoint. This is the most important chart on the dashboard because it immediately shows whether the system is making or losing money.

**Positions Table**
A table listing all current positions: which assets are held, the side (long/short), quantity, entry price, current price, unrealized profit/loss, and PnL percentage. This answers "what are we currently exposed to?"

**Performance Card**
Below the positions table sits a 4-column analytics card populated from `GET /api/portfolio/analytics` (polled every 30 seconds). It shows:
- **Daily return** — portfolio return since midnight UTC, green if positive, red if negative
- **Weekly return** — portfolio return over the last 7 days
- **Sharpe (30d)** — rolling 30-day Sharpe ratio computed from equity snapshots in the `portfolio_snapshots` table
- **Max DD** — maximum drawdown observed across the entire history

All four values show `—` while insufficient history exists (less than 2 equity snapshots). The card only renders when the `analytics` endpoint returns a non-null result.

**Risk Panel**
Displays current risk metrics including: current drawdown with a visual progress bar showing proximity to the kill switch threshold, max drawdown, portfolio volatility, Sharpe ratio, concentration percentage, and kill switch status (active/inactive).

**Regime Detection**
A panel showing the current market regime detected by the HMM (trending, mean-reverting, or choppy) with a confidence percentage, regime badge, and model details. This is displayed prominently because the regime drives the entire signal weighting system.

**System Info**
A small panel at the bottom showing execution mode (PAPER), timeframe (4H), and server uptime.

### Page 2: Trades (`/trades`)

The trading page combines order entry with trade history.

**Order Entry Panel**
A "Place Order" form at the top of the page, clearly marked as "Paper Mode." The form includes:
- **Symbol selector** -- dropdown for BTC/USDT, ETH/USDT, SOL/USDT, with the current price displayed below
- **Side** -- BUY (green) / SELL (red) toggle buttons
- **Quantity** -- numeric input
- **Type** -- Market or Limit order dropdown
- **Price** -- shows estimated market price for market orders, or a manual input field for limit orders
- **Place Order button** -- submits via `POST /api/orders` to the backend's `OrderManager(paper_mode=True)`

Orders are filled instantly in paper mode. Success/error feedback appears below the form. Placed orders are prepended to the local trade list (React state) so they appear immediately without waiting for the next poll.

**Summary Cards**
Four cards showing: Total Trades, Net PnL, Win Rate, and Average Fees for the currently filtered trade set.

**Filter Bar**
Filter buttons for: All, Winners (PnL > 0), Losers (PnL < 0), and per-symbol (BTC/USDT, ETH/USDT, SOL/USDT).

**Trade History Table**
A detailed table with columns for Time, ID, Symbol, Side, Quantity, Price, PnL, Fees, and Regime. Each row is color-coded: buy sides in green, sell in red, PnL colored by sign, and regime names colored by type (trending/mean-reverting/choppy).

### Page 3: Backtest (`/backtest`)

The backtesting page lets you run real backtests against the vectorized engine and compare strategies.

**Run Backtest Form**
A parameter form with:
- **Symbol** -- BTC/USDT, ETH/USDT, or SOL/USDT
- **Strategy** -- Buy & Hold, MA Crossover (20/50), or Mean Reversion (z-score)
- **Lookback** -- 90 days, 180 days, 1 year, or 2 years
- **Capital** -- initial capital amount (default $100,000)
- **Run Backtest button** -- submits via `POST /api/backtest/run`

When running, an indeterminate progress bar animates below the form. The backend fetches real candle data from TimescaleDB if available; otherwise it generates synthetic candles using Geometric Brownian Motion (GBM). The actual `run_vectorized_backtest()` engine runs the math -- the backtest logic is real even when the candles are synthetic.

**Best Strategy Hero**
A highlighted card showing the top-performing strategy by Sharpe ratio from all results (both live runs and demo comparisons).

**Strategy Comparison Table**
All results ranked by Sharpe ratio, showing: rank, strategy name, total return, Sharpe ratio, max drawdown, total trades, and hit rate. Live-run results are tagged with a cyan "LIVE" badge to distinguish them from the pre-loaded demo comparisons.

**Methodology Note**
A footer card explaining the backtesting methodology: walk-forward validation with purged k-fold (gap=3, embargo=2), cost model details, and triple-barrier label parameters.

### Page 4: Settings (`/settings`)

The configuration page with editable and read-only sections.

**Editable Sections**

Three sections can be modified and saved:

- **Universe** -- toggle trading symbols on/off (pill buttons for BTC/USDT, ETH/USDT, SOL/USDT, AVAX/USDT, DOGE/USDT), select timeframe (1h/4h/1d), set lookback days
- **Risk Management** -- sliders for vol target (5-30%), max drawdown / kill switch threshold (5-25%), max position size (10-50%), and a numeric input for minimum trade USD
- **Execution** -- paper/live mode toggle (live mode is highlighted in red as a warning), order timeout, max retries

All editable settings persist to `config/default.yaml` via `PATCH /api/config`. The Save button writes the YAML file on the backend. The Reset button reverts to the last saved values.

**Exchange API Keys Section**
A new section lets you enter Binance API key and secret, then click "Test Connection." This calls `POST /api/config/exchange/test`, which attempts a lightweight authenticated request (e.g., fetch account balance) and returns `{"status": "ok", "message": "..."}` or an error. The keys are **not persisted** to disk — they are session-scoped React state only. This protects against accidental credential storage in `config/default.yaml`. To use live trading, set `BINANCE_API_KEY` and `BINANCE_API_SECRET` as environment variables.

**Model Retraining Section**
Shows the current model status fetched from `GET /api/model/status` on page load:
- **Not trained** — no model has been trained yet (first startup)
- **Training** — a retrain job is currently running in the background
- **OK** — model is ready, shows the timestamp of the last retrain

The "Retrain Model" button calls `POST /api/model/retrain`. The response updates the status display immediately. A retrain job runs the full walk-forward training pipeline on the available candle data in the DB, saves the result to `model_artifacts` via `save_to_db()`, and marks status as `ok`. The `asyncio.Lock` in the API prevents two concurrent retrain jobs from running simultaneously.

**Read-Only Sections**

Three sections are displayed but not editable (they require code changes to modify safely):

- **Features** -- technical indicator parameters, normalization settings
- **Model** -- LightGBM hyperparameters, walk-forward configuration
- **Regime Detection** -- HMM states, transition thresholds

Each read-only section renders values with type-colored formatting: numbers in cyan, booleans in green/red, strings in white, arrays in brackets.

---

## 16. Data Sources & Demo Mode

### The Three-Tier Data Strategy

QuantFlow's API implements a graceful degradation pattern with three tiers:

1. **Database (LIVE)** -- When TimescaleDB is connected and tables contain data, the API serves real candles, signals, positions, portfolio snapshots, risk metrics, and trades from the database. The header shows a green dot with "LIVE" and displays the candle count.

2. **Demo Fallback (DEMO)** -- When the API is running but the database is unavailable or tables are empty, every endpoint falls back to pre-generated demo data. The header shows an amber dot with "DEMO." This is the most common state during development.

3. **Offline (OFFLINE)** -- When the backend is completely unreachable, the frontend shows a red dot with "OFFLINE" and displays loading skeletons.

The fallback logic is simple: each endpoint calls its `_get_db_*()` helper, which returns `None` if the DB is unavailable or the query returns no rows. The endpoint then returns `db_result or demo_fallback`.

### How Demo Data Is Generated

At server startup, `_generate_demo_data()` runs once with `random.seed(42)`, producing a fixed set of demo data that is identical every time the server starts:

- **Equity curve** -- 540 data points (90 days of 4-hour bars) generated by a random walk with slight upward drift (mean return +0.03% per bar, volatility 1.2% per bar). Starting equity: $100,000.
- **Signals** -- 3 literal signal objects: BTC long (strength 0.72, confidence 0.85, trending), ETH short (strength -0.35, confidence 0.62, mean-reverting), SOL flat (strength 0.08, confidence 0.41, choppy).
- **Positions** -- 2 literal positions: BTC long 0.45 units at $96,420 entry, ETH short 3.2 units at $3,450 entry.
- **Portfolio** -- Computed from the equity curve endpoint and position values.
- **Trades** -- 50 pre-generated trades cycling through BTC/ETH/SOL with randomized prices, quantities, and PnL values.
- **Backtest comparisons** -- 5 hardcoded `BacktestSummary` objects representing the full system, buy & hold, MA crossover, no-regime, and no-sentiment variants.
- **Risk metrics** -- Derived from the equity curve's drawdown, with a Sharpe of 1.85 and kill switch inactive.
- **Regime** -- Set to "trending" with 0.85 confidence and a short history of regime changes.

### Demo Prices

`_DEMO_PRICES` is a constant dictionary used when the database has no candle data:

```
BTC/USDT: $98,150
ETH/USDT: $3,380
SOL/USDT: $182
```

These prices are used for paper order fills and as fallback values for the `/api/prices` endpoint.

### Synthetic Candles for Backtests

When you run a backtest via the UI and the database has fewer than 50 candles for the selected symbol, the API generates synthetic candles using `_generate_demo_candles()`. This function uses Geometric Brownian Motion (GBM):

- Seeded by `hash(symbol) + lookback_days` for reproducibility
- Starts at 85% of the demo price (so the chart trends upward)
- Slight upward drift: μ = 0.0002 per bar
- Per-bar volatility: σ = 0.015
- Generates OHLCV data with realistic high/low spreads

The important point: the backtest **math is real** (the vectorized engine runs with cost models, metrics, and benchmark comparisons), only the input candles are synthetic.

### What Persists vs. What Is Session-Only

| Data | Persists across refreshes? | Why |
|------|---------------------------|-----|
| Demo dashboard data | Yes | Same seed 42 generates identical data every server start |
| Demo comparison backtests | Yes | Hardcoded constants |
| Placed paper orders (Trades page) | **No** -- lost on page refresh | Stored in React state (`localTrades`), not written to DB in demo mode |
| Live backtest runs | **No** -- lost on server restart | Stored in Python list (`_backtest_history`) in server memory |
| Settings changes | **Yes** | Written to `config/default.yaml` on disk via `save_config()` |
| Orders placed with DB running | **Yes** | Written to the `orders` table in TimescaleDB |

---

## 17. Running the System

### Quick Start (Demo Mode -- No Database Required)

```bash
# 1. Start the backend API
PYTHONPATH=. uv run uvicorn apps.api.main:app --reload --port 8000

# 2. In a separate terminal, start the frontend
cd frontend && npm run dev

# 3. Open http://localhost:4000
```

The frontend runs on port 4000 and proxies all `/api/*` requests to the backend on port 8000 via Next.js rewrites. Without a database, you will see:
- An **amber "DEMO"** indicator in the header
- Pre-generated portfolio metrics, equity chart, signals, positions, and trades
- Fully functional order entry (paper mode) -- orders fill instantly but do not survive page refresh
- Fully functional backtest runner -- uses synthetic GBM candles, real backtest math
- Settings that save and persist to `config/default.yaml`

### With TimescaleDB (Real Candle Data)

```bash
# 1. Start the database (requires Docker Desktop)
docker compose -f docker-compose.dev.yml up -d

# 2. Run migrations to create all 11 tables
uv run python scripts/migrate.py

# 3. Backfill real candles from Binance (one-time, data persists in Docker volume)
PYTHONPATH=. uv run python scripts/backfill_candles.py --no-sandbox

# 4. Start backend and frontend as above
PYTHONPATH=. uv run uvicorn apps.api.main:app --reload --port 8000
cd frontend && npm run dev
```

With the database connected, you will see:
- A **green "LIVE"** indicator in the header with a candle count (e.g., "13,140 candles")
- Real BTC/ETH/SOL prices from the latest candles
- Backtests running on real historical data instead of synthetic candles
- Orders persisted to the `orders` table

Note: Even with the database, most dashboard data (signals, positions, portfolio, risk, regime) will still show demo values until the worker process is wired to write computed results back to the database. The candles and prices are real; the derived analytics are not yet.

### With Grafana + Prometheus (Full Observability Stack)

```bash
# Starts TimescaleDB, Redis, Prometheus, and Grafana
docker compose up -d

# Visit Grafana at http://localhost:3000 (admin / admin)
# QuantFlow dashboard is auto-provisioned — no manual setup needed
```

Set `GRAFANA_ADMIN_PASSWORD` in your `.env` file to change the default password.

### Against Timescale Cloud (Production Database)

```bash
# Set these env vars (or add to .env)
export POSTGRES_HOST=your-host.tsdb.cloud.timescale.com
export POSTGRES_PORT=30237
export POSTGRES_DB=tsdb
export POSTGRES_USER=tsdbadmin
export POSTGRES_PASSWORD=<your-password>
export POSTGRES_SSLMODE=require

# Apply all 4 migrations (idempotent — safe to run multiple times)
uv run python scripts/migrate.py
```

`scripts/migrate.py` reads the same `POSTGRES_*` env vars as the rest of the application via `load_config()`. It discovers all `migrations/*.sql` files in alphabetical order (001 → 004), splits each file into individual statements, and executes them with one connection commit per file. Failed files are reported but do not abort subsequent files. The script exits with code 1 if any migration fails.

### Running Tests

```bash
uv run pytest tests/ -v
```

Currently 72 tests passing. The Binance integration test is excluded from CI (geo-blocked on GitHub runners) but can be run locally.

---

## 18. Glossary

**AlertManager** -- The rule engine in `packages/monitoring/alerting.py` that evaluates alert conditions on a schedule and dispatches notifications to Telegram for HIGH/CRITICAL severity events.

**AlertSeverity** -- An enum that controls how often each alert can fire: CRITICAL (no cooldown), HIGH (15 min), MEDIUM (60 min), LOW (120 min).

**Alpha** -- Returns generated above a benchmark (like "beating the market"). If the market returns 10% and your strategy returns 13%, your alpha is 3%.

**ATR (Average True Range)** -- A measure of price volatility that accounts for gaps between candles. See Section 3.

**Autocorrelation** -- The tendency of a data point to be correlated with nearby data points. In finance, today's return is somewhat predictive of tomorrow's return.

**Backtest** -- Testing a trading strategy on historical data to evaluate its performance. See Section 11.

**Barrier (in triple-barrier labeling)** -- A price level or time limit that, when hit, determines the trade outcome label for ML training. See Section 5.

**Block Bootstrap** -- A resampling technique that shuffles blocks of data (rather than individual data points) to preserve autocorrelation structure. See Section 11.

**Bollinger Bands** -- Price bands set at a fixed number of standard deviations above and below a moving average. See Section 3.

**Candle (Candlestick)** -- A summary of price action over a time period, containing four prices (open, high, low, close) and volume.

**ccxt** -- An open-source library that provides a unified interface to many cryptocurrency exchanges.

**Choppy (Regime)** -- A market state characterized by high volatility and no clear directional trend. The most dangerous regime to trade in. See Section 7.

**Confidence Score** -- A number between 0 and 1 representing how certain the model is about its prediction. Derived from the IQR of quantile predictions. See Section 4.

**Concentration Limit** -- The maximum percentage of the portfolio that can be allocated to a single position. Default: 30%.

**Drawdown** -- The decline from a portfolio's peak equity to its current value, expressed as a percentage.

**Embargo Period** -- A gap after the test window in walk-forward validation that prevents data leakage into the next fold's training set. See Section 6.

**Exponential Decay** -- A mathematical function where a value decreases by a fixed proportion over each time period. Used for sentiment time decay.

**Feature** -- A measurable property of the data that is used as input to a machine learning model (e.g., RSI, ATR, VWAP deviation).

**Gradient Boosting** -- A machine learning technique that builds an ensemble of simple models (usually decision trees), each correcting the errors of the previous ones.

**Grafana** -- An open-source observability platform. QuantFlow provisions a 7-panel dashboard automatically via `monitoring/grafana/` volume mounts in Docker Compose.

**HMM (Hidden Markov Model)** -- A statistical model for systems that transition between unobservable states over time. Used for regime detection. See Section 7.

**IQR (Interquartile Range)** -- The difference between the 75th and 25th percentiles of a distribution. Used as an uncertainty measure in QuantFlow.

**Kill Switch** -- An automatic safety mechanism that halts all trading when the portfolio drawdown exceeds 15%. Requires manual reset. See Section 10.

**Label** -- The "correct answer" that a machine learning model is trained to predict. In QuantFlow, labels are 0 (down), 1 (neutral), or 2 (up).

**LightGBM** -- A fast, efficient gradient boosting framework developed by Microsoft. See Section 4.

**Log Return** -- The natural logarithm of the ratio of two consecutive prices. See Section 3.

**Long** -- A position that profits when the price goes up. "Going long" means buying an asset.

**Lookahead Bias** -- Accidentally using future information to make past decisions. The most common and dangerous error in backtesting. See Section 6.

**Market Order** -- An order to buy or sell immediately at the best available price.

**model_artifacts** -- A PostgreSQL table (created in migration 004) that stores pickled ML model binaries as BYTEA alongside JSONB metadata. Enables model survival across container restarts on Railway.

**Mean-Reverting (Regime)** -- A market state where prices tend to return to a central level after moving away from it. See Section 7.

**Mixture of Experts (MoE)** -- A model architecture where multiple specialized sub-models (experts) are combined using a gating mechanism. See Section 8.

**Monte Carlo Simulation** -- A technique for understanding uncertainty by running many randomized experiments. See Section 11.

**Overfitting** -- When a model memorizes the training data too closely and fails to generalize to new data.

**Paper Trading** -- Simulated trading with no real money, used to test strategies in live market conditions. See Section 12.

**Partial Fill** -- When only a portion of an order is executed, typically due to insufficient liquidity.

**Purge Gap** -- A buffer of bars between training and test data in walk-forward validation that prevents label leakage. See Section 6.

**Quantile** -- A value that divides a probability distribution at a specific percentage point. The 25th percentile (q25) means 25% of values fall below this point.

**Quantile Regression** -- A type of regression that predicts specific percentiles of the outcome distribution, rather than the mean. See Section 4.

**Realized Volatility** -- The actual historical volatility of an asset, measured from observed price changes. See Section 3.

**Regime** -- A distinct behavioral state of the market (trending, mean-reverting, or choppy). See Section 7.

**RSI (Relative Strength Index)** -- An oscillator that measures the speed and magnitude of recent price changes, scaled 0-100. See Section 3.

**Sharpe Ratio** -- A measure of risk-adjusted return: (average return - risk-free rate) / standard deviation of returns. A Sharpe above 1.0 is generally considered good.

**Short** -- A position that profits when the price goes down. "Going short" means selling an asset you do not own (or betting against it).

**Signal** -- A trading recommendation produced by the system, including direction (long/short/flat), strength, and confidence.

**Slippage** -- The difference between the expected trade price and the actual execution price. See Section 11.

**Spread (Bid-Ask)** -- The difference between the highest buy price and lowest sell price in the order book.

**Staleness** -- When market data is older than a defined threshold and may no longer reflect current conditions.

**Telegram Bot** -- A chat bot used to deliver HIGH and CRITICAL alerts to a designated Telegram chat. Configured via `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables.

**TimescaleDB** -- A time-series database extension for PostgreSQL, used to store candle data and trade history.

**Trending (Regime)** -- A market state characterized by clean, directional price movement with relatively low volatility. See Section 7.

**Triple-Barrier Labeling** -- A method for creating ML training labels based on which exit condition (profit target, stop loss, or time limit) is hit first. See Section 5.

**VWAP (Volume-Weighted Average Price)** -- The average price of an asset weighted by the volume traded at each price level. See Section 3.

**Volatility** -- A statistical measure of how much prices fluctuate. Higher volatility means bigger price swings.

**Volatility Targeting** -- A position sizing method that adjusts trade size inversely to volatility, aiming to keep portfolio risk constant. See Section 10.

**Walk-Forward Validation** -- A method for testing ML models on sequential time-series data without lookahead bias. See Section 6.
