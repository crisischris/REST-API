# REST-API

# DataModel and general API - Overview

Overview: The user in this API is assumed as a real-estate agent. This API allows access to the user’s listings that
they have created as well as any listings they have favorited. There are three tables (see spec documentation) that
comprise this API. The user table, the listings table and the favorites tables. The relationships are as follows: The
user’s unique ID is attached to any listing that is created by the user. Each listing requires a user unique ID - this is
done automatically. Any user can favorite any listing by using the listing unique ID. When a user favorites a listing,
the user’s unique ID is attached to that favorite. Every user has their own unique favorites list that they can
request. The user can find the listings - along with the listing unique ID by querying all listings (see below).
