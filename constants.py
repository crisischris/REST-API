######################## Tables ########################
users = "users"
listings = "listings"
favorites = "favorites"

################## Content Validation ##################
user_properties = ['UID', 'fname', 'lname', 'agency']
listing_properties = ['price', 'square_feet', 'bedrooms', 'bathrooms', 'keywords', 'type', 'representative']
favorites_properties = ['LID', 'comments', 'strength']

######################## Errors ########################
error_400 = {"Error": "The request object is not formatted correctly, see specifications"}
error_403 = {"Error": "You are forbidden"}
error__404 = {"Error": "No listing with that id exists"}

error_405 = {"Error": "Not an acceptable method"}
error_406 = {"Error": "Server expects application/json Content-Type"}
error_415 = {"Error": "Not an acceptable media type"}

error_user_401 = {"Error": "You are not authorized"}
error_user_403 = {"Error": "You are not authorized or resource already exists"}

error_listing_401 = {"Error": "You are not authorized"}
error_listing_404 = {"Error": "No listing with that id exists"}

error_favorite_403 = {"Error": "This listing is already in your favorites"}
error_favorite_404 = {"Error": "No favorite with that id exists"}

json = "application/json"
html = "text/html"

################ Endpoints etc ######################
self_url = '{{your URL here}}'
url = '{{your URL here}}/login'
googleAuthEndpoint = 'https://accounts.google.com/o/oauth2/v2/auth?'
expectedArgs = {'state','code','prompt','scope','authuser','hd'}
oauth2 = 'https://oauth2.googleapis.com/token?'
peopleAPI='https://people.googleapis.com/v1/people/me?personFields=names&access_token='

######################## SECRETS ########################
client_id = '{{your OAuth client ID api key here}}'
client_secret = '{{your OAuth client secret here}}'
secret_key = '{{your flask session secret here}}'
