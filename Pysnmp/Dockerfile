FROM python:2.7.14-slim
RUN apt-get update
RUN apt-get install gcc -y
RUN pip install pysnmp==4.2.5 \
pyasn1==0.1.9 \
pyYaml
COPY src /app
EXPOSE 162/udp
WORKDIR /app/bin
ENTRYPOINT ["python","v3-multiple-users.py","-f","/app/config"]
