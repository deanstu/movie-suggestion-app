from curl_cffi import requests
import math
from bs4 import BeautifulSoup
import random
import json

# this will be sent with the request to letterboxd.com to make it look like a real user is making the request, otherwise letterboxd will block the request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://google.com" # Tells the site you found them via Google
}


def cachePosters(posterDict = {}):
    '''
    caches the movie posters URLs for all Movies already suggested.

    Args:
        posterDict (dict): A dictionary where the keys are movie and the values are the poster's URL. Will used "cleaned title".
        Dictionary format: 
            {
                "Cleaned Movie Title": "URL of poster image"
            }
    Returns:
        dict: updated dictionary of URLs
    '''
    new_data={}

    with open('posterURLs.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
    
    if posterDict == {}:
        return data
    
    with open('posterURLs.json', 'w') as file:
        for movie in posterDict:
            if movie not in data:
                new_data[movie] = posterDict[movie]
        data.update(new_data)
        json.dump(data, file, indent=4)

    return data


def getWatchlistUrls(user):
    '''
    gets the URLs of all pages in a user's watchlist.
    when a user has more than 28 movies in their watchlist, letterboxd.com will create multiple pages for the watchlist.
    This will return an empty list if the user does not have a watchlist or if the user does not exist. Does not distinguish between the two cases.

    Args:
        user (str): The username of the user whose watchlist URLs are to be retrieved.

    Returns:
        list: A list of URLs for all pages in the user's watchlist.
    '''

    baseUrl = f'https://letterboxd.com/{user}/watchlist/'
    
    html = requests.get(baseUrl, headers=headers, impersonate="chrome120")
    if html.status_code != 200:
        return []
    html = html.text

    varStart = html.find('data-num-entries')+18 # data segement in the HTML that contains the number of movies in the watchlist

    if varStart == 17: # if the string is not found, the user does not have a watchlist
        return []
    
    numOfPages = math.ceil(int(html[varStart:html.find('"', varStart)]) / 28) # letterboxed watch list has a seperate page for every 28 movies, so we need to find out how many pages there are in the watchlist

    urls = []
    urls.append(baseUrl) # add the first page of the watchlist to the list of urls, each page after is in the format baseUrl/page/{pageNum}/

    for i in range(2, numOfPages + 1):
        urls.append(f'{baseUrl}page/{i}/') # add the rest of the pages to the list of urls

    return urls


def getMoviePoster(url):
    '''
    gets the poster image from a movie page. This function will return None if the page does not exist or if there is no poster on the page.
    
    Args:
        url (str): The URL of the movie page from which to retrieve the poster image.
        
    Returns:
        str: The URL of the poster image retrieved from the movie page, or None if no poster is found.
    '''

    html = requests.get(url, headers=headers, impersonate="chrome120")
    if html.status_code != 200:
        return None
    
    varStart = str(html.text).find("https://a.ltrbxd.com/resized/film-poster")

    if varStart == -1: # if the string is not found, try something else
        varStart = str(html.text).find("https://a.ltrbxd.com/resized/sm/upload")

    if varStart == -1: # if the string is still not found, there is no poster on the page
        return None
   
    return html.text[varStart:html.text.find('"', varStart)]


def getWatchlistMovies(url):
    '''
    gets the movies from a watchlist page. This function will return an empty list if the page does not exist or if there are no movies on the page.
    
    Args:
        url (str): The URL of the watchlist page from which to retrieve the movies.
        
    Returns:
        list: A list of movie titles retrieved from the watchlist page.
    '''

    html = requests.get(url, headers=headers, impersonate="chrome120")
    if html.status_code != 200:
        return []
    soup = BeautifulSoup(html.text, 'html.parser').find_all(attrs={"data-component-class": "LazyPoster"})
    movies = []
    
    for movie in soup:
        #get title
        varStart = str(movie).find('data-item-full-display-name')+29
        title = str(movie)[varStart:str(movie).find('"', varStart)].replace('&amp;', '&') # replace &amp; with & in the title
        movies.append(title)
        
    return movies


def cleanMovieTitle(title):
    '''
    cleans a movie title to be used in a URL. This function will remove any special characters from the title and replace spaces with hyphens.
    
    Args:
        title (str): The movie title to be cleaned.
        
    Returns:
        str: The cleaned movie title.
    '''

    specialChars = ['!', '@', '#', '$', '%', '&', '*', '(', ')', '+', ':', ';', '"', ',', '.', '?', '/']

    # split from year
    title = title.lower().split(" (19")[0]
    title = title.split(" (20")[0]
    titleWords = title.split("'")
    title = "".join(titleWords)
    for c in specialChars:
        words = title.split(c)
        title = " ".join(words)
    titleWords = title.split()
    title = "-".join(titleWords)
    return title


def getRandomMovie(movies, username, numSuggestions):
    '''
    gets a random movie from a list of movies. If a username is provided, it will get a random movie from that user's watchlist. 
    If no username is provided, it will get a random movie from all users' watchlists.'

    args:
        movies (dict): A dictionary where the keys are usernames and the values are lists of movies in their watchlists.
        username (str): The username of the user whose watchlist to get a random movie from. If no username is provided, it will get a random movie from all users' watchlists.
        numSuggestions (int): The number of random movies to suggest.   

    returns:
        list: A list containing the randomly selected suggested movie(s).   
        dict: A dictionary where the keys are movie titles and the values are the URLs of their posters.
    '''

    if len(movies) == 0:
        return [],{}

    posters = {}
    cachedPosters = cachePosters() # get the cached posters from the posterURLs.json file
    toCache = {}
    returnList = []
    if username == "":
        movieList = []
        for userList in movies.values():
            movieList.extend(userList)
        numIters= numSuggestions if numSuggestions <= len(movieList) else len(movieList)
        for i in range(numIters):
            movieIndex = random.randint(0,len(movieList)-1)
            returnList.append(movieList[movieIndex]) 
            title=cleanMovieTitle(movieList[movieIndex])
            if title in cachedPosters:
                posters[movieList[movieIndex]] = cachedPosters[title] # if the poster is already cached, use the cached URL
            else:
                posterURL = getMoviePoster(f"https://letterboxd.com/film/{title}/")
                posters[movieList[movieIndex]] = posterURL # get the poster for the movie and add it to the posters dictionary
                if posterURL != None: toCache[title] = posterURL # add the poster to the toCache dictionary so it can be cached later
            movieList.pop(movieIndex) # remove the movie from the list so it doesn't get suggested again   

        cachePosters(toCache) # cache the posters for the movies that were suggested so they don't have to be retrieved again in the future
        return returnList,posters

    else:
        if username not in movies:
            return [],{}
        numIters= numSuggestions if numSuggestions <= len(movies[username]) else len(movies[username])
        for i in range(numIters):
            movieIndex = random.randint(0,len(movies[username])-1)
            returnList.append(movies[username][movieIndex])
            title=cleanMovieTitle(movies[username][movieIndex])
            if title in cachedPosters:
                posters[movies[username][movieIndex]] = cachedPosters[title] # if the poster is already cached, use the cached URL
            else:
                posterURL = getMoviePoster(f"https://letterboxd.com/film/{title}/")
                posters[movies[username][movieIndex]] =  posterURL# get the poster for the movie and add it to the posters dictionary
                if posterURL != None: toCache[title] = posterURL
            movies[username].pop(movieIndex) # remove the movie from the list so it doesn't get suggested again
                
        cachePosters(toCache)
        return returnList,posters


if __name__ == "__main__":
    print("*** Welcome to the Watchlist Randomizer ***\n\nPress enter between usernames.\nLeave blank to end the list.")

    usernames = []

    username = input("\nEnter your Letterboxd username: ")
    while(username != ""):
        usernames.append(username)
        username = input("\nEnter your Letterboxd username: ")

    if usernames == []:
        print("\nNo usersnames entered. Quiting...")
        quit()

    count = int(input("\nHow many movies should I suggest? "))

    userWatchlists = {}
    for user in usernames:
        print(f"Getting watchlist for user: {user}")
        movieList=[]
        urls = getWatchlistUrls(user)
        for url in urls:
            movieList.extend(getWatchlistMovies(url))
        userWatchlists[user] = movieList

    print("\nPicking movie!")
    movieList, posters = getRandomMovie(userWatchlists, "", count)

    if movieList == []:
        print("\nNone")
    else:
        for i in range(len(movieList)):
            print(f"\nSuggestion {i+1}: {movieList[i]}")
            if posters[movieList[i]] is not None:
                print(f"Poster URL: {posters[movieList[i]]}")
            else:
                print("No poster available for this movie.")



