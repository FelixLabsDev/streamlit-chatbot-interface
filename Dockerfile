FROM python:3.12-slim

# Install git
RUN apt-get update && apt-get install -y git && apt-get clean

WORKDIR /app

COPY . /app

RUN python3 -m pip install --upgrade pip \
    && pip3 install -r requirements.txt

ARG GITHUB_TOKEN

#dont forget to add the credentials when initializing the building process.
RUN pip install git+https://$GITHUB_TOKEN@github.com/FelixLabsDev/TomerBot.git@main#egg=TomerBot . \
    && pip install -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for Flask
ENV FLASK_APP=st_server.py

# Run the Flask app
CMD ["python", "st_server.py"]