# NAME: Reza Banankhah
# ID: 7205660407
# DATE: 2022-11-15
# DESCRIPTION: A movie library tracker created in Python using SQL and Cinemagoer.
#              Uses data from IMDb to create a database of a user's watched movies
#              and those that they want to watch. Users can search through their
#              library, mark movies as watched, and view information about movies.

from imdb import Cinemagoer, IMDbError
import sqlite3
import sys


conn = sqlite3.connect('movies.db')
c = conn.cursor()


def create_table():
    c.execute('''CREATE TABLE IF NOT EXISTS movies 
                 (title TEXT, year INT, runtime INT, 
                 genres TEXT, director TEXT,
                 plot TEXT, poster TEXT,
                 imdb_rating TEXT, imdb_votes TEXT,
                 watched BOOLEAN)''')

    conn.commit()


def add_movie(title):
    ia = Cinemagoer()
    results = []
    # Sometimes the request returns an empty list, so keep trying until it works
    while not results:
        try:
            results = ia.search_movie(title)
        # Throw an error if applicable
        except IMDbError as e:
            print(e)
    # Get the first result
    # TODO: Add a selection menu for choosing which option is correct
    movie = ia.get_movie(results[0].movieID)

    # Get movie data
    m_title = movie['title']
    m_year = movie['year']
    m_runtime = int(movie['runtime'][0])
    m_genres = ", ".join(movie['genres'])
    directors = []
    for director in movie['directors']:
        directors.append(director['name'])
    m_directors = ", ".join(directors)
    m_plot = movie['plot outline']
    m_poster = movie['cover']
    # The below line is necessary to get a full size cover instead of a thumbnail
    m_poster = m_poster[:m_poster.rindex('@') + 1]
    m_imdb_rating = movie['rating']
    m_imdb_votes = movie['votes']

    # Add movie to database
    c.execute("INSERT INTO movies VALUES (?,?,?,?,?,?,?,?,?,?)",
              (m_title, m_year, m_runtime, m_genres, m_directors, m_plot, m_poster,
               m_imdb_rating, m_imdb_votes, False))

    conn.commit()


def remove_movie(title):
    # Get movie using title
    c.execute("SELECT * FROM movies WHERE title=?", (title,))
    movie = c.fetchone()
    # Check if movie was found
    if movie is None:
        print(f"Error! Couldn't find \"{title}\". Check the title and try again.")
        return
    # Delete from database
    c.execute("DELETE FROM movies WHERE title=?", (title,))
    # Commit changes
    conn.commit()


def mark_watched(title, unwatch=None):
    # Get movie using title
    c.execute("SELECT * FROM movies WHERE title=?", (title,))
    movie = c.fetchone()
    # Check if movie was found
    if movie is None:
        print(f"Error! Couldn't find \"{title}\". Check the title and try again.")
        return
    # Update 'watched' variable to true or false
    if unwatch is None:
        print("Marking movie as watched. Check database for changes.")
        c.execute("UPDATE movies SET watched=1 WHERE title=?", (title,))
    else:
        print("Marking movie as unwatched. Check database for changes.")
        c.execute("UPDATE movies SET watched=0 WHERE title=?", (title,))
    # Commit changes
    conn.commit()


def print_info(movie):
    print(f"Title: {movie[0]}")
    print(f"Year Released: {movie[1]}")
    print(f"Runtime: {movie[2]} minutes")
    print(f"Genres: {movie[3]}")
    print(f"Director(s): {movie[4]}")
    print(f"Synopsis: {movie[5]}")
    print(f"Poster Image: {movie[6]}")
    print(f"Rating: {movie[7]}/10")
    # movie[8] is the number of IMDb Votes
    print("Watched: " + str(movie[9] == 1))


def view_info(title):
    # Get movie using title
    c.execute("SELECT * FROM movies WHERE title=?", (title,))
    movie = c.fetchone()
    # Check if movie was found
    if movie is None:
        print(f"Error! Couldn't find \"{title}\". Check the title and try again.")
        return
    print_info(movie)


def view_all():
    c.execute("SELECT * FROM movies")
    results = c.fetchall()
    if not results:
        print("\nNo movies currently in the library. "
              "Add a movie using the \"Add movie\" option.")
        return
    print_helper(results)


# Search for movies by director
def search_title(title):
    c.execute("SELECT * FROM movies WHERE title=?", (title,))
    results = c.fetchall()
    print_helper(results)


# Search for movies by director
def search_director(director):
    c.execute("SELECT * FROM movies WHERE director=?", (director,))
    results = c.fetchall()
    print_helper(results)


# Search for movies by genre
def search_genre(genre):
    c.execute("SELECT * FROM movies WHERE genre=?", (genre,))
    results = c.fetchall()
    print_helper(results)


# Search for movies by release year
def search_year(year):
    c.execute("SELECT * FROM movies WHERE year=?", (year,))
    results = c.fetchall()
    print_helper(results)


def print_helper(results):
    if not results:
        print("\nNo movies found. "
              "Add a movie using the \"Add movie\" option.")
        return
    for movie in results:
        print("------------------------------")
        print_info(movie)
    print("------------------------------")


def menu():
    print("1. Add movie")
    print("2. Remove movie")
    print("3. Mark as watched")
    print("4. View movie info")
    print("5. View all")
    print("6. Search")
    print("7. Miscellaneous actions menu")
    print("Press any other key to exit.")

    choice = sanitize_choice(input(">> "))

    newline = "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"

    if choice == 1:
        title = input("Title: ")
        add_movie(title)
    elif choice == 2:
        title = input("Title: ")
        remove_movie(title)
    elif choice == 3:
        title = input("Title: ")
        mark_watched(title)
    elif choice == 4:
        title = input("Title: ")
        view_info(title)
    elif choice == 5:
        view_all()
    elif choice == 6:
        print(f"\n{newline}\n")
        search_menu()
    elif choice == 7:
        print(f"\n{newline}\n")
        misc_menu()
    else:
        print("Exiting")
        conn.close()
        sys.exit(0)

    print(f"\n{newline}\n")


def search_menu():
    print("1. Search by Title")
    print("2. Search by Director")
    print("3. Search by Genre")
    print("4. Search by Year")
    print("Press any other key to go back to menu")

    choice = sanitize_choice(input(">> "))

    if choice == 1:
        title = input("Title: ")
        search_title(title)
    elif choice == 2:
        director = input("Director: ")
        search_director(director)
    elif choice == 3:
        genre = input("Genre: ")
        search_genre(genre)
    elif choice == 4:
        year = input("Year: ")
        search_year(year)
    else:
        return


def misc_menu():
    print("1. Delete database")
    print("2. Mark movie as unwatched")
    print("3. ")
    print("4. ")
    print("Press any other key to go back to menu")

    choice = sanitize_choice(input(">> "))

    newline = "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"

    if choice == 1:
        print(f"\n{newline}\n")
        confirm_choice("delete")
    elif choice == 2:
        title = input("Title: ")
        mark_watched(title, True)
    elif choice == 3:
        pass
    elif choice == 4:
        pass
    else:
        return


def sanitize_choice(choice) -> int:
    choice.strip()
    if choice == "":
        # goes to exit call
        return 0
    else:
        return int(choice)


def confirm_choice(choice):
    if choice == "delete":
        print("Are you sure you want to delete the movie database?\n"
              "Type \"DELETE DATABASE\" to confirm:")
        confirmation = input()
        if confirmation == "DELETE DATABASE":
            print("\nDeleting...")
            c.execute('''DROP TABLE if exists movies''')
            conn.commit()
            print("Success! Program will now exit.")
            conn.close()
            sys.exit(0)
        else:
            print("Deletion aborted.")
            return
    else:
        "Undeclared usage, please edit \"confirm_choice\" function"


def main():
    create_table()
    """
    try:
        ia = Cinemagoer()
        movies = ia.search_movie('matrix')
        print(movies)
        movie = ia.get_movie(movies[0].movieID)
        print(movie['directors'])
    except IMDbError as e:
        print(e)
    """

    """
    add_movie('The Shawshank Redemption')
    add_movie('The Godfather')
    add_movie('The Dark Knight')
    add_movie('The Godfather, Part II')
    remove_movie('The Dark Knight')
    mark_watched('The Shawshank Redemption')
    view_info('The Shawshank Redemption')
    search_director('Francis Ford Coppola')
    search_year(2008)
    """
    while True:
        menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        conn.close()
        sys.exit(1)
