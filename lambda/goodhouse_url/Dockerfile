# Use the pulled image as the base image
FROM umihico/aws-lambda-selenium-python:3.12.2-selenium4.20.0-chrome124.0.6367.91

RUN mkdir -m 777 log/
RUN mkdir -m 777 data/


COPY main.py ./

RUN pip install python-dotenv
RUN pip install boto3


# Set the entry point to one of your crawler files
CMD [ "main.handler" ]
