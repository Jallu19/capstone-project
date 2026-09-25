-- select_where_order_limit
SELECT title, price_inr FROM books WHERE in_stock = 1 ORDER BY price_inr DESC LIMIT 10;

-- distinct_categories
SELECT DISTINCT category_name FROM categories ORDER BY category_name;

-- price_between
SELECT title, price_gbp FROM books WHERE price_gbp BETWEEN 20 AND 40 ORDER BY price_gbp;

-- in_clause
SELECT title, rating FROM books WHERE category_id IN (SELECT category_id FROM categories WHERE category_name IN ('Travel', 'Mystery')) ORDER BY rating DESC LIMIT 10;

-- join_highest_rated
SELECT c.category_name, b.title, b.rating, b.price_inr FROM books b JOIN categories c ON b.category_id = c.category_id ORDER BY b.rating DESC, c.category_name LIMIT 10;

