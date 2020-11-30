from google.cloud import datastore
from flask import Flask, session, request, Response, jsonify, make_response, render_template
import requests
import json
import random
import string
from google.auth import jwt

##my files
import constants

app = Flask(__name__)
app.secret_key = constants.secret_key
client = datastore.Client()

##############################################################
################### start helper methods ###################
##############################################################
#fetches a specific user by id
def fetch_single_user(id):
    user_key = client.key(constants.users, int(id))
    user = client.get(user_key)
    if not user:
        user = {}
        return user

    user['id'] = user.key.id
    user['self'] = constants.self_url + '/user/'+str(user.key.id)

    return user

#fetches all users on the app
def fetch_all_users():
    query = client.query(kind=constants.users)
    users = query.fetch(limit=1000)

    list = []
    for user in users:
            user['id'] = user.key.id
            user['self'] = constants.self_url + '/users/'+str(user.key.id)
            list.append(user)

    return list

#This method returns a single user from all users using the JWT sub propoerty
def fetch_user_using_UID(user):
    #parse the user
    users = fetch_all_users()
    ID = None
    for usr in users:
        #finding matching unique ID
        if usr['UID'] == user:
            ID = usr.key.id
    #update the user
    user = fetch_single_user(int(ID))
    return user

#This method checks uniqueness of user profiles
def checkUniqueUser(UID):
    query = client.query(kind=constants.users)
    users = query.fetch(limit=1000)

    for user in users:
            if user['UID'] == UID:
                #found user
                return False
    #user is unique
    return True

#fetches a specific favorite by id
def fetch_single_favorite(id):
    listing_key = client.key(constants.favorites, int(id))
    listing = client.get(listing_key)
    if not listing:
        listing = {}
        return listing

    listing['id'] = listing.key.id

    #we want to point the 'self' to the actual listing
    listing['self'] = constants.self_url + '/listings/'+str(listing.key.id)

    return listing


#fetches a specific favorite by id
def fetch_single_user_favorite(user, LID):
    query = client.query(kind=constants.favorites)
    favorites = query.fetch(limit=1000)

    #build the user list
    fav = {}
    for favorite in favorites:
        if favorite['UID'] == user and favorite['LID'] == LID:
            favorite['self'] = constants.self_url + '/listings/'+str(LID)
            fav = favorite

    return fav

#fetches a specific lisitng by id
def fetch_single_listing(id):
    listing_key = client.key(constants.listings, int(id))
    listing = client.get(listing_key)
    if not listing:
        listing = {}
        return listing

    listing['id'] = listing.key.id
    listing['self'] = constants.self_url + '/listings/'+str(listing.key.id)

    return listing

#fetches a specific user by id
def fetch_user_listings(user, offset, limit):
    query = client.query(kind=constants.listings)
    listings = query.fetch(limit=1000)
    numEntities = 0

    #build the user list
    list = []
    for listing in listings:
        if listing['representative'] == user['UID']:
            listing['id'] = listing.key.id
            listing['self'] = constants.self_url + '/listings/'+str(listing.key.id)
            list.append(listing)
            numEntities+=1

    #determine the amount left to page through
    newList = []

    for i in range(offset, min(numEntities,offset+limit)):
        if list[i]:
            newList.append(list[i])

    numEntities-=offset

    #user is unique
    return newList, numEntities


#fetches a specific user by id
def fetch_all_listings(offset, limit):
    query = client.query(kind=constants.listings)
    listings = query.fetch(limit=1000)

    #count the entities
    numEntities = 0
    for l in listings:
        numEntities+=1

    #determine the amount left to page through
    numEntities -= offset
    listings = query.fetch(limit=limit, offset=offset)

    list = []
    for listing in listings:
        listing['id'] = listing.key.id
        listing['self'] = constants.self_url + '/listings/'+str(listing.key.id)
        list.append(listing)
    #user is unique
    return list, numEntities

#fetches a specific user by id
def fetch_user_favorites(user, offset, limit):
    query = client.query(kind=constants.favorites)
    favorites = query.fetch(limit=1000)
    numEntities = 0

    #build the user list
    list = []
    for favorite in favorites:
        if favorite['UID'] == user:
            # favorite = fetch_single_listing(int(favorite['LID']))
            # favorite['id'] = favorite.key.id
            favorite['self'] = constants.self_url + '/listings/'+str(favorite['LID'])
            list.append(favorite)
            numEntities+=1

    #determine the amount left to page through
    newList = []

    for i in range(offset, min(numEntities,offset+limit)):
        if list[i]:
            newList.append(list[i])

    numEntities-=offset

    #user is unique
    return newList, numEntities

#confirms the entry is unique in the user's favorite
def confirmUniqueFavorite(user, id):
    query = client.query(kind=constants.favorites)
    favorites = query.fetch(limit=1000)

    userFavorites = []

    for listing in favorites:
        if listing['UID'] == user and listing.key.id == id:
            return False

    return True


#use this for OAuth
def generateState():
    state = ""
    for i in range(20):
        state += random.choice(string.ascii_letters)
    return state

#check for valid or any JWT
def checkJWT(req):
    tkn=''
    for r in req:
        if r[0] == 'Authorization':
            tkn=req['Authorization']

    if tkn == '':
        return False
    else:
        tkn = tkn.split('Bearer ')
        return tkn[1]

#make the response with this method
def makeRep(content, mimetype, status_code):
    rep = make_response(content)
    rep.mimetype = mimetype
    rep.status_code = status_code

    return rep

def decodeUser(JWT):
    sub = jwt.decode(JWT, verify=False)
    user = sub['sub']
    return user

def validateUserContent(content):
    for key in content:
        if key != 'agency':
            return False
    return True

def validateUserPatchContent(content):
    for key in content:
        if key == 'UID':
            return False
        if key not in constants.user_properties:
            return False
    return True

def validateUserPutContent(content):
    count = len(constants.user_properties)-1
    for key in content:
        if key not in constants.user_properties:
            return False
        count-=1

    #bad content
    if count != 0:
        return False
    else:
        return True

#make sure that all keys given in content is acceptable for PATCH
def validateListingPatchContent(content):
    for key in content:
        if key not in constants.listing_properties:
            return False
    return True

#make sure that all keys given in content is acceptable for PATCH
def validateFavoritePatchContent(content):
    for key in content:
        if key not in constants.favorites_properties:
            return False
    return True

def validateListingContent(content):
    count = len(constants.listing_properties)-1
    for key in content:
        if key not in constants.listing_properties:
            return False
        count-=1

    #bad content
    if count != 0:
        return False
    else:
        return True

def validateFavoritesContent(content):
    count = len(constants.favorites_properties)
    for key in content:
        if key not in constants.favorites_properties:
            return False
        count-=1

    #bad content
    if count != 0:
        return False
    else:
        return True

def updateUserObject(user, content):
    #update the profile
    for key in content:
        user[key] = content[key]

    return user

#use this method to update the object via PUT or PATCH
def updateListingObject(listing, content,):
    #update the profile
    for key in content:
        listing[key] = content[key]

    return listing

#use this method to update the object via PUT or PATCH
def updateFavoriteObject(favorite, content,):
    #update the profile
    for key in content:
        favorite[key] = content[key]

    return favorite

#this method checks for a JWT and decodes it
def checkAuthentication(req):
    #global JWT for methods
    JWT = checkJWT(req)
    user = ''
    #detect if user is authed
    if not JWT:
        return user
    #authenticate the token
    try:
        user = decodeUser(JWT)
    except:
        return user
    return user


def deleteFromFavorites(id):
    #wipe the favorites
    query = client.query(kind=constants.favorites)
    favorites = query.fetch(limit=1000)

    for favorite in favorites:
        if favorite['LID'] == id:
            favorite = client.key(constants.favorites, favorite.key.id)
            client.delete(favorite)

#delete a single favorite from user favorites
def deleteUserFavorite(user, id):
    query = client.query(kind=constants.favorites)
    favorites = query.fetch(limit=1000)
    check = False
    for favorite in favorites:
        if favorite['UID'] == user and favorite['LID'] == id:
            favorite = client.key(constants.favorites, favorite.key.id)
            client.delete(favorite)
            check = True

    return check

##############################################################
#################### end helper functions ####################
##############################################################
@app.errorhandler(405)
def handle_405():
    allow = "POST, GET"
    return makeRep(constants.error_405, constants.json, 405, allow)

@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        stateString = generateState()
        c_id = "client_id="+constants.client_id
        redirect = "redirect_uri="+constants.url
        response_type = 'response_type=code'
        scope = 'scope=profile'
        state = 'state='+stateString

        #build the url
        url = constants.googleAuthEndpoint
        url= url+c_id+'&'+redirect+'&'+response_type+'&'+scope+'&'+state
        #set the session
        session['state'] = stateString
        return render_template('index.html', url=url)


##############################################################
#################### start /boats routes  ####################
##############################################################
#create a auth route, confirm user has credentials, then validate
@app.route('/login', methods=['GET'])
def User():
    if request.method == 'GET':
        #bad args
        for i in request.args:
            if i not in constants.expectedArgs:
                return render_template('login.html', error='You are not authorized, return to landing page')
        #didn't proved exptected args
        if not request.args:
                return render_template('login.html', error='You are not authorized, return to landing page')
        #validate state
        if request.args['state'] != session.get('state'):
            return render_template('login.html', error='Incorrect user state')

        else:
            #build the token for API key transfer
            base = constants.oauth2
            client_id = 'client_id=' + constants.client_id
            client_secret = 'client_secret=' + constants.client_secret
            code = 'code=' + request.args['code']
            grant_type = 'grant_type=authorization_code'
            redirect_uri = 'redirect_uri=' + constants.url

            target = base+client_id+'&'+client_secret+'&'+code+'&'+grant_type+'&'+redirect_uri

            #transfer the token for an API key
            data = requests.post(target)
            data = data.json()

            access_token = data['access_token']
            JWT = data['id_token']
            sub = decodeUser(JWT)

            req = requests.get(constants.peopleAPI+access_token)
            req = req.json()['names']
            fname = req[0]['givenName']
            lname = req[0]['familyName']


            return render_template('login.html', sub=sub, JWT=JWT, access_token=access_token, fname=fname, lname=lname)

#create a user profile
@app.route('/users', methods=['GET','POST','PATCH','PUT'])
def user_post():
    #get the request info
    content = request.get_json()
    headers = request.headers

    #Since each CRUD method requires Authentication (besides GET),
    #we can gloabally check that here

    ################## CHECK AUTHENTICATION ########################
    if request.method != 'GET':
        #valide the content-type
        if headers['Content-Type'] != 'application/json':
            return makeRep(constants.error_415, constants.json, 415)

        #catch any accept type header
        if headers['Accept'] != '*/*' and headers['Accept'] != 'application/json':
            return makeRep(constants.error_406, constants.json, 406)

        user = checkAuthentication(request.headers)
        if not user:
            return makeRep(constants.error_user_401, constants.json, 401)
    ################## END AUTHENTICATION ########################


    if request.method == 'POST':
        check = validateUserContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)

        #check for unique user
        if not checkUniqueUser(user):
            return makeRep(constants.error_user_403, constants.json, 403)

        access_token = headers['token']

        #get user profile information
        req = requests.get(constants.peopleAPI+access_token)
        try:
            req = req.json()['names']
        except:
            return makeRep(constants.error_user_401, constants.json, 401)

        fname = req[0]['givenName']
        lname = req[0]['familyName']

        #build the entry
        new_user = datastore.entity.Entity(key=client.key(constants.users))
        new_user.update({"UID": user, "fname": fname, "lname": lname, "agency":content['agency']})
        client.put(new_user)

        user = fetch_single_user(new_user.key.id)
        return makeRep(user, constants.json, 201)

    elif request.method == 'GET':
        #catch any accept type header
        if headers['Accept'] != '*/*' and headers['Accept'] != 'application/json':
            return makeRep(constants.error_406, constants.json, 406)

        users = fetch_all_users()
        results = {}
        results['results'] = users
        return makeRep(results, constants.json, 200)

    elif request.method == 'PATCH':
        #validate patch content
        check = validateUserPatchContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)

        #update the user
        user = fetch_user_using_UID(user)
        user = updateUserObject(user, content)
        client.put(user)
        return makeRep(user, constants.json, 200)

    elif request.method == 'PUT':
        #validate patch content
        check = validateUserPutContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)

        #update the user
        user = fetch_user_using_UID(user)
        user = updateUserObject(user, content)
        client.put(user)
        return makeRep(user, constants.json, 200)

    #bad method
    else:
        return makeRep(constants.error_405, constants.json, 405)

##############################################################
##################### end /users routes  #####################
##############################################################

#create listings
@app.route('/listings', methods=['GET','POST'])
def listings_get_post():
    #get the request info
    content = request.get_json()
    headers = request.headers

    ################## CHECK AUTHENTICATION ########################
    if request.method != 'GET':
        if headers['Content-Type'] != 'application/json':
            return makeRep(constants.error_415, constants.json, 415)

        user = checkAuthentication(request.headers)
        if not user:
            return makeRep(constants.error_user_401, constants.json, 401)
    ################## END AUTHENTICATION ########################

    if request.method == 'POST':

        check = validateListingContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)

        #build the entry
        new_listing = datastore.entity.Entity(key=client.key(constants.listings))
        listing = {}
        for key in content:
            listing[key] = content[key]
        #add the user
        listing['representative'] = user;

        # new_listing.update({"price": content["price"], "sqaure_feet": content["square_feet"], "bedrooms": content["bedrooms"], "bathrooms":content["bathrooms"], "keywords":content["keywords"], "type":content["type"], "representative":content["representative"]})
        new_listing.update(listing)
        client.put(new_listing)

        listing = fetch_single_listing(new_listing.key.id)
        return makeRep(listing, constants.json, 201)

    elif request.method == 'GET':
        #catch any content type header
        test =  headers['Accept']
        if test != '*/*' and test != 'application/json':
            return makeRep(constants.error_406, constants.json, 406)

        limit = 5
        args = request.args.get('page', type=int)
        if args is None:
            args = 0

        #detect if this is an authenticated user or not,
        #if not, give all listings, if so, give only user listings
        user = checkAuthentication(request.headers)
        if not user:
            listings, numEntities = fetch_all_listings(args*limit, limit)
        else:
            user = fetch_user_using_UID(user)
            listings, numEntities = fetch_user_listings(user, args*limit, limit)

        results = {}
        results['results'] = listings
        if numEntities > limit:
            results["next"] = constants.self_url+"/listings"+"?page="+str(args+1)
        #there are previous entities
        if args > 0:
            results["prev"] = constants.self_url+"/listings"+"?page="+str(args-1)

        return makeRep(results, constants.json, 200)

    #bad method
    else:
        return makeRep(constants.error_405, constants.json, 405)

#listings view - all endpoints require a JWT
@app.route('/listings/<id>', methods=['GET','PATCH','PUT', 'DELETE'])
def listings_id_modify_get(id):
    #get the request info
    content = request.get_json()
    headers = request.headers

    ################## CHECK AUTHENTICATION ########################
    if request.method == 'PUT' or request.method == 'PATCH':
        if headers['Content-Type'] != 'application/json':
            return makeRep(constants.error_415, constants.json, 415)
    #catch any accept type header
    if headers['Accept'] != '*/*' and headers['Accept'] != 'application/json':
        if request.method != 'DELETE':
            return makeRep(constants.error_406, constants.json, 406)

    user = checkAuthentication(request.headers)
    if not user:
        return makeRep(constants.error_user_401, constants.json, 401)
    ################## END AUTHENTICATION ########################

    if request.method == 'PATCH':
        #validate patch content
        listing = fetch_single_listing(int(id))
        tmp_listing = fetch_single_listing(int(id))

        if not listing:
            return makeRep(constants.error_listing_404, constants.json, 404)

        #confirm ownership
        if user != listing['representative']:
            return makeRep(constants.error_403, constants.json, 403)

        #confirm valid content given
        check = validateListingPatchContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)

        #remove self and id from listing before we send back to DB
        listing.pop('self', None)
        listing.pop('id', None)

        listing = updateListingObject(listing, content)
        client.put(listing)

        #add back keys
        listing['self'] = tmp_listing['self']
        listing['id'] = tmp_listing['id']

        return makeRep(listing, constants.json, 200)


    if request.method == 'PUT':
        #validate patch content
        listing = fetch_single_listing(int(id))
        tmp_listing = fetch_single_listing(int(id))

        if not listing:
            return makeRep(constants.error_listing_404, constants.json, 404)

        #confirm ownership
        if user != listing['representative']:
            return makeRep(constants.error_403, constants.json, 403)

        #confirm valid content given
        check = validateListingContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)

        #remove self and id from listing before we send back to DB
        listing.pop('self', None)
        listing.pop('id', None)

        listing = updateListingObject(listing, content)
        client.put(listing)

        #add back keys
        listing['self'] = tmp_listing['self']
        listing['id'] = tmp_listing['id']

        return makeRep(listing, constants.json, 200)

    if request.method == 'DELETE':
        #validate patch content
        listing = fetch_single_listing(int(id))
        if not listing:
            return makeRep(constants.error_listing_404, constants.json, 404)

        #confirm ownership
        if user != listing['representative']:
            return makeRep(constants.error_403, constants.json, 403)

        #need to delete the relationship between favorites as well
        deleteFromFavorites(int(id))

        listing = client.key(constants.listings, int(id))
        client.delete(listing)
        return makeRep('', constants.json, 204)

    if request.method == 'GET':
        #catch any accept type header
        if headers['Accept'] != '*/*' and headers['Accept'] != 'application/json':
            return makeRep(constants.error_406, constants.json, 406)

        listing = fetch_single_listing(int(id))
        if not listing:
            return makeRep(constants.error_listing_404, constants.json, 404)

        #check if listing is owned by user
        if user != listing['representative']:
            return makeRep(constants.error_403, constants.json, 403)

        return makeRep(listing, constants.json, 200)

    #bad method
    else:
        return makeRep(constants.error_405, constants.json, 405)

##############################################################
##################### end /listings routes  ##################
##############################################################


#listings view - root resource endpoints require a JWT
@app.route('/favorites', methods=['GET'])
def favorites_get():
    #get the request info
    content = request.get_json()
    headers = request.headers

    ################## CHECK AUTHENTICATION ########################
    #catch any accept type header
    if headers['Accept'] != '*/*' and headers['Accept'] != 'application/json':
        return makeRep(constants.error_406, constants.json, 406)

    user = checkAuthentication(request.headers)
    if not user:
        return makeRep(constants.error_user_401, constants.json, 401)
    ################## END AUTHENTICATION ########################

    if request.method == 'GET':
        #catch any accept type header
        if headers['Accept'] != '*/*' and headers['Accept'] != 'application/json':
            return makeRep(constants.error_406, constants.json, 406)
        limit = 5
        args = request.args.get('page', type=int)
        if args is None:
            args = 0

        favorites, numEntities  = fetch_user_favorites(user, args*limit, limit)

        results = {}
        results['results'] = favorites
        if numEntities > limit:
            results["next"] = constants.self_url+"/favorites"+"?page="+str(args+1)
        #there are previous entities
        if args > 0:
            results["prev"] = constants.self_url+"/favorites"+"?page="+str(args-1)

        return makeRep(results, constants.json, 200)

    #bad method
    else:
        return makeRep(constants.error_405, constants.json, 405)


#TODO: add in PUT / PATCH support to favorites
@app.route('/favorites/<id>', methods=['POST','PATCH','PUT','DELETE'])
def favorites_post_modify(id):
    #get the request info
    content = request.get_json()
    headers = request.headers

    ################## CHECK AUTHENTICATION ########################
    if request.method != 'DELETE':
        if headers['Content-Type'] != 'application/json':
            return makeRep(constants.error_415, constants.json, 415)

    user = checkAuthentication(request.headers)
    if not user:
        return makeRep(constants.error_user_401, constants.json, 401)
    ################## END AUTHENTICATION ########################

    if request.method == 'POST':
        #check to see if the listing is real
        listing = fetch_single_listing(int(id))
        if not listing:
            return makeRep(constants.error_listing_404, constants.json, 404)

        #make sure this isn't a duplicate
        check = confirmUniqueFavorite(user, int(id))
        if not check:
            return makeRep(constants.error_favorite_403, constants.json, 403)

        #make sure content is valid
        check = validateFavoritesContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)


        #build the entry
        new_favorite = datastore.entity.Entity(key=client.key(constants.favorites))
        favorite = {}
        for key in content:
            favorite[key] = content[key]
        #add the user
        favorite['UID'] = user;

        # new_listing.update({"price": content["price"], "sqaure_feet": content["square_feet"], "bedrooms": content["bedrooms"], "bathrooms":content["bathrooms"], "keywords":content["keywords"], "type":content["type"], "representative":content["representative"]})
        new_favorite.update(favorite)
        client.put(new_favorite)

        #add the self in
        favorite['self'] = listing['self']
        return makeRep(favorite, constants.json, 201)


    if request.method == 'PATCH':
        #validate patch content
        favorite = fetch_single_user_favorite(user, int(id))
        if not favorite:
            return makeRep(constants.error_favorite_404, constants.json, 404)

        #confirm valid content given
        check = validateFavoritePatchContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)

        favorite = updateFavoriteObject(favorite, content)
        client.put(favorite)
        return makeRep(favorite, constants.json, 200)

    if request.method == 'PUT':
        #validate patch content
        favorite = fetch_single_user_favorite(user, int(id))
        if not favorite:
            return makeRep(constants.error_favorite_404, constants.json, 404)

        #confirm valid content given
        check = validateFavoritesContent(content)
        if not check:
            return makeRep(constants.error_400, constants.json, 400)

        favorite = updateFavoriteObject(favorite, content)

        #change the self link
        favorite['self'] = constants.self_url + '/listings/'+str(content['LID'])
        client.put(favorite)
        return makeRep(favorite, constants.json, 200)


    if request.method == 'DELETE':
        #validate patch content
        check = deleteUserFavorite(user, int(id))
        if not check:
            return makeRep(constants.error_favorite_404, constants.json, 404)

        return makeRep('', constants.json, 204)


    #bad method
    else:
        return makeRep(constants.error_405, constants.json, 405)


##############################################################
##################### end /favorites routes  #################
##############################################################


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
