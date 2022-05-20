# KKFinance
Stock Portfolio Full Stack Web App wt IEX API, build wt Flask and Jinja

# Usage
You will need to get an API key from IEX (free account registration), which lets you download stock quotes via their API (application programming interface) using URLs like 
https://cloud.iexapis.com/stable/stock/nflx/quote?token=API_KEY

With the API, run the following within a CS50 IDE's terminal: $ export API_KEY=value (value is your acquired personal API KEY)

Install Flask and it's dependencies and start Flask’s built-in web server: $ flask run

# UI Overview
The web app has built-in sessions for storing data about the current user after he makes a registration. After it, it will create a new user in the users database after making a request to it.

![alt text](https://github.com/skyllex94/KKFinance/blob/main/readme-images/6.png?raw=true)

After creating account, you will be sent to the login page and after login you will have a session created with your credentials which are encripted and stored on the back end and controlled with MySQL database.

As you are logged in, you will see a preview of all the stocks you currently own, with important information about them - by default when you open your account you will be given artificial $10K to start buying and trading stocks with.

![alt text](https://github.com/skyllex94/KKFinance/blob/main/readme-images/1.png?raw=true)

Furthermore you have functionality to search, buy and sell from your positions. The data it being fetched from the IEX API and given back to you in the form of dictionaries. From there you can manipulate them and draw on a POST or GET request on the html forms, check for correct inputs and start populating into all 3 tables - users, positions and purchases (history of all purchases.)

![alt text](https://github.com/skyllex94/KKFinance/blob/main/readme-images/2.png?raw=true)

![alt text](https://github.com/skyllex94/KKFinance/blob/main/readme-images/4.png?raw=true)

![alt text](https://github.com/skyllex94/KKFinance/blob/main/readme-images/3.png?raw=true)

All of the history has a "type" column that is of type of BOOLEAN in SQL an is responsible for recording the type of transaction that was make - either a buy or a sell and it being populated among with all the other data.


![alt text](https://github.com/skyllex94/KKFinance/blob/main/readme-images/5.png?raw=true)

The Jinja language assures an easier template build-ups and conditional and loop statements to dynamically generate the content of the page. All of the users can be viewed and managed from the database among with their positions and purchase history.

![alt text](https://github.com/skyllex94/KKFinance/blob/main/readme-images/7.png?raw=true)

