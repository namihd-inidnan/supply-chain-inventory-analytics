# Insights and Recommendations

Findings from the Supply Chain Inventory Analytics project. All numbers come from the **synthetic dataset** (Nov 2025 to Oct 2026) and are calculated in PostgreSQL (queries in `sql/09_insight_queries.sql`) and Power BI. Stock and ageing figures are as of **31 Oct 2026**.

**Definitions**

- **Item** = one product in one warehouse (600 product-warehouse pairs in total).
- **Out of stock** = stock on hand is 0.
- **Low stock** = stock above 0 but below the item's safety stock.
- **Excess stock** = stock larger than the item's total sales in the last 90 days.
- **Ageing stock** = stock received more than 90 days ago (FIFO batches).

## Headline numbers

| Metric | Value |
|---|---|
| Total revenue (12 months) | ₹10.03 crore (₹100,313,649) |
| Inventory value (31 Oct 2026) | ₹44.8 lakh (₹4,479,618) |
| Out-of-stock items | 27 |
| Low-stock items | 34 |
| Excess-stock items | 48, worth ₹4.90 lakh (₹490,364), 10.9% of inventory value |
| Ageing stock (over 90 days) | ₹3.04 lakh (₹304,064), 6.8% of inventory value |

## Priority actions

1. Replenish the 10 items in finding 2 first. They put about ₹11,200 of daily sales at risk, and four of them have no stock at all.
2. Stop reordering excess items in Mumbai, Kolkata and Bengaluru, starting with Household and Personal Care.
3. Raise safety stock before the October to November peak, and review reorder points item by item.

---

## Findings

### 1. Excess stock is concentrated in three warehouses and two categories
- **Finding:** Excess stock is ₹490,364 across 48 items. Mumbai (₹135,441), Kolkata (₹113,866) and Bengaluru (₹113,402) hold 74% of it. Household (₹170,714) and Personal Care (₹96,245) together hold 54%.
- **Why it matters:** Cash is tied up in stock that will not sell for more than 90 days.
- **Recommendation:** Pause reorders on the excess items, starting with Household in Mumbai. Review their order quantities, since the problem is concentrated rather than spread across the whole range.

### 2. A small set of fast-selling items is short of stock
- **Finding:** 34 items are below safety stock and 27 are out of stock. The top 10 low-stock items, ranked by average daily sales times price, put about ₹11,212 of sales per day at risk. Eight of the 10 are in Mumbai or Bengaluru, and four have zero stock (Besan 1kg in Kolkata, Mouthwash 250ml in Mumbai, Electrolyte Drink 500ml in Bengaluru, and Whole Wheat Atta in Bengaluru). The biggest single item is UrbanCart Besan 1kg in Mumbai: 7 units on hand against a safety stock of 21, selling 5.4 units a day.
- **Why it matters:** These items sell quickly, so each day without stock is lost revenue.
- **Recommendation:** Place replenishment orders for these 10 items first. Besan 1kg and Cheese Spread 180g each appear in two warehouses, so check their reorder settings across the network.
- **Note:** "Daily revenue at risk" uses list price and the 90-day average, so it is an estimate and ignores discounts.

### 3. Excess and shortage exist in the same warehouses
- **Finding:** Mumbai has the most excess items (12) and also four of the top 10 shortage items. Bengaluru has nine excess items and four shortage items.
- **Why it matters:** The issue is not that a warehouse holds too much or too little overall. Stock is wrong at item level, with too much of some items and too little of others.
- **Recommendation:** Set reorder points and quantities per item and warehouse, based on recent demand, rather than adjusting a whole warehouse up or down.

### 4. Ageing stock sits mostly in Household and Personal Care
- **Finding:** ₹304,064 of stock (6.8% of inventory value) is older than 90 days. Household (₹101,657) and Personal Care (₹95,435) make up 65% of it, and Packaged Foods has the least (₹7,323).
- **Why it matters:** Ageing stock risks write-offs and markdowns, and the same two categories also lead the excess-stock list.
- **Recommendation:** Plan clearance or promotions for the oldest batches in these categories, and stop reordering them until stock falls.
- **Note:** The dataset does not model shelf life, so ageing here means time in the warehouse, not expiry.

### 5. Demand peaks around October and November
- **Finding:** Monthly revenue peaks in Nov 2025 (₹10.29M). It is lowest in Feb 2026 (₹6.72M), about a third lower than the peak, partly because February is a short month. Per day, July is the lowest. Revenue in Oct 2026 is 21.8% higher than in Sep 2026, and there is a smaller rise in May.
- **Why it matters:** Reorder points set from average demand will fall short in the peak months.
- **Recommendation:** Raise safety stock and order earlier ahead of the October to November peak, and lower them in the slow months of February and July.
- **Note:** The dataset covers a single year, so these patterns cannot be confirmed as repeating. Seasonal effects were also built into the data generator, so this finding shows the dashboard picks up seasonality, not a real market trend.

### 6. Supplier delays vary widely, but do not explain stockouts
- **Finding:** On-time delivery ranges from 69.1% (Supplier 12) to 97.5% (Supplier 04). Suppliers 12, 06 and 03 are on time less than 75% of the time and average 1.2 to 1.4 days late. Across the 12 suppliers there is almost no relationship between on-time rate and stockout days (correlation about 0.04). For example, Supplier 10 has the most stockout days (1,439) at 79.3% on time, while Supplier 03, one of the least reliable, has only 298.
- **Why it matters:** Fixing late suppliers alone will not remove stockouts. Reorder timing and quantities appear to matter more.
- **Recommendation:** Add a delivery buffer to the lead time for Suppliers 12, 06 and 03, and review reorder points for the items behind Supplier 10's stockout days.
- **Note:** Stockout days are not adjusted for how many items each supplier covers, so this is a rough comparison. The dataset also deliberately includes badly managed items, which drives some stockouts by design.

---

## Supporting observations

- **Inventory turnover** is similar across warehouses: Panipat 18.35, Mumbai 18.25, Kolkata 17.24, Bengaluru 16.70 and Hyderabad 16.39. That is about 20 to 22 days of stock on hand. Hyderabad is the lowest, but the gap is small, so turnover by warehouse does not point to a clear problem.
- **Gross margin by category** is narrow, from 15.2% (Packaged Foods) to 17.4% (Beverages), with about 16.2% overall. Grocery & Staples is the largest category (₹23.6M, 23.5% of revenue). Household has the most excess and ageing stock with a slightly below-average margin (15.8%).

## Validation

- Total revenue is ₹100,313,649 in both SQL (after removing duplicates) and Power BI.
- Total inventory value is ₹4,479,618 from the month-end snapshots and from the batch table, which come from separate tables.
- Excess stock adds up to ₹490,364 by warehouse and by category.

## Limitations

- The data is **synthetic** and covers one year, so patterns may not hold for a real business.
- Seasonality and poorly managed items were **built into the data generator**, so some findings (such as seasonality and the item-level shortages) reflect that design.
- The excess-stock rule (more than 90 days of cover) is a simple threshold. Real policies vary by product.
- Ageing is calculated at a fixed date (31 Oct 2026), with FIFO batches and no shelf-life or expiry.
- Revenue at risk uses list price and the 90-day average, so it is an estimate.
- Supplier comparisons are not adjusted for the number of items each supplier covers.
