FROM alpine:3.17

RUN apk --update add curl bash git cargo python3 py3-pip openjdk17-jre-headless rsync zola
RUN pip install rtoml python-slugify

RUN git clone https://github.com/ppeetteerrs/obsidian-zola.git /app/obsidian-zola
RUN git clone https://github.com/knyar/athens-export.git /app/athens-export

RUN curl https://download.clojure.org/install/linux-install-1.11.1.1208.sh | bash

RUN cargo install obsidian-export
ENV PATH=/root/.cargo/bin:$PATH

RUN mkdir -p /app/src
COPY . /app/src

WORKDIR /app/src
