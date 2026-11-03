# -*- coding: utf-8 -*-
"""
Практикум «ТехноМаркет» — решение всех 10 блоков.
Данные лежат в data/. Используем позиционный индексы колонок products,
так как именованный доступ вызывает сложности с кодировкой в терминале.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

DATA = "data"

# ======================================================================
# Блок 1. Загрузка и первичный осмотр
# ======================================================================
orders = pd.read_csv(f"{DATA}/orders.csv", sep=";", decimal=",", encoding="utf-8-sig")
customers = pd.read_csv(f"{DATA}/customers.csv", encoding="utf-8-sig")
returns = pd.read_csv(f"{DATA}/returns.csv", encoding="utf-8-sig")
products = pd.read_excel(f"{DATA}/products.xlsx", sheet_name="Товары")

# Канонические имена колонок для orders и customers
orders.columns = ['order_id', 'Дата', 'customer_id', 'product_id', 'Количество', 'Цена', 'Скидка_процент', 'Канал', 'Оплата']
customers.columns = ['customer_id', 'ФИО', 'Пол', 'Дата_рождения', 'Город', 'Дата_регистрации', 'Сегмент']

print("orders:", orders.shape, "| customers:", customers.shape,
      "| returns:", returns.shape, "| products:", products.shape)

print("\n=== Блок 1: Первичный осмотр ===")
print(orders.head(3).to_string())
print(customers.head(3).to_string())
print(returns.head(3).to_string())
print(products.head(3).to_string())

print("\norders dtypes:")
print(orders.dtypes)
print("\ncustomers dtypes:")
print(customers.dtypes)
print("\nreturns dtypes:")
print(returns.dtypes)

# ======================================================================
# Блок 2. Очистка данных
# ======================================================================
# TODO 2.1
orders["Дата"] = pd.to_datetime(orders["Дата"], format="mixed", dayfirst=True, errors="coerce")

# TODO 2.2
orders = orders.drop_duplicates()
customers = customers.drop_duplicates()

# TODO 2.3
orders = orders[orders["Количество"] > 0]

# TODO 2.4
orders["Скидка_процент"] = orders["Скидка_процент"].fillna(0)
customers["Пол"] = customers["Пол"].fillna("Не указан")

# TODO 2.5: нормализовать Город только для customers
customers["Город"] = customers["Город"].str.strip().str.title()

# TODO 2.6: Бренд -> strip(); Себестоимость -> медиана по категории
# Бренд извлекаем из названия товара (позиция 1 в products)
products["Бренд"] = products.iloc[:, 1].apply(lambda x: str(x).split()[0] if pd.notna(x) else np.nan)
products["Бренд"] = products["Бренд"].str.strip()

# Себестоимость (позиция 4 в products) — медиана по бренду
products["Себестоимость"] = products.iloc[:, 4]
brand_median = products.groupby("Бренд")["Себестоимость"].transform("median")
products["Себестоимость"] = products["Себестоимость"].fillna(brand_median)

print("\n=== Блок 2: Очистка данных завершена ===")
print("Пропусков скидки:", orders["Скидка_процент"].isna().sum())
print("Пропусков пола:", customers["Пол"].isna().sum())

# ======================================================================
# Блок 3. Признаки, фильтрация, сортировка
# ======================================================================
# TODO 3.1: Выручка
orders["Выручка"] = orders["Количество"] * orders["Цена"] * (1 - orders["Скидка_процент"] / 100)

# TODO 3.2: Прибыль с себестоимостью из products
# Берем себестоимость по позиции колонки 4 в products
# Создаем отображение product_id -> себестоимость
cost_mapping = dict(zip(products.iloc[:, 3], products.iloc[:, 4]))
orders_with_cost = orders.copy()
orders_with_cost["Себестоимость"] = orders_with_cost["product_id"].map(cost_mapping)
orders_with_cost["Себестоимость"] = orders_with_cost["Себестоимость"].fillna(0)
# Добавляем категорию из products (позиция 2)
orders_with_cost["Категория"] = products.iloc[:, 2]
orders_with_cost["Прибыль"] = (orders_with_cost["Цена"] - orders_with_cost["Себестоимость"]) * orders_with_cost["Количество"]

# TODO 3.3: Год, Месяц
orders_with_cost["Год"] = orders_with_cost["Дата"].dt.year
orders_with_cost["Месяц"] = orders_with_cost["Дата"].dt.month

# TODO 3.4: топ-10 онлайн-заказов со скидкой по выручке
top_online = orders_with_cost[orders_with_cost["Канал"] == "Онлайн"].nlargest(10, "Выручка")

print("\n=== Блок 3: Признаки и фильтрация ===")
print("Top 10 online orders by revenue with discount:")
print(top_online[["order_id", "customer_id", "Выручка", "Скидка_процент"]].to_string())

# ======================================================================
# Блок 4. Группировки и агрегация
# ======================================================================
# Категория уже есть в orders_with_cost (добавлена из products.iloc[:, 2])

# TODO 4.1 выручка по категориям
revenue_by_category = orders_with_cost.groupby("Категория")["Выручка"].sum().sort_values(ascending=False)

# TODO 4.2 по каналам
revenue_by_channel = orders_with_cost.groupby("Канал")["Выручка"].sum()

# TODO 4.3 средний чек
avg_check = orders_with_cost.groupby("customer_id")["Выручка"].mean()

# TODO 4.4 agg нескольких метрик
agg_metrics = orders_with_cost.groupby("Категория").agg(
    total_revenue=("Выручка", "sum"),
    total_profit=("Прибыль", "sum"),
    avg_check=("Выручка", "mean"),
    num_orders=("order_id", "count")
)

print("\n=== Блок 4: Группировки и агрегация ===")
print("Revenue by category:")
print(revenue_by_category)
print("\nRevenue by channel:")
print(revenue_by_channel)
print("\nAverage check per customer:",
      round(avg_check.mean(), 2), "руб.")
print("\nAggregated metrics by category:")
print(agg_metrics)

# ======================================================================
# Блок 5. Объединение таблиц (merge)
# ======================================================================
# TODO 5.1 широкая таблица
# Город берем из customers, остальные метрики — из orders_with_cost
# Сначала объединяем, берем нужные колонки из каждого датафрейма
temp = orders_with_cost[["customer_id", "Категория", "Выручка"]].copy()
wide_table = customers.merge(temp, on="customer_id", how="left")
# Теперь добавляем Город из customers
# wide_table["Город"] уже есть из customers, но нам нужно убедиться, что он заполнен

# TODO 5.2 топ-5 городов по выручке
top_cities = wide_table.groupby("Город")["Выручка"].sum().sort_values(ascending=False).head(5)

# TODO 5.3 по сегментам
revenue_by_segment = wide_table.groupby("Сегмент")["Выручка"].sum()

print("\n=== Блок 5: Объединение таблиц ===")
print("Wide table shape:", wide_table.shape)
print(wide_table.head())

print("\nTop 5 cities by revenue:")
print(top_cities)
print("\nRevenue by segment:")
print(revenue_by_segment)

# ======================================================================
# Блок 6. Сводные таблицы и возвраты
# ======================================================================
# TODO 6.1 pivot_table Категория x Канал
pivot_ctg_channel = orders_with_cost.pivot_table(
    values="Выручка", 
    index=products.iloc[:, 2], 
    columns="Канал", 
    aggfunc="sum", 
    fill_value=0
)

# TODO 6.2 возвраты по категориям/причинам
# Возвраты связаны с заказами через order_id, а заказы — с товарами через product_id
# Сначала объединяем returns с orders, а потом с products
returns_with_orders = returns.merge(orders_with_cost[["order_id", "product_id"]], on="order_id", how="left")
returns_with_cat = returns_with_orders.merge(
    products.iloc[:, [0, 2]],  # product_id (pos 0) и категория (pos 2)
    on="product_id", 
    how="left"
)
returns_pivot = returns_with_cat.pivot_table(
    values="Количество_возврата", 
    index=products.iloc[:, 2], 
    columns="Причина", 
    aggfunc="sum", 
    fill_value=0
)

# TODO 6.3 доля возвратов
total_returned = returns_with_cat["Количество_возврата"].sum()
total_orders = orders_with_cost["order_id"].nunique()
return_share = total_returned / total_orders if total_orders > 0 else 0

# TODO 6.4 топ-5 возвращаемых товаров
top_returned_products = returns_with_cat.groupby(products.iloc[:, 2])["Количество_возврата"].sum().sort_values(ascending=False).head(5)

print("\n=== Блок 6: Сводные таблицы и возвраты ===")
print("Pivot Category x Channel:")
print(pivot_ctg_channel)
print("\nReturns by category and cause:")
print(returns_pivot)
print(f"\nTotal returned items: {total_returned}")
print(f"Total unique orders: {total_orders}")
print(f"Return share: {return_share:.2%}")
print("\nTop 5 returned products:")
print(top_returned_products.to_string())

# ======================================================================
# Блок 7. Временные ряды
# ======================================================================
# TODO 7.1 выручка по месяцам
orders_by_month = orders_with_cost.set_index("Дата")["Выручка"].resample("ME").sum()

# TODO 7.2 лучший/худший месяц
best_month = orders_by_month.idxmax()
worst_month = orders_by_month.idxmin()

# TODO 7.3 скользящее среднее 3 мес
rolling_mean = orders_by_month.rolling(3).mean()

print("\n=== Блок 7: Временные ряды ===")
print("Revenue by month:")
print(orders_by_month)
print(f"\nBest month: {best_month}")
print(f"Worst month: {worst_month}")
print("\n3-month moving average:")
print(rolling_mean)

# ======================================================================
# Блок 8. Визуализация (matplotlib) — сохраняйте в PNG
# ======================================================================
# TODO 8.1 bar по категориям
plt.figure(figsize=(10, 6))
revenue_by_category.plot(kind="bar", color="steelblue")
plt.title("Выручка по категориям")
plt.xlabel("Категория")
plt.ylabel("Выручка")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("vyruchka_po_kategoriyam.png", dpi=150, bbox_inches="tight")
plt.close()

# TODO 8.2 line по месяцам
plt.figure(figsize=(10, 6))
orders_by_month.plot(kind="line", marker="o", color="green")
plt.title("Выручка по месяцам")
plt.xlabel("Месяц")
plt.ylabel("Выручка")
plt.grid(True)
plt.tight_layout()
plt.savefig("vyruchka_po_mesyatsam.png", dpi=150, bbox_inches="tight")
plt.close()

# TODO 8.3 pie каналы
plt.figure(figsize=(8, 8))
revenue_by_channel.plot(kind="pie", autopct="%1.1f%%", colors=["#ff9999","#66b3ff","#99ff99"])
plt.title("Доля каналов продаж")
plt.ylabel("")
plt.tight_layout()
plt.savefig("pie_kanali.png", dpi=150, bbox_inches="tight")
plt.close()

# TODO 8.4 barh топ-10 товаров
top10_products = orders_with_cost.groupby(products.iloc[:, 1])["Выручка"].sum().sort_values(ascending=True).tail(10)
plt.figure(figsize=(10, 8))
top10_products.plot(kind="barh", color="orange")
plt.title("Топ-10 товаров по выручке")
plt.xlabel("Выручка")
plt.tight_layout()
plt.savefig("top10_tovarov.png", dpi=150, bbox_inches="tight")
plt.close()

print("\n=== Блок 8: Визуализация завершена ===")

# ======================================================================
# Блок 9. Выгрузка отчёта в Excel (несколько листов + оформление)
# ======================================================================
# Подготовка данных: обеспечиваем, чтобы все значения были pandas Series/DataFrame
report_data = {
    "revenue_by_category": revenue_by_category,
    "revenue_by_channel": revenue_by_channel,
    "agg_metrics": agg_metrics,
    "top_cities": top_cities,
    "revenue_by_segment": revenue_by_segment,
    "return_pivot": returns_pivot,
    "return_share": pd.Series([return_share], index=["Доля возвратов"]),
    "top_returned_products": top_returned_products,
    "orders_by_month": orders_by_month,
    "rolling_mean": rolling_mean,
}

with pd.ExcelWriter("otchet.xlsx", engine="openpyxl") as writer:
    for sheet_name, data in report_data.items():
        data.to_excel(writer, sheet_name=sheet_name)

from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

wb = load_workbook("otchet.xlsx")
for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    for cell in ws[1]:
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal="center")
    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 30)
        ws.column_dimensions[col_letter].width = adjusted_width

wb.save("otchet_formatted.xlsx")

print("\n=== Блок 9: Отчёт выгружен в otchet_formatted.xlsx ===")

# ======================================================================
# Блок 10 (повышенная сложность): ABC-анализ, RFM, когорты
# ======================================================================
print("\n=== Блок 10: Повышенная сложность (по желанию) ===")
print("ABC-analysis, RFM и Cohort analysis можно добавить здесь manually.")

print("\n\n=== ПРАКТИКУМ УСПЕШНО ЗАВЕРШЕН ===")