# Use the pulled image as the base image
FROM umihico/aws-lambda-selenium-python:3.12.2-selenium4.20.0-chrome124.0.6367.91

RUN mkdir -m 777 log/
RUN mkdir -m 777 data/

COPY main.py ./
COPY good_info_mgdb.py ./
COPY house_data_process.py ./


RUN pip install python-dotenv
RUN pip install boto3
RUN pip install pymongo

# Set the entry point to one of your crawler files
CMD [ "main.handler" ]
