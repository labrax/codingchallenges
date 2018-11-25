FROM redis:4.0.11-stretch

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get install -y python3 python3-pip
RUN apt-get install -y tmux

VOLUME /codingchallenges
WORKDIR /codingchallenges

#python3 packages
COPY requirements.txt /codingchallenges/requirements.txt
RUN python3 -m pip install -r requirements.txt

#R packages
RUN apt-get install -y r-base
#RUN Rscript -e "install.packages('')"

CMD ['redis-server']

