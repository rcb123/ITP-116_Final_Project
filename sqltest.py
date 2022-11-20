from imdb import Cinemagoer
import sqlite3

conn = sqlite3.connect('movies.db')
c = conn.cursor()

c.execute('''DROP TABLE if exists movies''')
c.execute('''CREATE TABLE movies 
             (title TEXT, year INT, runtime INT, 
             genres TEXT, plot TEXT, 
             poster TEXT, imdb_rating TEXT, 
             imdb_votes TEXT,
             watched BOOLEAN)''')


def add_movie(title, year):
    ia = Cinemagoer()
    movie = ia.get_movie(title, info=["main"])

    # get movie data
    m_title = movie['title']
    m_year = movie['year']
    m_runtime = movie['runtime']
    m_genres = ",".join(movie['genres'])
    m_plot = movie['plot outline']
    m_poster = movie['cover URL']
    m_imdb_rating = movie['rating']
    m_imdb_votes = movie['votes']

    # add movie to database
    c.execute("INSERT INTO movies VALUES (?,?,?,?,?,?,?,?,?)",
              (m_title, m_year, m_runtime, m_genres, m_plot, m_poster,
               m_imdb_rating, m_imdb_votes, False))

    conn.commit()


def remove_movie(title):
    c.execute("DELETE from movies WHERE title=?", (title,))
    conn.commit()


def mark_watched(title):
    c.execute("UPDATE movies SET watched=1 WHERE title=?", (title,))
    conn.commit()


def view_movie(title):
    c.execute("SELECT * from movies WHERE title=?", (title,))
    return c.fetchone()