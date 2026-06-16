"""
Noah Walton
IS303-A07

Book Market Analysis Pipeline

Inputs:
    - books.toscrape.com (5 pages of book listings scraped with requests + BeautifulSoup) # Get 100 books

Processes:
    - fetch_page(): fetches and parses one page of the site
    - scrape_books(): loops through multiple pages, collects book data
    - store_books(): saves each book to a SQLite database via Peewee, skips duplicates
    - analyze(): queries the database into a Pandas DataFrame and runs groupby analysis
    - visualize(): creates and saves a bar chart of average price by star rating

Outputs:
    - Printed analysis (total records, summary stats, groupby results, findings)
    - price_by_rating.png (bar chart saved to disk)
    - books.db (SQLite database file)
"""

import requests
from bs4 import BeautifulSoup
from peewee import SqliteDatabase, Model, CharField, FloatField, IntegerField
import pandas as pd
import matplotlib.pyplot as plt
import time
import os 

if os.path.exists("books.db"):
    os.remove("books.db")

db = SqliteDatabase("books.db")

class Book(Model):
    title = CharField(unique=True)   # unique=True prevent duplicates
    price = FloatField()
    rating = IntegerField()          # stored as number(1-5)
    availability = CharField()

    class Meta:
        database = db

def fetch_page(url):  # Fetch a single URL and return a BeautifulSoup object, or None on failure.
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    print(f"  Failed to fetch {url} (status {response.status_code})")
    return None

def scrape_books(num_pages=5):  #Scrape book listings from books.toscrape.com across multiple pages.
    word_to_num = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    base_url = "https://books.toscrape.com/catalogue/"
    books = []

    for page_num in range(1, num_pages + 1):
        url = base_url + f"page-{page_num}.html"
        print(f"Scraping page {page_num}: {url}")
        soup = fetch_page(url)
        if soup is None:
            continue
        for article in soup.find_all("article", class_="product_pod"):
            title = article.h3.a["title"]
            price_text = article.find("p", class_="price_color").get_text(strip=True)
            price = float(price_text.replace("£", "").replace("Â", "").strip())
            rating_word = article.find("p", class_="star-rating")["class"][1]
            rating = word_to_num.get(rating_word, 0)
            availability = article.find("p", class_="instock availability").get_text(strip=True)
            books.append({
                "title": title,
                "price": price,
                "rating": rating,
                "availability": availability
            })
        time.sleep(1)   # Rate limit :)
    print(f"\nTotal books scraped: {len(books)}")
    return books

def store_books(book_list):  #Store a list of book dicts in the database, skipping any duplicates.
    saved = 0
    skipped = 0
    for book in book_list:
        existing = Book.get_or_none(Book.title == book["title"])
        if existing:
            skipped += 1
            continue
        Book.create(**book)
        saved += 1
    print(f"Stored {saved} books | Skipped {skipped} duplicates")

def analyze():  #Query all books from the database, load into a DataFrame, and print analysis.
    rows = [
        {
            "title": b.title,
            "price": b.price,
            "rating": b.rating,
            "availability": b.availability
        }
        for b in Book.select()
    ]
    df = pd.DataFrame(rows)
    print("\n--- Analysis Results ---------------------------")
    print(f"Total books in database: {len(df)}")
    print(f"\nPrice summary statistics:")
    print(df["price"].describe().round(2))
    print(f"\nAverage price by star rating:")
    avg_price_by_rating = df.groupby("rating")["price"].mean().round(2)
    print(avg_price_by_rating)
    print(f"\nNumber of books per star rating:")
    count_by_rating = df.groupby("rating")["title"].count()
    print(count_by_rating)
    most_expensive = df.loc[df["price"].idxmax()]
    least_expensive = df.loc[df["price"].idxmin()]
    print(f"\nMost expensive book:  '{most_expensive['title']}' at £{most_expensive['price']:.2f}")
    print(f"Least expensive book: '{least_expensive['title']}' at £{least_expensive['price']:.2f}")
    highest_rated_avg = avg_price_by_rating.idxmax()
    print(f"\nStar rating with highest average price: {highest_rated_avg} stars "
          f"(£{avg_price_by_rating[highest_rated_avg]:.2f} avg)")
    print("-----------------------------------------------------\n")
    return df

def visualize(df):  # Create and save a bar chart of average book price by star rating.
    avg_price = df.groupby("rating")["price"].mean().round(2)
    plt.figure(figsize=(8, 5))
    plt.bar(avg_price.index, avg_price.values, color="steelblue", edgecolor="black")
    plt.title("Average Book Price by Star Rating")
    plt.xlabel("Star Rating (1 = Lowest, 5 = Highest)")
    plt.ylabel("Average Price (£)")
    plt.xticks(avg_price.index)
    plt.tight_layout()
    plt.savefig("price_by_rating.png")
    plt.show()
    plt.clf()
    print("Chart saved to price_by_rating.png")

def main():
    db.connect()
    db.create_tables([Book])
    books = scrape_books(num_pages=5)
    store_books(books)
    df = analyze()
    visualize(df)
    db.close()

main()
# End!!