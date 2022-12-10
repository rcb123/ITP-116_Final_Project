# NAME: Reza Banankhah
# ID: 7205660407
# DATE: 2022-11-15
# DESCRIPTION: A movie library tracker created in Python using SQL and Cinemagoer.
#              Uses data from IMDb to create a database of a user's watched movies
#              and those that they want to watch. Users can search through their
#              library, mark movies as watched, view information about movies, and
#              add notes to movies.

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
    # Creates a new table
    c.execute('''CREATE TABLE IF NOT EXISTS movies 
                 (title TEXT, year INT, runtime INT, 
                 genres TEXT, director TEXT,
                 plot TEXT, poster TEXT,
                 imdb_rating TEXT, imdb_votes TEXT,
                 watched BOOLEAN, notes TEXT)''')

    # Commits changes to file
    conn.commit()


def add_movie(title):
    ia = Cinemagoer()
    results = []
    # Sometimes the request returns an empty list, so keep trying until it works
    x = 0
    while not results:
        try:
            # Search for movie based on title, limit number of search results to 20
            results = ia.search_movie(title, 20)
            x += 1
            # Since it will keep trying until it gets a result (due to strange behavior),
            # make a limit to how many requests it will make before it gives up
            if x > 20:
                print("ERROR! Search timed out. Please try again or check to see if you spelled the title correctly.")
                return
        # Throw an error if applicable
        except (IMDbError, IOError, HTTPError) as error:
            print(error)

    # Get the user's choice from the results
    movie_index = movie_selection_menu(results, ia)

    # If user does not choose a movie, return
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
        c.execute("INSERT INTO movies VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (m_title, m_year, m_runtime, m_genres, m_directors, m_plot, m_poster,
                   m_imdb_rating, m_imdb_votes, False, None))
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


# Adds a note to a movie
def add_note(title):
    # Get movie using title
    c.execute("SELECT * FROM movies WHERE title=?", (title,))
    movie = c.fetchone()
    # Check if movie was found
    if movie is None:
        print(f"Error! Couldn't find \"{title}\". Check the title and try again.")
        return
    note = input("Please enter the note you would like to leave for this movie:\n")
    # If no note is left, do nothing
    if note is None:
        print("Nothing was entered for the note! The database will not be changed.")
        return
    # Otherwise, update the database
    print(f"Updating the note for \"{title}\". Check database for changes.")
    c.execute("UPDATE movies SET notes=? WHERE title=?", (note, title))
    # Commit changes
    conn.commit()


def print_info(movie):
    # This function only works for movies already in the database
    print(f"Title: {movie[0]}")
    print(f"Year Released: {movie[1]}")
    # Because sometimes movies do not have all the data, check to see which fields are actually filled
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
    # movie[8] is the number of IMDb Votes, unused
    print("Watched: " + str(movie[9] == 1))
    if movie[10] is not None:
        print(f"User Notes:\n{movie[10]}")


def print_imdb_info(movie):
    # This function works for movies retrieved directly from IMDb
    print(f"Title: {movie['title']}")
    if 'year' in movie:
        print(f"Year Released: {movie['year']}")
    else:
        print("Year unavailable")
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
        try:
            # 'rindex' is used to get the higher quality movie cover
            poster = poster[:poster.rindex('@') + 1]
        # Only very old movies have a different url scheme and
        # throw substring value errors, just ignore the 'rindex'
        except:
            pass
        print(f"Poster Image: {poster}")
    elif 'cover' in movie:
        poster = movie['cover']
        try:
            poster = poster[:poster.rindex('@') + 1]
        except:
            pass
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


# View all movies in the library, tell user if library is empty
def view_all():
    c.execute("SELECT * FROM movies")
    results = c.fetchall()
    if not results:
        print("\nNo movies currently in the library. "
              "Add a movie using the \"Add movie\" option.")
        return
    print_helper(results)
    input("\nPress any key to continue: ")


# Search for movies by title
def search_title(title):
    c.execute("SELECT * FROM movies WHERE title LIKE ?", ('%'+title+'%',))
    results = c.fetchall()
    print_helper(results)


# Search for movies by director
def search_director(director):
    c.execute("SELECT * FROM movies WHERE director LIKE ?", ('%'+director+'%',))
    results = c.fetchall()
    print_helper(results)


# Search for movies by genre
def search_genre(genre):
    c.execute("SELECT * FROM movies WHERE genres LIKE ?", ('%'+genre+'%',))
    results = c.fetchall()
    print_helper(results)


# Search for movies by release year
def search_year(year):
    c.execute("SELECT * FROM movies WHERE year=?", (year,))
    results = c.fetchall()
    print_helper(results)


# Helps format printing of results
def print_helper(results):
    if not results:
        print("\nNo movies found. "
              "Add a movie using the \"Add movie\" option.")
        return
    for movie in results:
        print(DIVIDER_LINE)
        print_info(movie)
    print(DIVIDER_LINE)


# Prints menu and handles user input
def menu():
    print("Please select one of the following options:\n\n"
          "1. Add movie\n"
          "2. Remove movie\n"
          "3. Mark as watched\n"
          "4. Add note to movie\n"
          "5. View movie info\n"
          "6. View all\n"
          "7. Search menu\n"
          "8. Additional Actions\n"
          "9. Exit")

    # Get user input
    choice = sanitize_choice(input(">> "))
    # Make sure it is within range
    if not (choice and 0 < choice < 10):
        print("\nERROR: Please enter a choice between 1 to 9.")

    title = ""  # Only to supress errors
    if 0 < choice < 6:
        title = input("Title: ")

    if choice == 1:
        add_movie(title)
    elif choice == 2:
        remove_movie(title)
    elif choice == 3:
        mark_watched(title)
    elif choice == 4:
        add_note(title)
    elif choice == 5:
        print()
        view_info(title)
    elif choice == 6:
        view_all()
    elif choice == 7:
        print(NEW_LINE)
        search_menu()
    elif choice == 8:
        print(NEW_LINE)
        misc_menu()
    elif choice == 9:
        print("Exiting")
        conn.close()
        sys.exit(0)

    print(NEW_LINE)


# Sub menu for searching through database
def search_menu():
    print("Please select one of the following options:\n\n"
          "1. Search by Title\n"
          "2. Search by Director\n"
          "3. Search by Genre\n"
          "4. Search by Year\n"
          "5. Go back to menu")

    # Get user choice
    choice = sanitize_choice(input(">> "))
    # Make sure it is in range
    if choice and choice < 1 or choice > 5:
        print("\nERROR: Please enter a choice between 1 to 5.")

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


# Miscellaneous options
def misc_menu():
    print("Please select one of the following options:\n\n"
          "1. Delete database\n"
          "2. Mark movie as unwatched\n"
          "3. Go back to menu")

    # Get user choice
    choice = sanitize_choice(input(">> "))
    # Make sure it is in range
    if choice < 1 or choice > 3:
        print("\nERROR: Please enter a choice between 1 to 3.")

    if choice == 1:
        print(NEW_LINE)
        confirm_choice("delete")
    elif choice == 2:
        title = input("Title: ")
        mark_watched(title, True)
    else:
        return


# Menu to show results of movie search and let user choose an option
def movie_selection_menu(results, ia) -> int:
    movie_list = []
    print("Searching...")
    i = 0
    while len(movie_list) < 10:
        movie = ia.get_movie(results[i].movieID)
        i += 1
        if i > 20:
            break
        # These checks make sure the result is not a TV show
        if 'year' not in movie:
            continue
        if 'kind' in movie and movie['kind'] != 'movie':
            continue
        else:
            movie_list.append(movie)
    print("Please select one of the following options:\n")

    # Enumerate through the results and print them out for the user
    for i, movie in enumerate(movie_list):
        print(i + 1)
        print_imdb_info(movie)
        print("\n")
        if i > 9:
            continue
    print("Press any other key to go cancel")

    # Get the user's choice
    choice = sanitize_choice(input(">> "))

    for i in range(1, 11):
        if choice == i:
            return i - 1
    return 10


# Makes sure menu choice is valid
def sanitize_choice(choice) -> int:
    if choice:
        try:
            # First strip any whitespace
            choice.strip()
            # Then convert to int
            choice = int(choice)
        except ValueError:
            print("\nERROR: Please enter a valid number.")
            return 0
        return choice
    else:
        # Handles None input
        return 0


# Used for menu options that require user confirmation
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


# Show menu indefinitely until user exits
def main():
    create_table()
    while True:
        menu()


if __name__ == "__main__":
    try:
        main()
    # Handle if the user decides to use CTRL+C to exit
    except KeyboardInterrupt:
        print('Interrupted')
        conn.close()
        sys.exit(1)
