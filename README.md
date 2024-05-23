# Roommate Matching and Renting Website
![Static Badge](https://img.shields.io/badge/python%20-%20I%20like
)
![Static Badge](https://img.shields.io/badge/Socket.IO%20-%20purple
)
![Static Badge](https://img.shields.io/badge/Data%20-%20red
)



This is a renting webiste which uses AI model match roommates. It also provide real-time notification about latest suitable houses for users. 

Website : https://rentright.info/login

Test account :
* Username : Ray
* Email : ray67672@gmail.com
* password : 12345678

## Table of Content
- [Data Collection](#data-collection)
  - [Extract](#extract)
  - [Transform](#transform)
  - [Load](#load)
- [Website Features](#website-feature)
  - [Search](#search)
  - [Tracking System](#tracking-system)
  - [Recommend Houses](#recommend-houses)
  - [Chatroom](#chatroom)
  - [Line Notification](#line-notification)
  - [Other Features](#other-features)
- [Monitoring (CloudWatch)](#monitoring-cloudwatch)
- [Architecture](#architecture)
- [Video](#demo-video)



## Data Collection 
* Extract
    * Use **Selenium** as a Web Crawler tool to get data from “好房網” “樂租網”
    * Put Selenium into AWS **lambda** which has event trigger and time schedule function
    * Use **S3** to store rent house URL and house detail information as backup

* Transform
    * Houses data will be transformed into vector by **one-hot encoding**, and filter irrelevant content

* Load
    * Load in **MongoDB Atlas**

## Website Feature 

* Search
    * Filters to search houses such as “Budget”, “House Age”, “Zone”, “Park”
    * User Profile
    * User basic information such as “Job”, “Gender”, “Introduction”
    * User daily routine such as “Sleep time”, “Hygiene Tolerance”, “Noise Tolerance”
    * Each user’s information will be transformed by one-hot encoding

* Tracking System
    * Track users’ saved and clicked houses
    * Track users’ number of friends and cancelled count
    * Above condition will be calculated as “active_status”

* Recommend Houses
    * Use KDTree to recommend similar houses base on user click
    * Base on information by track system to recommend customized houses "AI GO"
    ![AI GO](video/AI_GO.mov)

* Chatroom
    * Use **KDTree** model to find matched roommates
    * Match priority will be ranked by user’s active_status
    * Use **socketIO** to allow users communicate with each other

* Line Notification
    * Send notification task through **Redis** served as a queue to organize tasks
    * Use **Celery** framework to run in background to get up-to-date houses from MongoDB, which can offload backend server
    * Use **Line Notify API** to send customized houses

* Other 
    * Use **Cloudwatch** Check EC2 CPU utilization and Memory usage as well as lambda health status
    * Use **Github Action** to auto deploy code to EC2
    * Use **NGINX** Load balance and reverse proxy


## Monitor (CloudWatch)
![CloudWatch](image/monitor.png)


## Architecture
![Structure](image/structure.png)



## Demo Video
[Demo Link](https://youtu.be/IXN778xn8X8)




