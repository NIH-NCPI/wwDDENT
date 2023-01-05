FROM python:3.11.1-alpine3.17
WORKDIR /usr/src/app
EXPOSE 3001
ENV FLASK_APP=ddentapp
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
RUN apk update && \
     apk add bash && \
     apk add git
COPY requirements.txt requirements.txt
# I don't know why requests isn't getting installed by 
# the downstream library's requirements. So, we are forcing it here.
RUN pip install requests
RUN pip install -r requirements.txt
COPY . .
#CMD ["flask run"]
CMD ["bash"]

