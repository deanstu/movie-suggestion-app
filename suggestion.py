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
                [letter]:
                    {"Cleaned Movie Title": "URL of poster image"}
            }
    Returns:
        dict: updated dictionary of URLs
    '''
    # just reading data
    with open('posterURLs.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
    
    if posterDict == {}:
        return data

    #writing to
    new_data={}

    with open('posterURLs.json', 'w') as file:
        for firstLetter, postersInLetter in posterDict.items():
            data.setdefault(firstLetter, {}).update(postersInLetter)
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

    htmlT = html.text

    with open("test.txt", "w") as file:
        file.write(htmlT)
    
    varStart = htmlT.find("https://a.ltrbxd.com/resized/film-poster")
    
    if varStart == -1: # if the string is not found, try something else
        section = htmlT.find("/* <![CDATA[ */")
        if section == -1:
            return None
        varStart = htmlT.find("https://a.ltrbxd.com/resized/sm/",section)

    # need to find alternative method. this link is not the poster image
    #if varStart == -1: # if the string is not found, try something else
        #varStart = str(html.text).find("https://a.ltrbxd.com/resized/sm/upload")

    if varStart == -1: # if the string is still not found, there is no poster on the page
        return None
   
    return htmlT[varStart:htmlT.find('"', varStart)]


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

    # get only list section
    htmlT = html.text
    htmlT = htmlT[htmlT.find('<div class="poster-grid"'):htmlT.find('<div class="pagination"')]
    
    soup = BeautifulSoup(htmlT, 'html.parser').find_all('li')
    movies = []
    
    for movie in soup:
        #get title
        varStart = str(movie).find('data-item-full-display-name')+29
        title = str(movie)[varStart:str(movie).find('"', varStart)].replace('&amp;', '&') # replace &amp; with & in the title

        #get URL Name (might include year, don't have to clean)
        varStart = str(movie).find('data-item-slug')+16
        title = title + "^" + str(movie)[varStart:str(movie).find('"', varStart)]
        movies.append(title)
        
    return movies


# OBSOLETE: made oboslete by additon of 'data-item-slug' in getWatchlistMovies
def cleanMovieTitle(title):
    '''
    cleans a movie title to be used in a URL. This function will remove any special characters from the title and replace spaces with hyphens.
    
    Args:
        title (str): The movie title to be cleaned.
        
    Returns:
        str: The cleaned movie title.
    '''

    specialChars = ['!', '@', '#', '$', '%', '&', '*', '(', ')', '+', ':', ';', '"', ',', '.', '?', '/']

    # split from year ex: 'Milk (2008)'
    year = int(title[-5:-1])
    title = title[:-7].lower()
    titleWords = title.split("'")
    title = "".join(titleWords)
    for c in specialChars:
        words = title.split(c)
        title = " ".join(words)
    titleWords = title.split()
    title = "-".join(titleWords)

    #test to see if year is needed

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

    # set movieList
    if username == "":
        movieList = []
        for userList in movies.values():
            movieList.extend(userList)
    else:
        if username not in movies:
            return [],{}
        movieList = movies[username]
    numIters= numSuggestions if numSuggestions <= len(movieList) else len(movieList)
    for i in range(numIters):
        movieIndex = random.randint(0,len(movieList)-1)
        fullTitle = movieList[movieIndex].split('^')[0]
        urlTitle=movieList[movieIndex].split('^')[1]
        firstLetter=urlTitle[0]
        returnList.append(fullTitle) 
        if urlTitle in cachedPosters.get(firstLetter, {}):
            posters[fullTitle] = cachedPosters[firstLetter][urlTitle] # if the poster is already cached, use the cached URL
        else:
            posterURL = getMoviePoster(f"https://letterboxd.com/film/{urlTitle}/")
            posters[fullTitle] = posterURL # get the poster for the movie and add it to the posters dictionary
            if posterURL is not None: 
                toCache.setdefault(firstLetter, {})[urlTitle] = posterURL # add the poster to the toCache dictionary so it can be cached later
        movieList.pop(movieIndex) # remove the movie from the list so it doesn't get suggested again
    if toCache !={}:       
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
    
    # test data usernames = ["deanonfilm","emilykaloudis","jessetheeph","delaneywoods","amandamccombs"]
    # test count=6000

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
            print()
            if posters[movieList[i]] != None:
                print(f"Poster URL: {posters[movieList[i]]}")
            else:
                print("No poster available for this movie.")