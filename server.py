from flask import Flask, render_template, request
from suggestion import *
from waitress import serve

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/suggestion', methods=['POST'])
def suggestion():
    usernamesFromPOST = request.form.get('usernames','')
    usernames = json.loads(usernamesFromPOST)

    userWatchlists = {}
    for user in usernames:
        movieList=[]
        urls = getWatchlistUrls(user)
        for url in urls:
            movieList.extend(getWatchlistMovies(url))
        userWatchlists[user] = movieList

    movieList, posters = getRandomMovie(userWatchlists, '', 1)
    print(posters)
    print(movieList)

    if movieList == []:
        return render_template('index.html')
    else:
        title = movieList[0]
        posterURL = posters[title]

    return render_template('suggestion.html',title=title,poster=posterURL)

if __name__ == "__main__":
    app.run(debug=True)