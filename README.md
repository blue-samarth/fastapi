Hello this is the Readme for this fastapi webapp

How to run this ?
it would not be very difficult as their are 2 docker containers that do almost all the setup on their own

just type in `docker-compose up --build`

after this command the containers would be pretty much set up and then we just have to run them

this is intialized to run at "localhost:80" the frontend is initialized here and thus the webapp would be accessible from here 

after testing the app you can escape the containers running via ^C 
and can finally close the network by typing in `docker-compose down`
