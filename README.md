# Roommate Matching and Renting Website

This is a renting webiste which uses AI model match roommates. It also provide real-time notification about latest suitable houses for users. 

Website : https://rentright.info/login

Test account :
* Email : ray67672@gmail.com
* password : 12345678

----

## Data Collection 
Extract
* Use **Selenium** as a Web Crawler tool to get data from “好房網” “樂租網”
* Put Selenium into AWS **lambda** which has event trigger and time schedule function
* Use **S3** to store rent house URL and house detail information as backup

Transform
* Houses data will be transformed into vector by **one-hot encoding**, and filter irrelevant content

Load
* Load in **Atlas MongoDB**

## Website Feature 

Search
* Filters to search houses such as “Budget”, “House Age”, “Zone”, “Park”

User Profile
* User basic information such as “Job”, “Gender”, “Introduction”
* User daily routine such as “Sleep time”, “Hygiene Tolerance”, “Noise Tolerance”
* Each user’s information will be transformed by one-hot encoding

Track System
* Track users’ saved and clicked houses
* Track users’ number of friends and cancelled count
* Above condition will be calculated as “active_status”

Recommend Houses
* Use KDTree to recommend similar houses base on user click
* Base on information by track system to recommend customized houses "AI GO"
![AI GO](image/track_user.png)

Chatroom
* Use **KDTree** model to find matched roommates
* Match priority will be ranked by user’s active_status
* Use **socketIO** to allow users communicate with each other
![Match User](image/match_user.png)

Line Notification
* Send notification task through **Redis** served as a queue to organize tasks
* Use **Celery** framework to run in background to get up-to-date houses from MongoDB, which can offload backend server
* Use **Line Notify API** to send customized houses

Other 
* Use **Cloudwatch** Check EC2 CPU utilization and Memory usage as well as lambda health status
* Use **Github Action** to auto deploy code to EC2
* Use **NGINX** Load balance and reverse proxy

----


----
## Structure
![Structure](image/structure.png)