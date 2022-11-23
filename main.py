# NAME: Reza Banankhah
# ID: 7205660407
# DATE: 2022-11-15
# DESCRIPTION: A movie library tracker created in Python using SQL and Cinemagoer.
#              Uses data from IMDb to create a database of a user's watched movies
#              and those that they want to watch. Users can search through their
#              library, mark movies as watched, and view information about movies.

# to install Cinemagoer, run 'pip install git+https://github.com/cinemagoer/cinemagoer'
from imdb import Cinemagoer, IMDbError
from urllib.error import HTTPError
import sqlite3
import sys

# Connect to SQL3 Database
conn = sqlite3.connect('movies.db')
# Declare cursor
c = conn.cursor()

# Global Variables
NEW_LINE = "\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+\n"
DIVIDER_LINE = "------------------------------"


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
            # For some reason I'm getting HTTP 403/405 Errors and IO Errors as a result
            # TODO: Fix HTTP 403/405 Error
            results = ia.search_movie(title)
        # Throw an error if applicable
        except IMDbError as e:
            print(e)
        except IOError as i:
            print(i)
        except HTTPError as h:
            print(h)

    # Get the first result
    movie_index = movie_selection_menu(results, ia)
    if movie_index == 10:
        return
    else:
        movie = ia.get_movie(results[movie_index].movieID)

    # Get movie data
    # Because sometimes keys are named similarly, need multiple checks for validity
    # keys also have aliases, but data is very inconsistent in that regard
    m_title = movie['title']
    m_year = movie['year']
    # Get the movie's runtime
    if 'runtime' in movie:
        m_runtime = movie['runtime'][0]
    elif 'runtimes' in movie:
        m_runtime = movie['runtimes'][0]
    else:
        m_runtime = None

    # Get the movie's genres
    if 'genre' in movie:
        m_genres = movie['genre']
    elif 'genres' in movie:
        m_genres = ", ".join(movie['genres'])
    else:
        m_genres = None

    # Get the movie's directors
    if 'directors' in movie:
        directors = []
        for director in movie['directors']:
            directors.append(director['name'])
        m_directors = ", ".join(directors)
    elif 'director' in movie:
        m_directors = movie['director'][0]['name']
    else:
        m_directors = None

    # Get a short plot outline of the movie
    if 'plot outline' in movie:
        m_plot = movie['plot outline']
    elif 'plot' in movie:
        m_plot = movie['plot'][0]
    else:
        m_plot = None

    # Get the poster image url and process it
    if 'cover' in movie:
        m_poster = movie['cover']
        # The below line is necessary to get a full size cover instead of a thumbnail
        m_poster = m_poster[:m_poster.rindex('@') + 1]
    elif 'cover url' in movie:
        m_poster = movie['cover url']
        m_poster = m_poster[:m_poster.rindex('@') + 1]
    else:
        m_poster = None

    # Get the movie's IMDb rating
    if 'rating' in movie:
        m_imdb_rating = movie['rating']
    else:
        m_imdb_rating = None

    # Get the movie's IMDb votes
    # This may be helpful in excluding search results of extremely obscure movies
    # Could also sort movies by votes and such
    if 'votes' in movie:
        m_imdb_votes = movie['votes']
    else:
        m_imdb_votes = None

    # Check to see if movie is already in database
    # Get movie using title
    c.execute('''SELECT * FROM movies WHERE title=? AND year=? AND runtime=? AND genres=?
              AND director=? AND plot=? AND poster=? AND imdb_rating=? AND imdb_votes=?''',
              (m_title, m_year, m_runtime, m_genres, m_directors, m_plot, m_poster,
               m_imdb_rating, m_imdb_votes,))
    movie_search = c.fetchone()
    # Only add movie into database if no duplicates are found
    if movie_search is None:
        # Add movie to database
        c.execute("INSERT INTO movies VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (m_title, m_year, m_runtime, m_genres, m_directors, m_plot, m_poster,
                   m_imdb_rating, m_imdb_votes, False))
        print(f"\n\"{m_title}\" has been added to the database successfully!")
        conn.commit()
    else:
        print(f"\nError! \"{m_title}\" is already in the library!\nPlease try again.")
        return


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
    print(f"\"{title}\" has been removed from the database!")
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
    # 'unwatch' is used to mark a movie as unwatched
    if unwatch is None:
        print("\nMarking movie as watched. Check database for changes.")
        c.execute("UPDATE movies SET watched=1 WHERE title=?", (title,))
    else:
        print("\nMarking movie as unwatched. Check database for changes.")
        c.execute("UPDATE movies SET watched=0 WHERE title=?", (title,))
    # Commit changes
    conn.commit()


def print_info(movie):
    # This function only works for movies already in the database
    print(f"Title: {movie[0]}")
    print(f"Year Released: {movie[1]}")
    if movie[2] is None:
        print("Runtime unavailable")
    else:
        print(f"Runtime: {movie[2]} minutes")
    if movie[3] is None:
        print("Genres unavailable")
    else:
        print(f"Genres: {movie[3]}")
    if movie[4] is None:
        print("Directors unavailable")
    else:
        print(f"Director(s): {movie[4]}")
    if movie[5] is None:
        print("Synopsis unavailable")
    else:
        print(f"Synopsis: {movie[5]}")
    print(f"Poster Image: {movie[6]}")
    if movie[7] is None:
        print("Rating unavailable")
    else:
        print(f"Rating: {movie[7]}/10")
    # movie[8] is the number of IMDb Votes
    print("Watched: " + str(movie[9] == 1))


def print_imdb_info(movie):
    # This function works for movies retrieved directly from IMDb
    print(f"Title: {movie['title']}")
    print(f"Year Released: {movie['year']}")
    if 'runtime' in movie:
        print(f"Runtime: {movie['runtime'][0]} minutes")
    elif 'runtimes' in movie:
        print(f"Runtime: {movie['runtimes'][0]} minutes")
    else:
        print("Runtime unavailable")
    genres = ", ".join(movie['genres'])
    print(f"Genres: {genres}")
    if 'directors' in movie:
        directors = []
        for director in movie['directors']:
            directors.append(director['name'])
        m_directors = ", ".join(directors)
        print(f"Directors: {m_directors}")
    elif 'director' in movie:
        print(f"Directors: {movie['director'][0]['name']}")
    else:
        print("Directors unavailable")
    if 'plot outline' in movie:
        print(f"Synopsis: {movie['plot outline']}")
    elif 'plot' in movie:
        print(f"Synopsis: {movie['plot'][0]}")
    else:
        print("Synopsis unavailable")
    if 'cover url' in movie:
        poster = movie['cover url']
        poster = poster[:poster.rindex('@') + 1]
        print(f"Poster Image: {poster}")
    elif 'cover' in movie:
        poster = movie['cover']
        poster = poster[:poster.rindex('@') + 1]
        print(f"Poster Image: {poster}")
    else:
        print("Poster Image unavailable")
    if 'rating' in movie:
        print(f"Rating: {movie['rating']}/10")
    else:
        print("Rating unavailable")
    # movie['rating'] is the number of IMDb Votes


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
    input("\nPress any key to continue: ")


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
        print(DIVIDER_LINE)
        print_info(movie)
    print(DIVIDER_LINE)


def menu():
    print("Please select one of the following options:\n\n"
          "1. Add movie\n"
          "2. Remove movie\n"
          "3. Mark as watched\n"
          "4. View movie info\n"
          "5. View all\n"
          "6. Search menu\n"
          "7. Additional Actions\n"
          "Press any other key to exit.")

    choice = sanitize_choice(input(">> "))

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
        print()
        view_info(title)
    elif choice == 5:
        view_all()
    elif choice == 6:
        print(NEW_LINE)
        search_menu()
    elif choice == 7:
        print(NEW_LINE)
        misc_menu()
    else:
        print("Exiting")
        conn.close()
        sys.exit(0)

    print(NEW_LINE)


def search_menu():
    # TODO: ensure that only movies appear
    # TV shows have different keys and cause issues
    print("Please select one of the following options:\n\n"
          "1. Search by Title\n"
          "2. Search by Director\n"
          "3. Search by Genre\n"
          "4. Search by Year")
    # TODO: Add top 100/250 option
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
    print("Please select one of the following options:\n\n"
          "1. Delete database\n"
          "2. Mark movie as unwatched\n"
          "Press any other key to go back to menu")

    choice = sanitize_choice(input(">> "))

    if choice == 1:
        print(NEW_LINE)
        confirm_choice("delete")
    elif choice == 2:
        title = input("Title: ")
        mark_watched(title, True)
    else:
        return


def movie_selection_menu(results, ia) -> int:
    movie_list = []
    print("Searching...")
    for i in range(10):
        movie = ia.get_movie(results[i].movieID)
        movie_list.append(movie)
    print("Please select one of the following options:\n")
    for i, movie in enumerate(movie_list):
        print(i + 1)
        print_imdb_info(movie)
        print("\n")
        if i > 9:
            continue
    print("Press any other key to go cancel")

    choice = sanitize_choice(input(">> "))

    for i in range(1, 11):
        if choice == i:
            return i - 1
    return 10


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
        print(f"Undeclared usage of the \"confirm_choice\" function. Please submit a bug report. Choice = {choice}")


def main():
    create_table()
    while True:
        menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        conn.close()
        sys.exit(1)
